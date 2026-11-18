# Feature Specification: Phase 4 PDF-to-Cited-Answer Vertical Slice

**Feature Branch**: `003-phase4-vertical-slice`
**Created**: 2026-11-18
**Status**: In progress
**Input**: Phase 4 roadmap in `RAG_Lucid_AI_Arch.docx`

## User Scenarios & Testing

### User Story 1 - Upload and index a PDF (Priority: P1)

As a local developer, I can upload a PDF through the web client and see it indexed so I can verify the first document-to-retrieval path end to end.

**Independent Test**: Upload a valid PDF using the upload-intent, local upload, and completion operations; verify the document reaches `indexed` and a repeated completion does not duplicate its chunks.

**Acceptance Scenarios**:

1. **Given** a valid PDF within the configured upload limit, **When** I upload and complete it, **Then** the API stores the original, extracts page-aware text, chunks it, and indexes it in persistent ChromaDB.
2. **Given** an unsupported, malformed, encrypted, empty, oversized, or checksum-mismatched file, **When** I upload or complete it, **Then** the API rejects it with a typed error and it is not searchable.
3. **Given** a client repeats an operation with the same idempotency key and payload, **When** it retries, **Then** it receives the original logical result without duplicate document or vector writes.

### User Story 2 - Ask a question and inspect evidence (Priority: P1)

As a local developer, I can ask a question about indexed documents and receive a response with citations to page-level evidence.

**Independent Test**: Create a conversation, stream a question against indexed content, and verify terminal SSE data cites only retrieved, tenant-scoped chunks; a no-evidence query returns the explicit insufficient-evidence terminal event.

**Acceptance Scenarios**:

1. **Given** matching indexed evidence, **When** I ask a question, **Then** retrieval is tenant-scoped and the deterministic mock generator returns evidence-grounded text and verifiable citations.
2. **Given** no authorized matching evidence, **When** I ask a question, **Then** no unsupported answer is generated and the stream terminates with `message.insufficient_evidence`.
3. **Given** an invalid or unauthorized conversation/document, **When** I query it, **Then** access is denied without exposing cross-tenant resource existence.

### User Story 3 - Run the vertical slice locally (Priority: P2)

As a contributor, I can start the API and React app with local development configuration and run the integration test without cloud credentials or hosted-model access.

**Independent Test**: Follow the Phase 4 quickstart from a clean checkout, run backend tests and frontend build, then exercise the upload-to-answer journey.

**Acceptance Scenarios**:

1. **Given** local development mode, **When** the apps are started, **Then** the UI's login placeholder uses a clearly development-only principal and no cloud credentials are required.
2. **Given** production mode or configuration, **When** the development-only identity is requested, **Then** it is rejected; this phase does not claim production authentication or deployment readiness.

## Edge Cases

- Duplicate upload intent, completion, or chat requests must not create duplicate logical records or messages.
- A PDF with no extractable text, encryption, or malformed page content fails with an observable status.
- Upload URL tokens are single-object, short-lived, and checked with exact declared size and content type.
- A request with document scope cannot expand the caller's tenant scope.
- An API process restart must preserve documents, job state, conversations, and vectors in configured local storage.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST implement the existing upload-intent, upload completion, document list/status, conversation creation/history, health, and chat SSE contracts required for this slice.
- **FR-002**: The upload path MUST persist a validated PDF locally, extract page-aware text, create bounded overlapping chunks, and index them in a persistent ChromaDB collection.
- **FR-003**: The API MUST derive tenant/user scope from an authenticated principal. The only built-in principal MUST be explicitly development-only and disabled outside development mode.
- **FR-004**: Retrieval MUST apply the tenant filter in ChromaDB on every query and MUST independently verify any requested document scope.
- **FR-005**: The chat workflow MUST use an application-owned embedding and answer-generator boundary. The first implementation MUST be deterministic, local, and clearly identified as a mock; it MUST NOT imply production model quality.
- **FR-006**: The stream MUST follow the existing SSE event contracts, emit only validated evidence-based answer content, and end with a terminal completion, insufficient-evidence, or error event.
- **FR-007**: Documents, conversations, and messages MUST persist in SQLite by default; originals and ChromaDB data MUST persist under a configurable local data directory.
- **FR-008**: The React application MUST provide the local login placeholder, PDF upload/status, conversation creation, streamed chat, and citation display.
- **FR-009**: Upload operations MUST enforce supported PDF media type, configured size limit, checksum when supplied, file magic, and idempotency.
- **FR-010**: This feature MUST NOT provision cloud resources, require third-party model credentials, or claim production authentication, scanning, or operational readiness.

### Key Entities

- **Local principal**: Development-only fixed tenant and user identity, derived server-side rather than from request data.
- **Document version**: Immutable PDF bytes, checksum, local object reference, and ingestion status.
- **Chunk**: Page-aware bounded text and tenant/document/version metadata stored in ChromaDB.
- **Conversation/message**: Locally persisted tenant-owned chat history with terminal status and verified citations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A developer can complete PDF upload-to-indexing-to-cited-answer locally without AWS or model-provider credentials.
- **SC-002**: Contract-aligned integration tests cover valid upload/query, malformed or unsupported PDFs, idempotency, insufficient evidence, and tenant-scoped retrieval.
- **SC-003**: The React production build succeeds and the UI presents ingestion status and citation source locations.
- **SC-004**: Restarting the API with the same data directory preserves indexed documents and conversation history.

## Assumptions

- Initial implementation uses local filesystem storage, SQLite, and persistent ChromaDB, as selected for Phase 4.
- The model and embedding providers are deterministic local mock adapters, as selected for Phase 4. Provider interfaces allow later replacement.
- Only PDF parsing is in this slice. DOCX/PPTX support, real identity, hosted LLMs, queue-backed workers, and AWS infrastructure are deferred.
- Document deletion, durable queue workers, and production malware scanning are deferred; this first vertical slice does not claim their lifecycle guarantees.
- Local development identity is not a security control and is never enabled in non-development environments.
- The provisional 25 MB/100-page SLO envelope is a benchmark hypothesis, not a production upload commitment; upload size remains configurable.
