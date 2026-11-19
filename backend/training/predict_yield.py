import os
import json
import pandas as pd
import numpy as np
from xgboost import XGBRegressor

# -----------------------------
# Paths
# -----------------------------
MODEL_PATH = "/content/models/yield_xgb_tuned.json"
META_PATH = "/content/models/yield_xgb_meta.json"

# -----------------------------
# Load metadata
# -----------------------------
with open(META_PATH, "r") as f:
    meta = json.load(f)

categorical_cols = meta["categorical_cols"]

# -----------------------------
# Load model
# -----------------------------
model = XGBRegressor()
model.load_model(MODEL_PATH)

print("Model loaded successfully.")

# -----------------------------
# Input sample
# -----------------------------
sample_df = pd.DataFrame([{
    "State_Name": "Maharashtra",
    "District_Name": "Pune",
    "Crop_Year": 2019,
    "Season": "Kharif",
    "Crop": "Rice",
    "Area": 1000
}])

# -----------------------------
# Convert categorical columns
# -----------------------------
for col in categorical_cols:
    sample_df[col] = sample_df[col].astype("category")

# -----------------------------
# Predict
# -----------------------------
pred_log = model.predict(sample_df)[0]
pred_actual = np.expm1(pred_log)

print("\n=== Yield Prediction Result ===")
print(sample_df)
print(f"\nPredicted Production: {pred_actual:.4f}")