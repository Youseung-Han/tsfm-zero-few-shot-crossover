# 시계열 파운데이션 모델의 제로샷·퓨샷 전환 구간 분석

[English](README.en.md) · [논문 결과표](results/paper/tables.md) · [재현 안내](docs/reproducibility.md)

시계열 파운데이션 모델을 미세조정할 때, 학습 윈도를 얼마나 확보하면 제로샷 예측보다 꾸준히 나아질까? TTM-R3와 MOIRAI 1.1-R-small을 대상으로, 학습 업데이트 예산을 고정하고 미세조정에 사용할 수 있는 윈도 비율을 바꿔 비교했다. 이 저장소에는 실험 코드와 최종 평가 270조건의 결과가 있다.

## 핵심 결과

- **평균 성능** 기준으로 모델·데이터 조합 10개 모두 학습 윈도 후보 풀의 1% 이하에서 제로샷 대비 개선이 나타났고, 이후 측정한 모든 비율에서 개선이 유지됐다.
- **실험 시드 3개 모두에서 개선**을 요구하면 10개 중 9개 조합이 5% 이하에서 기준을 충족했다. TTM–ETTm1은 측정한 비율 범위에서 이 기준을 충족하지 못했다.
- 후보 풀을 100% 허용했을 때 최종 평균 오차는 다섯 데이터셋 모두 TTM이 더 낮았다.

![학습 윈도 후보 풀 비율에 따른 제로샷 대비 상대 오차 개선율](results/paper/figure1.png)

실선은 시드별 상대 개선율의 평균이다. 음영은 시드 3개의 최솟값부터 최댓값까지를 나타낸다. [조합별 전환 구간과 오차](results/paper/tables.md) · [평가 결과 CSV](results/public/conditions.csv)

## 실험 설계

| 항목 | 설정 |
| --- | --- |
| 모델 | IBM Granite TTM-R3, Salesforce MOIRAI 1.1-R-small |
| 데이터 | ETTh1, ETTh2, ETTm1, ETTm2, Tetouan |
| 분할과 예측 | 시간순 60/20/20 분할, 입력 512스텝, 예측 96스텝 |
| 비교 조건 | 제로샷과 미세조정 8개 비율(0.5%~100%), 조건마다 시드 3개 |
| 학습 예산과 지표 | 최대 1,000회 업데이트, NMAE(훈련 표준편차로 정규화한 채널별 MAE의 평균) |

전환 구간은 처음 개선이 확인되고 더 큰 모든 측정 비율에서 개선이 유지된 지점을 기준으로 계산했다. 비율의 분모는 훈련 기간에서 만들 수 있는 윈도 후보 풀이다. 후보 풀 전체를 허용한 조건에도 같은 업데이트 상한을 적용했다. 결과 해석 범위는 사용한 모델, 데이터 출처, 예측 길이와 학습 예산에 한정된다. [상세 실험 프로토콜](docs/final-protocol.md)

## 결과 재현

기존 실험 결과로 표와 그림을 다시 만드는 데는 Python 3.12를 권장한다. GPU와 모델 가중치가 필요 없다. 가상환경을 활성화한 뒤 저장소 루트에서 다음을 실행한다.

```bash
python -m pip install -r requirements/analysis.txt
python -m tsfm_crossover.analysis.public_results --output outputs/paper-reproduction
```

새 출력 경로를 지정하면 표·그림과 시드별 개선율이 생성된다. [Colab에서 결과 분석](https://colab.research.google.com/github/Youseung-Han/tsfm-zero-few-shot-crossover/blob/main/notebooks/50_results_analysis.ipynb) · [모델 재실행 및 데이터 준비](docs/reproducibility.md) · [인용 정보](CITATION.cff)
