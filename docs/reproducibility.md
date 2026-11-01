# 재현 안내

## 재현 수준

1. **저장 metric 재집계**: 공개 CSV 270행으로 논문의 표·그림·전환 구간을 재생성. CPU만 필요. 이번 작업에서 검증한 수준입니다.
2. **원 기록 출처 대조**: 검증된 canonical review, 자료집의 raw result JSON 및 체크섬 대조. 72개 원 실행 ZIP 전체를 이번에 다시 열었다는 뜻은 아닙니다.
3. **모델 재실행**: 공식 모델과 원 데이터를 내려받아 학습·시험 재평가. 새 GPU 실행은 이번 작업에서 하지 않았습니다. 같은 설정도 하드웨어·라이브러리의 비결정성 때문에 bitwise 동일성을 보장하지 않습니다.

## CPU: 깨끗한 환경

저장소 루트에서 Python 3.12 환경을 만들고 활성화합니다.

```bash
python -m venv .venv
python -m pip install -r requirements/analysis.txt
python -m pytest
python -m tsfm_crossover.analysis.public_results --input results/public/conditions.csv --output outputs/paper-run-1 --paper-reference docs/paper-reference.json
```

출력은 table1.csv, table2.csv, tables.md, figure1.png/svg, pairs.csv, curves.csv, coverage.csv, verification.json입니다. figure1은 같은 관측 metric을 다시 그린 것으로 최종 PDF와 픽셀 단위 일치 검사가 아닙니다. 폰트·레이아웃은 다를 수 있습니다. 표는 전체 정밀도를 보존하고, 논문과 비교할 때만 ZS/FT 소수 5자리·개선율 소수 2자리로 반올림합니다.

실험 결과 CSV를 바꾸면 더 이상 배포 snapshot과 같은 자료가 아닙니다. 원본을 보존하고 다른 경로의 사본으로 분석하세요. 중복·범위·metric·평가 identity 검사가 실패하면 다른 실험을 합치지 마세요.

## 원 자료집에서 공개 CSV를 다시 추출

```bash
python scripts/export_public_results.py --kit LOCAL_WRITING_KIT.zip --output outputs/reexported-public
```

자료집 내부 SHA-256, 원 review의 고정 SHA, 270개 raw 결과와 compact review 일치, 데이터·시험 윈도·표본 identity를 검증합니다. 이번 로컬 자료집에는 claims_and_checklist.txt가 빠져 있습니다. 도구는 이 편집 문서 1개의 누락만 명시적으로 허용하고 provenance.json에 기록합니다. 다른 누락이나 checksum 불일치는 중단합니다. PDF 숫자로 CSV를 만드는 경로는 없습니다. 원본 ZIP은 수정하지 않습니다.

## 모델: 최소 두 조건

Linux CUDA / Python 3.12의 TTM 전용 환경에서:

```bash
python -m pip install -r requirements/ttm-main.txt
python scripts/prepare_study_data.py --dataset ETTh1
python scripts/reproduce_paper.py --scope pair --output outputs/pair
python scripts/reproduce_paper.py --scope pair --output outputs/pair --execute
```

계획은 CPU에서도 가능하지만 데이터 준비는 numpy/pandas가 필요합니다. 실제 실행은 모델 가중치 다운로드, 엄격한 runtime 확인, 깨끗한 tracked source를 요구합니다. 명령에 --execute가 있어야 GPU 작업을 시작합니다. 확인한 변경을 commit한 checkout에서 실행하세요. 실험 identity에는 실제 실행 HEAD를 기록합니다. **원 논문 실행 commit은 3e18305032484239966026f14395b903c9abf268**이며, 현재 공개 도구 commit과 구분해야 합니다.

원 코드 자체를 재실행하려면 별도 checkout에서 해당 commit을 사용하고, 기존 CLI로 정확한 condition ID를 실행할 수 있습니다:

```bash
python -m tsfm_crossover.experiments.main_study --expected-commit 3e18305032484239966026f14395b903c9abf268 --condition-id ttm-ETTh1-h96-s1729-r0 --output outputs/original-engine
python -m tsfm_crossover.experiments.main_study --expected-commit 3e18305032484239966026f14395b903c9abf268 --condition-id ttm-ETTh1-h96-s1729-r0.005 --output outputs/original-engine
```

원 CLI의 condition-id 없는 실행은 **원 계획 1,944조건**을 표시합니다. 이것이 논문 범위는 아닙니다. 최종 범위만 실행하려면 신규 reproduce_paper.py를 사용하세요. 기존 엔진·프로토콜 YAML은 그대로 유지했습니다.

## 전체 270조건

모델마다 별도 환경을 만들고 ttm-main.txt 또는 moirai1-main.txt를 설치합니다. 데이터 준비를 다섯 번 수행합니다.

```bash
python scripts/prepare_study_data.py --dataset ETTh1
python scripts/prepare_study_data.py --dataset ETTh2
python scripts/prepare_study_data.py --dataset ETTm1
python scripts/prepare_study_data.py --dataset ETTm2
python scripts/prepare_study_data.py --dataset Tetouan
python scripts/reproduce_paper.py --scope full --family ttm --output outputs/full-ttm --execute
# MOIRAI 전용 환경:
python scripts/reproduce_paper.py --scope full --family moirai1 --output outputs/full-moirai1 --execute
```

각 모델 135조건입니다. main_study.run의 기존 runtime gate·immutable identity·학습·checkpoint 선택·시험 평가·resume를 사용합니다. runtime gate는 예산 검증 기록의 패키지·torch/CUDA를 엄격하게 비교합니다. 최신 Colab 기본 환경이 그대로 통과한다고 가정하지 마세요. 검증 기록과 requirements는 [버전 문서](versions.md)를 참고하세요. 100% 풀도 최대 1,000 updates이며 수렴 실험이 아닙니다.

## Colab 및 축소 smoke

[50_results_analysis.ipynb](../notebooks/50_results_analysis.ipynb)는 GPU 없이 실행합니다. [51_minimal_ttm_etth1.ipynb](../notebooks/51_minimal_ttm_etth1.ipynb)는 기본 smoke 모드로, scripts/reproduce_minimal.py를 호출합니다. 이 runner는 기존 prepare_condition, stability, final_windows, evaluate_final 및 공식 adapter를 재사용하며 2 updates, 4 validation, 동일한 8 test windows로 줄입니다. 결과는 smoke_result.json에 별도로 쓰며 논문 CSV에 섞지 않습니다.

```bash
python scripts/reproduce_minimal.py --output outputs/smoke-1
python scripts/reproduce_minimal.py --output outputs/smoke-1 --execute
```

기본 plan 명령은 실행 검증이 아닙니다. 이번에는 새 runner의 CPU 계획·구문·공유 함수 연결만 검증했고 GPU 다운로드·학습·시험은 미검증입니다. 모델 가중치나 optimizer checkpoint가 로컬에 없으므로 기존 checkpoint를 업로드할 근거도 없습니다.

## 새 실행 결과를 같은 스키마로 재집계

```bash
python scripts/import_public_runs.py --run-dir outputs/full-ttm --run-dir outputs/full-moirai1 --output outputs/normalized-new-runs
python -m tsfm_crossover.analysis.public_results --input outputs/normalized-new-runs/conditions.csv --output outputs/new-run-analysis
```

원 main-study의 condition/result.json을 읽고 중복·조건 identity·완료 상태·시험 no-update를 검사합니다. 누락은 unavailable, 실패 또는 GPU 대기 파일이 있는 경우 해당 근거 상태로 보존합니다. 실패 기록은 최종 retry 상태를 보장하지 않습니다. 기존 결과를 덮어쓰지 않습니다. smoke 결과는 이 입력이 아니며 논문 CSV에 섞을 수 없습니다. 새 metric과 논문이 다르면 verification.json의 비교 결과에 차이를 남기고 어느 쪽도 자동 수정하지 않습니다.
