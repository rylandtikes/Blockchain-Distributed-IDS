"""
Blockchain-Distributed-IDS - Server Node

This script runs on the server node in the Blockchain-Distributed-IDS system.  
It is responsible for:
- Coordinating Federated Learning among IDS client nodes.
- Aggregating model updates received from clients.
- Managing global model updates and distributing them back to clients.
- Using the Flower Federated Learning framework for decentralized training.

Author:
- Charles Stolz (cstolz2@und.edu)

Acknowledgments:
This project builds upon the following open-source contributions:

Flower Federated Learning Framework:
- Used for decentralized machine learning model coordination and aggregation.
- Documentation: https://flower.ai/docs/
- GitHub: https://github.com/adap/flower
- Reference Paper: Beutel, D.J., Topal, T., Mathur, A. et al. (2020). 
  "Flower: A Friendly Federated Learning Framework."
"""


import os
import flwr as fl
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import logging

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.config.set_visible_devices([], "GPU")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = "ann_model_server.keras"

INPUT_SHAPE = 78

# Build ANN model
def build_model():
    model = Sequential([
        Dense(64, activation="relu", input_shape=(INPUT_SHAPE,)),
        Dense(32, activation="relu"),
        Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss="binary_crossentropy", metrics=["accuracy"])
    return model

if os.path.exists(MODEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        logger.info("load existing ANN model for server.")
    except Exception as e:
        logger.error(f"error loading model: {e}. rebuilding")
        model = build_model()
else:
    model = build_model()
    logger.info("no saved model found creating new")

# Custom Aggregation Strategy
class FedAvgStrategy(fl.server.strategy.FedAvg):
    def configure_fit(self, server_round, parameters, client_manager):
        """Configure the training round, ensuring clients are selected properly."""
        available_clients = client_manager.num_available()
        logger.info(f"{available_clients} clients available. Selecting for training.")

        sample_size = min(available_clients, 1)
        clients = client_manager.sample(num_clients=sample_size)
        
        if not clients:
            logger.warning("no clients available for training.")
            return None
        
        logger.info(f"requesting training from {len(clients)} clients.")
        return [(client, fl.common.FitIns(parameters, {})) for client in clients]

    def aggregate_fit(self, server_round, results, failures):
        """Aggregates model parameters from clients"""
        logger.info(f"aggregating results for round {server_round}")

        if failures:
            logger.warning(f"{len(failures)} client(s) failed.")

        if not results:
            logger.error("no valid results received for aggregation.")
            return None, {}

        # validate all client weight shapes before aggregation
        try:
            client_weights = [fl.common.parameters_to_ndarrays(res.parameters) for _, res in results]

            for idx, weights in enumerate(client_weights):
                if weights[0].shape[0] != INPUT_SHAPE:
                    logger.error(f"client {idx+1} sent incorrect feature shape: {weights[0].shape}. Expected {INPUT_SHAPE}.")
                    return None, {}

            # calc average weights
            aggregated_weights = np.mean(np.array(client_weights, dtype=object), axis=0)

            model.set_weights(aggregated_weights)

            model.save(MODEL_PATH)
            logger.info("model aggregated and saved.")

            return fl.common.ndarrays_to_parameters(aggregated_weights), {}

        except Exception as e:
            logger.error(f" aggregation Error: {e}")
            return None, {}

logger.info("Starting Flower Server...")
fl.server.start_server(
    server_address="0.0.0.0:9091",
    config=fl.server.ServerConfig(num_rounds=1000, round_timeout=300),
    strategy=FedAvgStrategy(),
)

