FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        dnsutils \
        iputils-ping \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt
COPY examples/ /workspace/examples/

CMD ["sleep", "infinity"]
