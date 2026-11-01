"""Normalize a new main-study run directory, retaining absent/failure/pending states.

Smoke outputs are deliberately incompatible. Never imports PDF numbers.
"""

import argparse
import json
from pathlib import Path

from reproduce_paper import select_rows

from tsfm_crossover.analysis.public_results import digest, load_conditions, write_csv, write_json
from tsfm_crossover.data.common import stable_hash
from tsfm_crossover.experiments.main_plan import load_plan


def normalize(root, directories, output):
    plan, _ = load_plan(root, root / "configs/study/main.yaml")
    rows, metadata = [], {}
    for c in select_rows(plan, "full"):
        files = [directory / c["id"] / "result.json" for directory in directories]
        files = [p for p in files if p.is_file()]
        if len(files) > 1:
            raise ValueError(f"duplicate completed condition: {c['id']}")
        row = {
            "condition_id": c["id"],
            "model": c["family"],
            "dataset": c["dataset"],
            "rate": c["rate"],
            "seed": c["seed"],
            "context": 512,
            "horizon": 96,
            "status": "unavailable",
            "nmae": None,
            "actual_optimizer_steps": None,
            "best_validation_step": None,
            "stopping_step": None,
            "selected_train_windows": None,
            "total_train_windows": None,
            "test_windows": None,
            "execution_commit": "",
            "protocol_hash": "",
            "data_sha256": "",
            "test_window_hash": "",
            "sampling_manifest_hash": "",
            "runtime_hash": "",
            "gpu": "",
            "source_review": "",
            "source_member": "",
            "source_result_path": "",
            "source_record_hash": "",
            "model_revision": "",
        }
        if files:
            path = files[0]
            record = json.loads(path.read_text(encoding="utf-8"))
            identity, test = record["identity"], record["test"]
            if identity["condition"] != c or not (
                record["status"] == "completed"
                and record["protocol_frozen"] is True
                and record["test_evaluation"] is True
                and record["external_scaler"] is False
                and record["adapter_settings"]["context"] == 512
                and test["no_update_verified"] is True
                and test["stride"] == 1
                and test["parameter_hash"] == record["selection"]["parameter_hash"]
                and identity["protocol_hash"] == stable_hash(plan.model_dump(mode="json"))
            ):
                raise ValueError(f"not a final paper-setting result: {c['id']}")
            train, data = record["training"], record["provenance"]
            row.update(
                {
                    "status": "completed",
                    "nmae": test["metrics"]["macro"]["normalized_mae"],
                    "actual_optimizer_steps": train["actual_optimizer_steps"],
                    "best_validation_step": train.get("best_validation_step"),
                    "stopping_step": train.get("stopping_step"),
                    "selected_train_windows": data["selected_train_windows"],
                    "total_train_windows": data["total_train_windows"],
                    "test_windows": test["number_of_test_windows"],
                    "execution_commit": identity["commit"],
                    "protocol_hash": identity["protocol_hash"],
                    "data_sha256": identity["data_sha256"],
                    "test_window_hash": test["window_hash"],
                    "sampling_manifest_hash": data["sampling_manifest_hash"],
                    "runtime_hash": record["runtime_hash"],
                    "gpu": record["runtime"]["gpu"],
                    "source_result_path": f"{c['id']}/result.json",
                    "source_record_hash": stable_hash(record),
                    "model_revision": identity["model_pin"]["revision"],
                }
            )
            metadata[c["id"]] = {
                "source_file_sha256": digest(path),
                "identity": identity,
                "adapter_settings": record["adapter_settings"],
                "metric_train_scale": data["metric_train_scale"],
                "target_counts": [r["count"] for r in test["metrics"]["per_channel"]],
            }
        else:
            for pattern, status in (
                ("failure-*.json", "failed"),
                ("pending-*.json", "pending_gpu"),
            ):
                evidence = [
                    p for directory in directories for p in (directory / c["id"]).glob(pattern)
                ]
                if evidence:
                    for p in evidence:
                        record = json.loads(p.read_text(encoding="utf-8"))
                        if record["identity"]["condition"] != c:
                            raise ValueError("failure/pending evidence condition mismatch")
                    row["status"] = status
                    break
        rows.append(row)
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "conditions.csv", rows)
    load_conditions(output / "conditions.csv")
    write_json(output / "condition_metadata.json", metadata)
    write_json(
        output / "provenance.json",
        {
            "source": "new main-study run directories",
            "new_model_execution_by_importer": False,
            "warning": "failure/pending is recorded evidence; final retry state is unknown",
            "files": {p.name: digest(p) for p in output.iterdir() if p.is_file()},
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    normalize(Path.cwd(), args.run_dir, args.output)
