# Phase 4 Local Development

This local-only vertical slice uses a development bearer token, SQLite, filesystem originals, persistent ChromaDB, PDF parsing, and deterministic mock embedding/answer adapters. It does not need cloud or hosted-model credentials.

## Prerequisites

- Python 3.11 or newer
- Node.js and npm
- A PDF to test with

## Install

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .\packages\contracts -e '.\apps\api[test]'
```

In another PowerShell terminal:

```powershell
Set-Location apps\web
npm install
```

## Run

Start the API from the repository root:

```powershell
python -m uvicorn rag_platform_api.main:app --app-dir apps/api/src --host 127.0.0.1 --port 8000
```

Start the web app in the second terminal:

```powershell
npm run dev
```

Open `http://localhost:5173`, upload a PDF, wait for the indexed status, and ask a question. The web app stores no credentials; the API uses `local-dev-token` and a fixed development tenant/user. Change local settings with environment variables:

- `RAG_DATA_DIR`: directory for SQLite, originals, and ChromaDB; defaults to `.local-data/`.
- `RAG_DEV_BEARER_TOKEN`: local demo bearer token; defaults to `local-dev-token`.
- `RAG_MAX_UPLOAD_BYTES`: maximum PDF size; defaults to 25 MiB.
- `VITE_API_BASE_URL`: API URL; defaults to `http://localhost:8000`.
- `VITE_DEV_BEARER_TOKEN`: local demo token sent by the browser; defaults to `local-dev-token`.

The local upload limit is configurable and is not an approved production policy. Never expose this setup to an untrusted network; production identity, scanning, queue-backed processing, and real model providers are not implemented.

## Tests and Build

From the repository root with the Python environment activated:

```powershell
python -m pytest -c apps/api/pyproject.toml
```

From `apps\web`:

```powershell
npm run build
```

The API tests cover upload validation/idempotency, PDF indexing, page citations, insufficient evidence, and tenant-scoped access. Local state is persistent; tests use temporary directories.
