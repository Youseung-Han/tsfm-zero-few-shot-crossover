"""CPU-only Gradio explorer. No model loading, inference, credentials or uploads."""

import os
import tempfile
from pathlib import Path

import gradio as gr

from tsfm_crossover.analysis.public_results import (
    DATASETS,
    LABELS,
    MODELS,
    analyze,
    load_conditions,
    plot_curves,
    write_csv,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "results/public/conditions.csv"
LIMITS = """
### 해석과 한계 / Interpretation
- 개선 폭과 최종 NMAE는 별개입니다. Improvement and final error are different quantities.
- 0.5%는 학습 기간 전체에서 선택한 **윈도 후보 풀의 비율**입니다.
  It does not mean collecting only 0.5% of the observation period.
- ETT hourly/minute variants share two transformer sources.
  All five datasets form three source groups.
- 선은 같은 seed의 상대 개선율 평균, 음영은 seed 최소–최대입니다. 신뢰구간이 아닙니다.
- 표의 비율은 0.005=0.5%, 개선율은 0.01=1%입니다. The plot uses percent units.
- 전환 구간은 관측 격자에서만 판정합니다. 모든 비율의 3개 seed가 없으면 판정 불가입니다.
- FP32, context 512, horizon 96, temporal split 60/20/20, batch 1,
  maximum 1,000 updates, validation 64 windows every 100 updates, patience 3.
  TTM LR 1e-4; MOIRAI LR 5e-6. Full parameters; native scaling; no external scaler.
- 100%는 학습 후보 풀 전체를 허용한다는 뜻이며 전체 순회나 수렴을 뜻하지 않습니다.
- 제한된 예산, seed 3개, H96, 3개 출처군의 기술적 결과입니다.
  Do not generalize to all time series, models or budgets. Pretraining overlap was not audited.
- 저장된 실험 metric을 읽으며 실시간 추론은 수행하지 않습니다. No live inference.
"""


def select(model, dataset, data_path=DEFAULT_DATA):
    if model not in MODELS or dataset not in DATASETS:
        raise ValueError("unknown model/dataset")
    if not Path(data_path).is_file():
        return None, [], [], "실제 결과 파일 없음 / Real results unavailable", None, []
    rows = load_conditions(data_path)
    result = analyze(rows)
    group = next(g for g in result["groups"] if g["model"] == model and g["dataset"] == dataset)
    chosen = [r for r in rows if r["model"] == model and r["dataset"] == dataset]
    pairs = [r for r in result["pairs"] if r["model"] == model and r["dataset"] == dataset]
    curves = [r for r in result["curves"] if r["model"] == model and r["dataset"] == dataset]
    coverage = [r for r in result["coverage"] if r["model"] == model and r["dataset"] == dataset]
    fig = plot_curves(curves, model=model, dataset=dataset)
    summary = (
        f"**{LABELS[model]} / {dataset}** — 실제 기록 {len(chosen)}/27 조건\n\n"
        f"평균 지속 개선 / Mean: **{group['mean_interval_percent']} %**\n\n"
        f"3seed 지속 개선 / All seeds: **{group['all_seed_interval_percent']} %**\n\n"
        "관측 비율 사이의 표시 구간이며 정확한 연속 전환점은 아닙니다. "
        "‘not observed’는 기준 미충족, ‘indeterminate’는 누락으로 판정 불가입니다."
    )
    # Temporary server-side downloads; never overwrite research evidence.
    directory = Path(tempfile.mkdtemp(prefix="tsfm-display-"))
    download = directory / f"{model}-{dataset}-displayed.csv"
    # Include both displayed seed pairs and aggregate/criterion columns in one CSV.
    by_rate = {r["rate"]: r for r in curves}
    exported = []
    for pair in pairs:
        c = by_rate[pair["rate"]]
        source = next(
            (r for r in chosen if r["seed"] == pair["seed"] and r["rate"] == pair["rate"]), {}
        )
        exported.append(
            pair
            | {f"aggregate_{k}": v for k, v in c.items() if k not in {"model", "dataset", "rate"}}
            | group
            | {
                f"source_{k}": v
                for k, v in source.items()
                if k not in {"model", "dataset", "seed", "rate"}
            }
        )
    write_csv(download, exported)
    pair_columns = ("rate", "seed", "zero_nmae", "ft_nmae", "relative_improvement", "pair_status")
    curve_columns = (
        "rate",
        "paired_seeds",
        "zero_mean",
        "ft_mean",
        "mean_relative_improvement",
        "improvement_from_mean_errors",
        "seed_min",
        "seed_max",
        "status",
    )
    return (
        fig,
        [[p[k] for k in pair_columns] for p in pairs],
        [[p[k] for k in curve_columns] for p in curves],
        summary,
        str(download),
        [[p[k] for k in ("rate", "seed", "status")] for p in coverage],
    )


def build_app(data_path=DEFAULT_DATA):
    with gr.Blocks(title="TSFM crossover results") as demo:
        gr.Markdown(
            "# TSFM Zero-Shot–Few-Shot 성능 전환 구간\n"
            "최종 논문 결과 270조건 탐색 / Explore 270 saved final-test conditions."
        )
        with gr.Row():
            model = gr.Dropdown(
                choices=[(LABELS[name], name) for name in MODELS], value="ttm", label="Model"
            )
            dataset = gr.Dropdown(choices=list(DATASETS), value="ETTh1", label="Dataset")
        summary = gr.Markdown()
        plot = gr.Plot(label="Paired improvement (%)")
        aggregate = gr.Dataframe(
            headers=[
                "rate",
                "paired_seeds",
                "ZS NMAE",
                "FT NMAE",
                "mean paired improvement",
                "improvement of means",
                "seed min",
                "seed max",
                "status",
            ],
            interactive=False,
            label="Seed mean and range (ratios, not percent)",
        )
        seed_table = gr.Dataframe(
            headers=[
                "rate",
                "seed",
                "ZS NMAE",
                "FT NMAE",
                "paired improvement",
                "pair status",
            ],
            interactive=False,
            label="Individual seeds",
        )
        coverage = gr.Dataframe(
            headers=["rate", "seed", "status"],
            interactive=False,
            label="Condition availability including Zero-Shot",
        )
        download = gr.File(label="Download displayed results, settings and provenance")
        gr.Markdown(LIMITS)
        gr.Markdown(
            "[Research repository](https://github.com/Han-Youseung/tsfm-zero-few-shot-crossover)"
            " · [Reproduction guide](https://github.com/Han-Youseung/"
            "tsfm-zero-few-shot-crossover/blob/main/docs/reproducibility.md)"
        )

        def update(m, d):
            return select(m, d, data_path)

        outputs = [plot, seed_table, aggregate, summary, download, coverage]
        model.change(update, [model, dataset], outputs, api_name="select_model")
        dataset.change(update, [model, dataset], outputs, api_name="select_dataset")
        demo.load(update, [model, dataset], outputs, api_name="initial_results")
    return demo


if __name__ == "__main__":
    build_app().launch(
        server_name=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.environ.get("GRADIO_SERVER_PORT", "7860")),
    )
