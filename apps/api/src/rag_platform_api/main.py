from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from rag_platform_api.identity import Principal, require_local_principal
from rag_platform_api.service import PlatformService
from rag_platform_api.settings import Settings
from rag_platform_api.storage import utc_now
from rag_contracts import (
    ChatRequest,
    Conversation,
    ConversationCreateRequest,
    Document,
    DocumentPage,
    Health,
    IngestionJob,
    MessagePage,
    SseDelta,
    SseProgress,
    UploadCompleteRequest,
    UploadIntentRequest,
    UploadIntentResponse,
)

class UploadAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    status: str


def _sse(event: BaseModel) -> str:
    event_name = getattr(event, "event")
    event_id = getattr(event, "event_id")
    return (
        f"id: {event_id}\n"
        f"event: {event_name}\n"
        f"data: {event.model_dump_json()}\n\n"
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings.from_environment()
    if active_settings.environment != "development":
        raise RuntimeError(
            "This Phase 4 slice is local-development only; production identity and providers are not implemented."
        )
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = active_settings
        app.state.service = PlatformService(active_settings)
        yield
    app = FastAPI(title="RAG Platform API", version="1.0.0", lifespan=lifespan)

    def get_service(request: Request) -> PlatformService:
        return request.app.state.service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-ID"],
    )

    @app.get("/v1/health/live", response_model=Health)
    def liveness():
        return Health(status="ok")

    @app.get("/v1/health/ready", response_model=Health)
    def readiness(service: PlatformService = Depends(get_service)):
        service.db.execute("SELECT 1")
        return Health(status="ready")

    @app.post(
        "/v1/documents/upload-intents",
        response_model=UploadIntentResponse,
        status_code=201,
    )
    def create_upload_intent(
        body: UploadIntentRequest,
        principal: Principal = Depends(require_local_principal),
        service: PlatformService = Depends(get_service),
        idempotency_key: str = Header(
            alias="Idempotency-Key", min_length=8, max_length=128, pattern=r"^[!-~]+$"
        ),
    ):
        return service.create_upload_intent(principal, body, idempotency_key)

    @app.put(
        "/v1/documents/{document_id}/versions/{version_id}/upload",
        response_model=UploadAccepted,
    )
    async def upload_document(
        document_id: UUID,
        version_id: UUID,
        request: Request,
        token: str,
        principal: Principal = Depends(require_local_principal),
        service: PlatformService = Depends(get_service),
    ):
        declared_length = request.headers.get("content-length")
        if declared_length:
            if not declared_length.isdecimal():
                raise HTTPException(status_code=400, detail="Invalid Content-Length.")
            if int(declared_length) > active_settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="File exceeds the configured upload limit.")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > active_settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="File exceeds the configured upload limit.")
        service.upload_file(
            principal,
            document_id,
            version_id,
            token,
            request.headers.get("content-type", ""),
            bytes(body),
        )
        return UploadAccepted(version_id=version_id, status="uploaded")

    @app.post(
        "/v1/documents/{document_id}/versions/{version_id}/complete",
        response_model=IngestionJob,
        status_code=202,
    )
    def complete_upload(
        document_id: UUID,
        version_id: UUID,
        body: UploadCompleteRequest,
        background_tasks: BackgroundTasks,
        principal: Principal = Depends(require_local_principal),
        service: PlatformService = Depends(get_service),
        idempotency_key: str = Header(
            alias="Idempotency-Key", min_length=8, max_length=128, pattern=r"^[!-~]+$"
        ),
    ):
        job = service.complete_upload(
            principal, document_id, version_id, body, idempotency_key
        )
        current = service.document(principal, document_id)
        if current.status.value == "queued":
            background_tasks.add_task(
                service.index_document, principal.tenant_id, document_id, version_id
            )
        return job

    @app.get("/v1/documents", response_model=DocumentPage)
    def list_documents(
        principal: Principal = Depends(require_local_principal),
        service: PlatformService = Depends(get_service),
    ):
        return DocumentPage(items=service.list_documents(principal), next_cursor=None)

    @app.get("/v1/documents/{document_id}", response_model=Document)
    def get_document(
        document_id: UUID,
        principal: Principal = Depends(require_local_principal),
        service: PlatformService = Depends(get_service),
    ):
        return service.document(principal, document_id)

    @app.post("/v1/conversations", response_model=Conversation, status_code=201)
    def create_conversation(
        body: ConversationCreateRequest,
        principal: Principal = Depends(require_local_principal),
        service: PlatformService = Depends(get_service),
    ):
        return service.create_conversation(principal, body.title)

    @app.get(
        "/v1/conversations/{conversation_id}/messages",
        response_model=MessagePage,
    )
    def list_messages(
        conversation_id: UUID,
        principal: Principal = Depends(require_local_principal),
        service: PlatformService = Depends(get_service),
    ):
        return MessagePage(items=service.list_messages(principal, conversation_id))

    @app.post(
        "/v1/conversations/{conversation_id}/messages/stream",
        responses={200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}}},
    )
    def stream_chat(
        conversation_id: UUID,
        body: ChatRequest,
        principal: Principal = Depends(require_local_principal),
        idempotency_key: str = Header(
            alias="Idempotency-Key",
            min_length=8,
            max_length=128,
            pattern=r"^[!-~]+$",
        ),
        x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
        service: PlatformService = Depends(get_service),
    ):
        correlation_id = x_correlation_id or str(uuid4())
        events: list[BaseModel] = [
            SseProgress(event_id=uuid4(), stage="authorizing"),
            SseProgress(event_id=uuid4(), stage="retrieving"),
        ]
        message_id, answer, citations = service.chat(
            principal, conversation_id, body.content, body.document_scope, idempotency_key
        )
        if citations:
            events.append(SseProgress(event_id=uuid4(), stage="generating"))
            events.append(SseProgress(event_id=uuid4(), stage="validating"))
            for start in range(0, len(answer), 80):
                events.append(
                    SseDelta(
                        event_id=uuid4(),
                        message_id=message_id,
                        delta=answer[start : start + 80],
                    )
                )
            terminal: BaseModel = service.terminal_event(message_id, answer, citations)
        else:
            terminal = service.terminal_event(message_id, answer, citations)
        events.append(terminal)

        def event_stream():
            for event in events:
                yield _sse(event)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Correlation-ID": correlation_id,
            },
        )

    return app


app = create_app()
