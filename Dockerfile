# NéoMêtis — Chainlit UI + FastAPI + Hermes engine
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VERSION pyproject.toml ./
COPY .chainlit ./.chainlit
COPY public ./public
COPY scripts ./scripts
COPY src ./src

RUN chmod +x scripts/vendor-hermes.sh && ./scripts/vendor-hermes.sh main

ENV HERMES_UPSTREAM=1
ENV NEOMETIS_HEADLESS=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
