from copy import deepcopy
from threading import RLock
from time import time

_lock = RLock()

_state = {
    "data": {},
    "source": "NONE",
    "received_at": None,
    "device_id": None,
    "verified": False,
    "last_sequence": None,
}

_last_action = {
    "status": "NONE",
    "execution": "NOT_REQUESTED",
}


def save_telemetry(
    data: dict,
    source: str,
    device_id: str,
    verified: bool = False,
    sequence: int | None = None,
) -> dict:
    global _state

    with _lock:
        _state = {
            "data": deepcopy(data),
            "source": source,
            "received_at": time(),
            "device_id": device_id,
            "verified": bool(verified),
            "last_sequence": sequence,
        }

    return snapshot()


def snapshot(max_age_seconds: int = 15) -> dict:
    with _lock:
        result = deepcopy(_state)

    received_at = result["received_at"]

    result["age_seconds"] = (
        round(time() - received_at, 2)
        if received_at is not None
        else None
    )

    result["fresh"] = (
        received_at is not None
        and time() - received_at <= max_age_seconds
    )

    return result


def record_action(record: dict):
    global _last_action

    with _lock:
        _last_action = deepcopy(record)


def last_action() -> dict:
    with _lock:
        return deepcopy(_last_action)