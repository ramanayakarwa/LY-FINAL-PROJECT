import json

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "models" / "yield_xgb_tuned.json"

META_PATH = BASE_DIR / "models" / "yield_xgb_meta.json"


FEATURES = [
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop",
    "Area",
]


@lru_cache(maxsize=1)
def load_production_model():

    from xgboost import XGBRegressor

    if not MODEL_PATH.exists():
        raise RuntimeError(
            "Production model missing"
        )

    if not META_PATH.exists():
        raise RuntimeError(
            "Production metadata missing"
        )

    model = XGBRegressor()

    model.load_model(str(MODEL_PATH))

    with META_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(file)

    return model, metadata


def match_category(value, categories):

    for category in categories:

        if (
            str(category).strip().casefold()
            == str(value).strip().casefold()
        ):
            return category

    raise ValueError(
        f"Unsupported model category: {value}"
    )


def predict_yield(data: dict) -> dict:

    model, metadata = load_production_model()

    row = {
        name: data[name]
        for name in FEATURES
    }

    row["Crop_Year"] = int(row["Crop_Year"])
    row["Area"] = float(row["Area"])

    if row["Area"] <= 0:
        raise ValueError(
            "Area must be greater than zero"
        )

    for column in metadata["categorical_cols"]:

        categories = metadata[
            "category_values"
        ][column]

        row[column] = match_category(
            row[column],
            categories,
        )

    frame = pd.DataFrame(
        [row],
        columns=FEATURES,
    )

    for column in metadata["categorical_cols"]:

        frame[column] = pd.Categorical(
            frame[column],
            categories=metadata[
                "category_values"
            ][column],
        )

    prediction_log = model.predict(frame)[0]

    predicted = float(
        np.expm1(prediction_log)
    )

    if not np.isfinite(predicted):
        raise RuntimeError(
            "Invalid production model output"
        )

    return {
        "predicted_production": round(
            max(0, predicted),
            2,
        ),
        "method": "XGBOOST",
        "unit": "tonnes",
        "input_used": row,
    }