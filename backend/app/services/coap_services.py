
"""
ARES LAN CoAP telemetry receiver.

Main ESP32 sends:
    POST coap://LAPTOP_LAN_IP:5683/telemetry

Features:
- HMAC-SHA256 authentication
- Timestamp and replay protection
- Sensor schema validation
- MQTT-first telemetry priority
- CoAP fallback when MQTT telemetry is stale
- Connection status and packet counters

SECURITY:
CoAP transport is NOT encrypted.
Use only on a trusted, isolated local network.
"""

import asyncio
import json
import os
import time

from threading import Lock

from app.services.security_service import (
    verify_telemetry_envelope,
)

from app.services.state_service import (
    save_telemetry,
    snapshot,
)

from app.services.log_service import write_log


# =====================================
# 1. GLOBAL STATE
# =====================================

_lock = Lock()

_running = False
_last_valid = None
_last_error = None

_received_count = 0
_verified_count = 0
_rejected_count = 0


# =====================================
# 2. INTERNAL STATUS HELPERS
# =====================================

def _mark_received():
    global _received_count

    with _lock:
        _received_count += 1


def _mark_verified(
    device_id: str,
    sequence: int,
):
    global _last_valid
    global _last_error
    global _verified_count

    with _lock:
        _verified_count += 1

        _last_valid = {
            "received_at": time.time(),
            "device_id": device_id,
            "sequence": sequence,
        }

        _last_error = None


def _reject(
    reason: str,
    event: str = "TELEMETRY_REJECTED",
):
    global _last_error
    global _rejected_count

    with _lock:
        _last_error = reason
        _rejected_count += 1

    write_log({
        "source": "coap",
        "event": event,
        "security": {
            "security_status": "ALERT",
            "decision": "BLOCK",
            "alerts": [reason],
        },
    })


# =====================================
# 3. COAP STATUS
# =====================================

def coap_status() -> dict:
    with _lock:
        accepted = (
            dict(_last_valid)
            if _last_valid is not None
            else None
        )

        error = _last_error
        running = _running

        received = _received_count
        verified = _verified_count
        rejected = _rejected_count

    now = time.time()

    age = (
        round(
            now - accepted["received_at"],
            2,
        )
        if accepted is not None
        else None
    )

    recent = bool(
        age is not None
        and age <= 20
    )

    return {
        "enabled": (
            os.getenv(
                "ARES_COAP_ENABLED",
                "false",
            ).lower() == "true"
        ),

        "running": running,

        "recent": recent,

        "verified_hmac": recent,

        "received_count": received,

        "verified_count": verified,

        "rejected_count": rejected,

        "last_received_at": (
            accepted["received_at"]
            if accepted
            else None
        ),

        "last_device_id": (
            accepted["device_id"]
            if accepted
            else None
        ),

        "last_sequence": (
            accepted["sequence"]
            if accepted
            else None
        ),

        "age_seconds": age,

        "last_error": error,

        "transport_encrypted": False,

        "warning": (
            "Plain CoAP on trusted LAN only. "
            "HMAC provides payload integrity, "
            "not transport confidentiality."
        ),
    }


# =====================================
# 4. START COAP SERVER
# =====================================

async def start_coap():
    """
    Starts an aiocoap UDP server.

    The FastAPI lifespan should create
    this as a background asyncio task.

    Default binding is localhost for
    software-only development.
    """

    global _running
    global _last_error

    from aiocoap import (
        Context,
        Message,
        Code,
        resource,
    )

    # =================================
    # 5. STATUS RESOURCE
    # =================================

    class StatusResource(
        resource.Resource
    ):

        async def render_get(
            self,
            request,
        ):
            response = {
                "service": "ARES CoAP",
                "status": "RUNNING",
                "message": (
                    "Signed telemetry accepted "
                    "through POST /telemetry"
                ),
            }

            return Message(
                code=Code.CONTENT,
                content_format=50,
                payload=json.dumps(
                    response
                ).encode("utf-8"),
            )

    # =================================
    # 6. TELEMETRY RESOURCE
    # =================================

    class TelemetryResource(
        resource.Resource
    ):

        async def render_post(
            self,
            request,
        ):
            _mark_received()

            # -------------------------
            # Packet size validation
            # -------------------------

            if len(request.payload) > 2048:
                _reject(
                    "OVERSIZED_COAP_PACKET"
                )

                return Message(
                    code=Code.REQUEST_ENTITY_TOO_LARGE
                )

            # -------------------------
            # Content format validation
            # -------------------------

            if request.opt.content_format != 50:
                _reject(
                    "UNSUPPORTED_CONTENT_FORMAT"
                )

                return Message(
                    code=Code.UNSUPPORTED_CONTENT_FORMAT
                )

            # -------------------------
            # JSON parsing
            # -------------------------

            try:
                incoming = json.loads(
                    request.payload.decode(
                        "utf-8"
                    )
                )

                if not isinstance(
                    incoming,
                    dict,
                ):
                    raise ValueError(
                        "Expected JSON object"
                    )

            except (
                ValueError,
                UnicodeDecodeError,
            ):
                _reject("INVALID_JSON")

                return Message(
                    code=Code.BAD_REQUEST
                )

            # -------------------------
            # HMAC + timestamp + replay
            # -------------------------

            try:
                envelope, error = (
                    verify_telemetry_envelope(
                        incoming
                    )
                )

            except Exception as exc:
                _reject(
                    "VERIFICATION_ERROR:"
                    + type(exc).__name__,
                    event="VERIFICATION_ERROR",
                )

                return Message(
                    code=Code.INTERNAL_SERVER_ERROR
                )

            if error is not None:
                _reject(error)

                return Message(
                    code=Code.UNAUTHORIZED
                )

            # -------------------------
            # Extract verified readings
            # -------------------------

            data = (
                envelope.data.model_dump(
                    exclude_none=True
                )
            )

            # -------------------------
            # MQTT priority
            # -------------------------

            try:
                current = snapshot()

                mqtt_is_fresh = (
                    current.get("fresh") is True
                    and current.get("verified") is True
                    and current.get("source")
                    == "MQTT_VERIFIED"
                )

                if not mqtt_is_fresh:
                    save_telemetry(
                        data=data,
                        source="COAP_SIGNED",
                        device_id=(
                            envelope.device_id
                        ),
                        verified=True,
                        sequence=(
                            envelope.sequence
                        ),
                    )

            except Exception as exc:
                _reject(
                    "TELEMETRY_STORAGE_ERROR:"
                    + type(exc).__name__,
                    event="STORAGE_ERROR",
                )

                return Message(
                    code=Code.INTERNAL_SERVER_ERROR
                )

            # Mark accepted only after
            # verification and processing.
            _mark_verified(
                device_id=envelope.device_id,
                sequence=envelope.sequence,
            )

            # -------------------------
            # Acknowledge success
            # -------------------------

            return Message(
                code=Code.CHANGED,
                content_format=50,
                payload=json.dumps({
                    "accepted": True,
                    "device_id": (
                        envelope.device_id
                    ),
                    "sequence": (
                        envelope.sequence
                    ),
                }).encode("utf-8"),
            )

    # =====================================
    # 7. REGISTER COAP ENDPOINTS
    # =====================================

    site = resource.Site()

    site.add_resource(
        ["status"],
        StatusResource(),
    )

    site.add_resource(
        ["telemetry"],
        TelemetryResource(),
    )

    # =====================================
    # 8. SERVER CONFIGURATION
    # =====================================

    host = os.getenv(
        "ARES_COAP_HOST",
        "127.0.0.1",
    )

    port = int(
        os.getenv(
            "ARES_COAP_PORT",
            "5683",
        )
    )

    context = None

    try:
        context = await (
            Context.create_server_context(
                site,
                bind=(host, port),
            )
        )

        with _lock:
            _running = True
            _last_error = None

        print(
            "ARES CoAP server running at "
            f"coap://{host}:{port}/telemetry"
        )

        print(
            "ARES CoAP: signed payloads, "
            "unencrypted LAN transport"
        )

        # Keep running until the
        # FastAPI lifespan cancels task.
        await asyncio.Future()

    except asyncio.CancelledError:
        print(
            "ARES CoAP shutdown requested"
        )

        raise

    except Exception as exc:
        with _lock:
            _last_error = (
                "COAP_SERVER_ERROR:"
                + type(exc).__name__
            )

        print(
            "ARES CoAP server failed:",
            type(exc).__name__,
        )

        raise

    finally:
        with _lock:
            _running = False

        if context is not None:
            await context.shutdown()

        print(
            "ARES CoAP server stopped"
        )
