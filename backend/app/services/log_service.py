import json

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock


BASE_DIR = Path(__file__).resolve().parents[2]

LOG_PATH = (
    BASE_DIR
    / "runtime"
    / "system_logs.jsonl"
)

_lock = RLock()


def write_log(data: dict):

    LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    entry = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        **data,
    }

    with _lock:
        with LOG_PATH.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    entry,
                    ensure_ascii=False,
                    default=str,
                ) + "\n"
            )

    return entry


def read_logs(limit: int = 20):

    if not LOG_PATH.exists():
        return []

    with _lock:
        with LOG_PATH.open(
            encoding="utf-8"
        ) as file:
            lines = file.readlines()[-limit:]

    result = []

    for line in lines:
        try:
            result.append(
                json.loads(line)
            )

        except json.JSONDecodeError:
            continue

    return result