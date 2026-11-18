# RAG Lucid AI Architecture

This repository develops the multi-tenant document knowledge assistant described in `RAG_Lucid_AI_Arch.docx`.

## Current Deliverables

- [Product brief](docs/product/product-brief.md), [provisional SLOs](docs/product/slo-proposals.md), [assumptions](docs/product/assumptions-log.md), and [risk register](docs/product/risk-register.md)
- [Architecture overview](docs/architecture/overview.md), [container view](docs/architecture/containers.md), [ingestion flow](docs/architecture/ingestion-sequence.md), [query flow](docs/architecture/online-query-sequence.md), [deployment](docs/architecture/deployment.md), and [threat model](docs/architecture/threat-model.md)
- [API and event contracts](docs/contracts/README.md) with Pydantic models in `packages/contracts/`
- [Monorepo structure and ownership](docs/architecture/repository-structure.md)
- Spec Kit feature records in `specs/001-rag-hld/` and `specs/002-product-contracts-structure/`

The app/package READMEs are structural ownership markers, not runnable services. SLOs are provisional. No cloud resources have been provisioned; Phase 4 is the first executable vertical slice.

