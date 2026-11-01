# 실행 도구

저장소 루트에서 실행합니다. [재현 안내](../docs/reproducibility.md)를 먼저 확인하세요.

| 도구 | 역할 |
|---|---|
| prepare_study_data.py | 최종5개 데이터 준비 및 고정 fingerprint 확인 |
| prepare_primary_candidates.py | Tetouan의 원 전처리 recipe 및 공통 QC helper |
| reproduce_paper.py | 최종270조건 또는 TTM–ETTh1의 ZS/0.5% pair. 기본값은 계획만 출력 |
| reproduce_minimal.py | 기존 학습/평가 함수를 사용하는 축소 smoke. 논문 비교 불가 |
| import_public_runs.py | 새 실행 JSON을 표준CSV로 읽고 실패·누락 상태 보존 |
| export_public_results.py | 보존 자료집의 원 JSON과 canonical review를 대조해 CSV 추출 |
| verify_public_project.py | checksum·논문 수치·링크·구문·공개 경로 검사 |
| package_space.py | 가중치 없이 실행하는 결과 탐색 Space 폴더 생성 |

표·그림 재생성의 공용 CLI는 `python -m tsfm_crossover.analysis.public_results --output outputs/paper`입니다. 이미 존재하는 산출물은 덮어쓰지 않습니다.
