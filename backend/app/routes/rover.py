import os
import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.schemas import RoverCommand

from app.routes.auth import require_operator

from app.services.security_service import (
    CybersecurityLayer,
    Telemetry,
    accept_once,
)

from app.services.state_service import (
    snapshot,
    last_action,
    save_telemetry,
)

from app.services.action_gate import ActionGate

from app.services.hardware_manager import (
    execute_simulated,
)

from app.services.mqtt_service import broker_status

from app.services.log_service import write_log


router = APIRouter(
    prefix="/rover",
    tags=["Rover"],
)


@router.get("/status")
def rover_status():

    return {
        "telemetry": snapshot(),
        "last_action": last_action(),
        "mqtt": broker_status(),
        "mode": "SIMULATION_ONLY",
        "hardware_commissioned": False,
    }


@router.post("/command")
def rover_command(
    payload: RoverCommand,
):

    # Reject old or future-dated commands
    if abs(time.time() - payload.issued_at) > 30:
        raise HTTPException(
            status_code=422,
            detail="Command timestamp expired",
        )

    # Replay protection
    if not accept_once(
        "command:" + payload.nonce,
        ttl_seconds=120,
    ):
        raise HTTPException(
            status_code=409,
            detail="Repeated command nonce",
        )

    # Current telemetry state
    state = snapshot()

    # Security check
    security = CybersecurityLayer(
        state["data"]
    ).final_security_output()

    # Final action authorization
    gate = ActionGate(
        security_result=security
    ).evaluate(
        action=payload.action,
        parameters=payload.parameters,
    )

    # NO physical actuator commands are sent.
    hardware = execute_simulated(
        action=payload.action,
        parameters=payload.parameters,
        gate_result=gate,
    )

    result = {
        "command_id": payload.command_id,
        "security": security,
        "action_gate": gate,
        "hardware": hardware,
    }

    write_log({
        "source": "rover_command",
        "command_id": payload.command_id,
        "command_action": payload.action,
        "security": security,
        "action_gate": gate,
        "hardware": hardware,
    })

    return result


@router.post("/simulation/telemetry")
def simulate_telemetry(
    payload: Telemetry,
):

    if os.getenv(
        "ARES_DEMO_MODE", "true"
    ).lower() != "true":

        raise HTTPException(
            status_code=403,
            detail="Simulation disabled",
        )

    result = save_telemetry(
        data=payload.model_dump(
            exclude_none=True
        ),
        source="SIMULATION",
        device_id="SIMULATED_ESP32",
        verified=False,
    )

    write_log({
        "source": "simulation_telemetry",
        "sensor_source": "SIMULATION",
    })

    return result