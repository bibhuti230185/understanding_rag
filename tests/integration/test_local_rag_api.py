import json
from io import BytesIO
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from rag_platform_api.identity import Principal, require_local_principal
from rag_platform_api.main import create_app
from rag_platform_api.settings import Settings


TOKEN = "local-dev-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


def make_pdf(text: str = "Annual leave is 20 days each year.") -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.drawString(72, 720, text)
    pdf.save()
    return output.getvalue()


def create_client(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        public_base_url="http://localhost:8000",
        max_upload_bytes=1024 * 1024,
    )
    return TestClient(create_app(settings))


def upload_pdf(client: TestClient, content: bytes | None = None, key: str = "upload-key-001"):
    body = content or make_pdf()
    response = client.post(
        "/v1/documents/upload-intents",
        headers={**AUTH, "Idempotency-Key": key},
        json={
            "file_name": "handbook.pdf",
            "media_type": "application/pdf",
            "size_bytes": len(body),
        },
    )
    assert response.status_code == 201, response.text
    intent = response.json()
    upload_url = urlparse(intent["upload_url"])
    uploaded = client.put(
        f"{upload_url.path}?{upload_url.query}",
        headers={**AUTH, "Content-Type": "application/pdf"},
        content=body,
    )
    assert uploaded.status_code == 200, uploaded.text
    completed = client.post(
        f"/v1/documents/{intent['document_id']}/versions/{intent['version_id']}/complete",
        headers={**AUTH, "Idempotency-Key": "complete-key-001"},
        json={"object_version_id": f"local:{intent['version_id']}"},
    )
    assert completed.status_code == 202, completed.text
    return intent, completed.json()


def parse_sse(text: str) -> list[tuple[str, dict]]:
    events = []
    for block in text.strip().split("\n\n"):
        event = next(line[7:] for line in block.splitlines() if line.startswith("event: "))
        data = next(line[6:] for line in block.splitlines() if line.startswith("data: "))
        events.append((event, json.loads(data)))
    return events


def test_upload_index_chat_and_citations(tmp_path):
    with create_client(tmp_path) as client:
        intent, job = upload_pdf(client)
        assert job["status"] == "queued"
        document = client.get(
            f"/v1/documents/{intent['document_id']}", headers=AUTH
        ).json()
        assert document["status"] == "indexed"

        conversation = client.post(
            "/v1/conversations", headers=AUTH, json={"title": "Handbook"}
        ).json()
        response = client.post(
            f"/v1/conversations/{conversation['conversation_id']}/messages/stream",
            headers={**AUTH, "Idempotency-Key": "chat-key-0001"},
            json={"content": "What is the annual leave policy?", "document_scope": []},
        )
        assert response.status_code == 200
        events = parse_sse(response.text)
        assert events[-1][0] == "message.completed"
        assert events[-1][1]["citations"][0]["document_id"] == intent["document_id"]
        assert events[-1][1]["citations"][0]["page_number"] == 1
        assert "Annual leave is 20 days" in events[-1][1]["content"]

        history = client.get(
            f"/v1/conversations/{conversation['conversation_id']}/messages", headers=AUTH
        ).json()["items"]
        assert [message["role"] for message in history] == ["user", "assistant"]


def test_upload_and_chat_retries_are_idempotent(tmp_path):
    with create_client(tmp_path) as client:
        intent, _ = upload_pdf(client)
        original_count = client.app.state.service.vectors.collection.count()
        retry = client.post(
            "/v1/documents/upload-intents",
            headers={**AUTH, "Idempotency-Key": "upload-key-001"},
            json={
                "file_name": "handbook.pdf",
                "media_type": "application/pdf",
                "size_bytes": len(make_pdf()),
            },
        )
        assert retry.status_code == 201
        assert retry.json()["document_id"] == intent["document_id"]

        conflict = client.post(
            "/v1/documents/upload-intents",
            headers={**AUTH, "Idempotency-Key": "upload-key-001"},
            json={
                "file_name": "different.pdf",
                "media_type": "application/pdf",
                "size_bytes": len(make_pdf()),
            },
        )
        assert conflict.status_code == 409
        assert client.app.state.service.vectors.collection.count() == original_count

        conversation = client.post("/v1/conversations", headers=AUTH, json={}).json()
        path = f"/v1/conversations/{conversation['conversation_id']}/messages/stream"
        request = {"content": "How many annual leave days?", "document_scope": []}
        first = client.post(
            path,
            headers={**AUTH, "Idempotency-Key": "chat-key-0001"},
            json=request,
        )
        repeated = client.post(
            path,
            headers={**AUTH, "Idempotency-Key": "chat-key-0001"},
            json=request,
        )
        first_terminal = parse_sse(first.text)[-1][1]
        retry_terminal = parse_sse(repeated.text)[-1][1]
        assert first_terminal["message_id"] == retry_terminal["message_id"]
        messages = client.get(
            f"/v1/conversations/{conversation['conversation_id']}/messages", headers=AUTH
        ).json()["items"]
        assert len(messages) == 2


def test_no_indexed_evidence_returns_terminal_insufficient_event(tmp_path):
    with create_client(tmp_path) as client:
        conversation = client.post("/v1/conversations", headers=AUTH, json={}).json()
        response = client.post(
            f"/v1/conversations/{conversation['conversation_id']}/messages/stream",
            headers={**AUTH, "Idempotency-Key": "chat-key-0002"},
            json={"content": "What does the document say?", "document_scope": []},
        )
        events = parse_sse(response.text)
        assert events[-1][0] == "message.insufficient_evidence"
        assert events[-1][1]["citations"] == []


def test_invalid_pdf_fails_ingestion_and_unsupported_type_is_rejected(tmp_path):
    with create_client(tmp_path) as client:
        unsupported = client.post(
            "/v1/documents/upload-intents",
            headers={**AUTH, "Idempotency-Key": "unsupported-001"},
            json={
                "file_name": "slides.pptx",
                "media_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "size_bytes": 100,
            },
        )
        assert unsupported.status_code == 415

        intent, _ = upload_pdf(client, b"%PDF-1.4 invalid", "upload-key-invalid")
        status_response = client.get(
            f"/v1/documents/{intent['document_id']}", headers=AUTH
        )
        assert status_response.json()["status"] == "failed"


def test_tenant_scope_protects_documents_and_conversations(tmp_path):
    with create_client(tmp_path) as client:
        intent, _ = upload_pdf(client)
        conversation = client.post("/v1/conversations", headers=AUTH, json={}).json()
        other_principal = Principal(tenant_id=uuid4(), user_id=uuid4())
        client.app.dependency_overrides[require_local_principal] = lambda: other_principal
        try:
            assert client.get(
                f"/v1/documents/{intent['document_id']}", headers=AUTH
            ).status_code == 404
            assert client.get(
                f"/v1/conversations/{conversation['conversation_id']}/messages",
                headers=AUTH,
            ).status_code == 404
            assert client.app.state.service.vectors.query(
                tenant_id=other_principal.tenant_id,
                question="annual leave",
                embedder=client.app.state.service.embedder,
                document_ids=[],
                limit=5,
            ) == []
        finally:
            client.app.dependency_overrides.clear()


def test_api_refuses_non_development_mode(tmp_path):
    settings = Settings(environment="production", data_dir=tmp_path / "prod-data")
    try:
        create_app(settings)
    except RuntimeError as error:
        assert "local-development only" in str(error)
    else:
        raise AssertionError("Production mode must not enable the development identity.")
