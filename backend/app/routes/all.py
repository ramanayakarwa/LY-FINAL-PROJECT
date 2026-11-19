from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from starlette.concurrency import run_in_threadpool

from app.services.crop_service import predict_crop
from app.services.disease_service import predict_disease
from app.services.yield_service import predict_yield

from app.services.agent_service import AgenticLayer
from app.services.security_service import CybersecurityLayer

from app.services.state_service import snapshot
from app.services.image_service import save_image
from app.services.log_service import write_log


router = APIRouter(
    tags=["Combined Prediction"]
)


@router.post("/predict/all")
async def predict_all(

    file: UploadFile = File(...),

    N: float = Form(...),
    P: float = Form(...),
    K: float = Form(...),

    temperature: float = Form(...),
    humidity: float = Form(...),

    ph: float = Form(...),
    rainfall: float = Form(...),

    soil_moisture: float = Form(...),

    # Optional production prediction fields
    State_Name: str | None = Form(None),
    District_Name: str | None = Form(None),
    Crop_Year: int | None = Form(None),
    Season: str | None = Form(None),
    Crop: str | None = Form(None),
    Area: float | None = Form(None),
):

    # -------------------------------------------------
    # 1. Image validation
    # -------------------------------------------------

    path = await save_image(file)

    try:

        crop_result = await run_in_threadpool(
            predict_crop,
            {
                "N": N,
                "P": P,
                "K": K,
                "temperature": temperature,
                "humidity": humidity,
                "ph": ph,
                "rainfall": rainfall,
            },
        )

        disease_result = await run_in_threadpool(
            predict_disease,
            str(path),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="AI inference unavailable",
        ) from exc

    finally:
        path.unlink(missing_ok=True)

    # -------------------------------------------------
    # 2. Distinguish two different AI tasks
    # -------------------------------------------------

    # This identifies the crop visible in the image.
    observed_crop = disease_result.get(
        "crop",
        "Unknown",
    )

    # This recommends crops based on NPK/environment.
    recommended_crop = crop_result.get(
        "recommended_crop"
    )

    # Never claim that soil suitability proves
    # what crop is actually visible.
    final_crop = observed_crop

    # -------------------------------------------------
    # 3. Optional production prediction
    # -------------------------------------------------

    production = {
        "predicted_production": None,
        "method": "NOT_REQUESTED",
        "input_used": {},
        "unit": "tonnes",
    }

    production_fields = {
        "State_Name": State_Name,
        "District_Name": District_Name,
        "Crop_Year": Crop_Year,
        "Season": Season,
        "Crop": Crop,
        "Area": Area,
    }

    supplied = [
        value is not None
        for value in production_fields.values()
    ]

    if any(supplied) and not all(supplied):
        raise HTTPException(
            status_code=422,
            detail=(
                "Provide all production fields: "
                "state, district, year, season, crop and area"
            ),
        )

    if all(supplied):

        try:

            production = await run_in_threadpool(
                predict_yield,
                production_fields,
            )

        except ValueError as exc:

            production = {
                "predicted_production": None,
                "method": "UNSUPPORTED_INPUT",
                "reason": str(exc),
                "unit": "tonnes",
            }

        except Exception:

            production = {
                "predicted_production": None,
                "method": "MODEL_UNAVAILABLE",
                "unit": "tonnes",
            }

    # -------------------------------------------------
    # 4. Sensor data
    # -------------------------------------------------

    live_state = snapshot()

    manual_sensor = {
        "temperature": temperature,
        "humidity": humidity,
        "soil_moisture": soil_moisture,
    }

    if live_state["fresh"] and live_state["data"]:

        sensor = live_state["data"]

        sensor_source = live_state["source"]

    else:

        sensor = manual_sensor
        sensor_source = "FORM_MANUAL"

    # -------------------------------------------------
    # 5. Security analysis
    # -------------------------------------------------

    security = CybersecurityLayer(
        sensor
    ).final_security_output()

    # Prediction checks are not permission
    # to activate physical hardware.
    security["scope"] = "PREDICTION_DATA_CHECK"

    # -------------------------------------------------
    # 6. Agentic AI decision
    # -------------------------------------------------

    context = {
        **sensor,
        "crop": observed_crop,
        "disease": disease_result.get("disease"),
        "confidence": disease_result.get(
            "confidence",
            0,
        ),
    }

    agent = AgenticLayer(
        context,
        security=security,
    ).final_agentic_output()

    # -------------------------------------------------
    # 7. Final response
    # -------------------------------------------------

    result = {
        "final_crop": final_crop,
        "observed_crop": observed_crop,
        "recommended_crop": recommended_crop,
        "crop_recommendation": crop_result,
        "disease": disease_result,
        "yield": production,
        "sensor": sensor,
        "sensor_source": sensor_source,
        "security": security,
        "decision": agent,

        # No action should execute from prediction.
        "action_gate": {
            "decision": "NOT_REQUESTED",
            "reason": (
                "Prediction endpoints only "
                "propose actions."
            ),
        },
    }

    # -------------------------------------------------
    # 8. Audit log
    # -------------------------------------------------

    write_log({
        "source": "predict_all",
        "final_crop": final_crop,
        "crop_recommendation": crop_result,
        "yield": production,
        "disease": disease_result,
        "sensor_source": sensor_source,
        "security": security,
        "decision": agent,
    })

    return result