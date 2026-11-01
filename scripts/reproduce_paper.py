"""Plan the exact final-paper subset, or explicitly execute it using the existing engine."""

import argparse
import json
import subprocess
from pathlib import Path

from tsfm_crossover.analysis.public_results import DATASETS, MODELS, RATES, SEEDS
from tsfm_crossover.experiments.main_plan import grid, load_plan
from tsfm_crossover.experiments.main_study import run


def select_rows(plan, scope, family=None):
    rows = [
        r
        for r in grid(plan)
        if r["dataset"] in DATASETS
        and r["horizon"] == 96
        and r["seed"] in SEEDS
        and r["family"] in MODELS
        and r["rate"] in (0.0, *RATES)
    ]
    if scope == "pair":
        rows = [
            r
            for r in rows
            if r["family"] == "ttm"
            and r["dataset"] == "ETTh1"
            and r["seed"] == 1729
            and r["rate"] in (0.0, 0.005)
        ]
    if family:
        rows = [r for r in rows if r["family"] == family]
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("pair", "full"), default="pair")
    parser.add_argument("--family", choices=MODELS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--execute", action="store_true", help="start GPU work; default is plan only"
    )
    args = parser.parse_args()
    root = Path.cwd()
    plan, prepared = load_plan(root, root / "configs/study/main.yaml")
    rows = select_rows(plan, args.scope, args.family)
    if not rows:
        raise ValueError("empty scope (the minimal pair is TTM only)")
    print(
        json.dumps(
            {"conditions": len(rows), "ids": [r["id"] for r in rows], "executing": args.execute},
            indent=2,
        )
    )
    if not args.execute:
        return
    if args.scope == "full" and not args.family:
        raise ValueError("execute each model family in its own environment using --family")
    if subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], text=True
    ).strip():
        raise ValueError(
            "GPU execution requires clean tracked source; preserve and commit reviewed work"
        )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    import os

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cuda.matmul.allow_tf32 = False
    for row in rows:
        status = run(plan, row, prepared, root, commit, args.output)
        print(row["id"], status, flush=True)
        if status not in ("completed", "skipped_completed"):
            raise RuntimeError(f"condition did not complete: {status}")
    if args.scope == "pair":
        metrics = [
            json.loads((args.output / row["id"] / "result.json").read_text(encoding="utf-8"))[
                "test"
            ]["metrics"]["macro"]["normalized_mae"]
            for row in rows
        ]
        print(
            json.dumps(
                {
                    "zero_nmae": metrics[0],
                    "ft_nmae": metrics[1],
                    "improvement_percent": (metrics[0] - metrics[1]) / metrics[0] * 100,
                }
            )
        )


if __name__ == "__main__":
    main()
