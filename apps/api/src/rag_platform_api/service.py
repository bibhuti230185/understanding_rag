import hashlib
import json
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, status
import chromadb
from pypdf.errors import PdfReadError

from rag_platform_api.identity import Principal
from rag_platform_api.ingestion import extract_pdf_chunks
from rag_platform_api.rag import (
    ChromaVectorStore,
    DeterministicEmbedder,
    EvidenceCopyAnswerGenerator,
)
from rag_platform_api.settings import Settings
from rag_platform_api.storage import Database, utc_now
from rag_contracts import (
    Citation,
    Conversation,
    Document,
    DocumentStatus,
    IngestionJob,
    Message,
    MessageRole,
    SseCompleted,
    SseInsufficientEvidence,
    TokenUsage,
)


SAFE_FILE_NAME = re.compile(r"^[^/\\\\\x00-\x1f\x7f]+$")
logger = logging.getLogger(__name__)


class PlatformService:
    def __init__(self, settings: Settings) -> None:
        if settings.environment != "development" and settings.dev_bearer_token == "local-dev-token":
            raise RuntimeError("The default development bearer token cannot be used outside development.")
        if settings.max_upload_bytes < 1:
            raise ValueError("RAG_MAX_UPLOAD_BYTES must be positive.")
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings = settings
        self.db = Database(settings.data_dir / "metadata.sqlite3")
        self.objects_dir = settings.data_dir / "objects"
        self.objects_dir.mkdir(parents=True, exist_ok=True)
        self.vectors = ChromaVectorStore(str(settings.data_dir / "chroma"))
        self.embedder = DeterministicEmbedder()
        self.answer_generator = EvidenceCopyAnswerGenerator()

    def _existing_idempotent(
        self, principal: Principal, operation: str, key: str, payload_hash: str
    ) -> dict | None:
        row = self.db.get_idempotent_response(principal.tenant_id, operation, key)
        if row is None:
            return None
        if row["payload_hash"] != payload_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key was already used with a different payload.",
            )
        return self.db.decode_idempotent_response(row)

    def create_upload_intent(
        self, principal: Principal, request, idempotency_key: str
    ) -> dict:
        payload = request.model_dump(mode="json")
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        existing = self._existing_idempotent(
            principal, "upload-intent", idempotency_key, payload_hash
        )
        if existing is not None:
            return existing
        if request.media_type != "application/pdf" or not request.file_name.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Phase 4 accepts PDF files only.",
            )
        if not SAFE_FILE_NAME.fullmatch(request.file_name) or request.file_name in {".", ".."}:
            raise HTTPException(status_code=400, detail="Invalid file name.")
        if request.size_bytes > self.settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="File exceeds the configured upload limit.")

        document_id, version_id = uuid4(), uuid4()
        upload_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.settings.upload_token_ttl_seconds)
        response = {
            "document_id": str(document_id),
            "version_id": str(version_id),
            "upload_url": (
                f"{self.settings.public_base_url}/v1/documents/{document_id}"
                f"/versions/{version_id}/upload?token={upload_token}"
            ),
            "expires_at": expires_at.isoformat(),
            "required_headers": {"Content-Type": request.media_type},
        }
        object_path = self.objects_dir / f"{version_id}.pdf"
        now_string = now.isoformat()
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    document_id, version_id, tenant_id, owner_user_id, file_name,
                    media_type, size_bytes, expected_sha256, object_path, upload_token,
                    upload_expires_at, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(document_id), str(version_id), str(principal.tenant_id),
                    str(principal.user_id), request.file_name, request.media_type,
                    request.size_bytes, request.sha256, str(object_path), upload_token,
                    expires_at.isoformat(), DocumentStatus.QUEUED.value,
                    now_string, now_string,
                ),
            )
        self.db.insert_idempotent_response(
            principal.tenant_id, "upload-intent", idempotency_key, payload_hash, response
        )
        return response

    def upload_file(
        self,
        principal: Principal,
        document_id: UUID,
        version_id: UUID,
        token: str,
        content_type: str,
        body: bytes,
    ) -> None:
        row = self.db.execute_one(
            """
            SELECT * FROM documents WHERE document_id = ? AND version_id = ? AND tenant_id = ?
            """,
            (str(document_id), str(version_id), str(principal.tenant_id)),
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Upload intent not found.")
        if row["upload_token"] != token or row["upload_expires_at"] < utc_now():
            raise HTTPException(status_code=403, detail="Upload token is invalid or expired.")
        if content_type != row["media_type"]:
            raise HTTPException(status_code=415, detail="Uploaded media type does not match the intent.")
        if len(body) != row["size_bytes"]:
            raise HTTPException(status_code=400, detail="Uploaded byte count does not match the intent.")
        if len(body) > self.settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="File exceeds the configured upload limit.")
        if not body.startswith(b"%PDF-"):
            raise HTTPException(status_code=415, detail="Uploaded file is not a PDF.")
        checksum = hashlib.sha256(body).hexdigest()
        if row["expected_sha256"] and checksum.lower() != row["expected_sha256"].lower():
            raise HTTPException(status_code=400, detail="Uploaded checksum does not match the intent.")
        path = Path(row["object_path"])
        temporary_path = path.with_suffix(".uploading")
        temporary_path.write_bytes(body)
        temporary_path.replace(path)
        now = utc_now()
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE documents SET sha256 = ?, updated_at = ? WHERE document_id = ? AND tenant_id = ?",
                (checksum, now, str(document_id), str(principal.tenant_id)),
            )

    def complete_upload(
        self,
        principal: Principal,
        document_id: UUID,
        version_id: UUID,
        request,
        idempotency_key: str,
    ) -> dict:
        payload = request.model_dump(mode="json")
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        operation = f"upload-complete:{document_id}:{version_id}"
        existing = self._existing_idempotent(principal, operation, idempotency_key, payload_hash)
        if existing is not None:
            return existing
        row = self.db.execute_one(
            "SELECT * FROM documents WHERE document_id = ? AND version_id = ? AND tenant_id = ?",
            (str(document_id), str(version_id), str(principal.tenant_id)),
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Document version not found.")
        if not Path(row["object_path"]).is_file() or not row["sha256"]:
            raise HTTPException(status_code=409, detail="Upload has not completed.")
        if request.sha256 and request.sha256.lower() != row["sha256"].lower():
            raise HTTPException(status_code=400, detail="Completion checksum does not match the uploaded file.")
        if request.object_version_id != f"local:{version_id}":
            raise HTTPException(status_code=400, detail="Unexpected local object version identifier.")

        job_id = uuid4()
        now = utc_now()
        response = {
            "job_id": str(job_id),
            "document_id": str(document_id),
            "version_id": str(version_id),
            "status": DocumentStatus.QUEUED.value,
            "attempt": 1,
            "created_at": now,
            "updated_at": now,
        }
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE document_id = ?",
                (DocumentStatus.QUEUED.value, now, str(document_id)),
            )
        self.db.insert_idempotent_response(
            principal.tenant_id, operation, idempotency_key, payload_hash, response
        )
        return response

    def index_document(self, tenant_id: UUID, document_id: UUID, version_id: UUID) -> None:
        row = self.db.execute_one(
            "SELECT * FROM documents WHERE document_id = ? AND version_id = ? AND tenant_id = ?",
            (str(document_id), str(version_id), str(tenant_id)),
        )
        if row is None or row["status"] == DocumentStatus.DELETED.value:
            return
        now = utc_now()
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE document_id = ?",
                (DocumentStatus.PROCESSING.value, now, str(document_id)),
            )
        try:
            chunks = extract_pdf_chunks(Path(row["object_path"]))
            self.vectors.upsert(
                tenant_id=tenant_id,
                document_id=document_id,
                version_id=version_id,
                chunks=chunks,
                embedder=self.embedder,
            )
            with self.db.connect() as connection:
                connection.execute(
                    """
                    UPDATE documents SET status = ?, failure_code = NULL,
                        failure_message = NULL, updated_at = ?
                    WHERE document_id = ? AND tenant_id = ?
                    """,
                    (DocumentStatus.INDEXED.value, utc_now(), str(document_id), str(tenant_id)),
                )
        except (PdfReadError, ValueError, OSError, chromadb.errors.ChromaError) as exc:
            logger.warning(
                "PDF indexing failed for document %s (tenant %s): %s",
                document_id,
                tenant_id,
                exc,
            )
            with self.db.connect() as connection:
                connection.execute(
                    """
                    UPDATE documents SET status = ?, failure_code = ?,
                        failure_message = ?, updated_at = ?
                    WHERE document_id = ? AND tenant_id = ?
                    """,
                    (
                        DocumentStatus.FAILED.value,
                        "pdf_processing_failed",
                        str(exc)[:500],
                        utc_now(),
                        str(document_id),
                        str(tenant_id),
                    ),
                )

    def document(self, principal: Principal, document_id: UUID) -> Document:
        row = self.db.execute_one(
            "SELECT * FROM documents WHERE document_id = ? AND tenant_id = ?",
            (str(document_id), str(principal.tenant_id)),
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        return Document(
            document_id=document_id,
            file_name=row["file_name"],
            media_type=row["media_type"],
            status=row["status"],
            current_version_id=UUID(row["version_id"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_documents(self, principal: Principal) -> list[Document]:
        rows = self.db.execute(
            "SELECT * FROM documents WHERE tenant_id = ? ORDER BY created_at DESC",
            (str(principal.tenant_id),),
        )
        return [
            Document(
                document_id=UUID(row["document_id"]),
                file_name=row["file_name"],
                media_type=row["media_type"],
                status=row["status"],
                current_version_id=UUID(row["version_id"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def create_conversation(self, principal: Principal, title: str | None) -> Conversation:
        conversation_id = uuid4()
        now = utc_now()
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations
                    (conversation_id, tenant_id, owner_user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(conversation_id), str(principal.tenant_id),
                    str(principal.user_id), title, now, now,
                ),
            )
        return Conversation(
            conversation_id=conversation_id,
            title=title,
            created_at=now,
            updated_at=now,
        )

    def _authorized_conversation(self, principal: Principal, conversation_id: UUID):
        row = self.db.execute_one(
            """
            SELECT * FROM conversations
            WHERE conversation_id = ? AND tenant_id = ? AND owner_user_id = ?
            """,
            (str(conversation_id), str(principal.tenant_id), str(principal.user_id)),
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return row

    def list_messages(self, principal: Principal, conversation_id: UUID) -> list[Message]:
        self._authorized_conversation(principal, conversation_id)
        rows = self.db.execute(
            """
            SELECT * FROM messages WHERE conversation_id = ?
            ORDER BY created_at, message_id
            """,
            (str(conversation_id),),
        )
        return [
            Message(
                message_id=UUID(row["message_id"]),
                conversation_id=conversation_id,
                role=row["role"],
                content=row["content"],
                status=row["status"],
                citations=json.loads(row["citations_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def chat(
        self,
        principal: Principal,
        conversation_id: UUID,
        content: str,
        document_scope: list[UUID],
        idempotency_key: str,
    ) -> tuple[UUID, str, list[Citation]]:
        self._authorized_conversation(principal, conversation_id)
        payload_hash = hashlib.sha256(
            json.dumps(
                {
                    "conversation_id": str(conversation_id),
                    "content": content,
                    "document_scope": sorted(str(item) for item in document_scope),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        operation = f"chat:{conversation_id}"
        existing = self._existing_idempotent(
            principal, operation, idempotency_key, payload_hash
        )
        if existing is not None:
            return (
                UUID(existing["message_id"]),
                existing["answer"],
                [Citation.model_validate(item) for item in existing["citations"]],
            )
        if document_scope:
            for document_id in document_scope:
                doc = self.db.execute_one(
                    """
                    SELECT status FROM documents WHERE document_id = ? AND tenant_id = ?
                    """,
                    (str(document_id), str(principal.tenant_id)),
                )
                if doc is None or doc["status"] != DocumentStatus.INDEXED.value:
                    raise HTTPException(status_code=404, detail="Document not found.")
        message_id = uuid4()
        now = utc_now()
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO messages
                    (message_id, conversation_id, tenant_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()), str(conversation_id), str(principal.tenant_id),
                    MessageRole.USER.value, content, now,
                ),
            )
        results = self.vectors.query(
            tenant_id=principal.tenant_id,
            question=content,
            embedder=self.embedder,
            document_ids=document_scope,
            limit=self.settings.retrieval_limit,
        )
        if not results:
            answer = "I could not find supporting evidence in your indexed documents."
            citations: list[Citation] = []
            answer_status = "insufficient_evidence"
        else:
            top_result = results[0]
            answer = self.answer_generator.answer(top_result.content, content)
            citations = [
                Citation(
                    document_id=result.document_id,
                    version_id=result.version_id,
                    chunk_id=result.chunk_id,
                    page_number=result.page_number,
                    excerpt=result.content[:1000],
                )
                for result in results[:3]
            ]
            answer_status = "completed"
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO messages
                    (message_id, conversation_id, tenant_id, role, content, status,
                     citations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(message_id), str(conversation_id), str(principal.tenant_id),
                    MessageRole.ASSISTANT.value, answer, answer_status,
                    json.dumps([citation.model_dump(mode="json") for citation in citations]),
                    utc_now(),
                ),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (utc_now(), str(conversation_id)),
            )
        self.db.insert_idempotent_response(
            principal.tenant_id,
            operation,
            idempotency_key,
            payload_hash,
            {
                "message_id": str(message_id),
                "answer": answer,
                "citations": [citation.model_dump(mode="json") for citation in citations],
            },
        )
        return message_id, answer, citations

    @staticmethod
    def terminal_event(message_id: UUID, answer: str, citations: list[Citation]):
        if citations:
            words = len(answer.split())
            return SseCompleted(
                event_id=uuid4(),
                message_id=message_id,
                content=answer,
                citations=citations,
                usage=TokenUsage(input_tokens=0, output_tokens=words),
                cost_usd="0",
            )
        return SseInsufficientEvidence(
            event_id=uuid4(),
            message_id=message_id,
            content=answer,
            citations=[],
        )
