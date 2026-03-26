FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -e .

FROM python:3.11-slim as runtime

WORKDIR /app

RUN addgroup --system --gid 1001 logiswarm \
    && adduser --system --uid 1001 --gid 1001 logiswarm

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/pyproject.toml .

RUN pip install --no-cache /wheels/*.whl \
    && rm -rf /wheels

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

RUN chown -R logiswarm:logiswarm /app

USER logiswarm

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:5001/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]