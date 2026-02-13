# Blockchain-Distributed-IDS

Blockchain-Enabled Distributed Intrusion Detection System for Securing IoT Networks

---

## 📘 Associated Publication

This repository accompanies the peer-reviewed paper:

Charles Stolz and Jielun Zhang  
“Blockchain-Enabled Distributed Intrusion Detection System for Securing IoT Networks”  
MILCOM 2025 – 2025 IEEE Military Communications Conference  
pp. 1–6, 2025  
DOI: https://doi.org/10.1109/MILCOM64451.2025.11310020  

If you use this software in academic work, please cite:

@INPROCEEDINGS{11310020,
  author={Stolz, Charles and Zhang, Jielun},
  booktitle={MILCOM 2025 - 2025 IEEE Military Communications Conference (MILCOM)}, 
  title={Blockchain-Enabled Distributed Intrusion Detection System for Securing IoT Networks}, 
  year={2025},
  pages={1-6},
  doi={10.1109/MILCOM64451.2025.11310020}
}

---

## Abstract (Project Summary)

This project implements a lightweight, blockchain-secured federated Intrusion Detection System (IDS) designed for resource-constrained IoT environments.

The system integrates:

• Federated Learning (Flower) for collaborative anomaly detection  
• Snort for signature-based intrusion detection  
• Hyperledger Fabric for tamper-evident logging of model updates  
• Reputation-based filtering to mitigate model poisoning  

All experiments were validated on a real hardware testbed consisting of:

• Raspberry Pi 4B and Raspberry Pi 5 nodes  
• ESP32 IoT sensor devices  
• An adversarial ODROID attacker node  

The framework demonstrates high detection accuracy while maintaining low computational overhead on edge devices.

---

## Key Contributions

• Hybrid IDS combining anomaly-based FL and signature-based Snort  
• Blockchain-backed SHA-256 model hash logging for integrity verification  
• Reputation scoring mechanism to detect and block poisoned model updates  
• Real-world deployment on Raspberry Pi and ESP32 hardware  
• Experimental validation using CICIDS2017 dataset  

---

## System Architecture

The architecture consists of:

1. ESP32 sensors  
   - Publish telemetry over secure MQTT  
   - Lightweight IoT data source  

2. Raspberry Pi IDS Nodes  
   - Local ANN training (78-feature CICIDS2017 input)  
   - Snort signature detection  
   - SHA-256 model hashing  
   - Hyperledger Fabric peer services  

3. Flower Federated Learning Server  
   - Coordinates aggregation (FedAvg / FedProx)  
   - Applies L2-norm filtering + reputation scoring  
   - Distributes global model  

4. Hyperledger Fabric Network  
   - Logs model hash, node ID, timestamp  
   - Records reputation score and acceptance status  
   - Provides tamper-evident audit trail  

---

## Experimental Results (MILCOM 2025)

### Federated Learning Performance

Best performance (FedAvg, 100 rounds):

Accuracy: 98.79%  
Precision: 98.20%  
Recall: 99.40%

### Model Poisoning Defense

Without filtering (poisoned round):
Accuracy ≈ 50%

With reputation scoring + L2-norm filtering:
Accuracy restored to:
• 97.41%
• 96.35%
• 95.77%

### Blockchain Logging Performance

1,000 model hash transactions  
Throughput: 21.47 TPS  
Average latency: 736 ms  
CPU overhead (blockchain peak): 12.9%  
Memory overhead: 51.4 MB  

All blockchain logging stores only model hashes (not full models) to minimize resource impact.

---

## Computational Efficiency

Under concurrent execution of:

• Federated learning  
• Snort IDS  
• Fabric peer + orderer  
• MQTT telemetry  

Observed on Raspberry Pi 4B (4GB):

CPU utilization: < 35%  
Memory utilization: < 38%

This validates feasibility for edge deployment.

---

## Dependencies

- Python 3.10+
- TensorFlow / Keras
- scikit-learn
- Flower
- Hyperledger Fabric (Docker-based)
- Snort 2.9
- Mosquitto MQTT
- ARM-based Linux (Debian 64-bit tested)

---

## Reproducibility

Release version corresponding to MILCOM 2025 results:

v1.0-milcom

Each federated round logs:

• Node ID  
• SHA-256 model hash  
• Reputation score  
• Acceptance/block status  
• UTC timestamp  

to the Fabric ledger via chaincode.

---

## Hardware Used in Paper

| Node      | Hardware          | RAM | Role |
|-----------|------------------|-----|------|
| Alpha     | Raspberry Pi 4B  | 4GB | ANN + Snort + Fabric |
| Beta      | Raspberry Pi 4B  | 4GB | ANN + Snort + Fabric |
| Epsilon   | Raspberry Pi 5   | 8GB | ANN + Snort + Fabric |
| Zeta      | Raspberry Pi 5   | 8GB | ANN + Snort + Fabric |
| Sensors   | ESP32 (6x)       | 512KB | Telemetry |

---

## Related Work

Previous edge IDS implementation:

Lightweight-IDS on Raspberry Pi  
https://github.com/rylandtikes/Lightweight-IDS

---

## License

This project is released for research and academic use.

For commercial or derivative use, please contact the authors.
