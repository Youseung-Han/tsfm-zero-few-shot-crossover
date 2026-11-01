# 의존성과 고정 모델 버전

실험 실행 commit: **3e18305032484239966026f14395b903c9abf268**. 기존 분석 기준 a2d3089, 저장소 조사 시작 HEAD 4840fbf. 신규 공개 도구는 별도 변경이며 기존 train/evaluate 함수의 동작은 수정하지 않았습니다.

| 항목 | TTM | MOIRAI |
|---|---|---|
| HF repository | ibm-granite/granite-timeseries-ttm-r3 | Salesforce/moirai-1.1-R-small |
| HF revision | 7b070728ff280ee2bb682bd8dfbe71da21ca2c7c | 0c24ab99db2c1a70ea2a0fc03bf113329772ac64 |
| 공식 코드 commit | fe7a35697723e2a2f5246ae979474bfc554e26c0 | cfd46d4510ed8896f263116f32928eede05b0a75 |
| 공식 package | granite-tsfm 0.3.9 | uni2ts 2.0.0 (tag 동일성은 가정하지 않음) |
| H96 trainable parameters | 5,328,932 | 13,827,528 |
| Python | 3.12.14 | 3.12.15 |
| torch/CUDA | 2.11.0+cu130 | 2.4.1+cu121 |
| 실제 GPU | A100-SXM4-40GB 131조건, Tesla T4 4조건 | A100-SXM4-40GB 135조건 |
| 코드 / 가중치 권리 기록 | Apache-2.0 / Apache-2.0 | Apache-2.0 / CC-BY-NC-4.0 |

TTM H96 selector: 512-96-dec-512-r3. 원 pin과 adapter 설정은 results/public/model_settings.json, 실제 환경 snapshot은 environments.json입니다. 설치용 requirements/ttm-main.txt와 moirai1-main.txt는 예산 검증 환경 snapshot을 보존합니다. 두 모델을 한 환경에 설치하지 마세요. 부가 package 버전까지 main runtime gate가 검증하므로 임의 업그레이드는 새 실험 조건입니다. 최신 원모델을 자동 선택하지 않습니다.

CPU 분석은 requirements/analysis.txt, 앱은 requirements.txt를 사용합니다. 공개 도구 검증 환경의 재설치 snapshot은 requirements/public-resolved.txt에 기록합니다. 이는 GPU 실험 환경 lock이 아닙니다. 버전 목록이 존재한다는 사실과 해당 환경을 이번에 GPU에서 재실행했다는 사실은 구분합니다.
