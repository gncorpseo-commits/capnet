FROM python:3.11-slim

WORKDIR /app

COPY apps/core/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/core/app /app/app
COPY apps/core/openapi.yaml /app/openapi.yaml

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
