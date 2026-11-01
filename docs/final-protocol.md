# 최종 논문 프로토콜

기준: 제공된 최종 PDF 3쪽, configs/analysis/primary5_h96.yaml, 원 result JSON 270개, 실행 commit 3e18305032484239966026f14395b903c9abf268. 초기 계획은 이 문서의 최종 범위를 대체하지 않습니다.

## 범위와 데이터

TTM-R3 / MOIRAI 1.1-R-small × ETTh1/ETTh2/ETTm1/ETTm2/Tetouan × ZS+8비율 × seed 1729/2718/31415 = 270조건. context 512, horizon 96. ETT는 7채널 전체, Tetouan은 8개 수치 채널 전체를 예측합니다. 원본 raw 데이터와 native model scaler를 사용하며 외부 StandardScaler를 적용하지 않습니다.

train_end=floor(0.6T), validation_end=floor(0.8T). 학습 윈도는 context512+target96이 모두 train에 포함됩니다. N=9,845(ETTh), 41,201(ETTm), 30,842(Tetouan). 각 비율 k=max(1,floor(rN)). 0.5%는 각각 49/206/154개의 후보 윈도입니다.

nested temporal stratification은 ceil(sqrt(N))개 시간층 안에서 seed별 shuffle을 하고 층을 교차 방문하는 master order의 prefix를 선택합니다. 모델 간 동일 seed·비율에서 sampling_manifest_hash가 같습니다. 표본 선택과 학습 batch shuffle은 별도입니다.

Validation/test는 **target 전체가 해당 split 안에** 있어야 하며 context는 직전 split의 과거 관측을 사용할 수 있습니다. stride1 rolling origins, 이후 입력에 실제로 관측된 과거 값 사용, 온라인 파라미터 갱신 없음. 시험 윈도 수는 3,389/13,841/10,389입니다. train 방식처럼 test 구간에서 context 512까지 빼면 이 수가 나오지 않습니다. PDF의 '시험구간에서 만든다'는 문장을 구현에 맞게 이처럼 구체화합니다.

## 학습·평가

각 FT는 사전학습 가중치에서 독립 시작, full parameters, FP32, batch1, accumulation1, drop_last=False, AdamW, 최대1,000updates. TTM LR1e-4/weight_decay0.01, MOIRAI LR5e-6/weight_decay0.1. scheduler와 gradient clipping 없음. 100updates마다 고정 64 validation origins의 NMAE 평가, 3번 연속 개선 없으면 종료. 최소 validation NMAE의 checkpoint를 시험에 사용합니다. ZS로 fallback하지 않습니다.

TTM의 공식 decomposed prediction loss와 prediction_outputs, MOIRAI의 MoiraiFinetune/PackedNLLLoss를 그대로 사용합니다. MOIRAI는 100 forecast samples에서 torch.median을 사용합니다(짝수 표본의 두 중앙값 평균이 아님). 원모델·공식 코드 revision은 versions.md 및 results/public/model_settings.json에 있습니다.

채널 c의 train population std(ddof=0)를 sigma_c라 하면 NMAE=mean_c(MAE_c/sigma_c). 실제 평가 원소는 (origin, lead, channel)의 유효 target입니다. 중첩 target은 예측 task마다 누적합니다. sigma<=1e-8은 normalized metric 제외 정책이나 이번 다섯 데이터에서는 제외 채널이 없습니다. train-only 통계는 오차 집계용이며 입력을 전역 표준화하는 scaler가 아닙니다.

## 개선율과 구간

I(r,s)=(NMAE(0,s)-NMAE(r,s))/NMAE(0,s). 표 1은 mean_s I의 백분율입니다. mean(I)와 (mean(ZS)-mean(FT))/mean(ZS)는 다릅니다. 둘을 public curves.csv에 별도 필드로 보존합니다.

평균 기준: 모든 k>=j에서 mean_s I(r_k,s)>0인 최초 j. 3seed 기준: 모든 k>=j 및 모든 seed에서 I(r_k,s)>0인 최초 j. 등호 0은 개선 아님. 표시 구간은 (r_(j-1),r_j], 첫 측정은 (0,0.5]%. 단일 최초 개선과 지속 개선을 혼동하지 않습니다. 비단조성·후속 재악화를 그대로 반영합니다. seed/비율 누락 시 earliest boundary 판정은 보수적으로 indeterminate_missing입니다. 완전한 격자에서 미충족은 not_observed_on_grid로 구분합니다.

이 정의는 최종 PDF의 평균 상대 개선율 정의입니다. 기존 analysis.paper와 crossover는 mean absolute delta>0을 사용하며 보존했습니다. 실제 270조건에서 두 정의가 판정을 바꾸는지 검증 보고에 적습니다. 새 공용 집계는 public_results.py이며 Gradio·Colab·CLI가 이를 공유합니다.

## 해석 범위

3개의 출처군, 3seed, H96(시간 간격마다 물리적 기간 다름), 제한 예산 및 사후 확정 범위입니다. 100%는 pool 허용량이고 실제 방문량·best checkpoint의 노출량과 다릅니다. 겹친 origins나 네 ETT 변형을 독립 표본으로 유의성 검정하지 않습니다. 모델 간 개선 폭과 최종 오차를 분리합니다. 실제 수집 비용·운영 이득·모든 TSFM으로의 일반화는 관측하지 않았습니다.
