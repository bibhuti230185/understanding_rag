# API Application

Target: FastAPI modular monolith. Planned modules: auth/tenant, documents, ingestion coordination, retrieval, chat, conversations, feedback, evaluations, health, and admin. Route handlers map `packages/contracts` to application use cases; business policies and infrastructure clients remain outside the HTTP layer.

**Status**: Scaffold only. No handlers or runtime dependencies are implemented yet.
