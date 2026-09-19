# ==============================================================================
# Samanvay-AI: Dedicated ML Inference Worker & Offline Embedding Engine
# Project: Samanvay-AI | Version: 2.0.0-PROD
# Organization: Ministry of Petroleum & Natural Gas (MoPNG) / BharatCodex
# ==============================================================================

FROM python:3.12-slim AS runner

LABEL maintainer="BharatCodex Team <samanvay-ai@mopng.gov.in>"
LABEL org.opencontainers.image.title="Samanvay-AI ML Worker Microservice"
LABEL org.opencontainers.image.description="Dedicated ML Worker for Local Sovereign Embedding & Document Intelligence"
LABEL org.opencontainers.image.version="2.0.0-PROD"
LABEL org.opencontainers.image.vendor="MoPNG / BharatCodex"
LABEL org.opencontainers.image.licenses="Proprietary"
LABEL project="Samanvay-AI"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

RUN uv pip install --system --no-cache \
    fastapi \
    uvicorn[standard] \
    pydantic \
    pydantic-settings \
    numpy \
    pandas \
    pymupdf \
    onnxruntime \
    sentence-transformers \
    pillow \
    torch --extra-index-url https://download.pytorch.org/whl/cpu

# Create dedicated non-root application user
RUN groupadd -g 10001 samanvay && \
    useradd -u 10001 -g samanvay -s /bin/bash -m samanvay

COPY --chown=samanvay:samanvay ml/ ./ml/
COPY --chown=samanvay:samanvay rules/ ./rules/
COPY --chown=samanvay:samanvay datasets/ ./datasets/
COPY --chown=samanvay:samanvay backend/ ./backend/

USER samanvay

EXPOSE 8001

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
