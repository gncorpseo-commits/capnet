FROM python:3.11-slim

WORKDIR /app

COPY apps/node/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/node/app /app/app
COPY apps/node/weights /weights

ENV PYTHONUNBUFFERED=1
ENV WEIGHTS_PATH=/weights/placeholder.safetensors
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
