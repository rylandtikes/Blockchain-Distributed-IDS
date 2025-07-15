
# # Blockchain-Distributed-IDS - Client Node  
#
# This notebook runs on a **client node** in the Blockchain-Distributed-IDS system. It trains a local Intrusion Detection System (IDS) model and participates in **Federated Learning** using the Flower framework.  
#
# ## Author  
# **Charles Stolz**  
# cstolz2@und.edu  
#
# ## Acknowledgments  
# This project builds upon the following open-source contributions:  
#
# ### Flower Federated Learning Framework  
# - Used for decentralized model training and updates across IDS nodes.  
# - **Documentation:** [Flower AI Docs](https://flower.ai/docs/)  
# - **GitHub:** [Flower GitHub](https://github.com/adap/flower)  
# - **Reference Paper:** Beutel, D.J., Topal, T., Mathur, A. et al. (2020). *Flower: A Friendly Federated Learning Framework.*  
#
from prometheus_client import start_http_server, Gauge, Counter
import time
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
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = "../config/client_config.json"
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

CLIENT_ID = config["client_id"]
SERVER_ADDRESS = config["server_address"]
BATCH_SIZE = config["batch_size"]
LEARNING_RATE = config["learning_rate"]
USE_GPU = config["use_gpu"]
DATASET_PATH = config["dataset_path"]

if not USE_GPU:
    tf.config.set_visible_devices([], "GPU")
    logger.info("using CPU.")

df = pd.read_csv(DATASET_PATH)

X = df.iloc[:, :-1].values
y = df.iloc[:, -1].values

logger.info(f"dataset shape: {X.shape}")

X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

scaler = StandardScaler()
X = scaler.fit_transform(X)

import collections
original_counts = collections.Counter(y)
print(f"Original class distribution: {original_counts}")

df["label_binary"] = df.iloc[:, -1].apply(lambda x: 0 if x == "BENIGN" else 1)
y = df["label_binary"].values.astype(np.int32)

ros = RandomOverSampler(sampling_strategy="auto", random_state=42)
X_resampled, y_resampled = ros.fit_resample(X, y)

oversampled_counts = collections.Counter(y_resampled)
print(f"After oversampling: {oversampled_counts}")

X_train, X_val, y_train, y_val = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled)

def build_model():
    model = Sequential([
        Dense(64, activation="relu", input_shape=(X_train.shape[1],)),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1, activation="sigmoid")
    ])
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                  loss="binary_crossentropy",
                  metrics=["accuracy", "Precision", "Recall", "AUC"])
    return model

def hash_model_weights(weights) -> str:
    hasher = hashlib.sha256()
    for weight in weights:
        hasher.update(weight.tobytes())
    return hasher.hexdigest()

def simulate_detection(X_stream, y_stream, model):
    logger.info("Starting real-time detection loop with Prometheus metrics...")
    attack_count = 0
    for x, y_true in zip(X_stream, y_stream):
        start = time.time()
        y_pred = model.predict(np.expand_dims(x, axis=0))[0][0]
        latency = (time.time() - start) * 1000
        inference_latency.set(latency)
        predicted_class.set(1 if y_pred >= 0.5 else 0)
        if y_pred >= 0.5:
            attack_count += 1
        alerts_triggered.set(attack_count)
        logger.info(f"Inference latency: {latency:.2f} ms | Prediction: {y_pred:.4f} | Total alerts: {attack_count}")
        time.sleep(1)

logger.info("initializing model")
model = build_model()

start_http_server(9100)

inference_latency = Gauge('inference_latency_ms', 'Latency per prediction in milliseconds')
alerts_triggered = Gauge('alerts_triggered', 'Number of attack predictions')
predicted_class = Gauge('predicted_class', 'Latest predicted class (0 or 1)')
model_training_rounds = Counter('model_training_rounds_total', 'Total number of FL training rounds completed')
model_hash_changes = Counter('model_hash_changes_total', 'Number of unique model weight updates')

class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return model.get_weights()

    def set_parameters(self, parameters):
        model.set_weights(parameters)

    def fit(self, parameters, config):
        logger.info("received training request from server start training")
        self.set_parameters(parameters)
        history = model.fit(
            X_train, y_train,
            batch_size=BATCH_SIZE,
            epochs=7,
            verbose=2,
            validation_data=(X_val, y_val)
        )
        logger.info(f"Training completed. Final Loss: {history.history['loss'][-1]}")
        current_weights = self.get_parameters(config)
        model_hash = hash_model_weights(current_weights)
        model_training_rounds.inc()
        model_hash_changes.inc()
        ssd_path = "/home/rtikes/ml-data/flower/model_hashes.log"
        timestamp = datetime.utcnow().isoformat() + 'Z'
        os.makedirs(os.path.dirname(ssd_path), exist_ok=True)
        with open(ssd_path, "a") as f:
            f.write(f"{CLIENT_ID},{timestamp},{model_hash}\n")
        logger.info(f"Model hash: {model_hash} (saved to {ssd_path})")
        return current_weights, len(X_train), {}

    def evaluate(self, parameters, config):
        logger.info("evaluating model")
        self.set_parameters(parameters)
        loss, accuracy, precision, recall, auc = model.evaluate(X_val, y_val)
        logger.info(f"Evaluation completed. Loss: {loss}, Accuracy: {accuracy}, Precision: {precision}, Recall: {recall}, AUC: {auc}")
        return loss, len(X_val), {"accuracy": accuracy, "precision": precision, "recall": recall, "auc": auc}

logger.info(f" starting flower Client {CLIENT_ID}. connecting to server at {SERVER_ADDRESS}...")
fl.client.start_numpy_client(server_address=SERVER_ADDRESS, client=FlowerClient())

simulate_detection(X_val, y_val, model)

