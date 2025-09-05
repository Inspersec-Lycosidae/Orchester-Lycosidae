# Orchester Dockerfile
FROM python:3.13-slim

# Install docker-cli (without daemon)
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker-cli && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /orchester
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x ./uvicorn.sh
ENV PYTHONPATH=/orchester/app
CMD ["/bin/bash", "./uvicorn.sh"]
