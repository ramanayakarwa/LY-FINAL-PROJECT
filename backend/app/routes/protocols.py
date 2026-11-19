
"""
ARES Protocol Monitoring API.

Provides read-only status for:
- MQTT broker connection
- CoAP telemetry receiver
- Latest verified rover telemetry

These endpoints do not control motors,
arm, pump or any physical hardware.
"""

from fastapi import APIRouter

from app.services.mqtt_service import broker_status
from app.services.coap_services import coap_status
from app.services.state_service import snapshot


router = APIRouter(
    prefix="/protocols",
    tags=["ARES Protocol Monitoring"],
)


@router.get("/status")
def protocols_status():
    """
    Combined MQTT, CoAP and telemetry status.
    """

    mqtt = broker_status()
    coap = coap_status()
    telemetry = snapshot()

    source = telemetry.get("source", "NONE")
    fresh = telemetry.get("fresh") is True
    verified = telemetry.get("verified") is True

    live_telemetry = (
        fresh
        and verified
        and source in (
            "MQTT_VERIFIED",
            "COAP_SIGNED",
        )
    )

    return {
        "mqtt": mqtt,
        "coap": coap,
        "telemetry": telemetry,
        "telemetry_source": source,
        "live_verified_telemetry": live_telemetry,
        "hardware_commissioned": False,
        "physical_actuation_enabled": False,
    }


@router.get("/mqtt")
def mqtt_status():
    """
    MQTT client and message counters.
    """

    return broker_status()


@router.get("/coap")
def get_coap_status():
    """
    CoAP server and verified packet counters.
    """

    return coap_status()


@router.get("/telemetry")
def get_protocol_telemetry():
    """
    Latest telemetry snapshot.

    Simulation telemetry must never be
    represented as verified hardware data.
    """

    telemetry = snapshot()

    source = telemetry.get("source", "NONE")
    fresh = telemetry.get("fresh") is True
    verified = telemetry.get("verified") is True

    return {
        "telemetry": telemetry,
        "source": source,
        "fresh": fresh,
        "verified": verified,
        "live_verified": (
            fresh
            and verified
            and source in (
                "MQTT_VERIFIED",
                "COAP_SIGNED",
            )
        ),
    }
