import uuid

from pathlib import Path

from fastapi import (
    HTTPException,
    UploadFile,
)

from PIL import Image


BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BASE_DIR / "runtime" / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


async def save_image(file: UploadFile) -> Path:

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG or WEBP images allowed",
        )

    max_size = 6 * 1024 * 1024

    payload = await file.read(max_size + 1)

    if not payload or len(payload) > max_size:
        raise HTTPException(
            status_code=413,
            detail="Image must be 6 MB or smaller",
        )

    path = UPLOAD_DIR / (
        uuid.uuid4().hex + ".img"
    )

    path.write_bytes(payload)

    try:
        with Image.open(path) as image:

            if (
                image.width * image.height
                > 20_000_000
            ):
                raise ValueError(
                    "Image pixel dimensions too large"
                )

            image.verify()

    except Exception as exc:

        path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail="Invalid image content",
        ) from exc

    return path