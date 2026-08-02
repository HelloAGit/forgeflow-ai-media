# ForgeFlow AI Media

A production-ready backend API built with FastAPI for generating and managing AI media assets using the Genblaze SDK and Backblaze B2 storage.

## Project Structure

```
.
├── app/
│   ├── config.py          # Pydantic settings (reads from .env)
│   ├── main.py            # FastAPI application entry point
│   ├── routes/
│   │   ├── assets.py      # Asset retrieval endpoints
│   │   └── generations.py # Media generation endpoints
│   └── services/
│       ├── pipeline.py    # Genblaze SDK integration
│       └── storage.py     # Backblaze B2 (S3-compatible) storage
├── tests/                 # Automated tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Development/test dependencies
└── .env.example           # Environment variable template
```

## Quick Start (Local)

### Prerequisites

- Python 3.11+
- A Backblaze B2 account with an application key and bucket
- A Genblaze (GMI) API key

### 1. Clone and configure

```bash
git clone https://github.com/HelloAGit/forgeflow-ai-media.git
cd forgeflow-ai-media

# Copy the template and fill in your credentials
cp .env.example .env
```

Edit `.env` and set:

| Variable      | Description                                                 | Example              |
|---------------|-------------------------------------------------------------|----------------------|
| `B2_KEY_ID`   | Backblaze B2 application key ID                             | `abc123def456`       |
| `B2_APP_KEY`  | Backblaze B2 application key secret                         | `K001...`            |
| `B2_BUCKET`   | B2 **bucket name** (not the bucket ID)                      | `my-media-bucket`    |
| `B2_REGION`   | B2 S3-compatible region (`<area>-<direction>-<NNN>`)        | `eu-central-003`     |
| `GMI_API_KEY` | Genblaze (GMI) API key                                      | `gmi-xxxxx`          |

### 2. Install dependencies and run

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

The API will be available at <http://localhost:8000>.

### 3. Verify health

```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"forgeflow-api"}
```

### 4. Run tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Quick Start (Docker)

```bash
cp .env.example .env   # fill in your credentials

docker compose up --build
```

The API is exposed on port **8000**. Verify:

```bash
curl http://localhost:8000/health
```

## API Endpoints

| Method | Path                          | Description                              |
|--------|-------------------------------|------------------------------------------|
| GET    | `/health`                     | Service health check                     |
| POST   | `/api/v1/generations/`        | Generate AI media from a text prompt     |
| GET    | `/api/v1/assets/{filename}`   | Get a pre-signed URL for a stored asset  |

### Example: Generate media

```bash
curl -X POST http://localhost:8000/api/v1/generations/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a futuristic cityscape at sunset"}'
```

## Notes

- **B2_REGION** must follow the format `<area>-<direction>-<NNN>` (e.g. `eu-central-003`, `us-west-004`). The app validates this at startup and emits a clear error if the value is wrong.
- **B2_BUCKET** must be the human-readable **bucket name**, not the internal bucket ID.
- When the `genblaze` SDK is not installed, `pipeline.py` logs a warning and returns a 1×1 white placeholder PNG so the rest of the API remains functional.
