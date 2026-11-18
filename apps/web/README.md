# Web Application

React/TypeScript client for the Phase 4 PDF upload, ingestion status, conversation, streamed answer, and citation path.

## Run

```powershell
npm install
npm run dev
```

The app runs at `http://localhost:5173` and calls the local API at `http://localhost:8000`. Configure `VITE_API_BASE_URL` and `VITE_DEV_BEARER_TOKEN` in an ignored `.env.local` only when changing local defaults.

The sign-in indicator is a development placeholder, not authentication. Use only with the local development API and do not expose it to untrusted networks.
