# syntax=docker/dockerfile:1
FROM python:3.12.12-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends chromium tesseract-ocr tesseract-ocr-eng tesseract-ocr-tha fonts-noto-core fonts-noto-color-emoji ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir -r requirements.lock; else pip install --no-cache-dir -r requirements.lock; fi
RUN useradd --create-home --uid 10001 pilot && chown pilot:pilot /app
COPY --chown=pilot:pilot collector ./collector
COPY --chown=pilot:pilot app.py .
USER pilot
FROM base AS test
USER root
COPY requirements-dev.txt .
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir -r requirements-dev.txt; else pip install --no-cache-dir -r requirements-dev.txt; fi
COPY --chown=pilot:pilot tests ./tests
USER pilot
RUN python -m pytest -q
FROM base AS runtime
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["sh", "-c", "exec streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.maxUploadSize=10 --browser.gatherUsageStats=false"]
