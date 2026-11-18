import os
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    data_dir: Path = REPOSITORY_ROOT / ".local-data"
    public_base_url: str = "http://localhost:8000"
    dev_bearer_token: str = "local-dev-token"
    max_upload_bytes: int = 25 * 1024 * 1024
    upload_token_ttl_seconds: int = 900
    retrieval_limit: int = 5

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            environment=os.getenv("RAG_ENV", "development"),
            data_dir=Path(os.getenv("RAG_DATA_DIR", str(REPOSITORY_ROOT / ".local-data"))),
            public_base_url=os.getenv("RAG_PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/"),
            dev_bearer_token=os.getenv("RAG_DEV_BEARER_TOKEN", "local-dev-token"),
            max_upload_bytes=int(os.getenv("RAG_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
            upload_token_ttl_seconds=int(os.getenv("RAG_UPLOAD_TOKEN_TTL_SECONDS", "900")),
            retrieval_limit=int(os.getenv("RAG_RETRIEVAL_LIMIT", "5")),
        )
