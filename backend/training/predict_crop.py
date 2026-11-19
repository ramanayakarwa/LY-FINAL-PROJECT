import os
import joblib
import pandas as pd
import numpy as np

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "crop_recommendation_model.pkl")

# -----------------------------
# Load model
# -----------------------------
model = joblib.load(MODEL_PATH)
print("Crop recommendation model loaded successfully.")

# -----------------------------
# Input
# -----------------------------
sample = pd.DataFrame([{
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.87,
    "humidity": 82.0,
    "ph": 6.5,
    "rainfall": 202.93
}])

# -----------------------------
# Predict
# -----------------------------
pred = model.predict(sample)[0]
probs = model.predict_proba(sample)[0]
classes = model.classes_

top_idx = np.argsort(probs)[::-1][:3]

print("\n=== Crop Prediction Result ===")
print("Recommended Crop:", pred)

print("\nTop 3 Suggestions:")
for i in top_idx:
    print(f"{classes[i]} -> {probs[i]:.4f}")