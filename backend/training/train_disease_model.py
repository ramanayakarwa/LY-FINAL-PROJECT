import os
import json
import tensorflow as tf

# ================= CPU-ONLY (SAFE DEFAULT) =================
# Force CPU so you don't depend on CUDA/cuDNN locally
tf.config.set_visible_devices([], 'GPU')
print("🖥️ Running on CPU")

# ================= PATHS =================
# IMPORTANT: use your FLATTENED dataset (train_final)
DATASET_DIR = r"C:\Users\Parigannu\Desktop\Pari clg 2024-25\LY PROJECT\LY Project\backend\data\train_final"
MODEL_DIR = r"backend/models"

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "disease_model.keras")
CLASS_PATH = os.path.join(MODEL_DIR, "class_names.json")

IMG_SIZE = (224, 224)
BATCH_SIZE = 32          # keep smaller on CPU
EPOCHS_STAGE1 = 8
EPOCHS_STAGE2 = 5
SEED = 42

print("Dataset:", DATASET_DIR)

# ================= LOAD DATA =================
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int"
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int"
)

class_names = train_ds.class_names
num_classes = len(class_names)

print("Classes:", class_names)

# ================= PERFORMANCE =================
AUTOTUNE = tf.data.AUTOTUNE
# cache() can be heavy on RAM; if RAM is low, remove cache()
train_ds = train_ds.shuffle(1000).prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# ================= AUGMENTATION =================
data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.1),
    tf.keras.layers.RandomZoom(0.1),
    tf.keras.layers.RandomContrast(0.1),
])

# ================= MODEL =================
base_model = tf.keras.applications.EfficientNetB0(
    include_top=False,
    weights="imagenet",
    input_shape=(224, 224, 3)
)
base_model.trainable = False

inputs = tf.keras.Input(shape=(224, 224, 3))
x = data_augmentation(inputs)
x = tf.keras.applications.efficientnet.preprocess_input(x)

x = base_model(x, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.BatchNormalization()(x)
x = tf.keras.layers.Dense(256, activation="relu")(x)
x = tf.keras.layers.Dropout(0.4)(x)

outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

model = tf.keras.Model(inputs, outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(5e-4),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# ================= CALLBACKS =================
callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=3,
        restore_best_weights=True
    ),
    tf.keras.callbacks.ModelCheckpoint(
        MODEL_PATH,
        monitor="val_accuracy",
        save_best_only=True
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=2,
        min_lr=1e-6
    )
]

# ================= STAGE 1 =================
print("🚀 Stage 1 training...")
history1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_STAGE1,
    callbacks=callbacks
)

# ================= STAGE 2 =================
print("🚀 Stage 2 fine-tuning...")
base_model.trainable = True

for layer in base_model.layers[:-50]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

history2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_STAGE1 + EPOCHS_STAGE2,
    initial_epoch=history1.epoch[-1] + 1,
    callbacks=callbacks
)

# ================= SAVE =================
model.save(MODEL_PATH)

with open(CLASS_PATH, "w") as f:
    json.dump(class_names, f)

print("✅ Model saved:", MODEL_PATH)
print("✅ Class names saved:", CLASS_PATH)