import os
import json
import numpy as np
import tensorflow as tf

# safer than direct submodule import for some VS Code setups
load_img = tf.keras.utils.load_img
img_to_array = tf.keras.utils.img_to_array

# ====== paths ======
img_path = r"backend\data\PlantVillage\Potato___healthy\0b3e5032-8ae8-49ac-8157-a1cac3df01dd___RS_HL 1817.JPG"
model_path = r"backend\models\disease_model.keras"
class_names_path = r"backend\models\class_names.json"

# ====== checks ======
if not os.path.exists(img_path):
    raise FileNotFoundError(f"Image not found: {img_path}")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model not found: {model_path}")

if not os.path.exists(class_names_path):
    raise FileNotFoundError(f"class_names.json not found: {class_names_path}")

# ====== load model ======
model = tf.keras.models.load_model(model_path)

# ====== load class names ======
with open(class_names_path, "r") as f:
    class_names = json.load(f)

# ====== preprocess image ======
img = load_img(img_path, target_size=(224, 224))
img_array = img_to_array(img)
img_array = np.expand_dims(img_array, axis=0)
img_array = img_array / 255.0

# ====== predict ======
pred = model.predict(img_array, verbose=0)[0]
idx = int(np.argmax(pred))
confidence = float(pred[idx])

# handles both list and dict class_names.json
if isinstance(class_names, dict):
    predicted_class = class_names[str(idx)]
else:
    predicted_class = class_names[idx]

print("Prediction:", predicted_class)
print("Confidence:", confidence)