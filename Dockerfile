# Multi-stage production container image.
# Stage 1 builds the Vite React SPA. Stage 2 runs FastAPI with Tesseract OCR
# behind Granian (production ASGI server).

FROM node:22-bookworm-slim AS ui

WORKDIR /src/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --omit=optional \
  && npm install --no-save --package-lock=false "$(node -e "const p=process.platform,a=process.arch,l=process.env.OPENCODE_LIBC||'gnu';console.log('@rollup/rollup-'+p+'-'+a+(p==='linux'?'-'+l:''))")"
COPY ui/ ./
RUN npm run build

FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=80 \
    GRANIAN_HOST=0.0.0.0 \
    GRANIAN_INTERFACE=asgi \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:/usr/local/bin:/usr/bin:/bin"

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY app ./app
COPY api ./api
COPY migrations ./migrations

RUN uv sync --frozen --no-dev --no-editable

# Copy built frontend assets to ./ui/dist for FastAPI app.frontend()
COPY --from=ui /src/ui/dist ./ui/dist

EXPOSE 80

CMD ["sh", "-c", "exec /app/.venv/bin/granian --interface asgi --host 0.0.0.0 --port ${PORT:-80} app.main:app"]
