# ADR-0002: ChromaDB Behind an Application-Owned Vector-Store Port

- **Status**: Accepted for initial architecture; production persistence requires validation
- **Date**: 2026-11-17
- **Context**: The source roadmap selects ChromaDB for a hands-on first release while requiring a path to a managed production vector database. Retrieval must remain tenant-scoped and the application should not depend on a vendor SDK.

## Decision

Define an application-owned vector-store port for upsert, tenant/document-scoped search, deletion, and health operations. Implement ChromaDB as an infrastructure adapter. Keep Chroma-specific records, query APIs, and configuration inside that adapter. Store the source of truth for document/index lifecycle in PostgreSQL; treat vector contents as derived.

## Consequences

- ChromaDB supports an accessible initial learning implementation while preserving a provider migration boundary.
- The adapter must enforce required tenant/document filters and expose enough metadata for source citations.
- The port should represent only capabilities the use cases need, not mirror a Chroma SDK.
- ChromaDB durability, backups, restore, scaling, and upgrade behavior are explicit production risks and must be tested before production.
- A managed vector database is not selected until scale, availability, cost, data-residency, and operations requirements are known.

## Alternatives Considered

- **Use ChromaDB types throughout retrieval/domain code**: Rejected; makes testing and later migration depend on vendor-specific schemas and semantics.
- **Choose a managed vector service immediately**: Deferred; no validated workload, budget, or operational constraints justify a specific provider yet.
- **Use PostgreSQL vector extensions from day one**: Deferred; not selected in the source roadmap and would alter the initial hands-on vector-store choice.

