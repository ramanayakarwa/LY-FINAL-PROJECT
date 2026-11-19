from fastapi import APIRouter, Query

from app.services.log_service import read_logs


router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
)


@router.get("/recent")
def get_recent_logs(
    limit: int = Query(
        default=20,
        ge=1,
        le=200,
    )
):

    return {
        "logs": read_logs(limit)
    }