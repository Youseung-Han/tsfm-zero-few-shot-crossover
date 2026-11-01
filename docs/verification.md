# 검증

## 실행 범위

공개 도구는 별도의 Python3.12 CPU 환경에서 설치·import·pip check를 확인했습니다. 저장된270조건에서 최종 PDF의 표1 수치30개와 표2 구간20개가 일치합니다. 그림1은 같은 원 metric을 다시 그린 것이며 PDF 픽셀 단위 비교는 아닙니다.

Gradio의10개 모델–데이터 선택, seed/평균/누락표 및 CSV 다운로드를 검사했습니다. 실제 앱 HTTP200과 선택 API도 확인했습니다. 분석 notebook의 분석·표시·ZIP 셀은 로컬 실행했으며, 원격 clone 대신 로컬 checkout을 사용했습니다. 모델 notebook은 구문과 CPU 계획을 확인했고 새 GPU 실행은 하지 않았습니다. 별도 torch CPU 환경에서는 adapter/학습 재개/시험 no-update의 toy 통합 테스트18개가 통과했습니다. 공식 모델 GPU 실행 검증으로 해석하지 않습니다.

다섯 데이터 준비 명령은 기존 준비본의 canonical fingerprint를 검증했습니다. 공개 CSV의 NMAE와 원 compact review float가 정확히 일치합니다. 테스트는 중복·NaN·평가/표본 identity 불일치, missing baseline/seed/rate, 0인 baseline, 재악화와 지속 개선, 평균 paired ratios와 ratio of means의 차이를 포함합니다.

정리된 배포 범위의 전체 테스트는 **124 passed, 3 skipped**입니다. 제외된3모듈의 toy CPU 통합 테스트는 별도 torch 환경에서 **18 passed**입니다. 저장 결과 재추출 CSV는 기존 공개 CSV와 byte 단위로 같았습니다.

## 실행 명령

```bash
python -m pip install -r requirements/analysis.txt
python -m pip install -r requirements.txt
python -m pytest -p no:cacheprovider -q
python -m ruff check app.py src scripts tests notebooks
python -m ruff format --check app.py src scripts tests notebooks
python scripts/verify_public_project.py --output outputs/public-verification.json
python -m pip check
```

최종 구조·출처·내부 링크·notebook 구문·공개 경로 검사는 [verification.json](../results/verification.json)에 기록합니다. 제거된 과거 실험/초안/호환성 조사 전용 테스트는 현재 배포 범위에 포함하지 않습니다. 남은 학습·평가 구현은 원 bytes와 비교하고, 삭제를 오류 수정처럼 처리하지 않습니다.

개인 절대경로·알려진 토큰/private-key 패턴을 검사합니다. 정적 패턴 검사는 가능한 모든 비밀정보 부재에 대한 보장은 아닙니다. 원 데이터·로그·캐시·가중치는 배포하지 않습니다. 외부 Colab GPU 환경 및 Hugging Face 서버에서의 배포는 별도 검증 대상입니다.
