"""Public result explorer and final-paper regeneration, without model dependencies.

The final paper defines the mean criterion using paired relative improvements.
Historical analysis.paper uses mean absolute deltas; it is intentionally unchanged.
"""

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

MODELS = ("ttm", "moirai1")
DATASETS = ("ETTh1", "ETTh2", "ETTm1", "ETTm2", "Tetouan")
SEEDS = (1729, 2718, 31415)
RATES = (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0)
STATUSES = {"completed", "failed", "not_run", "unavailable", "pending_gpu"}
LABELS = {"ttm": "TTM-R3", "moirai1": "MOIRAI 1.1-R-small"}
IDENTITY = ("execution_commit", "data_sha256", "test_window_hash", "protocol_hash")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_csv(path, rows):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def load_conditions(path):
    """Fail closed on duplicates, invalid metrics, unknown grid or mixed identities."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    lookup = {}
    for row in rows:
        row["seed"] = int(row["seed"])
        row["rate"] = float(row["rate"])
        key = row["model"], row["dataset"], row["seed"], row["rate"]
        if (
            key[0] not in MODELS
            or key[1] not in DATASETS
            or key[2] not in SEEDS
            or key[3] not in (0.0, *RATES)
        ):
            raise ValueError(f"out-of-scope condition: {key}")
        if key in lookup:
            raise ValueError(f"duplicate condition: {key}")
        if row["status"] not in STATUSES:
            raise ValueError(f"unknown status: {row['status']}")
        value = row.get("nmae", "")
        row["nmae"] = float(value) if value != "" else None
        if row["nmae"] is not None and (not math.isfinite(row["nmae"]) or row["nmae"] < 0):
            raise ValueError(f"invalid NMAE: {key}")
        if row["status"] == "completed":
            if row["nmae"] is None or any(
                not row.get(k) for k in (*IDENTITY, "sampling_manifest_hash", "model_revision")
            ):
                raise ValueError(f"completed row lacks metric/provenance: {key}")
            if int(row["horizon"]) != 96 or int(row["context"]) != 512:
                raise ValueError("context/horizon mismatch")
        elif row["nmae"] is not None:
            raise ValueError("non-completed result must not carry an NMAE")
        lookup[key] = row
    for model in MODELS:
        revisions = {
            r["model_revision"] for r in rows if r["model"] == model and r["status"] == "completed"
        }
        if len(revisions) > 1:
            raise ValueError(f"mixed model revisions: {model}")
    # Data, test targets and execution protocol must match within each dataset.
    for dataset in DATASETS:
        done = [r for r in rows if r["dataset"] == dataset and r["status"] == "completed"]
        for field in IDENTITY:
            if len({r[field] for r in done}) > 1:
                raise ValueError(f"unpaired {field}: {dataset}")
        for seed in SEEDS:
            for rate in (0.0, *RATES):
                paired = [lookup.get((model, dataset, seed, rate)) for model in MODELS]
                paired = [r for r in paired if r and r["status"] == "completed"]
                if len({r.get("sampling_manifest_hash") for r in paired}) > 1:
                    raise ValueError("models use different sampling manifests")
    return rows


def sustained(values):
    """No interpolation; missing grid values make the earliest boundary indeterminate."""
    if len(values) != len(RATES):
        raise ValueError("sustained criterion requires the full eight-rate grid")
    if any(value is None for value in values):
        return {"status": "indeterminate_missing", "lower": None, "upper": None}
    index = next((i for i in range(len(values)) if all(v > 0 for v in values[i:])), None)
    if index is None:
        return {"status": "not_observed_on_grid", "lower": None, "upper": None}
    return {
        "status": "observed_on_grid",
        "lower": 0.0 if index == 0 else RATES[index - 1],
        "upper": RATES[index],
    }


def interval_label(boundary):
    if boundary["status"] == "indeterminate_missing":
        return "indeterminate (missing results)"
    if boundary["status"] == "not_observed_on_grid":
        return "not observed on grid"
    return f"({boundary['lower'] * 100:g}, {boundary['upper'] * 100:g}]"


def analyze(rows):
    lookup = {(r["model"], r["dataset"], r["seed"], r["rate"]): r for r in rows}
    pairs, curves, groups, coverage = [], [], [], []
    for model in MODELS:
        for dataset in DATASETS:
            group_curves = []
            for rate in (0.0, *RATES):
                for seed in SEEDS:
                    row = lookup.get((model, dataset, seed, rate))
                    coverage.append(
                        {
                            "model": model,
                            "dataset": dataset,
                            "rate": rate,
                            "seed": seed,
                            "status": row["status"] if row else "unavailable",
                        }
                    )
            for rate in RATES:
                valid = []
                for seed in SEEDS:
                    zero = lookup.get((model, dataset, seed, 0.0))
                    few = lookup.get((model, dataset, seed, rate))
                    reason = "completed"
                    if not zero or zero["status"] != "completed":
                        reason = "missing_baseline"
                    elif not few or few["status"] != "completed":
                        reason = "missing_fine_tuning"
                    elif zero["nmae"] <= 0:
                        reason = "undefined_zero_baseline"
                    relative = (
                        (zero["nmae"] - few["nmae"]) / zero["nmae"]
                        if (reason == "completed")
                        else None
                    )
                    pair = {
                        "model": model,
                        "dataset": dataset,
                        "rate": rate,
                        "seed": seed,
                        "zero_nmae": zero["nmae"] if zero else None,
                        "ft_nmae": few["nmae"] if few else None,
                        "relative_improvement": relative,
                        "pair_status": reason,
                    }
                    pairs.append(pair)
                    if relative is not None:
                        valid.append(pair)
                complete = len(valid) == len(SEEDS)
                mean = statistics.fmean(p["relative_improvement"] for p in valid) if valid else None
                zero_mean = statistics.fmean(p["zero_nmae"] for p in valid) if valid else None
                few_mean = statistics.fmean(p["ft_nmae"] for p in valid) if valid else None
                curve = {
                    "model": model,
                    "dataset": dataset,
                    "rate": rate,
                    "paired_seeds": len(valid),
                    "status": "complete" if complete else "incomplete",
                    "zero_mean": zero_mean if complete else None,
                    "ft_mean": few_mean if complete else None,
                    "mean_relative_improvement": mean if complete else None,
                    "available_seed_mean": mean,
                    "improvement_from_mean_errors": (
                        (zero_mean - few_mean) / zero_mean if complete else None
                    ),
                    "seed_min": min(p["relative_improvement"] for p in valid) if complete else None,
                    "seed_max": max(p["relative_improvement"] for p in valid) if complete else None,
                }
                curves.append(curve)
                group_curves.append(curve)
            mean_bound = sustained([c["mean_relative_improvement"] for c in group_curves])
            seed_bound = sustained([c["seed_min"] for c in group_curves])
            groups.append(
                {
                    "model": model,
                    "dataset": dataset,
                    "mean_status": mean_bound["status"],
                    "mean_interval_percent": interval_label(mean_bound),
                    "all_seed_status": seed_bound["status"],
                    "all_seed_interval_percent": interval_label(seed_bound),
                    "mean_lower": mean_bound["lower"],
                    "mean_upper": mean_bound["upper"],
                    "all_seed_lower": seed_bound["lower"],
                    "all_seed_upper": seed_bound["upper"],
                }
            )
    return {"pairs": pairs, "curves": curves, "groups": groups, "coverage": coverage}


def plot_curves(curves, model=None, dataset=None):
    import matplotlib.pyplot as plt

    datasets = [dataset] if dataset else list(DATASETS)
    fig, axes = plt.subplots(len(datasets), 1, figsize=(7, 2.25 * len(datasets)), squeeze=False)
    for ax, name in zip(axes[:, 0], datasets, strict=True):
        for family, color in (("ttm", "#2563eb"), ("moirai1", "#dc6825")):
            if model and family != model:
                continue
            points = [c for c in curves if c["dataset"] == name and c["model"] == family]
            x = [100 * c["rate"] for c in points]

            def percent(key, points=points):
                return [100 * c[key] if c[key] is not None else math.nan for c in points]

            ax.plot(
                x, percent("mean_relative_improvement"), "o-", color=color, label=LABELS[family]
            )
            ax.fill_between(x, percent("seed_min"), percent("seed_max"), color=color, alpha=0.16)
        ax.set_xscale("log")
        ax.set_xticks([100 * r for r in RATES], [f"{100 * r:g}" for r in RATES])
        ax.axhline(0, color="#555555", linewidth=0.8, linestyle="--")
        ax.set_title(name, loc="left", fontsize=10)
        ax.set_ylabel("Improvement (%)")
        ax.grid(alpha=0.15)
        ax.legend(fontsize=8, loc="best")
    axes[-1, 0].set_xlabel("Selected training-window pool (%)")
    fig.suptitle("Paired-seed mean; shading = seed min-max (not a CI)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return fig


def compare_paper(result, reference):
    """Rounded PDF values are comparison targets only, never experimental inputs."""
    checks = []
    endpoints = {(c["model"], c["dataset"]): c for c in result["curves"] if c["rate"] == 1}
    groups = {(g["model"], g["dataset"]): g for g in result["groups"]}
    for ref in reference["rows"]:
        key = ref["model"], ref["dataset"]
        row = endpoints[key]
        for field, source, digits, factor in (
            ("zs", "zero_mean", 5, 1),
            ("ft100", "ft_mean", 5, 1),
            ("improvement_percent", "mean_relative_improvement", 2, 100),
        ):
            actual = row[source]
            rendered = f"{actual * factor:.{digits}f}" if actual is not None else None
            checks.append(
                {
                    "model": key[0],
                    "dataset": key[1],
                    "field": field,
                    "pdf": ref[field],
                    "computed_rounded": rendered,
                    "matches": rendered == ref[field],
                }
            )
        for field in ("mean_interval_percent", "all_seed_interval_percent"):
            checks.append(
                {
                    "model": key[0],
                    "dataset": key[1],
                    "field": field,
                    "pdf": ref[field],
                    "computed": groups[key][field],
                    "matches": groups[key][field] == ref[field],
                }
            )
    return {
        "source": reference["source"],
        "checks": checks,
        "all_match": all(c["matches"] for c in checks),
        "figure": "regenerated from original metrics; not a pixel comparison",
        "new_model_execution": False,
    }


def regenerate(input_path, output, reference=None):
    rows = load_conditions(input_path)
    result = analyze(rows)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name in ("pairs", "curves", "coverage"):
        write_csv(output / f"{name}.csv", result[name])
    table1 = []
    for c in result["curves"]:
        if c["rate"] == 1:
            table1.append(
                {
                    k: c[k]
                    for k in (
                        "model",
                        "dataset",
                        "zero_mean",
                        "ft_mean",
                        "mean_relative_improvement",
                        "improvement_from_mean_errors",
                        "paired_seeds",
                        "status",
                    )
                }
            )
    write_csv(output / "table1.csv", table1)
    write_csv(output / "table2.csv", result["groups"])
    lines = [
        "# Final paper tables",
        "",
        "Full precision: table1.csv / table2.csv.",
        "",
        "| Model | Data | ZS | FT100 | Improvement (%) |",
        "|---|---|---:|---:|---:|",
    ]
    for c in table1:

        def fmt(key, digits, factor=1, c=c):
            return "unavailable" if c[key] is None else f"{c[key] * factor:.{digits}f}"

        lines.append(
            f"| {LABELS[c['model']]} | {c['dataset']} | {fmt('zero_mean', 5)} | "
            f"{fmt('ft_mean', 5)} | {fmt('mean_relative_improvement', 2, 100)} |"
        )
    lines += ["", "| Model | Data | Mean sustained (%) | All 3 seeds (%) |", "|---|---|---|---|"]
    for g in result["groups"]:
        lines.append(
            f"| {LABELS[g['model']]} | {g['dataset']} | {g['mean_interval_percent']} | "
            f"{g['all_seed_interval_percent']} |"
        )
    (output / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fig = plot_curves(result["curves"])
    fig.savefig(output / "figure1.png", dpi=180)
    fig.savefig(output / "figure1.svg")
    svg = output / "figure1.svg"
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
    )
    import matplotlib.pyplot as plt

    plt.close(fig)
    report = {
        "input_sha256": digest(input_path),
        "available_rows": len(rows),
        "completed_conditions": sum(r["status"] == "completed" for r in rows),
        "expected_conditions": 270,
        "new_gpu_execution": False,
    }
    if reference:
        report["paper_comparison"] = compare_paper(
            result, json.loads(Path(reference).read_text(encoding="utf-8"))
        )
    write_json(output / "verification.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/public/conditions.csv"))
    parser.add_argument("--output", type=Path, required=True, help="new directory; never overwrite")
    parser.add_argument("--paper-reference", type=Path, default=Path("docs/paper-reference.json"))
    args = parser.parse_args()
    report = regenerate(args.input, args.output, args.paper_reference)
    print(
        json.dumps(
            {
                "conditions": report["completed_conditions"],
                "paper_tables_match": report["paper_comparison"]["all_match"],
                "output": str(args.output),
                "new_gpu_execution": False,
            }
        )
    )


if __name__ == "__main__":
    main()
