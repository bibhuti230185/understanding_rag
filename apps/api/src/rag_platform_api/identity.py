from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, Request, status

from rag_platform_api.settings import Settings


DEV_TENANT_ID = UUID("00000000-0000-4000-8000-000000000001")
DEV_USER_ID = UUID("00000000-0000-4000-8000-000000000002")


@dataclass(frozen=True)
class Principal:
    tenant_id: UUID
    user_id: UUID


def require_local_principal(request: Request) -> Principal:
    settings: Settings = request.app.state.settings
    if settings.environment != "development":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Production identity provider is not configured.",
        )

    authorization = request.headers.get("authorization", "")
    expected = f"Bearer {settings.dev_bearer_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid local development bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Principal(tenant_id=DEV_TENANT_ID, user_id=DEV_USER_ID)
