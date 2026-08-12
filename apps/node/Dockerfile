FROM python:3.11-slim

WORKDIR /app

ARG INSTALL_TORCH=false

# torch 는 requirements.txt 에 두지 않는다 — 조건부(INSTALL_TORCH)이고 별도 인덱스에서 온다.
# 대신 **여기서 핀한다.** 무버전이면 2차 심사(F4 라이선스 검증) 때 재빌드한 것과
# 붙임1 명세서에 적어 낸 버전이 달라질 수 있다. 버전을 바꾸면 붙임1·sbom.json 도 같이 고친다.
ARG TORCH_VERSION=2.13.0+cpu
ARG TORCHVISION_VERSION=0.28.0+cpu

COPY apps/node/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && if [ "$INSTALL_TORCH" = "true" ]; then \
         pip install --no-cache-dir \
           "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}" \
           --index-url https://download.pytorch.org/whl/cpu ; \
       fi

COPY apps/node/app /app/app
COPY apps/node/weights /weights

ENV PYTHONUNBUFFERED=1
ENV WEIGHTS_DIR=/weights
ENV WEIGHTS_PATH=/weights/placeholder.safetensors
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
