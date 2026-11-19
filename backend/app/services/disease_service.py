import json
import re

from functools import lru_cache
from pathlib import Path

import numpy as np

from PIL import Image, UnidentifiedImageError

from app.services.disease_advice_service import (
    get_disease_advice,
)


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR / "models" / "disease_model.keras"
)

CLASS_PATH = (
    BASE_DIR / "models" / "class_names.json"
)


@lru_cache(maxsize=1)
def load_disease_model():

    import tensorflow as tf

    if not MODEL_PATH.exists():
        raise RuntimeError(
            "Disease model missing"
        )

    if not CLASS_PATH.exists():
        raise RuntimeError(
            "Disease class names missing"
        )

    model = tf.keras.models.load_model(
        str(MODEL_PATH)
    )

    with CLASS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        class_names = json.load(file)

    if isinstance(class_names, dict):
        # Supports {label: index}.
        class_names = [
            label
            for label, index in sorted(
                class_names.items(),
                key=lambda item: int(item[1]),
            )
        ]

    return model, class_names


def clean_label(raw_label: str):

    label = raw_label.replace(
        "Tomoto", "Tomato"
    )

    label = re.sub(
        r"^Tomato_cleaned_",
        "",
        label,
        flags=re.I,
    )

    label = re.sub(
        r"^Spinach_augmented_",
        "Spinach_",
        label,
        flags=re.I,
    )

    label = re.sub(
        r"\([^)]*\)",
        "",
        label,
    )

    lower = label.casefold()

    if "tomato" in lower:
        crop = "Tomato"

    elif "spinach" in lower:
        crop = "Spinach"

    else:
        crop = "Unknown"

    disease = label

    # Remove repeated prefixes such as Tomato_Tomato.
    for _ in range(2):
        disease = re.sub(
            r"^(tomato|spinach)[_\- ]+",
            "",
            disease,
            flags=re.I,
        )

    disease = re.sub(
        r"[_\-]+",
        " ",
        disease,
    ).strip().title()

    return crop, disease


def predict_disease(image_path: str):

    model, classes = load_disease_model()

    try:
        with Image.open(image_path) as image:

            image = image.convert(
                "RGB"
            ).resize((224, 224))

            image_array = np.asarray(
                image,
                dtype=np.float32,
            )

            image_array = image_array[
                None, ...
            ]

    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(
            "Unreadable plant image"
        ) from exc

    # EfficientNet training expects this input scale.
    # Do not divide by 255 unless the model was
    # trained with that same additional scaling.
    predictions = model.predict(
        image_array,
        verbose=0,
    )[0]

    index = int(
        np.argmax(predictions)
    )

    if index >= len(classes):
        raise RuntimeError(
            "Model output/class-name mismatch"
        )

    raw_label = classes[index]

    crop, disease = clean_label(
        raw_label
    )

    confidence = float(
        predictions[index]
    )

    advice = get_disease_advice(
        raw_label
    )

    if "healthy" in disease.casefold():

        advice = {
            "health_status": "Healthy",
            "treatment": "No treatment indicated.",
            "precautions": [
                "Continue regular monitoring."
            ],
            "prevention": [
                "Maintain appropriate watering "
                "and sanitation."
            ],
        }

    return {
        "crop": crop,
        "disease": disease,
        "confidence": round(confidence, 4),
        "raw_label": raw_label,
        "health_status": advice["health_status"],
        "treatment": advice["treatment"],
        "precautions": advice["precautions"],
        "prevention": advice["prevention"],
        "target_localized": False,
        "physical_intervention_ready": False,
    }