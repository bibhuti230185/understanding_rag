# ADR-0001: Modular API Monolith with a Separate Ingestion Worker

- **Status**: Accepted for initial architecture
- **Date**: 2026-11-17
- **Context**: The product needs authenticated document operations, chat, feedback, and admin/evaluation journeys, alongside long-running parsing and embedding jobs. The source roadmap recommends a modular monolith first, with extraction boundaries for later service decomposition.

## Decision

Keep interactive use cases in one modular FastAPI application and deploy ingestion as a separate worker. Organize application modules around bounded contexts and keep domain/application logic behind ports for infrastructure integrations.

## Consequences

- Fewer deployable services and simpler initial operations than a microservice-per-context design.
- API and worker can scale, deploy, and fail independently according to interactive latency versus asynchronous job demand.
- Module boundaries must be enforced in code; one deployable API must not become an unstructured shared layer.
- Extract a context into a service only when ownership, scaling, availability, or team boundaries demonstrate a concrete need.

## Alternatives Considered

- **Microservice per bounded context**: Rejected initially; adds network contracts, deployment pipelines, and distributed failure modes before independent scaling needs are known.
- **One process for API and ingestion**: Rejected; long-running parsing/embedding work can consume interactive capacity and is harder to retry independently.

