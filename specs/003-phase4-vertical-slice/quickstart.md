# Phase 4 Local Quickstart

This quickstart is completed alongside the implementation. The slice is local-only and uses a development identity, deterministic mock embeddings/answers, SQLite, filesystem storage, and persistent ChromaDB.

## Security Boundary

Do not expose the development API to an untrusted network. The local bearer token is a demo credential, not authentication. Production identity and hosted AI providers are deferred.

## Verification

The implementation will document commands to install Python packages, run API tests, start FastAPI and Vite, upload a PDF, create a conversation, and ask a cited question.
