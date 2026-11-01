"""TTM/ETTh1 two-update smoke, reusing official adapters and recorded evaluation code.

This reduced run is not comparable with paper metrics. No GPU work without --execute.
"""

import argparse
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from tsfm_crossover.analysis.public_results import digest, write_json
from tsfm_crossover.experiments.main_plan import grid, load_plan
from tsfm_crossover.experiments.main_study import evaluate_final, final_windows
from tsfm_crossover.experiments.pilot import prepare_condition, stability
from tsfm_crossover.models.adapters import create_adapter
from tsfm_crossover.models.contract import parameter_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    print("SMOKE ONLY: 2 updates, 4 validation windows, 8 test windows; NOT paper reproduction")
    if not args.execute:
        return
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required for this notebook example")
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cuda.matmul.allow_tf32 = False
    root = Path.cwd()
    plan, prepared = load_plan(root, root / "configs/study/main.yaml")
    row = next(
        r
        for r in grid(plan)
        if r["family"] == "ttm"
        and r["dataset"] == "ETTh1"
        and r["seed"] == 1729
        and r["horizon"] == 96
        and r["rate"] == 0.005
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    config = SimpleNamespace(
        seed=1729,
        sampling_rate=0.005,
        num_samples=1,
        learning_rates={"ttm": [1e-4]},
        max_steps=2,
        eval_every=1,
        patience_evals=3,
        validation_windows=4,
        training_batch=1,
        checkpoint_every=1,
        selection_metric="normalized_mae",
    )
    args.output.mkdir(parents=True, exist_ok=False)
    identity = {
        "kind": "smoke_not_paper",
        "commit": commit,
        "condition": row,
        "source_sha256": {
            str(p.relative_to(root).as_posix()): digest(p)
            for p in sorted((root / "src").rglob("*.py"))
        },
        "runner_sha256": digest(__file__),
    }
    settings, selected, validating, batch, scale, provenance = prepare_condition(
        config,
        row,
        prepared["ETTh1"],
        root,
        commit,
        sampling_rates=(0.0, *plan.sampling_rates),
        protocol_frozen=False,
    )
    write_json(args.output / "identity.json", identity)
    write_json(args.output / "provenance.json", provenance)
    adapter = None
    try:

        def factory():
            instance = create_adapter(
                settings, root=root, device="cuda", cache_dir=root / ".cache/ttm"
            )
            instance.load_model()
            return instance

        adapter = factory()
        selection = {
            "identity": identity,
            "status": "selection_locked",
            "parameter_hash": parameter_hash(adapter.parameter_state()),
        }
        zero_dir = args.output / "zero"
        zero_dir.mkdir()
        write_json(zero_dir / "selection.json", selection)
        windows, test_batch, _ = final_windows(root, prepared["ETTh1"], settings, selection)
        windows = windows[:8]
        zero = evaluate_final(adapter, windows, test_batch, scale, zero_dir, identity, selection)
        # A fresh pretrained instance starts FT. Test data never enter validation/training.
        adapter.cleanup()
        adapter = factory()
        train_dir = args.output / "training"
        train_dir.mkdir()
        training = stability(
            adapter,
            config,
            selected,
            validating,
            batch,
            scale,
            train_dir,
            identity,
            provenance,
            "cuda",
        )
        checkpoint = train_dir / training["loop"]["best_checkpoint"]
        adapter.cleanup()
        adapter = factory()
        adapter.load_training_state(checkpoint)
        adapter.optimizer = None
        selection = {
            "identity": identity,
            "status": "selection_locked",
            "parameter_hash": parameter_hash(adapter.parameter_state()),
        }
        few_dir = args.output / "few"
        few_dir.mkdir()
        write_json(few_dir / "selection.json", selection)
        few = evaluate_final(adapter, windows, test_batch, scale, few_dir, identity, selection)
        if zero["window_hash"] != few["window_hash"]:
            raise RuntimeError("unpaired test samples")
        z, f = (r["metrics"]["macro"]["normalized_mae"] for r in (zero, few))
        result = {
            "status": "completed_smoke_only",
            "paper_comparable": False,
            "zero_nmae": z,
            "ft_nmae": f,
            "improvement_percent": 100 * (z - f) / z,
            "actual_steps": training["stopping_step"],
            "best_step": training["best_validation_step"],
            "test_windows": len(windows),
            "zero": zero,
            "few": few,
            "runtime": adapter.execution_metadata(),
        }
        write_json(args.output / "smoke_result.json", result)
        print(
            json.dumps(
                {k: result[k] for k in ("status", "zero_nmae", "ft_nmae", "improvement_percent")}
            )
        )
    finally:
        if adapter:
            adapter.cleanup()


if __name__ == "__main__":
    main()
