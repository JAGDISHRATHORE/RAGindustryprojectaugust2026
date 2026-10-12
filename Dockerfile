# syntax=docker/dockerfile:1.7

# ---- build stage: install dependencies into a virtualenv ----
FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml README.md ./
COPY complyrag ./complyrag
RUN pip install ".[models,otlp]"

# ---- runtime stage ----
FROM python:3.12-slim
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    COMPLYRAG_DATA_DIR=/app/data \
    COMPLYRAG_INDEX_DIR=/app/state/index \
    COMPLYRAG_RUNS_DIR=/app/state/runs \
    COMPLYRAG_AUDIT_LOG=/app/state/runs/audit.jsonl \
    COMPLYRAG_CACHE_DIR=/app/state/cache \
    HF_HOME=/app/state/models

RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY complyrag ./complyrag
COPY data ./data
RUN mkdir -p /app/state && chown -R app:app /app/state
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "complyrag.api:app", "--host", "0.0.0.0", "--port", "8000"]
