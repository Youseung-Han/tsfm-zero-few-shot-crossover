"""Importer preserves unavailable and observed failure evidence without fabricating scores."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tsfm_crossover.analysis.public_results import load_conditions
from tsfm_crossover.experiments.main_plan import grid, load_plan

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "import_public_runs", ROOT / "scripts/import_public_runs.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_failure_and_unavailable(tmp_path):
    plan, _ = load_plan(ROOT, ROOT / "configs/study/main.yaml")
    c = grid(plan)[0]
    directory = tmp_path / "runs" / c["id"]
    directory.mkdir(parents=True)
    (directory / "failure-one.json").write_text(json.dumps({"identity": {"condition": c}}))
    module.normalize(ROOT, [tmp_path / "runs"], tmp_path / "normalized")
    rows = load_conditions(tmp_path / "normalized/conditions.csv")
    assert len(rows) == 270
    assert sum(r["status"] == "failed" for r in rows) == 1
    assert sum(r["status"] == "unavailable" for r in rows) == 269
    assert all(r["nmae"] is None for r in rows)


def test_duplicate_completed_paths_rejected(tmp_path):
    name = "ttm-ETTh1-h96-s1729-r0"
    roots = [tmp_path / "a", tmp_path / "b"]
    for root in roots:
        (root / name).mkdir(parents=True)
        (root / name / "result.json").write_text("{}")
    with pytest.raises(ValueError, match="duplicate"):
        module.normalize(ROOT, roots, tmp_path / "out")
