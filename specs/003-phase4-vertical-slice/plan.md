# Implementation Plan: Phase 4 PDF-to-Cited-Answer Vertical Slice

**Feature**: `003-phase4-vertical-slice` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Implement a local, executable vertical slice using FastAPI, SQLite, local filesystem object storage, persistent ChromaDB, a PDF parser, and React/TypeScript. Follow the established OpenAPI/Pydantic contracts where practical. The API owns a development-only local principal, document lifecycle, persistence, retrieval filters, and evidence validation. Mock embedding and answer-generation adapters keep the slice deterministic and credential-free.

## Technical Context

**Language/Version**: Python 3.11+; TypeScript/React on Node.js.
**Dependencies**: FastAPI, Uvicorn, Pydantic contracts, pypdf, ChromaDB; React, Vite, TypeScript.
**Storage**: SQLite, filesystem originals, persistent ChromaDB beneath `.local-data/` by default.
**Testing**: Pytest/FastAPI TestClient integration tests; frontend production build; existing contract tests.
**Runtime**: Local development only; no cloud provisioning.

## Design

- `apps/api/src/rag_platform_api/` contains HTTP routes, settings, SQLite repository, local object storage, PDF chunking, vector-store adapter, mock model adapters, and RAG orchestration.
- Uploads use a short-lived random local URL token tied to tenant/document/version, declared size, and media type. Completion verifies the uploaded bytes/checksum before indexing.
- The SQLite metadata source of truth records document lifecycle and conversations. ChromaDB stores page-aware chunks and mandatory tenant/document metadata.
- A deterministic hashing embedder and evidence-copying mock generator are behind provider interfaces; neither claims hosted-model semantics.
- The React client uses the local-only development identity and existing upload/chat contracts. The identity mode refuses startup/use outside development.
- Do not weaken existing API contracts or allow client-provided tenant IDs to authorize any operation.

## Scope and Deferred Work

This phase is one-user local demonstration with a development-only identity and a synchronous local indexing task. It does not implement production OIDC, malware scanning, DOCX/PPTX, durable worker queues, hosted AI providers, AWS adapters, deletion workflows, or production-ready tenancy.
