# 공개 결과 스키마 v1

입력: results/public/conditions.csv, UTF-8, 조건당 1행. 실험에서 계산한 원래 Python float 정밀도를 CSV round-trip으로 보존합니다. PDF 반올림 값이나 예시 데이터는 입력으로 사용하지 않습니다.

| 컬럼 | 의미 |
|---|---|
| condition_id | 기존 원 실행 조건 식별자 |
| model / dataset | ttm 또는 moirai1 / 최종 5개 데이터 이름 |
| rate | 분수 단위: 0=ZS, .005=.5%, 1=100% |
| seed / context / horizon | 1729,2718,31415 / 512 / 96 |
| status | completed, failed, not_run, unavailable, pending_gpu |
| nmae | 해당 조건의 실제 test normalized_mae; 상태가 completed일 때 필수 |
| actual_optimizer_steps | 실제 optimizer update 수, ZS=0 |
| best_validation_step | validation 최소 checkpoint step; ZS는 공란 |
| stopping_step | 학습 종료 step; best step과 구분 |
| selected_train_windows / total_train_windows | 선택 k / 전체 후보 N |
| test_windows | 동일한 final test rolling origins 수 |
| execution_commit / protocol_hash | 실행 코드 / 원 설정 identity |
| data_sha256 / test_window_hash | 준비 데이터 bytes / 시험 window identity |
| sampling_manifest_hash | 모델 간 동일 seed·비율의 선택 표본 identity |
| runtime_hash / gpu / model_revision | 실행환경 식별자 / 실제 GPU / 고정 HF revision |
| source_review | 저장소의 canonical compact review 상대경로 |
| source_member | 보존 자료집의 final_results.json 내 JSON array index |
| source_result_path | 원 실행 ZIP 안의 condition_id/result.json 경로 |
| source_record_hash | canonical review가 보존한 원 result hash |

공란은 누락·적용 불가이며 0으로 채우지 않습니다. 실패나 미실행은 평가 metric을 갖지 않습니다. 현재 배포본은 270행 모두 completed이나 도구는 불완전 자료도 읽고 coverage 270행을 생성합니다. 아예 빠진 조건은 unavailable이며 failed/not_run으로 추측하지 않습니다. 결과가 완전한데 기준을 충족하지 못한 경우와 누락은 다릅니다.

load_conditions는 중복·범위·NMAE 유한성·고정 context/horizon·dataset별 실행/데이터/test/protocol identity, 모델 간 sampling hash를 확인합니다. 독립적인 다른 실험을 단순 이름으로 결합하지 마세요. 원 raw result의 masks·metric scale 검사는 추출 단계 validate_records가 수행하며 CSV만으로 원 prediction을 재검증할 수는 없습니다.

출력 pairs.csv는 동일 model/dataset/seed의 ZS와 각 FT를 연결합니다. relative_improvement는 분수 단위, 양수가 개선. pair_status는 completed/missing_baseline/missing_fine_tuning/undefined_zero_baseline입니다.

curves.csv는 paired_seeds, zero_mean, ft_mean, mean_relative_improvement, improvement_from_mean_errors, seed_min/max를 분리합니다. 완전한 3seed가 아닐 때 주요 평균은 공란이며 available_seed_mean만 진단용으로 계산합니다. 다른 seed의 ZS로 대체하지 않습니다. 음영은 min-max이고 CI가 아닙니다.

table1.csv: 최종 비율 1의 seed 평균 오차와 paired 상대 개선. table2.csv: mean/all_seed 상태와 표시 구간(%), 정확한 경계용 lower/upper는 분수입니다. earliest sustained 판정에는 8비율 모두의 3seed pair가 필요합니다. 그래프는 누락을 NaN gap으로 표시합니다.

provenance.json은 공개 파일 SHA와 원 자료집 SHA, 검증 범위를 기록합니다. source_archive_hashes.json은 원 72개 ZIP의 전체 inventory이며 개별 조건과 ZIP 이름 매핑을 추측하지 않습니다. model_settings.json / environments.json은 원 설정·공식 코드 및 실제 package versions입니다. 원 result 전체는 로컬 자료집에 보존되며 공개 CSV는 소용량 분석용 export입니다.

공개 export는 .gitattributes의 -text 규칙으로 checkout 시 줄바꿈 변환을 막습니다. 플랫폼이 달라도 provenance의 SHA-256이 유지되어야 합니다.
