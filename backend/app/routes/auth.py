import hmac
import os

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def require_operator(
    authorization: str | None = Header(default=None),
):
    secret = os.getenv("ARES_OPERATOR_TOKEN", "")

    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Operator token not configured",
        )

    if (
        authorization is None
        or not authorization.startswith("Bearer ")
    ):
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
        )

    received = authorization.removeprefix("Bearer ")

    if not hmac.compare_digest(received, secret):
        raise HTTPException(
            status_code=403,
            detail="Unauthorized operator",
        )

    return True


@router.get("/check")
def check_authorization(
    _: bool = Depends(require_operator),
):
    return {
        "authorized": True,
        "role": "operator",
    }