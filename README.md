# ForgeFlow AI Media

A production-ready monorepo containing a React/Next.js interface and a FastAPI backend, designed for generating and managing AI media assets.

## Project Structure
- `/apps/web` - Next.js frontend
- `/apps/api` - FastAPI backend
- `/packages/shared` - Shared schemas and types

## Deployed API
- Base URL: `https://forgeflow-ai-media.swoony-map-9040.chatgpt.site/`
- Interactive API Docs (Swagger UI): `https://forgeflow-ai-media.swoony-map-9040.chatgpt.site/docs`
- OpenAPI schema: `https://forgeflow-ai-media.swoony-map-9040.chatgpt.site/openapi.json`

## Quick Start
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Run the API service (from the API app directory):
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Verify locally:
   - API: `http://localhost:8000`
   - Docs: `http://localhost:8000/docs`

## Environment Variables
Configure these values in `.env`:
- `B2_KEY_ID`
- `B2_APP_KEY`
- `B2_BUCKET`
- `B2_REGION`
- `GMI_API_KEY`

> Security note: Never commit real API keys or secrets to the repository. Use environment variables and rotate any exposed credentials.
