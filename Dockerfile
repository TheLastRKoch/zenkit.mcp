# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Resolve dependencies before copying source so edits do not invalidate this layer.
COPY pyproject.toml uv.lock README.md VERSION ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=0 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY --from=builder /app /app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin appuser

USER appuser

EXPOSE 9010

ENTRYPOINT ["zenkit-mcp"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "9010"]
