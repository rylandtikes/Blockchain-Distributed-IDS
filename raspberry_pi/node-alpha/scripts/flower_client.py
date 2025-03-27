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

import json
import logging
import numpy as np
import pandas as pd
import flwr as fl
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# +
# #!pip install flwr tensorflow pandas numpy scikit-learn imbalanced-learn pyarrow
# -

CONFIG_PATH = "../config/client_config.json"
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

CLIENT_ID = config["client_id"]
SERVER_ADDRESS = config["server_address"]
BATCH_SIZE = config["batch_size"]
LEARNING_RATE = config["learning_rate"]
USE_GPU = config["use_gpu"]
DATASET_PATH = config["dataset_path"]

# Disable GPU Raspberry Pi
if not USE_GPU:
    tf.config.set_visible_devices([], "GPU")
    logger.info("using CPU.")

df = pd.read_csv(DATASET_PATH)

# extract features and labels
X = df.iloc[:, :-1].values
y = df.iloc[:, -1].values

logger.info(f"dataset shape: {X.shape}")

X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

#scale feeatures
scaler = StandardScaler()
X = scaler.fit_transform(X)

import collections
# debug before oversampling
original_counts = collections.Counter(y)
print(f"Original class distribution: {original_counts}")

# convert multi-class labels into binary labels (Attack = 1, Benign = 0)
df["label_binary"] = df.iloc[:, -1].apply(lambda x: 0 if x == "BENIGN" else 1)
y = df["label_binary"].values.astype(np.int32)


# oversampling
ros = RandomOverSampler(sampling_strategy="auto", random_state=42)
X_resampled, y_resampled = ros.fit_resample(X, y)

oversampled_counts = collections.Counter(y_resampled)
print(f"After oversampling: {oversampled_counts}")

# split into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled)

def build_model():
    model = Sequential([
        Dense(64, activation="relu", input_shape=(X_train.shape[1],)),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1, activation="sigmoid")  # Binary classification output
    ])
    
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                  loss="binary_crossentropy",
                  metrics=["accuracy", "Precision", "Recall", "AUC"])
    
    return model

logger.info("initializing model")
model = build_model()

class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return model.get_weights()

    def set_parameters(self, parameters):
        model.set_weights(parameters)

    def fit(self, parameters, config):
        logger.info("received training request from server start training")
        self.set_parameters(parameters)
        history = model.fit(X_train, y_train, batch_size=BATCH_SIZE, epochs=7, verbose=2, validation_data=(X_val, y_val))
        logger.info(f"Training completed. Final Loss: {history.history['loss'][-1]}")
        return self.get_parameters(config), len(X_train), {}

    def evaluate(self, parameters, config):
        logger.info("evaluating model")
        self.set_parameters(parameters)
        loss, accuracy, precision, recall, auc = model.evaluate(X_val, y_val)
        logger.info(f"Evaluation completed. Loss: {loss}, Accuracy: {accuracy}, Precision: {precision}, Recall: {recall}, AUC: {auc}")
        return loss, len(X_val), {"accuracy": accuracy, "precision": precision, "recall": recall, "auc": auc}

# Start Flower client
logger.info(f" starting flower Client {CLIENT_ID}. connecting to server at {SERVER_ADDRESS}...")
fl.client.start_numpy_client(server_address=SERVER_ADDRESS, client=FlowerClient())



