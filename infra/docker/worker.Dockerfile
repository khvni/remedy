FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .
COPY . /app
CMD ["python","apps/worker/worker.py"]
