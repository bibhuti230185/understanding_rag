# Phase 0, 2, and 3 Review Quickstart

This feature establishes product framing, interface contracts, and repository ownership. It does not start application services or provision cloud resources.

## Review

1. Read `docs\product\product-brief.md` and `docs\product\slo-proposals.md`; verify the brief fits a one-page framing and all six SLO proposals/measurement definitions are understood as provisional.
2. Read `docs\product\assumptions-log.md` and `docs\product\risk-register.md`; confirm open product/security/platform decisions have an owner before implementation.
3. Validate `docs\contracts\openapi.yaml` as OpenAPI 3.1 and inspect document, conversation, chat/SSE, feedback, evaluation, and health operations.
4. Validate `docs\contracts\events.schema.json` as JSON Schema 2020-12; test each of the four event variants and reject extra fields.
5. In PowerShell, set `$env:PYTHONPATH="$PWD\packages\contracts\python"` and run `python -m unittest discover -s tests\contract -p test_*.py`; this validates representative payloads and invalid upload/chat input using Pydantic v2.
6. Read `docs\contracts\domain-model.md`, `rag-state.md`, `idempotency-and-tracing.md`, and `authorization-and-pagination.md`; trace tenant scope, state transitions, retries, event metadata, and errors.
7. Read `docs\architecture\repository-structure.md` and inspect the app/package/test/infra/documentation README markers. Confirm they distinguish placeholders from executable systems.

## Acceptance Checks

- OpenAPI paths and local references resolve, and all tenant-facing operations inherit bearer authentication.
- No request accepts tenant ID as authoritative scope; auth and resource policies are documented.
- Valid request/event payloads pass, while invalid type/size, empty chat, key conflict, or unknown event fields are rejected according to contract.
- All four domain event names and all required job states are defined.
- Every planned monorepo directory has an ownership/readme marker.
- SLO targets and 25 MB/100-page benchmark envelope remain labeled provisional.
