import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

import chromadb


TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class AnswerGenerator(Protocol):
    def answer(self, evidence: str, question: str) -> str: ...


class DeterministicEmbedder:
    """Local feature-hash embedder for repeatable development, not production quality."""

    dimensions = 256

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN_PATTERN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            number = int.from_bytes(digest, "big")
            index = number % self.dimensions
            vector[index] += -1.0 if number & (1 << 63) else 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector


class EvidenceCopyAnswerGenerator:
    """Returns a short verbatim evidence excerpt; does not emulate an LLM."""

    def answer(self, evidence: str, question: str) -> str:
        del question
        excerpt = " ".join(evidence.split())[:600]
        if len(evidence) > 600:
            excerpt += "…"
        return f'The retrieved document states: “{excerpt}”'


@dataclass(frozen=True)
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    content: str
    page_number: int
    score: float


class ChromaVectorStore:
    def __init__(self, path: str) -> None:
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name="rag_platform_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        *,
        tenant_id: UUID,
        document_id: UUID,
        version_id: UUID,
        chunks: list[tuple[UUID, str, int]],
        embedder: Embedder,
    ) -> None:
        if not chunks:
            raise ValueError("No extractable text was found in the PDF.")
        self.collection.upsert(
            ids=[str(chunk_id) for chunk_id, _, _ in chunks],
            documents=[text for _, text, _ in chunks],
            embeddings=[embedder.embed(text) for _, text, _ in chunks],
            metadatas=[
                {
                    "tenant_id": str(tenant_id),
                    "document_id": str(document_id),
                    "version_id": str(version_id),
                    "page_number": page_number,
                }
                for _, _, page_number in chunks
            ],
        )

    def query(
        self,
        *,
        tenant_id: UUID,
        question: str,
        embedder: Embedder,
        document_ids: list[UUID],
        limit: int,
    ) -> list[SearchResult]:
        where: dict[str, object] = {"tenant_id": str(tenant_id)}
        if document_ids:
            where = {
                "$and": [
                    {"tenant_id": str(tenant_id)},
                    {"document_id": {"$in": [str(item) for item in document_ids]}},
                ]
            }
        result = self.collection.query(
            query_embeddings=[embedder.embed(question)],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            SearchResult(
                chunk_id=UUID(chunk_id),
                document_id=UUID(metadata["document_id"]),
                version_id=UUID(metadata["version_id"]),
                content=content,
                page_number=int(metadata["page_number"]),
                score=1.0 - float(distance),
            )
            for chunk_id, content, metadata, distance in zip(
                ids, documents, metadatas, distances
            )
        ]

    def delete_document(self, tenant_id: UUID, document_id: UUID) -> None:
        self.collection.delete(
            where={
                "$and": [
                    {"tenant_id": str(tenant_id)},
                    {"document_id": str(document_id)},
                ]
            }
        )
