# ForgeFlow AI Media

ForgeFlow is an early-stage prototype for orchestrating generative-media workflows with Genblaze and storing generated assets and provenance records in Backblaze B2.

**Status:** frontend demo available; **backend not deployed**. Docker builds and tests pass locally. Do not advertise `/docs` until a real backend deployment is verified.

## Deployment Status

- **Frontend demo:** https://forgeflow-ai-media.swoony-map-9040.chatgpt.site/
- **Backend API:** Not deployed

## Architecture / Data Flow

```
POST /api/v1/generations/
  │
  ├─ Validate: prompt (3–1000 chars) · media_type · model name
  │
  ├─ GenblazePipeline.generate_media()
  │    └─ genblaze-core Pipeline
  │         └─ GMICloudImageProvider  (GMI_API_KEY)
  │              └─ polls GMICloud until image ready
  │                   └─ downloads image bytes from provider CDN (httpx)
  │
  ├─ StorageService.upload_file(bytes, "generations/{uuid}/output.{ext}")
  │    └─ private put_object → Backblaze B2 (boto3, S3-compatible)
  │
  ├─ StorageService.upload_file(provenance_json, "generations/{uuid}/provenance.json")
  │    └─ records: id · model · prompt_sha256 · media_type · asset_key · created_at
  │
  └─ StorageService.generate_presigned_url("generations/{uuid}/output.{ext}")
       └─ 1-hour presigned GET URL returned to client

GET /api/v1/assets/{object_key}
  └─ Returns a fresh presigned URL for any stored object

GET /health
  └─ Always 200; no credentials required
```

## Required Environment Variables

Copy `.env.example` to `.env` and fill in **real** values before running locally.

| Variable | Description |
|---|---|
| `GMI_API_KEY` | GMICloud API key (https://console.gmicloud.ai/) |
| `GMI_BASE_URL` | Override GMICloud queue URL (optional; defaults to production) |
| `B2_ENDPOINT` | Backblaze B2 S3 endpoint, e.g. `https://s3.eu-central-003.backblazeb2.com` |
| `B2_REGION` | B2 region code, e.g. `eu-central-003` |
| `B2_BUCKET` | B2 bucket **name** (not bucket ID) |
| `B2_ACCESS_KEY_ID` | B2 application key ID |
| `B2_SECRET_ACCESS_KEY` | B2 application key |
| `CORS_ORIGINS` | Comma-separated allowed origins (default: `http://localhost:3000`) |

**Never commit real credentials.** Store secrets only in your deployment platform's secret manager.

## Quick Start (Local)

### Option A: Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option B: Docker Compose

```bash
cp .env.example .env   # fill in real values
docker compose up --build
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests use mocked SDK boundaries — no real credentials or network access needed.

## Supported Image Models

Pass one of these as `model` in the generation request:

| Model slug | Notes |
|---|---|
| `seedream-5.0-lite` | Default — fast, general purpose |
| `flux-kontext-pro` | FLUX-based, high detail |
| `gemini-2.5-flash-image` | Gemini image generation |

## Current Repository Structure

```
app/
├── main.py          # FastAPI app, CORS from CORS_ORIGINS env var
├── config.py        # pydantic-settings, lazy credential validation
├── routes/
│   ├── generations.py   # POST /api/v1/generations/
│   └── assets.py        # GET /api/v1/assets/{key}
└── services/
    ├── pipeline.py  # Genblaze SDK integration (GMICloudImageProvider)
    └── storage.py   # Backblaze B2 via boto3 (private objects + presigned URLs)
tests/
├── test_config.py
├── test_health.py
├── test_generations.py
├── test_pipeline.py
└── test_storage.py
Dockerfile
docker-compose.yml
requirements.txt
requirements-dev.txt
.env.example
.github/workflows/ci.yml
```

## Security

- **Rotate any previously committed credentials immediately.** Earlier git history may contain real-looking GMI and Backblaze credentials. Revoke them at each provider, then scrub history with `git-filter-repo` or BFG.
- Enable **GitHub secret scanning and push protection** in repository settings.
- Never commit, paste in chat, or include in issues any real API key or secret.
- Use your deployment platform's secret manager (e.g. Fly.io secrets, Railway variables, GitHub Actions secrets) for all credentials at runtime.
- All B2 objects are uploaded **privately**; assets are only accessible via short-lived presigned URLs.
- API errors return a structured `{"error": "...", "request_id": "..."}` — raw exception text is never sent to clients.

## Deployment Checklist

- [ ] Old credentials rotated and removed from git history
- [ ] GitHub secret scanning enabled
- [ ] Real `GMI_API_KEY` set in secret manager
- [ ] B2 bucket created (private), credentials scoped to that bucket
- [ ] `B2_*` variables set in secret manager
- [ ] `CORS_ORIGINS` set to actual frontend domain
- [ ] `docker build` succeeds on target platform
- [ ] `GET /health` returns 200 on deployed URL
- [ ] End-to-end generation test with real credentials passes
- [ ] README deployment status updated to reflect live backend
