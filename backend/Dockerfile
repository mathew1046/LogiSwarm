# LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
# Copyright (C) 2025 LogiSwarm Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml .
RUN uv pip compile pyproject.toml -o requirements.txt \
    && uv pip download -r requirements.txt -d /app/wheels

# Stage 2: Runtime
FROM python:3.11-slim as runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 logiswarm \
    && adduser --system --uid 1001 --gid 1001 logiswarm

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/pyproject.toml .

RUN pip install --no-cache-dir /wheels/*.whl 2>/dev/null || pip install --no-cache-dir /wheels/*.tar.gz 2>/dev/null || true \
    && pip install --no-cache-dir uvicorn fastapi sqlalchemy asyncpg redis httpx loguru pydantic python-dotenv prometheus-client slowapi bcrypt PyJWT aiosmtplib chardet alembic \
    && rm -rf /wheels

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

RUN chown -R logiswarm:logiswarm /app

USER logiswarm

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]