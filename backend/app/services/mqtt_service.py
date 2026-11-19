import json
import os
import threading
import time

from app.services.security_service import (
    verify_telemetry_envelope,
)
from app.services.state_service import save_telemetry
from app.services.log_service import write_log


TELEMETRY_TOPIC = "ares/rover/telemetry"

_client = None
_connected = False

_last_message_at = None
_last_verified_at = None
_last_error = None
_received_count = 0
_verified_count = 0
_rejected_count = 0

_lock = threading.Lock()


def _set_error(message: str):
    global _last_error

    with _lock:
        _last_error = message


def _reject(reason: str):
    global _rejected_count

    with _lock:
        _rejected_count += 1

    _set_error(reason)

    write_log({
        "source": "mqtt",
        "event": "TELEMETRY_REJECTED",
        "security": {
            "security_status": "ALERT",
            "decision": "BLOCK",
            "alerts": [reason],
        },
    })


def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties=None,
):
    global _connected

    connected = int(reason_code) == 0

    with _lock:
        _connected = connected

    if connected:
        result, mid = client.subscribe(
            TELEMETRY_TOPIC,
            qos=1,
        )

        if result != 0:
            _set_error(
                f"MQTT subscription failed: {result}"
            )
            print("ARES MQTT subscription failed")
            return

        _set_error(None)
        print(
            f"ARES MQTT connected; subscribed to "
            f"{TELEMETRY_TOPIC}"
        )

    else:
        _set_error(
            f"MQTT connection rejected: {reason_code}"
        )
        print("ARES MQTT connection rejected")


def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties=None,
):
    global _connected

    with _lock:
        _connected = False

    if int(reason_code) != 0:
        _set_error(
            f"MQTT disconnected: {reason_code}"
        )


def on_message(client, userdata, message):
    global _last_message_at
    global _last_verified_at
    global _received_count
    global _verified_count

    if message.topic != TELEMETRY_TOPIC:
        return

    with _lock:
        _received_count += 1
        _last_message_at = time.time()

    if len(message.payload) > 8192:
        _reject("OVERSIZED_MQTT_PACKET")
        return

    try:
        raw = json.loads(
            message.payload.decode("utf-8")
        )

        if not isinstance(raw, dict):
            raise ValueError(
                "MQTT payload must be a JSON object"
            )

    except (ValueError, UnicodeDecodeError):
        _reject("MALFORMED_MQTT_JSON")
        return

    try:
        envelope, error = verify_telemetry_envelope(
            raw
        )

    except Exception as exc:
        _reject(
            f"TELEMETRY_VERIFICATION_ERROR: "
            f"{type(exc).__name__}"
        )
        return

    if error is not None:
        _reject(error)
        return

    data = envelope.data.model_dump(
        exclude_none=True
    )

    try:
        save_telemetry(
            data=data,
            source="MQTT_VERIFIED",
            device_id=envelope.device_id,
            verified=True,
            sequence=envelope.sequence,
        )

    except Exception as exc:
        _reject(
            f"TELEMETRY_STORAGE_ERROR: "
            f"{type(exc).__name__}"
        )
        return

    with _lock:
        _verified_count += 1
        _last_verified_at = time.time()
        _last_error = None

    print(
        f"ARES verified MQTT telemetry: "
        f"device={envelope.device_id}, "
        f"sequence={envelope.sequence}"
    )


def start_mqtt():
    global _client
    global _connected

    enabled = (
        os.getenv(
            "ARES_MQTT_ENABLED",
            "false",
        ).lower() == "true"
    )

    if not enabled:
        print(
            "ARES MQTT disabled. "
            "Hardware telemetry not connected."
        )
        return

    if _client is not None:
        return

    import paho.mqtt.client as mqtt

    host = os.getenv(
        "ARES_MQTT_HOST",
        "",
    ).strip()

    port = int(
        os.getenv(
            "ARES_MQTT_PORT",
            "8883",
        )
    )

    username = os.getenv(
        "ARES_MQTT_USERNAME",
        "",
    )

    password = os.getenv(
        "ARES_MQTT_PASSWORD",
        "",
    )

    ca_cert = os.getenv(
        "ARES_MQTT_CA_CERT",
        "",
    )

    secret = os.getenv(
        "ARES_DEVICE_HMAC_SECRET",
        "",
    )

    if not all([
        host,
        username,
        password,
        ca_cert,
        secret,
    ]):
        raise RuntimeError(
            "ARES MQTT configuration incomplete. "
            "Set MQTT host, username, password, "
            "CA certificate and device HMAC secret."
        )

    if not os.path.isfile(ca_cert):
        raise RuntimeError(
            "ARES MQTT CA certificate file not found"
        )

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="ares_backend",
    )

    client.username_pw_set(
        username,
        password,
    )

    client.tls_set(
        ca_certs=ca_cert,
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.connect(
            host,
            port,
            keepalive=30,
        )

        client.loop_start()

        _client = client

        print(
            "ARES MQTT client started. "
            "Waiting for broker connection."
        )

    except Exception:
        with _lock:
            _connected = False

        _set_error(
            "MQTT broker connection failed"
        )

        raise


def stop_mqtt():
    global _client
    global _connected

    client = _client
    _client = None

    if client is not None:
        client.disconnect()
        client.loop_stop()

    with _lock:
        _connected = False


def broker_status():
    with _lock:
        connected = _connected
        last_message = _last_message_at
        last_verified = _last_verified_at
        last_error = _last_error
        received = _received_count
        verified = _verified_count
        rejected = _rejected_count

    now = time.time()

    return {
        "enabled": (
            os.getenv(
                "ARES_MQTT_ENABLED",
                "false",
            ).lower() == "true"
        ),
        "connected": connected,
        "topic": TELEMETRY_TOPIC,
        "received_count": received,
        "verified_count": verified,
        "rejected_count"
        : rejected,
        "last_message_at": last_message,
        "last_verified_at": last_verified,
        "last_verified_age_seconds": (
            round(now - last_verified, 2)
            if last_verified is not None
            else None
        ),
        "last_error": last_error,
    }