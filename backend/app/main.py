
"""
ARES - Agentic Secure Smart Agriculture Scientific Rover

Main FastAPI application.

Features:
- Operator authentication
- Crop recommendation
- Disease detection
- Yield prediction
- Plant inspection
- Rover monitoring and commands
- MQTT verified telemetry
- CoAP signed telemetry
- ESP32-CAM image capture
- Protocol monitoring
- Audit logs

Hardware commissioning status:
NOT COMMISSIONED

No physical motor, arm or pump execution
is claimed by this application.
"""

import asyncio
import os

from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Depends,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.routes import (
    all,
    crop,
    disease,
    yield_route,
    inspection,
    system,
    sensor,
    logs,
    rover,
    auth,
    camera,
    protocols,
)

from app.routes.auth import require_operator

from app.services.mqtt_service import (
    start_mqtt,
    stop_mqtt,
)

from app.services.coap_services import (
    start_coap,
)


# =====================================
# 1. ENVIRONMENT HELPERS
# =====================================

def env_enabled(
    name: str,
    default: str = "false",
) -> bool:
    return (
        os.getenv(
            name,
            default,
        ).strip().lower()
        == "true"
    )


# =====================================
# 2. APPLICATION LIFESPAN
# =====================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print()
    print("=" * 50)
    print("ARES BACKEND STARTING")
    print("=" * 50)

    coap_task = None

    try:
        # -----------------------------
        # MQTT SERVICE
        # -----------------------------

        if env_enabled(
            "ARES_MQTT_ENABLED"
        ):
            print(
                "ARES MQTT enabled"
            )

            start_mqtt()

        else:
            print(
                "ARES MQTT disabled"
            )

        # -----------------------------
        # COAP SERVICE
        # -----------------------------

        if env_enabled(
            "ARES_COAP_ENABLED"
        ):
            print(
                "ARES CoAP enabled"
            )

            coap_task = (
                asyncio.create_task(
                    start_coap(),
                    name="ares_coap_server",
                )
            )

        else:
            print(
                "ARES CoAP disabled"
            )

        # -----------------------------
        # CAMERA CONFIGURATION
        # -----------------------------

        camera_host = os.getenv(
            "ARES_CAMERA_HOST",
            "",
        ).strip()

        if camera_host:
            print(
                "ARES ESP32-CAM configured"
            )

        else:
            print(
                "ARES ESP32-CAM not configured"
            )

        print()
        print(
            "ARES API ready"
        )
        print(
            "Physical hardware commissioning: PENDING"
        )
        print("=" * 50)
        print()

        yield

    finally:

        print(
            "ARES backend shutting down..."
        )

        # -----------------------------
        # STOP COAP
        # -----------------------------

        if coap_task is not None:
            coap_task.cancel()

            try:
                await coap_task

            except asyncio.CancelledError:
                pass

        # -----------------------------
        # STOP MQTT
        # -----------------------------

        stop_mqtt()

        print(
            "ARES services stopped"
        )


# =====================================
# 3. FASTAPI APPLICATION
# =====================================

app = FastAPI(
    title=(
        "ARES - ESP32 Agricultural Rover"
    ),

    description=(
        "Agentic Secure Smart Agriculture "
        "Scientific Rover API. "
        "Supports MQTT telemetry, CoAP telemetry, "
        "ESP32-CAM image capture, AI predictions "
        "and safety-gated rover commands. "
        "Physical hardware is not commissioned."
    ),

    version="0.3.0",

    lifespan=lifespan,
)


# =====================================
# 4. CORS CONFIGURATION
# =====================================

default_origins = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:8081,"
    "http://127.0.0.1:8081"
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "ARES_CORS_ORIGINS",
        default_origins,
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,

    allow_origins=origins,

    allow_credentials=False,

    allow_methods=[
        "GET",
        "POST",
    ],

    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


# =====================================
# 5. PROTECTED API ROUTES
# =====================================

protected_routes = (
    all,
    crop,
    disease,
    yield_route,
    inspection,
    system,
    sensor,
    logs,
    rover,
    camera,
    protocols,
)

for route_module in protected_routes:

    app.include_router(
        route_module.router,

        dependencies=[
            Depends(
                require_operator
            )
        ],
    )


# =====================================
# 6. OPERATOR AUTHENTICATION
# =====================================

app.include_router(
    auth.router
)


# =====================================
# 7. ROOT ENDPOINT
# =====================================

@app.get("/")
def root():

    return {
        "name": "ARES",

        "project": (
            "Agentic Secure Smart Agriculture "
            "Scientific Rover"
        ),

        "status": "API_RUNNING",

        "controller": "ESP32",

        "camera": "ESP32-CAM OV2640",

        "hardware": "NOT_COMMISSIONED",

        "services": {
            "mqtt_enabled": env_enabled(
                "ARES_MQTT_ENABLED"
            ),

            "coap_enabled": env_enabled(
                "ARES_COAP_ENABLED"
            ),

            "camera_configured": bool(
                os.getenv(
                    "ARES_CAMERA_HOST",
                    "",
                ).strip()
            ),
        },

        "message": (
            "ARES backend is running. "
            "Real hardware connections are "
            "not yet commissioned. "
            "Physical rover actuation is disabled."
        ),
    }


# =====================================
# 8. API HEALTH ENDPOINT
# =====================================

@app.get("/health")
def health():

    return {
        "api": "RUNNING",

        "hardware_commissioned": False,

        "mqtt_enabled": env_enabled(
            "ARES_MQTT_ENABLED"
        ),

        "coap_enabled": env_enabled(
            "ARES_COAP_ENABLED"
        ),

        "camera_configured": bool(
            os.getenv(
                "ARES_CAMERA_HOST",
                "",
            ).strip()
        ),
    }
