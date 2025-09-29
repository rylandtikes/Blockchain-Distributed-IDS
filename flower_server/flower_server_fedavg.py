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
import hashlib

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.config.set_visible_devices([], "GPU")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = "./models/ann_model_server.keras"
HASH_LOG_PATH = "./received_model_hashes.log"
INPUT_SHAPE = 78

USE_REPUTATION_SCORING = True

MIN_CLIENTS = 3
MIN_FIT_CLIENTS = 3 

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
        logger.info("Loaded existing ANN model for server.")
    except Exception as e:
        logger.error(f"Error loading model: {e}. Rebuilding model.")
        model = build_model()
else:
    model = build_model()
    logger.info("No saved model found. Created new model.")

def compute_hash(weights):
    flat_bytes = b"".join([w.tobytes() for w in weights])
    return hashlib.sha256(flat_bytes).hexdigest()

# Simple FedAvg Strategy with hash logging only
class FedAvgWithHashLogging(fl.server.strategy.FedAvg):
    def aggregate_fit(self, server_round, results, failures):
        # First, do the standard FedAvg aggregation
        aggregated_parameters, metrics = super().aggregate_fit(server_round, results, failures)
        
        if results and aggregated_parameters:
            # Log SHA-256 hashes of received model updates
            with open(HASH_LOG_PATH, "a") as f:
                for client, fit_res in results:
                    client_id = client.cid
                    weights = fl.common.parameters_to_ndarrays(fit_res.parameters)
                    model_hash = compute_hash(weights)
                    logger.info(f"Received model update from {client_id} with SHA-256 hash: {model_hash}")
                    f.write(f"{client_id},{server_round},{model_hash}\n")
        
        return aggregated_parameters, metrics
# Custom FedAvg Strategy with reputation scoring and hash logging (for E6-R)
class FedAvgWithReputationScoring(fl.server.strategy.FedAvg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize reputation dictionary
        self.reputation = {
            "node-beta": 1.0,
            "node-epsilon": 1.0, 
            "node-zeta": 1.0
        }
        # Thresholds for anomaly detection
        self.norm_threshold = 50.0  #threshold based on clean model norms
        self.outlier_factor = 2.5   # 2.5x the average to be considered suspicious
        self.reputation_log_path = "./reputation_scores.log"
        
        # Initialize reputation log
        with open(self.reputation_log_path, "w") as f:
            f.write("round,client_id,reputation_score,timestamp,reason\n")
    
    def compute_update_norm(self, weights):
        """Compute L2 norm of model weights"""
        total_norm = 0.0
        for w in weights:
            total_norm += np.linalg.norm(w.flatten()) ** 2
        return np.sqrt(total_norm)
    
    def update_reputation(self, client_id, is_suspicious, reason=""):
        if client_id not in self.reputation:
            self.reputation[client_id] = 1.0
            
        if is_suspicious:
            #penalize suspicious updates
            self.reputation[client_id] = max(0.2, self.reputation[client_id] * 0.8)
            logger.warning(f"Client {client_id} flagged as suspicious ({reason}). "
                         f"Reputation: {self.reputation[client_id]:.3f}")
        else:
            # reward good behavior
            self.reputation[client_id] = min(1.0, self.reputation[client_id] + 0.05)
            if self.reputation[client_id] < 1.0:
                logger.info(f"Client {client_id} reputation recovering: {self.reputation[client_id]:.3f}")
    
    def log_reputation(self, server_round, client_id, reason=""):
        """Log reputation changes to file"""
        import time
        timestamp = time.time()
        with open(self.reputation_log_path, "a") as f:
            f.write(f"{server_round},{client_id},{self.reputation[client_id]:.3f},{timestamp},{reason}\n")

    def aggregate_fit(self, server_round, results, failures):
        logger.info(f"=== REPUTATION-BASED AGGREGATION - Round {server_round} ===")
        
        if failures:
            logger.warning(f"{len(failures)} client(s) failed.")

        if not results:
            logger.error("No valid results received for aggregation.")
            return None, {}

        try:
            # Extract client weights and analyze each update
            client_weights = []
            client_norms = []
            client_ids = []
            
            for client, fit_res in results:
                weights = fl.common.parameters_to_ndarrays(fit_res.parameters)
                client_weights.append(weights)
                client_ids.append(client.cid)
                
                # Compute update norm for anomaly detection
                update_norm = self.compute_update_norm(weights)
                client_norms.append(update_norm)
                
                logger.info(f"Client {client.cid}: Update norm = {update_norm:.4f}")
            
            # Ultra-simple approach: Find the obvious outlier
            min_norm = min(client_norms)
            max_norm = max(client_norms)
            
            logger.info(f"Update norms - Min: {min_norm:.1f}, Max: {max_norm:.1f}")
            
            # If max is more than 5x the min, it's obviously suspicious
            if max_norm > min_norm * 5.0:
                outlier_threshold = min_norm * 5.0
                logger.info(f"Outlier detected: threshold={outlier_threshold:.1f}")
            else:
                outlier_threshold = float('inf')  # No outliers
                logger.info("No clear outliers detected")
            
            # DETECTION & PREVENTION: Filter out extreme outliers
            filtered_results = []
            filtered_client_ids = []
            
            for i, (client_id, norm) in enumerate(zip(client_ids, client_norms)):
                is_suspicious = norm > outlier_threshold
                
                if is_suspicious:
                    reason = f"extreme_outlier_{norm:.1f}_vs_{min_norm:.1f}"
                    logger.warning(f"BLOCKED: Client {client_id} norm={norm:.1f} - EXCLUDED from aggregation")
                    # Update reputation but DON'T include in aggregation
                    self.update_reputation(client_id, is_suspicious, reason)
                    self.log_reputation(server_round, client_id, reason)
                else:
                    reason = ""
                    logger.info(f"ACCEPTED: Client {client_id} norm={norm:.1f}")
                    # Include in aggregation
                    filtered_results.append(results[i])
                    filtered_client_ids.append(client_id)
                    self.update_reputation(client_id, is_suspicious, reason)
                    self.log_reputation(server_round, client_id, reason)
            
            # Check if we have any clean clients left after filtering
            if not filtered_results:
                logger.error("ALL CLIENTS BLOCKED! Falling back to standard aggregation")
                # Fallback to prevent system failure
                return super().aggregate_fit(server_round, results, failures)
            
            logger.info(f"PREVENTION: Using {len(filtered_results)}/{len(results)} clients after filtering")
            
            # Log current reputation state
            logger.info("Current reputation scores:")
            for client_id in client_ids:
                rep_score = self.reputation[client_id]
                logger.info(f"  {client_id}: {rep_score:.3f}")
            
            # Use ONLY clean clients for standard FedAvg aggregation
            logger.info("Performing clean-client-only aggregation...")
            aggregated_weights = super().aggregate_fit(server_round, filtered_results, failures)
            
            # Log hashes for ALL clients (including blocked ones)
            with open(HASH_LOG_PATH, "a") as f:
                for client_id, weights in zip(client_ids, client_weights):
                    model_hash = compute_hash(weights)
                    rep_score = self.reputation[client_id]
                    status = "BLOCKED" if client_id not in filtered_client_ids else "ACCEPTED"
                    logger.info(f"Client {client_id}: hash={model_hash}, reputation={rep_score:.3f}, status={status}")
                    f.write(f"{client_id},{server_round},{model_hash},{rep_score:.3f},{status}\n")
            
            return aggregated_weights
            
        except Exception as e:
            logger.error(f" reputation-based aggregation error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, {}

# Select strategy based on configuration
if USE_REPUTATION_SCORING:
    logger.info(" starting Flower Server with Reputation Scoring...")
    strategy = FedAvgWithReputationScoring(
        min_available_clients=3,
        min_fit_clients=3,
        min_evaluate_clients=3,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
    )
else:
    logger.info("starting Flower Server with Vanilla FedAvg ...")
    strategy = FedAvgWithHashLogging(
        min_available_clients=3,
        min_fit_clients=3,
        min_evaluate_clients=3,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
    )

fl.server.start_server(
    server_address="0.0.0.0:9091",
    config=fl.server.ServerConfig(num_rounds=1, round_timeout=300),
    strategy=strategy,
)

