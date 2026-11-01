"""Boundary and evidence tests for the public final-paper analysis."""

import copy
import json
from pathlib import Path

import pytest

from tsfm_crossover.analysis.public_results import (
    RATES,
    SEEDS,
    analyze,
    compare_paper,
    load_conditions,
    sustained,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[2]


def rows_for(zero=(1, 10, 100), few=(0.5, 8, 110)):
    return [
        {
            "model": "ttm",
            "dataset": "ETTh1",
            "seed": seed,
            "rate": rate,
            "status": "completed",
            "nmae": z if rate == 0 else f,
        }
        for seed, z, f in zip(SEEDS, zero, few, strict=True)
        for rate in (0.0, *RATES)
    ]


def test_paired_ratios_not_ratio_of_means():
    result = analyze(rows_for())
    curve = result["curves"][0]
    assert curve["mean_relative_improvement"] == pytest.approx(0.2)
    assert curve["improvement_from_mean_errors"] < 0
    assert result["groups"][0]["mean_upper"] == 0.005
    assert result["groups"][0]["all_seed_status"] == "not_observed_on_grid"


def test_missing_seed_and_missing_rate_are_not_negative_or_zero():
    rows = rows_for()
    rows = [r for r in rows if not (r["seed"] == 2718 and r["rate"] == 0.5)]
    result = analyze(rows)
    assert result["groups"][0]["mean_status"] == "indeterminate_missing"
    assert result["groups"][0]["all_seed_status"] == "indeterminate_missing"
    curve = next(
        r
        for r in result["curves"]
        if r["model"] == "ttm" and r["dataset"] == "ETTh1" and r["rate"] == 0.5
    )
    assert curve["paired_seeds"] == 2
    assert curve["mean_relative_improvement"] is None
    assert curve["available_seed_mean"] is not None


def test_missing_zero_and_zero_baseline():
    rows = [r for r in rows_for() if not (r["seed"] == 1729 and r["rate"] == 0)]
    result = analyze(rows)
    assert result["pairs"][0]["pair_status"] == "missing_baseline"
    result = analyze(rows_for(zero=(0, 10, 100)))
    assert result["pairs"][0]["pair_status"] == "undefined_zero_baseline"
    assert result["pairs"][0]["relative_improvement"] is None


def test_sustained_reversal_strict_zero_and_last_grid():
    assert sustained([1, -1, 0, 1, 1, 1, 1, 1]) == {
        "status": "observed_on_grid",
        "lower": 0.02,
        "upper": 0.05,
    }
    assert sustained([-1] * 7 + [1])["lower"] == 0.5
    assert sustained([1] * 7 + [0])["status"] == "not_observed_on_grid"
    assert sustained([None] + [1] * 7)["status"] == "indeterminate_missing"
    assert sustained([1] * 8)["lower"] == 0


def test_failed_row_retains_missing_status():
    rows = rows_for()
    rows[1].update(status="failed", nmae=None)
    result = analyze(rows)
    assert result["pairs"][0]["pair_status"] == "missing_fine_tuning"
    assert any(r["status"] == "failed" for r in result["coverage"])


def test_public_data_matches_pdf_and_historical_analysis():
    rows = load_conditions(ROOT / "results/public/conditions.csv")
    result = analyze(rows)
    ref = json.loads((ROOT / "docs/paper-reference.json").read_text(encoding="utf-8"))
    assert len(rows) == 270
    comparison = compare_paper(result, ref)
    assert len(comparison["checks"]) == 50
    assert comparison["all_match"]
    old = json.loads(
        (ROOT / "results/summaries/primary5_h96_two_model_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    for group in old["groups"]:
        curves = [
            c
            for c in result["curves"]
            if c["model"] == group["family"] and c["dataset"] == group["dataset"]
        ]
        for new, previous in zip(curves, group["metrics"]["normalized_mae"]["curve"], strict=True):
            assert new["mean_relative_improvement"] == pytest.approx(
                previous["mean_relative_improvement"]
            )


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("duplicate", "duplicate"),
        ("nan", "invalid NMAE"),
        ("test_hash", "unpaired"),
        ("sample_hash", "sampling"),
        ("horizon", "horizon"),
        ("failed_metric", "non-completed"),
    ],
)
def test_reject_invalid_public_inputs(tmp_path, mutation, match):
    rows = load_conditions(ROOT / "results/public/conditions.csv")
    rows = copy.deepcopy(rows)
    if mutation == "duplicate":
        rows.append(rows[0])
    elif mutation == "nan":
        rows[0]["nmae"] = "nan"
    elif mutation == "test_hash":
        rows[0]["test_window_hash"] = "wrong"
    elif mutation == "sample_hash":
        rows[0]["sampling_manifest_hash"] = "wrong"
    elif mutation == "horizon":
        rows[0]["horizon"] = 192
    elif mutation == "failed_metric":
        rows[0]["status"] = "failed"
    write_csv(tmp_path / "conditions.csv", rows)
    with pytest.raises(ValueError, match=match):
        load_conditions(tmp_path / "conditions.csv")
