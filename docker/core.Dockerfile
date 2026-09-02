# NéoMêtis Core - FastAPI + Hermes agent
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VERSION pyproject.toml ./
COPY scripts ./scripts
COPY src ./src

# Vendor Hermes upstream engine subset at build time (headless mode).
RUN chmod +x scripts/vendor-hermes.sh && ./scripts/vendor-hermes.sh main

ENV HERMES_UPSTREAM=1
ENV NEOMETIS_HEADLESS=1

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
