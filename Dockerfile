# Multi-stage build for production deployment
FROM node:20-alpine AS web-builder
WORKDIR /app
COPY apps/web/package*.json ./
RUN npm ci --only=production
COPY apps/web/ ./
RUN npm run build

FROM python:3.11-slim AS api
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .
COPY . /app
COPY --from=web-builder /app/dist /app/apps/web/dist

EXPOSE 8000
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
