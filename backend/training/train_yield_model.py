import os
import json
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# -----------------------------
# PATHS (FIXED)
# -----------------------------
DATA_PATH = r"C:\Users\Parigannu\Desktop\Pari clg 2024-25\LY PROJECT\LY Project\backend\data\filtered_crop_production.csv"
MODEL_DIR = "models"

MODEL_PATH = os.path.join(MODEL_DIR, "yield_xgb_tuned.json")
META_PATH = os.path.join(MODEL_DIR, "yield_xgb_meta.json")

os.makedirs(MODEL_DIR, exist_ok=True)

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv(DATA_PATH)

# -----------------------------
# DO NOT FILTER CROPS ❌
# -----------------------------
# KEEP FULL DATASET

# -----------------------------
# REQUIRED COLUMNS
# -----------------------------
cols = [
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop",
    "Area",
    "Production"
]

df = df[cols].dropna()

df = df[df["Area"] > 0]
df = df[df["Production"] > 0]

# -----------------------------
# SAMPLE (FAST)
# -----------------------------
if len(df) > 50000:
    df = df.sample(n=50000, random_state=42)

# -----------------------------
# FEATURES
# -----------------------------
X = df.drop(columns=["Production"]).copy()
y = np.log1p(df["Production"])

categorical_cols = ["State_Name", "District_Name", "Season", "Crop"]

for col in categorical_cols:
    X[col] = X[col].astype("category")

# -----------------------------
# SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# MODEL
# -----------------------------
model = XGBRegressor(
    objective="reg:squarederror",
    tree_method="hist",
    enable_categorical=True,
    random_state=42
)

# -----------------------------
# TUNING
# -----------------------------
param_dist = {
    "n_estimators": [200, 300],
    "max_depth": [6, 8],
    "learning_rate": [0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0]
}

search = RandomizedSearchCV(
    model,
    param_dist,
    n_iter=5,
    scoring="r2",
    cv=3,
    verbose=2,
    random_state=42,
    n_jobs=-1
)

print("🔥 Training model...")
search.fit(X_train, y_train)

best_model = search.best_estimator_

# -----------------------------
# EVALUATION
# -----------------------------
y_pred_log = best_model.predict(X_test)

y_test_actual = np.expm1(y_test)
y_pred_actual = np.expm1(y_pred_log)

mae = mean_absolute_error(y_test_actual, y_pred_actual)
rmse = np.sqrt(mean_squared_error(y_test_actual, y_pred_actual))
r2 = r2_score(y_test_actual, y_pred_actual)

print("\n📊 RESULTS:")
print("MAE :", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2  :", round(r2, 4))

# -----------------------------
# SAVE MODEL
# -----------------------------
best_model.save_model(MODEL_PATH)

category_values = {}
for col in categorical_cols:
    category_values[col] = list(X[col].cat.categories)

meta = {
    "categorical_cols": categorical_cols,
    "category_values": category_values
}

with open(META_PATH, "w") as f:
    json.dump(meta, f)

print("\n✅ Model saved!")