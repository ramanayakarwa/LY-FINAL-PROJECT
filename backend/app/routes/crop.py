from fastapi import APIRouter
from app.schemas import CropInput, CropResponse
from app.services.crop_service import predict_crop

router = APIRouter(prefix="/predict", tags=["Crop"])


@router.post("/crop", response_model=CropResponse)
def crop_prediction(payload: CropInput):
    return predict_crop(payload.model_dump())