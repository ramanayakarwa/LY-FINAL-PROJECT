from fastapi import (
    APIRouter,
    HTTPException,
)

from app.schemas import YieldInput

from app.services.yield_service import (
    predict_yield,
)


router = APIRouter(
    prefix="/predict",
    tags=["Production"],
)


@router.post("/yield")
def production_prediction(
    payload: YieldInput,
):

    try:
        return predict_yield(
            payload.model_dump()
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Production model unavailable",
        ) from exc