# ⚽ football-api — SofaScore REST API (sofascore-wrapper)

Cette API est basée sur **sofascore-wrapper** (async, Playwright/Chromium). :contentReference[oaicite:6]{index=6}

## 🚀 Lancer
```bash
cp .env.example .env
docker compose up --build
```

Docs OpenAPI (auto FastAPI) :
- http://localhost:8000/docs
- http://localhost:8000/redoc

## Endpoints principaux
- GET  /api/health
- GET  /api/sofa/search?q=saka&sport=football
- GET  /api/sofa/player/{player_id}
- GET  /api/sofa/team/{team_id}
- GET  /api/sofa/match/{match_id}

Persistance (JSONB, Postgres) :
- POST /api/store/player/{player_id}
- POST /api/store/team/{team_id}
- POST /api/store/match/{match_id}

Rate limit:
- par IP, par minute (config `RATE_LIMIT_PER_MINUTE`)

Cache Redis:
- TTL `SOFA_CACHE_TTL` (seconds)

## Admin (si activé)
- POST /api/admin/warmup (header \`X-API-KEY\`)

Ex:
\`\`\`bash
curl -X POST "http://localhost:8000/api/admin/warmup?q=saka&sport=football" \\
  -H "X-API-KEY: change-this-key"
\`\`\`

## Tests
```bash
docker compose run --rm api pytest -q
```

## Note Playwright
Le module requiert Playwright + installation Chromium (déjà géré dans le Dockerfile). :contentReference[oaicite:7]{index=7}
