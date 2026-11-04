# syntax=docker/dockerfile:1.7
# ==============================================================================
# Samanvay-AI: Dedicated ML Inference Worker (RESERVED / NOT YET DEPLOYED)
#
# Standalone ML microservice with sentence-transformers + torch for future
# horizontal scaling where embedding inference is offloaded from backend.
# ==============================================================================

FROM python:3.12-slim-bookworm AS runner

LABEL maintainer="BharatCodex Team <samanvay-ai@mopng.gov.in>" \
      org.opencontainers.image.title="Samanvay-AI ML Worker (Reserved)" \
      org.opencontainers.image.description="Dedicated ML Worker for Local Sovereign Embedding & Document Intelligence" \
      org.opencontainers.image.version="2.0.0-PROD" \
      org.opencontainers.image.vendor="MoPNG / BharatCodex" \
      project="Samanvay-AI"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Inherit official uv binary
COPY --from=ghcr.io/astral-sh/uv:0.5.26 /uv /uvx /bin/

COPY pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-progress \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    numpy \
    pandas \
    pymupdf \
    onnxruntime \
    sentence-transformers \
    pillow \
    torch --extra-index-url https://download.pytorch.org/whl/cpu

RUN groupadd -g 10001 -r samanvay && \
    useradd -u 10001 -r -g samanvay -s /sbin/nologin -M -d /nonexistent samanvay

COPY --chown=samanvay:samanvay --chmod=550 machine_learning/ ./machine_learning/
COPY --chown=samanvay:samanvay --chmod=550 OCR/ ./OCR/
COPY --chown=samanvay:samanvay --chmod=550 rules/ ./rules/

COPY --chown=samanvay:samanvay --chmod=550 data/ ./data/
COPY --chown=samanvay:samanvay --chmod=550 scripts/ ./scripts/
COPY --chown=samanvay:samanvay --chmod=550 backend/ ./backend/

RUN python -m compileall -q -f /app

USER samanvay

EXPOSE 8001

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--timeout-graceful-shutdown", "25"]
