# 결과 출처와 재현 범위

논문 분석 범위는 TTM-R3와 MOIRAI 1.1-R-small, ETTh1/ETTh2/ETTm1/ETTm2/Tetouan, H96, seed1729/2718/31415의 270조건입니다. 원 실행 commit은 **3e18305032484239966026f14395b903c9abf268**입니다.

공개 CSV는 보존된 원 result JSON 270개를 고정 canonical review와 대조해 추출했습니다. review의 SHA는 configs/analysis/primary5_h96.yaml에 있습니다. model/dataset/seed/rate, 실제 NMAE, optimizer/best/stop step, 원 condition/result.json 경로와 record hash를 보존합니다. 원 72개 ZIP의 파일명/SHA는 results/public/source_archive_hashes.json에 있습니다. 공개 파일별 SHA와 검증 범위는 results/public/provenance.json을 확인하세요.

출처 자료집의 evidence/final_results.json은 scientific 원 기록이며 PDF 숫자가 아닙니다. 현재 로컬 자료집에는 inventory의 claims_and_checklist.txt 편집 문서 1개가 없습니다. 존재하는 나머지 멤버 체크섬 및 raw/compact review 대조는 통과했습니다. 추출 도구는 이 누락을 provenance에 기록하고 다른 파일 누락·불일치에서는 중단합니다. 원 자료집을 전체 무결성 성공으로 보고하지 않습니다.

공개 재현은 두 수준입니다.

1. results/public/conditions.csv만으로 저장 metric의 집계·전환 구간·표·그림을 재생성합니다. 원 ZIP이나 GPU가 필요하지 않습니다.
2. 원모델·원데이터로 학습과 시험을 다시 실행하려면 기록된 모델·환경 pin과 호환 GPU가 필요합니다. 원 optimizer checkpoint·prediction 배열은 제공하지 않습니다.

이번 공개 도구 검증에서 새로운 GPU 학습이나 prediction에서 metric 재계산은 수행하지 않았습니다. 원 ZIP72개 전체를 다시 개봉한 검증과도 구분합니다. seed 최소–최대는 신뢰구간이 아니며, 제공되지 않은 prediction 배열로 bootstrap을 계산한 것처럼 표시하지 않습니다.

초기 계획·과거 초안·pilot 및 복구 기록은 현재 파일 목록에서 제거했습니다. 원 실행 설정과 모델·데이터·검증 근거 중 엔진이 참조하는 항목은 원 bytes로 남겼습니다. 더 넓은 후보/비율/horizon이 원 설정에 있더라도 논문 최종 범위는 final-protocol.md와 reproduce_paper.py의 270조건입니다.
