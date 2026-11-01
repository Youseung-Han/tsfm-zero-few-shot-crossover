# 데이터 출처·다운로드·전처리

| 데이터 | 공식 출처 | 채널 / 주기 | 학습 후보 / 시험 origins |
|---|---|---|---|
| ETTh1, ETTh2 | [ETDataset](https://github.com/zhouhaoyi/ETDataset) | 7 / 1시간 | 9,845 / 3,389 |
| ETTm1, ETTm2 | [동일 ETDataset](https://github.com/zhouhaoyi/ETDataset) | 7 / 15분 | 41,201 / 13,841 |
| Tetouan | [UCI Power Consumption of Tetouan City](https://archive.ics.uci.edu/dataset/849/power+consumption+of+tetouan+city) | 8 / 10분 | 30,842 / 10,389 |

Tetouan DOI는 10.24432/C5B034입니다. ETT 원본은 commit 1d16c8f4f943005d613b5bc962e9eeb06058cf07의 ETT-small/*.csv를 고정합니다. URL 및 source SHA는 results/manifests/pilot/prepared_primary9.json의 source_files에 있습니다. 준비본 경로·QC·채널 순서·split·canonical SHA도 같은 파일에 있습니다. 해당 manifest의 다른 데이터는 역사적 계획에 속하며 논문 범위에 포함되지 않습니다.

```bash
python scripts/prepare_study_data.py --dataset ETTh1
python scripts/prepare_study_data.py --dataset ETTh2
python scripts/prepare_study_data.py --dataset ETTm1
python scripts/prepare_study_data.py --dataset ETTm2
python scripts/prepare_study_data.py --dataset Tetouan
```

기존 스크립트를 재사용하며 없을 때만 공식 원본을 내려받고 frozen canonical fingerprint를 확인합니다. numpy/pandas는 모델 환경 또는 CPU 분석 환경에 설치되어 있어야 합니다. checksum이 다르면 대체 데이터로 실행하지 않고 중단합니다.

ETT는 공식 raw CSV를 사용합니다. Tetouan의 날짜 parsing·정렬·8 numeric channel 변환은 scripts/prepare_primary_candidates.py의 기존 recipe를 사용합니다. 원본·준비본을 Git으로 재배포하지 않습니다. legacy benchmark bundle의 표준화된 ETT로 교체하지 마세요.

시간순 60/20/20, 학습은 context+target 모두 train 안, validation/test는 target이 해당 split 안에 있고 context는 앞선 과거를 허용합니다. 이번 준비본은 결측·중복 timestamp가 없습니다. 결측 보간의 효과를 주장하지 않습니다. train-only ddof0 std는 NMAE 계산용이며 모델 입력은 native scaling을 유지합니다.

권리 기록: ETT 저장소의 CC BY-ND 4.0, Tetouan UCI의 CC BY 4.0 조건을 원 출처에서 확인하고 따라야 합니다. 모델 코드·가중치·데이터의 권리는 서로 다릅니다. 원 결과와 checksum 근거는 [출처 문서](provenance.md)를 참고하세요. 5개 변형은 독립 출처 5개가 아니라 두 ETT 변압기와 Tetouan의 세 출처군입니다.

2026-11-01 공식 출처 재확인: [고정 ETT LICENSE](https://raw.githubusercontent.com/zhouhaoyi/ETDataset/1d16c8f4f943005d613b5bc962e9eeb06058cf07/LICENSE)는 CC BY-ND 4.0, [UCI Tetouan](https://archive.ics.uci.edu/dataset/849/power+consumption+of+tetouan+city)은 CC BY 4.0을 명시합니다. 이는 프로젝트 자체의 새 코드 라이선스를 정하는 근거가 아닙니다.
