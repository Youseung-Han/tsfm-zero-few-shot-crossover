# 실행 환경

| 파일 | 용도 |
|---|---|
| analysis.txt | CPU 결과 집계·그림·테스트·notebook |
| ../requirements.txt | CPU Gradio 앱과 Hugging Face Spaces |
| public-resolved.txt | 검증한 CPU 분석·앱 환경의 package snapshot |
| ttm-main.txt | 원 TTM GPU 실행 환경 snapshot |
| moirai1-main.txt | 원 MOIRAI1 GPU 실행 환경 snapshot |
| ttm.txt / moirai1.txt | 고정 공식 구현 commit |
| *-gpu.txt / base.txt | 위 GPU 환경에서 사용하는 공통 설치 입력 |

모델별 별도 Python3.12/Linux CUDA 환경을 사용합니다. requirements의 존재 자체가 현재 Colab에서 GPU 재실행을 완료했다는 뜻은 아닙니다. [고정 버전](../docs/versions.md)과 [재현 안내](../docs/reproducibility.md)를 확인하세요.
