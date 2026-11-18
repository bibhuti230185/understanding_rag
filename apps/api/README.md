# API Application

FastAPI API for the Phase 4 local PDF-to-cited-answer vertical slice. It uses SQLite for metadata, local filesystem object storage, persistent ChromaDB, and deterministic local mock embedding/answer adapters. The local API accepts only PDFs.

## Run

From the repository root, install the contracts and API:

```powershell
python -m pip install -e .\packages\contracts -e '.\apps\api[test]'
python -m uvicorn rag_platform_api.main:app --app-dir apps/api/src --host 127.0.0.1 --port 8000
```

Run API and contract tests with:

```powershell
python -m pytest -c apps/api/pyproject.toml
```

The API defaults to `http://localhost:8000`, a local bearer token of `local-dev-token`, and persistent state in `.local-data/`. Configure `RAG_DATA_DIR` and `RAG_DEV_BEARER_TOKEN` as needed. The fixed local identity is explicitly development-only; the application refuses to start outside `RAG_ENV=development`.

This is not production authentication, durable queue processing, malware scanning, or a hosted LLM integration. Do not expose the local API to untrusted networks.
