from collections import Counter

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from starlette.concurrency import run_in_threadpool

from app.services.image_service import save_image
from app.services.disease_service import predict_disease
from app.services.agent_service import AgenticLayer
from app.services.log_service import write_log


router = APIRouter(
    prefix="/inspection",
    tags=["Plant Inspection"],
)


@router.post("/analyze")
async def inspect_plant(
    plant_id: str = Form(...),
    images: list[UploadFile] = File(...),
):

    if not plant_id.strip() or len(plant_id) > 64:
        raise HTTPException(
            status_code=422,
            detail="Invalid plant ID",
        )

    if not (1 <= len(images) <= 6):
        raise HTTPException(
            status_code=422,
            detail="Provide 1 to 6 plant images",
        )

    results = []

    for image in images:

        path = await save_image(image)

        try:
            prediction = await run_in_threadpool(
                predict_disease,
                str(path),
            )

            results.append(prediction)

        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="Disease inference unavailable",
            ) from exc

        finally:
            path.unlink(missing_ok=True)

    # Compare predictions across camera views.
    labels = [
        (result["crop"], result["disease"])
        for result in results
    ]

    (crop, disease), votes = (
        Counter(labels).most_common(1)[0]
    )

    consistent = votes == len(results)

    matched_confidences = [
        result["confidence"]
        for result in results
        if (
            result["crop"],
            result["disease"],
        ) == (crop, disease)
    ]

    confidence = min(matched_confidences)

    agent = AgenticLayer({
        "crop": crop,
        "disease": disease,
        "confidence": confidence,
    }).final_agentic_output()

    if not consistent:
        agent = {
            "priority": "MEDIUM",
            "action": "RECAPTURE_IMAGES",
            "reason": (
                "Different camera angles produced "
                "conflicting predictions."
            ),
            "precautions": [
                "Capture additional images.",
                "Improve lighting.",
                "Request manual review.",
                "Do not remove leaves automatically.",
            ],
            "requires_gate": True,
            "execution_status": "PROPOSAL_ONLY",
            "agent_type": "RULE_BASED",
        }

    response = {
        "plant_id": plant_id,
        "views": results,
        "consensus": {
            "crop": crop,
            "disease": disease,
            "agreement_ratio": round(
                votes / len(results),
                3,
            ),
            "consistent": consistent,
        },
        "leaf_target_localized": False,
        "robotic_removal_allowed": False,
        "decision": agent,
    }

    write_log({
        "source": "plant_inspection",
        "plant_id": plant_id,
        "consensus": response["consensus"],
        "decision": agent,
    })

    return response