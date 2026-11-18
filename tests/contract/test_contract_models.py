import unittest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from rag_contracts import (
    ChatRequest,
    DomainEvent,
    DocumentStatus,
    DocumentUploadedEvent,
    FeedbackRequest,
    RagWorkflowState,
    UploadIntentRequest,
)


class ContractModelTests(unittest.TestCase):
    def test_supported_upload_is_accepted(self):
        request = UploadIntentRequest(
            file_name="handbook.pdf",
            media_type="application/pdf",
            size_bytes=1024,
            sha256="a" * 64,
        )
        self.assertEqual(request.media_type, "application/pdf")

    def test_unsupported_upload_type_is_rejected(self):
        with self.assertRaises(ValidationError):
            UploadIntentRequest(
                file_name="payload.exe",
                media_type="application/octet-stream",
                size_bytes=10,
            )

    def test_extra_request_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            UploadIntentRequest(
                file_name="handbook.pdf",
                media_type="application/pdf",
                size_bytes=1024,
                tenant_id=uuid4(),
            )

    def test_empty_chat_question_is_rejected(self):
        with self.assertRaises(ValidationError):
            ChatRequest(content="   ")

    def test_duplicate_document_scope_is_rejected(self):
        document_id = uuid4()
        with self.assertRaises(ValidationError):
            ChatRequest(content="question", document_scope=[document_id, document_id])

    def test_feedback_rating_is_constrained(self):
        self.assertEqual(FeedbackRequest(rating="positive").rating.value, "positive")
        with self.assertRaises(ValidationError):
            FeedbackRequest(rating="maybe")

    def test_uploaded_event_requires_typed_versioned_payload(self):
        event = DocumentUploadedEvent(
            event_id=uuid4(),
            event_type="document.uploaded",
            event_version=1,
            occurred_at=datetime.now(timezone.utc),
            tenant_id=uuid4(),
            correlation_id="corr-test",
            data={
                "document_id": uuid4(),
                "version_id": uuid4(),
                "job_id": uuid4(),
                "object_key": "tenant/document",
                "object_version_id": "object-version-1",
                "sha256": "b" * 64,
            },
        )
        self.assertEqual(event.event_version, 1)
        parsed = TypeAdapter(DomainEvent).validate_python(
            {
                "event_id": uuid4(),
                "event_type": "document.uploaded",
                "event_version": 1,
                "occurred_at": datetime.now(timezone.utc),
                "tenant_id": uuid4(),
                "correlation_id": "corr-test",
                "data": {
                    "document_id": uuid4(),
                    "version_id": uuid4(),
                    "job_id": uuid4(),
                    "object_key": "tenant/document",
                    "object_version_id": "object-version-1",
                    "sha256": "c" * 64,
                },
            }
        )
        self.assertIsInstance(parsed, DocumentUploadedEvent)
        with self.assertRaises(ValidationError):
            TypeAdapter(DomainEvent).validate_python(
                {
                    "event_id": uuid4(),
                    "event_type": "unknown.event",
                    "event_version": 1,
                    "occurred_at": datetime.now(timezone.utc),
                    "tenant_id": uuid4(),
                    "correlation_id": "corr-test",
                    "data": {},
                }
            )
        with self.assertRaises(ValidationError):
            DocumentUploadedEvent(
                event_id=uuid4(),
                event_type="ingestion.failed",
                event_version=1,
                occurred_at=datetime.now(timezone.utc),
                tenant_id=uuid4(),
                correlation_id="corr-test",
                data={
                    "document_id": uuid4(),
                    "version_id": uuid4(),
                    "job_id": uuid4(),
                    "object_key": "tenant/document",
                    "object_version_id": "object-version-1",
                    "sha256": "b" * 64,
                },
            )

    def test_workflow_state_defaults_without_framework_state_types(self):
        state = RagWorkflowState(
            question="What is the retention period?",
            tenant_id=uuid4(),
            user_id=uuid4(),
            conversation_id=uuid4(),
            message_id=uuid4(),
        )
        self.assertEqual(state.retrieved_documents, [])
        self.assertIsNone(state.answer)
        self.assertEqual(DocumentStatus.QUEUED.value, "queued")


if __name__ == "__main__":
    unittest.main()
