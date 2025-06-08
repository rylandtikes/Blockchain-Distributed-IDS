# Blockchain-Distributed-IDS

A Blockchain-Enabled Federated Intrusion Detection System for Securing IoT Networks.

## Overview

This project implements a lightweight, distributed Intrusion Detection System (IDS) tailored for resource-constrained IoT environments. It integrates:

- Federated Learning (via [Flower](https://flower.dev)) for collaborative anomaly detection across edge devices
- Hyperledger Fabric for tamper-resistant blockchain logging of model updates
- Snort for local, signature-based threat detection
- Support for heterogeneous edge devices including Raspberry Pi and ESP32

This work supports experiments presented in the paper:

> **Blockchain-Enabled Distributed Intrusion Detection System for Securing IoT Networks**  
> (Submitted to MILCOM 2025)

---

## System Architecture

- Raspberry Pi nodes host anomaly-based ML detection and Snort
- Model updates are shared via Flower and verified using SHA-256 hashes
- Hashes are recorded on a private blockchain using Hyperledger Fabric
- ESP32 nodes simulate lightweight IoT sensors (optional, future work)

---

## Features

- Federated anomaly detection using CNN or Random Forest
- Secure logging of model hash values via blockchain
- Lightweight edge deployment using Raspberry Pi
- Snort integration for signature-based detection
- Evaluation using CICIDS2017 subset

---

## Dependencies

- Python 3.10+
- TensorFlow 2.x, Keras, scikit-learn
- [Flower](https://flower.dev)
- Hyperledger Fabric (via Docker)
- Snort IDS (on supported hardware)
- MQTT broker (e.g., Mosquitto) for sensor simulation

---

## Authors

| Author           | Email                     |
|------------------|----------------------------|
| Charles Stolz    | charles.stolz@und.edu      |
| Dr. Jielun Zhang | jielun.zhang@und.edu      |

---

## Related Work

For our earlier system that inspired this design, see:  
[Lightweight-IDS on Raspberry Pi](https://github.com/rylandtikes/Lightweight-IDS)

---

## License

This project is licensed for research and educational use. For commercial or derivative uses, please contact the authors.

### Third-Party Licenses and Attribution

This project uses portions of [Hyperledger Fabric](https://github.com/hyperledger/fabric),  
licensed under the Apache License, Version 2.0.

You may obtain a copy of the License at:  
http://www.apache.org/licenses/LICENSE-2.0

We thank the Hyperledger Fabric contributors and maintainers for providing the foundational blockchain framework.
