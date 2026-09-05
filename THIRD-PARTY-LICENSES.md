# Third-party licenses

사람용 SPDX 표. 기계 가독 SBOM은 루트 [`sbom.json`](sbom.json) (`scripts/generate_sbom.ps1` / `.sh` + cyclonedx-py).

| 패키지 | 라이선스 | 용도 |
|--------|----------|------|
| FastAPI | MIT | Core HTTP |
| Starlette | BSD-3-Clause | FastAPI 의존 |
| Uvicorn | BSD-3-Clause | ASGI 서버 |
| psycopg | LGPL-3.0 | PostgreSQL 드라이버 |
| psycopg-pool | LGPL-3.0 | psycopg 커넥션 풀 (SD-017) |
| Pydantic | MIT | 설정·요청 모델 |
| pydantic-settings | MIT | 환경변수 설정 |
| PostgreSQL 16 (Docker 이미지 `postgres:16`) | PostgreSQL License | DB |
| Python 3.11 (Docker 이미지 `python:3.11-slim`) | PSF-2.0 | Core·Node 런타임 베이스 이미지 |
| safetensors | Apache-2.0 | Node 가중치 로드 (pickle 거부) |
| numpy | BSD-3-Clause | safetensors numpy 백엔드 |
| Pillow | MIT-CMU (HPND-derived) | 골든셋 JPEG 로드 |
| torch | BSD-3-Clause | EuroSAT scratch 학습·추론 (CPU 휠, node-m-team만) |
| torchvision | BSD-3-Clause | 32×32 텐서 변환 |
| httpx (optional `capreq/`) | BSD-3-Clause | capreq → Ollama·Core HTTP |
| FastAPI/Uvicorn (optional `capreq[server]`) | MIT / BSD-3-Clause | capreq 웹 챗봇 |
| python-multipart (optional `capreq[server]`) | Apache-2.0 | capreq 챗봇 파일 첨부 multipart 파싱 |
