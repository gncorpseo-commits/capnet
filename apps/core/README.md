# CapNet Core (W1)

FastAPI + PostgreSQL 16. claim은 `INSERT … SELECT` + `FOR UPDATE SKIP LOCKED`만 쓴다.

```bash
# 저장소 루트
docker compose up --build
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/v1/internal/claim -H "content-type: application/json" -d "{}"
```

스키마·시드는 compose 첫 볼륨 생성 시 `docker-entrypoint-initdb.d`로 적재된다. 처음부터 다시:

```bash
docker compose down -v
docker compose up --build
```
