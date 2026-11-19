from functools import lru_cache
from pathlib import Path

import pandas as pd


MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "models"
    / "crop_recommendation_model.pkl"
)

FEATURES = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]


@lru_cache(maxsize=1)
def load_crop_model():

    import joblib

    if not MODEL_PATH.exists():
        raise RuntimeError(
            "Crop recommendation model is missing"
        )

    # Only load your own trusted .pkl model.
    return joblib.load(MODEL_PATH)


def predict_crop(data: dict) -> dict:

    model = load_crop_model()

    row = pd.DataFrame([{
        key: float(data[key])
        for key in FEATURES
    }])

    probabilities = model.predict_proba(row)[0]

    ranked = sorted(
        zip(model.classes_, probabilities),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    best_crop, confidence = ranked[0]

    alternatives = [
        {
            "crop": str(name),
            "confidence": round(float(prob), 4),
        }
        for name, prob in ranked[1:4]
    ]

    return {
        "recommended_crop": str(best_crop),
        "confidence": round(
            float(confidence), 4
        ),
        "alternatives": alternatives,
    }