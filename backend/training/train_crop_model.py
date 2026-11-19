import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# -----------------------------
# PATHS
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "Crop_recommendation.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "crop_recommendation_model.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv(DATA_PATH)
df = df.drop_duplicates().dropna()

print("Dataset shape:", df.shape)

# -----------------------------
# FEATURES
# -----------------------------
X = df.drop(columns=["label"])
y = df["label"]

# -----------------------------
# SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------------
# MODEL
# -----------------------------
model = ExtraTreesClassifier(
    random_state=42,
    n_jobs=-1
)

param_grid = {
    "n_estimators": [200, 300],
    "max_depth": [None, 20]
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid = GridSearchCV(
    model,
    param_grid,
    scoring="accuracy",
    cv=cv,
    n_jobs=-1,
    verbose=1
)

print("\n🔥 Training...")
grid.fit(X_train, y_train)

best_model = grid.best_estimator_

print("\nBest Params:", grid.best_params_)

# -----------------------------
# EVALUATION
# -----------------------------
y_pred = best_model.predict(X_test)

print("\n===== RESULTS =====")
print("Accuracy :", round(accuracy_score(y_test, y_pred), 4))
print("Precision:", round(precision_score(y_test, y_pred, average="weighted"), 4))
print("Recall   :", round(recall_score(y_test, y_pred, average="weighted"), 4))
print("F1 Score :", round(f1_score(y_test, y_pred, average="weighted"), 4))

print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# -----------------------------
# SAVE MODEL
# -----------------------------
joblib.dump(best_model, MODEL_PATH)
print("\nModel saved at:", MODEL_PATH)

# =====================================================
# 🌱 MAPPING TO YOUR PROJECT CROPS (IMPORTANT)
# =====================================================
def map_to_project_crop(crop):
    crop = crop.lower()

    if crop in ["rice", "maize", "banana", "papaya"]:
        return "Tomato"

    if crop in ["coconut", "coffee", "mango"]:
        return "Spinach"

    return "Other"

# -----------------------------
# TEST SAMPLE
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

raw_pred = best_model.predict(sample)[0]
final_pred = map_to_project_crop(raw_pred)

probs = best_model.predict_proba(sample)[0]
classes = best_model.classes_

top_idx = np.argsort(probs)[::-1][:3]

print("\n===== TOP 3 PREDICTIONS =====")
for i in top_idx:
    mapped = map_to_project_crop(classes[i])
    print(f"{classes[i]} → {mapped} ({probs[i]:.4f})")

print("\n🌱 Final Crop (Mapped):", final_pred)