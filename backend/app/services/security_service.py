"""Detection and validation rules. No claims of ML-based attack detection.

The safety gate is separate; sensor plausibility is not authentication.
"""
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, ConfigDict

class Telemetry(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    temperature: float | None = Field(default=None, ge=-20, le=70)
    humidity: float | None = Field(default=None, ge=0, le=100)
    soil_moisture: float | None = Field(default=None, ge=0, le=100)
    light: float | None = Field(default=None, ge=0)
    distance_cm: float | None = Field(default=None, ge=0)
    battery_percent: float | None = Field(default=None, ge=0, le=100)
    arm_homed: bool | None = None
    pump_off: bool | None = None
    obstacle_stop: bool | None = None
    gps_lat_e6: int | None = Field(default=None, ge=-90000000, le=90000000)
    gps_lon_e6: int | None = Field(default=None, ge=-180000000, le=180000000)
    gps_satellites: int | None = Field(default=None, ge=0, le=100)

class TelemetryEnvelope(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    device_id: str = Field(min_length=3, max_length=80)
    sequence: int = Field(ge=0)
    issued_at: float
    data: Telemetry
    signature: str

class SecurityResult(BaseModel):
    security_status: str
    decision: str
    alerts: list[str]
    checks: dict[str, str]

class CybersecurityLayer:
    def __init__(self, data=None):
        self.data = data or {}

    def final_security_output(self):
        alerts=[]
        checks={}
        try:
            Telemetry.model_validate({k:v for k,v in self.data.items() if k in Telemetry.model_fields})
            checks['sensor_ranges']='PASS'
        except (ValidationError, TypeError, ValueError) as err:
            alerts.append('Sensor reading outside configured bounds or malformed')
            checks['sensor_ranges']='FAIL'
        return {'security_status':'ALERT' if alerts else 'NO_SENSOR_ANOMALY',
                'decision':'BLOCK' if alerts else 'ALLOW',
                'alerts':alerts,'checks':checks}


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def sign_payload(payload: dict, secret: str) -> str:
    return hmac.new(secret.encode('utf8'), canonical(payload), hashlib.sha256).hexdigest()

def verify_signature(payload: dict, signature: str, secret: str) -> bool:
    if not isinstance(signature, str) or len(signature) != 64 or not secret:
        return False
    return hmac.compare_digest(sign_payload(payload, secret), signature)

# Keeps replay protection over service restarts on a single-machine demonstration.
_nonce_lock=threading.Lock()

def accept_once(key: str, ttl_seconds: int=120) -> bool:
    db=Path(os.getenv('ARES_REPLAY_DB',str(Path(__file__).resolve().parents[2] / 'runtime/replay.db')))
    db.parent.mkdir(parents=True,exist_ok=True)
    with _nonce_lock, sqlite3.connect(db, timeout=5) as con:
        con.execute('CREATE TABLE IF NOT EXISTS replay(key TEXT PRIMARY KEY, expires REAL NOT NULL)')
        con.execute('DELETE FROM replay WHERE expires < ?', (time.time(),))
        try:
            con.execute('INSERT INTO replay(key,expires) VALUES(?,?)',(key,time.time()+ttl_seconds))
            con.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def verify_telemetry_envelope(raw: dict):
    """Reject spoofed/expired/out-of-order packets unless HMAC and broker policy are correct."""
    try:
        msg=TelemetryEnvelope.model_validate(raw)
    except ValidationError as e:
        return None, 'INVALID_SCHEMA'
    if msg.device_id != os.getenv('ARES_DEVICE_ID','ARES_ROVER_01'):
        return None, 'WRONG_DEVICE'
    if abs(time.time()-msg.issued_at)>30:
        return None, 'STALE_TIMESTAMP'
    secret=os.getenv('ARES_DEVICE_HMAC_SECRET','')
    body=msg.model_dump(exclude={'signature'},exclude_none=True)
    if not verify_signature(body,msg.signature,secret):
        return None, 'BAD_SIGNATURE_OR_KEY_UNCONFIGURED'
    if not accept_once(f'telemetry:{msg.device_id}:{msg.sequence}',120):
        return None, 'REPLAY_DETECTED'
    return msg, None
