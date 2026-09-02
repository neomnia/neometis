# NéoMêtis — Local & Remote Deployment

## Architecture

### Local (dev / prod on your machine)

```
[ Browser ] ──► http://localhost:8000 ──► [ neometis-app: Chainlit + FastAPI ]
                                              │
                                              ▼
                                         [ Qdrant ]
```

- No TLS, no Traefik — fastest iteration
- Chainlit UI at `/`, API at `/api/*`, health at `/health`
- Auth disabled unless `CHAINLIT_AUTH_SECRET` is set

### Remote (self-hosted server / K3s + Docker)

```
[ Browser ] ──HTTPS──► [ Traefik :443 ] ──► [ neometis-app :8000 ]
                         │ TLS (Let's Encrypt)
                         │ WebSocket + SSE passthrough
                         └─ optional Basic Auth middleware
```

## Quick start — Local

```bash
cp .env.example .env
docker compose up --build
# → http://localhost:8000  (Chainlit workbench)
# → http://localhost:8000/health
# → http://localhost:8000/api/chat/stream  (SSE)
```

Direct Python (without Docker):

```bash
pip install -r requirements.txt
EMBEDDING_PROVIDER=hash uvicorn src.api.main:app --reload --port 8000
```

## Remote deployment with Traefik

1. Point DNS `neometis.your-domain.com` to your server
2. Configure `.env`:

```env
DOMAIN_NAME=neometis.your-domain.com
ACME_EMAIL=admin@your-domain.com
TRAEFIK_ENABLE=true
TRAEFIK_BASIC_AUTH_MIDDLEWARE=neometis-auth
BASIC_AUTH_USERS=admin:$$apr1$$....   # htpasswd -nb admin 'your-password'
CHAINLIT_AUTH_SECRET=change-me-long-random-string
NEOMETIS_AUTH_USER=admin
NEOMETIS_AUTH_PASSWORD=your-password
```

3. Launch:

```bash
DOMAIN_NAME=neometis.your-domain.com docker compose --profile remote up -d --build
```

### Security options

| Layer | Mechanism | Env vars |
|-------|-----------|----------|
| Traefik (Option A) | Basic Auth middleware | `BASIC_AUTH_USERS`, `TRAEFIK_BASIC_AUTH_MIDDLEWARE=neometis-auth` |
| Chainlit (Option B) | Password auth callback | `CHAINLIT_AUTH_SECRET`, `NEOMETIS_AUTH_USER`, `NEOMETIS_AUTH_PASSWORD` |

Both can be combined. For local dev, leave `CHAINLIT_AUTH_SECRET` empty.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `8000` | Host port for neometis-app |
| `RAG_QDRANT_HOST` | `qdrant` | Qdrant hostname (Docker network) |
| `RAG_QDRANT_PORT` | `6333` | Qdrant REST port |
| `QDRANT_URL` | derived | Full URL override |
| `CHAINLIT_AUTH_SECRET` | — | Enables Chainlit session auth when set |
| `DOMAIN_NAME` | `neometis.local` | Traefik Host rule |
| `TRAEFIK_ENABLE` | `false` | Set `true` on remote deployments |

## Optional Next.js UI

The legacy Next.js chat UI remains available behind a Compose profile:

```bash
docker compose --profile nextjs up
# → http://localhost:3000
```

Chainlit is the primary workbench UI going forward.
