# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Install git and system build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy codebase and install reddie
COPY . .
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["reddie"]
CMD ["--help"]
