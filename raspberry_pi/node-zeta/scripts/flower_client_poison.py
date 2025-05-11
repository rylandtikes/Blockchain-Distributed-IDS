import json
import logging
import hashlib
import os
import numpy as np
import pandas as pd
import flwr as fl
import tensorflow as tf
from datetime import datetime
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CONFIG_PATH = "../config/client_config.json"
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

CLIENT_ID = config["client_id"]
SERVER_ADDRESS = config["server_address"]
BATCH_SIZE = config["batch_size"]
LEARNING_RATE = config["learning_rate"]
USE_GPU = config["use_gpu"]
DATASET_PATH = config["dataset_path"]

# Disable GPU on Raspberry Pi if not configured
if not USE_GPU:
    tf.config.set_visible_devices([], "GPU")
    logger.info("Using CPU only.")

# Load and preprocess dataset
df = pd.read_csv(DATASET_PATH)
X = df.iloc[:, :-1].values
y = df.iloc[:, -1].values
X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Convert labels to binary
df["label_binary"] = df.iloc[:, -1].apply(lambda x: 0 if x == "BENIGN" else 1)
y = df["label_binary"].values.astype(np.int32)

# Oversample to balance classes
ros = RandomOverSampler(sampling_strategy="auto", random_state=42)
X_resampled, y_resampled = ros.fit_resample(X, y)

# Train/validation split
X_train, X_val, y_train, y_val = train_test_split(
    X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled
)

# Poisoning toggle: enable on node-zeta for one round
POISON_MODEL = True if CLIENT_ID == "node-zeta" else False
POISON_ROUND = 1  # apply poisoning on first round
tc = 0  # training counter

# Model builder
def build_model():
    model = Sequential([
        Dense(64, activation="relu", input_shape=(X_train.shape[1],)),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1, activation="sigmoid")
    ])
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="binary_crossentropy",
        metrics=["accuracy", "Precision", "Recall", "AUC"]
    )
    return model

# Hashing function
def hash_model_weights(weights) -> str:
    hasher = hashlib.sha256()
    for weight in weights:
        hasher.update(weight.tobytes())
    return hasher.hexdigest()

# Initialize model
model = build_model()
class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return model.get_weights()

    def set_parameters(self, parameters):
        model.set_weights(parameters)

    def fit(self, parameters, config):
        global tc
        tc += 1
        logger.info(f"Starting training round {tc}...")
        self.set_parameters(parameters)
        # Train local model
        history = model.fit(
            X_train, y_train,
            batch_size=BATCH_SIZE,
            epochs=7,
            verbose=2,
            validation_data=(X_val, y_val)
        )
        logger.info(f"Training completed for round {tc}.")

        # Poison model on first round if enabled
        if POISON_MODEL and tc == POISON_ROUND:
            logger.warning("Injecting poisoned weights on this client...")
            for layer in model.layers:
                w = layer.get_weights()
                poisoned = [np.random.normal(size=wi.shape) for wi in w]
                layer.set_weights(poisoned)

        current_weights = model.get_weights()
        model_hash = hash_model_weights(current_weights)
        timestamp = datetime.utcnow().isoformat() + 'Z'
        log_line = f"{CLIENT_ID},{timestamp},{model_hash}\n"
        ssd_path = "/home/rtikes/ml-data/flower/model_hashes.log"
        os.makedirs(os.path.dirname(ssd_path), exist_ok=True)
        with open(ssd_path, "a") as f:
            f.write(log_line)
        logger.info(f"Logged model hash: {model_hash}")

        return current_weights, len(X_train), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy, precision, recall, auc = model.evaluate(X_val, y_val)
        return loss, len(X_val), {"accuracy": accuracy, "precision": precision, "recall": recall, "auc": auc}

# Start Flower client
logger.info(f"Starting Flower client {CLIENT_ID} connecting to {SERVER_ADDRESS}")
fl.client.start_numpy_client(server_address=SERVER_ADDRESS, client=FlowerClient())

