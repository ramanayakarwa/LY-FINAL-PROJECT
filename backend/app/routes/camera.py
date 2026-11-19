
"""
ARES ESP32-CAM backend routes.

Fetches actual JPEG images from an ESP32-CAM
on a trusted local Wi-Fi network.

No simulated camera images are generated.
"""

import asyncio
import ipaddress
import json
import os
import urllib.error
import urllib.request

from io import BytesIO

from fastapi import APIRouter, HTTPException, Response
from PIL import Image, UnidentifiedImageError


router = APIRouter(
    prefix="/camera",
    tags=["ARES ESP32-CAM"],
)

MAX_IMAGE_BYTES = 6 * 1024 * 1024


def _camera_config():
    host = os.getenv("ARES_CAMERA_HOST", "").strip()
    key = os.getenv("ARES_CAMERA_KEY", "").strip()

    if not host or not key:
        raise HTTPException(
            status_code=503,
            detail="ESP32-CAM is not configured",
        )

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="Camera host must be a private IPv4 address",
        )

    if (
        address.version != 4
        or not address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
    ):
        raise HTTPException(
            status_code=503,
            detail="Camera must use a trusted private LAN IPv4 address",
        )

    return host, key


def _fetch_camera(path: str):
    host, key = _camera_config()

    request = urllib.request.Request(
        f"http://{host}/{path}",
        headers={
            "X-ARES-Camera-Key": key,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=5,
        ) as response:
            if response.status != 200:
                raise RuntimeError("Camera returned an error")

            payload = response.read(MAX_IMAGE_BYTES + 1)

            if len(payload) > MAX_IMAGE_BYTES:
                raise RuntimeError("Camera response too large")

            return payload

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as exc:
        raise RuntimeError(
            f"Camera unreachable: {type(exc).__name__}"
        ) from exc


@router.get("/status")
async def camera_status():
    """
    Check whether the actual ESP32-CAM
    responds over the local network.
    """

    configured = bool(
        os.getenv("ARES_CAMERA_HOST", "").strip()
        and os.getenv("ARES_CAMERA_KEY", "").strip()
    )

    if not configured:
        return {
            "configured": False,
            "connected": False,
            "camera": "ESP32-CAM OV2640",
            "source": "REAL_HARDWARE_ONLY",
        }

    try:
        payload = await asyncio.to_thread(
            _fetch_camera,
            "status",
        )

        data = json.loads(payload.decode("utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Invalid camera status")

        return {
            "configured": True,
            "connected": True,
            "camera": "ESP32-CAM OV2640",
            "source": "REAL_HARDWARE",
            "device_status": data,
        }

    except (
        RuntimeError,
        ValueError,
        UnicodeDecodeError,
    ):
        return {
            "configured": True,
            "connected": False,
            "camera": "ESP32-CAM OV2640",
            "source": "REAL_HARDWARE_ONLY",
            "message": "Camera offline or unreachable",
        }


@router.get("/capture")
async def camera_capture():
    """
    Return a JPEG captured by the real camera.
    Never substitute a sample image.
    """

    try:
        payload = await asyncio.to_thread(
            _fetch_camera,
            "capture",
        )

        with Image.open(BytesIO(payload)) as image:
            if image.format != "JPEG":
                raise ValueError("Expected JPEG image")

            image.verify()

    except HTTPException:
        raise

    except (
        RuntimeError,
        ValueError,
        UnidentifiedImageError,
        OSError,
    ):
        raise HTTPException(
            status_code=503,
            detail="Real ESP32-CAM image unavailable",
        )

    return Response(
        content=payload,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
        },
    )
