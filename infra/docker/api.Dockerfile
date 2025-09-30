FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir uv pip && pip install -U pip && pip install --no-cache-dir -e .
COPY . /app
EXPOSE 8000
CMD ["uvicorn","apps.api.main:app","--host","0.0.0.0","--port","8000"]
