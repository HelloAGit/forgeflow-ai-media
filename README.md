# ForgeFlow AI Media

ForgeFlow is an early-stage prototype for orchestrating generative-media workflows with Genblaze and storing generated assets and provenance records in Backblaze B2.

**Status:** frontend demo available; backend integration under development.

## Deployment Status

- **Frontend demo:** https://forgeflow-ai-media.swoony-map-9040.chatgpt.site/
- **Backend API:** Not deployed

> Note: Do not advertise `/docs` or `/openapi.json` until a real FastAPI backend deployment is verified.

## Current Repository Structure

```text
app/
├── main.py
├── config.py
├── routes/
└── services/
Dockerfile
docker-compose.yml
.env.example
```

## Quick Start (Local)

### Option A: Run with Python

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env template and set real values:
   ```bash
   cp .env.example .env
   ```
4. Start API:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Option B: Run with Docker Compose

```bash
docker compose up --build
```

## Limitations (Current Prototype)

- Some media generation/storage flows may still be scaffolded or mocked.
- Provider integration hardening and production deployment are in progress.

## Security

- Never commit credentials in source, commits, pull requests, issues, or chat.
- Use only runtime secret configuration (deployment environment / secret manager).
