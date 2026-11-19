"""Backend health, verified real-time telemetry and per-protocol status."""
import os
from fastapi import APIRouter
from app.services.state_service import snapshot, last_action
from app.services.mqtt_service import broker_status
from app.services.coap_services import coap_status

router = APIRouter(prefix='/system', tags=['System'])

@router.get('/status')
def status():
    t = snapshot()
    demo = os.getenv('ARES_DEMO_MODE', 'true').lower() == 'true'
    live_source = (
        t['fresh'] and t['verified'] and
        t['source'] in ('MQTT_VERIFIED', 'COAP_SIGNED')
    )
    state = 'ONLINE' if live_source else 'SIMULATION' if demo else 'OFFLINE'
    mode = (
        'LIVE_SENSORS_SIMULATED_ACTUATION' if live_source and demo
        else 'LIVE_SENSORS_ONLY' if live_source
        else 'SIMULATION' if demo else 'NOT_COMMISSIONED'
    )
    return {
        'unit_name': os.getenv('ARES_DEVICE_ID', 'ARES_ROVER_01'),
        'status': state,
        'mode': mode,
        'telemetry': t,
        'mqtt': broker_status(),
        'coap': coap_status(),
        'last_action': last_action(),
        'arm_actuation_available': False,
        'live_hardware_commissioned': False,
    }
