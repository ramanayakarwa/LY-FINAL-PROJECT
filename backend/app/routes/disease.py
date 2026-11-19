from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)

from starlette.concurrency import run_in_threadpool

from app.services.disease_service import (
    predict_disease,
)

from app.services.image_service import save_image


router = APIRouter(
    prefix="/predict",
    tags=["Disease"],
)


@router.post("/disease")
async def disease_prediction(
    file: UploadFile = File(...),
):

    path = await save_image(file)

    try:
        return await run_in_threadpool(
            predict_disease,
            str(path),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Disease model is unavailable",
        ) from exc

    finally:
        path.unlink(missing_ok=True)