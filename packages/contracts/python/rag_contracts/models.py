"""Pydantic v2 transport and workflow schemas; no infrastructure SDK imports."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class FeedbackRating(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class UploadIntentRequest(ContractModel):
    file_name: str = Field(min_length=1, max_length=255)
    media_type: Literal[
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ]
    size_bytes: int = Field(gt=0)
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")


class UploadIntentResponse(ContractModel):
    document_id: UUID
    version_id: UUID
    upload_url: str = Field(min_length=1, max_length=8192, pattern=r"^https?://")
    expires_at: datetime
    required_headers: dict[str, str]


class UploadCompleteRequest(ContractModel):
    object_version_id: str = Field(min_length=1, max_length=1024)
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")


class FailureSummary(ContractModel):
    code: str = Field(max_length=64)
    message: str | None = Field(default=None, max_length=500)
    retryable: bool


class IngestionJob(ContractModel):
    job_id: UUID
    document_id: UUID
    version_id: UUID
    status: DocumentStatus
    attempt: int = Field(default=1, ge=1)
    failure: FailureSummary | None = None
    created_at: datetime
    updated_at: datetime


class DocumentVersion(ContractModel):
    version_id: UUID
    document_id: UUID
    version_number: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: int = Field(gt=0)
    media_type: str
    status: DocumentStatus
    embedding_model_version: str | None = Field(default=None, max_length=128)
    index_version: str | None = Field(default=None, max_length=128)
    created_at: datetime


class Document(ContractModel):
    document_id: UUID
    file_name: str = Field(max_length=255)
    media_type: str
    status: DocumentStatus
    current_version_id: UUID
    created_at: datetime
    updated_at: datetime


class Chunk(ContractModel):
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    ordinal: int = Field(ge=0)
    content_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    source_location: dict[str, str | int | None] = Field(default_factory=dict)


class EmbeddingReference(ContractModel):
    chunk_id: UUID
    model_version: str = Field(min_length=1, max_length=128)
    index_version: str = Field(min_length=1, max_length=128)


class DocumentPage(ContractModel):
    items: list[Document]
    next_cursor: str | None = None


class DeletionAccepted(ContractModel):
    document_id: UUID
    status: Literal["deleted"]
    accepted_at: datetime


class ConversationCreateRequest(ContractModel):
    title: str | None = Field(default=None, max_length=200)


class Conversation(ContractModel):
    conversation_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class Citation(ContractModel):
    document_id: UUID
    version_id: UUID
    chunk_id: UUID
    page_number: int | None = Field(default=None, ge=1)
    slide_number: int | None = Field(default=None, ge=1)
    section: str | None = Field(default=None, max_length=500)
    excerpt: str | None = Field(default=None, max_length=1000)


class ChatRequest(ContractModel):
    content: str = Field(min_length=1, max_length=12000)
    document_scope: list[UUID] = Field(
        default_factory=list,
        max_length=100,
        json_schema_extra={"uniqueItems": True},
    )

    @field_validator("document_scope")
    @classmethod
    def document_scope_must_be_unique(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("document_scope must not contain duplicate IDs")
        return value


class TokenUsage(ContractModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class Message(ContractModel):
    message_id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    status: Literal["completed", "insufficient_evidence", "failed"] | None = None
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


class MessagePage(ContractModel):
    items: list[Message]
    next_cursor: str | None = None


class FeedbackRequest(ContractModel):
    rating: FeedbackRating
    note: str | None = Field(default=None, max_length=2000)


class Feedback(ContractModel):
    feedback_id: UUID
    message_id: UUID
    rating: FeedbackRating
    note: str | None = None
    created_at: datetime


class EvaluationConfiguration(ContractModel):
    prompt_version: str = Field(max_length=128)
    retrieval_version: str = Field(max_length=128)
    model: str | None = Field(default=None, max_length=128)


class EvaluationRunRequest(ContractModel):
    dataset_id: str = Field(min_length=1, max_length=128)
    configuration: EvaluationConfiguration


class EvaluationRun(ContractModel):
    run_id: UUID
    dataset_id: str
    status: Literal["queued", "running", "completed", "failed"]
    metrics: dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class Health(ContractModel):
    status: Literal["ok", "ready"]


class ValidationIssue(ContractModel):
    location: list[str | int]
    code: str
    message: str


class Problem(ContractModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    type: str
    title: str
    status: int = Field(ge=400, le=599)
    detail: str | None = None
    instance: str | None = None
    code: str
    correlation_id: str = Field(max_length=128)
    errors: list[ValidationIssue] = Field(default_factory=list)


class SseProgress(ContractModel):
    event: Literal["message.progress"] = "message.progress"
    event_id: UUID
    stage: Literal["authorizing", "retrieving", "generating", "validating"]


class SseDelta(ContractModel):
    event: Literal["message.delta"] = "message.delta"
    event_id: UUID
    message_id: UUID
    delta: str = Field(min_length=1)


class SseCompleted(ContractModel):
    event: Literal["message.completed"] = "message.completed"
    event_id: UUID
    message_id: UUID
    content: str
    citations: list[Citation]
    usage: TokenUsage
    cost_usd: Decimal = Field(ge=0)


class SseInsufficientEvidence(ContractModel):
    event: Literal["message.insufficient_evidence"] = "message.insufficient_evidence"
    event_id: UUID
    message_id: UUID
    content: str
    citations: list[Citation] = Field(default_factory=list)


class SseError(ContractModel):
    event: Literal["message.error"] = "message.error"
    event_id: UUID
    problem: Problem


class RetrievedChunk(ContractModel):
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    content: str
    score: float
    source_location: dict[str, str | int | None] = Field(default_factory=dict)


class RagWorkflowState(ContractModel):
    """Serializable state fields shared with the graph; graph runtime stays outside."""

    question: str = Field(min_length=1, max_length=12000)
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID
    message_id: UUID
    rewritten_queries: list[str] = Field(default_factory=list)
    retrieved_documents: list[RetrievedChunk] = Field(default_factory=list)
    reranked_context: list[RetrievedChunk] = Field(default_factory=list)
    answer: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    token_usage: TokenUsage | None = None
    cost_usd: Decimal | None = Field(default=None, ge=0)


class DocumentUploadedData(ContractModel):
    document_id: UUID
    version_id: UUID
    job_id: UUID
    object_key: str = Field(min_length=1, max_length=1024)
    object_version_id: str = Field(min_length=1, max_length=1024)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")


class IngestionCompletedData(ContractModel):
    document_id: UUID
    version_id: UUID
    job_id: UUID
    chunk_count: int = Field(ge=0)
    embedding_model_version: str = Field(max_length=128)
    index_version: str = Field(max_length=128)


class IngestionFailedData(ContractModel):
    document_id: UUID
    version_id: UUID
    job_id: UUID
    failure: FailureSummary


class DocumentDeletedData(ContractModel):
    document_id: UUID
    version_ids: list[UUID] = Field(min_length=1)
    deletion_operation_id: UUID


class DocumentUploadedEvent(ContractModel):
    event_id: UUID
    event_type: Literal["document.uploaded"]
    event_version: Literal[1]
    occurred_at: datetime
    tenant_id: UUID
    correlation_id: str = Field(min_length=1, max_length=128)
    traceparent: str | None = Field(default=None, max_length=256)
    data: DocumentUploadedData


class IngestionCompletedEvent(ContractModel):
    event_id: UUID
    event_type: Literal["ingestion.completed"]
    event_version: Literal[1]
    occurred_at: datetime
    tenant_id: UUID
    correlation_id: str = Field(min_length=1, max_length=128)
    traceparent: str | None = Field(default=None, max_length=256)
    data: IngestionCompletedData


class IngestionFailedEvent(ContractModel):
    event_id: UUID
    event_type: Literal["ingestion.failed"]
    event_version: Literal[1]
    occurred_at: datetime
    tenant_id: UUID
    correlation_id: str = Field(min_length=1, max_length=128)
    traceparent: str | None = Field(default=None, max_length=256)
    data: IngestionFailedData


class DocumentDeletedEvent(ContractModel):
    event_id: UUID
    event_type: Literal["document.deleted"]
    event_version: Literal[1]
    occurred_at: datetime
    tenant_id: UUID
    correlation_id: str = Field(min_length=1, max_length=128)
    traceparent: str | None = Field(default=None, max_length=256)
    data: DocumentDeletedData


DomainEvent = Annotated[
    DocumentUploadedEvent
    | IngestionCompletedEvent
    | IngestionFailedEvent
    | DocumentDeletedEvent,
    Field(discriminator="event_type"),
]
