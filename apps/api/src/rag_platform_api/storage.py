import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    version_id TEXT NOT NULL UNIQUE,
                    tenant_id TEXT NOT NULL,
                    owner_user_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT,
                    expected_sha256 TEXT,
                    object_path TEXT NOT NULL,
                    upload_token TEXT NOT NULL UNIQUE,
                    upload_expires_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    failure_code TEXT,
                    failure_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_documents_tenant
                    ON documents (tenant_id, created_at);
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    owner_user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_owner
                    ON conversations (tenant_id, owner_user_id, created_at);
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
                    tenant_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT,
                    citations_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages (conversation_id, created_at);
                CREATE TABLE IF NOT EXISTS idempotency (
                    tenant_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, operation, idempotency_key)
                );
                """
            )

    def execute(self, query: str, values: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(connection.execute(query, values).fetchall())

    def execute_one(self, query: str, values: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        rows = self.execute(query, values)
        return rows[0] if rows else None

    def insert_idempotent_response(
        self,
        tenant_id: UUID,
        operation: str,
        key: str,
        payload_hash: str,
        response: dict[str, Any],
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO idempotency
                    (tenant_id, operation, idempotency_key, payload_hash, response_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(tenant_id),
                    operation,
                    key,
                    payload_hash,
                    json.dumps(response, separators=(",", ":"), sort_keys=True),
                    utc_now(),
                ),
            )

    def get_idempotent_response(
        self, tenant_id: UUID, operation: str, key: str
    ) -> sqlite3.Row | None:
        return self.execute_one(
            """
            SELECT payload_hash, response_json FROM idempotency
            WHERE tenant_id = ? AND operation = ? AND idempotency_key = ?
            """,
            (str(tenant_id), operation, key),
        )

    @staticmethod
    def decode_idempotent_response(row: sqlite3.Row) -> dict[str, Any]:
        return json.loads(row["response_json"])
