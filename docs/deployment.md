# Hugging Face Spaces 배포

저장된 결과 CSV를 읽는 CPU Gradio 앱입니다. 원모델 가중치, 실시간 추론, 비밀 토큰이 필요하지 않습니다.

## 로컬 실행

```bash
python -m pip install -r requirements.txt
python app.py
```

기본 주소는 http://127.0.0.1:7860 입니다. Space에서는 GRADIO_SERVER_NAME=0.0.0.0을 설정할 수 있습니다.

## Space 폴더 만들기

```bash
python scripts/package_space.py --output outputs/space-bundle
```

새 폴더에 app.py, 설치 입력, 필요한 분석 package, 실제 공개 결과와 관련 문서만 복사합니다. Space 루트 README는 spaces/README.md에서 가져옵니다. bundle-manifest.json은 파일별 SHA-256입니다. 데이터 원본·가중치·로그·캐시는 포함하지 않습니다.

Gradio Space를 만든 뒤 생성 폴더의 파일을 올립니다. 모델–데이터10조합, 실제 NMAE, 두 지속 개선 구간과 CSV 다운로드를 확인하세요. 현재 저장소에는 호스팅된 Space 주소가 없습니다. 가중치를 배포하지 않으므로 모델 업로드나 추가 학습이 필요하지 않습니다.

## 권리와 코드 revision

프로젝트 LICENSE는 미지정입니다. 공개 가시성은 이용 허락을 의미하지 않습니다. 원모델·데이터 조건은 별도로 적용되며 MOIRAI 가중치에는 비상업 조건이 기록되어 있습니다. 앱에 가중치를 포함하지 않습니다. 논문 PDF 자체도 재배포하지 않습니다.

Colab notebook은 검토한 코드 commit을 SOURCE_REF로 고정합니다. 이후 코드를 업데이트하면 테스트를 완료한 새 commit으로 갱신하세요. notebook은 개인 Drive·토큰·절대경로를 사용하지 않습니다.
