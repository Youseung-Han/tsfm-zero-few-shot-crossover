"""Run all actual model/dataset selectors without loading a forecasting model."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("gradio")
pytest.importorskip("matplotlib")

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("public_app", ROOT / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def test_all_selectors_and_downloads():
    import matplotlib.pyplot as plt

    from tsfm_crossover.analysis.public_results import DATASETS, MODELS

    for model in MODELS:
        for dataset in DATASETS:
            fig, seeds, means, summary, download, coverage = app.select(model, dataset)
            assert len(seeds) == 24 and len(means) == 8 and len(coverage) == 27
            assert model.upper().split("1")[0] in summary.upper()
            assert Path(download).is_file()
            assert "source_record_hash" in Path(download).read_text(encoding="utf-8")
            plt.close(fig)


def test_missing_data_is_explicit(tmp_path):
    assert app.select("ttm", "ETTh1", tmp_path / "absent.csv")[4] is None


def test_builds_blocks():
    assert app.build_app().config["components"]
