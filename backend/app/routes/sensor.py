from fastapi import APIRouter

from app.services.state_service import snapshot


router = APIRouter(
    prefix="/sensor",
    tags=["Sensor"],
)


@router.get("/latest")
def latest_sensor():
    return snapshot()