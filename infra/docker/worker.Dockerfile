FROM python:3.11-slim

# Install system dependencies for scanners
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Go for osv-scanner
RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && \
    rm go1.21.5.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

# Install security scanners
RUN pip install semgrep

# Install Syft and Grype
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Install OSV Scanner
RUN go install github.com/google/osv-scanner/cmd/osv-scanner@latest
ENV PATH="/root/go/bin:${PATH}"

COPY . /app
CMD ["python","apps/worker/worker.py"]
