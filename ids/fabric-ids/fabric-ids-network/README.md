# Fabric IDS Network

This directory contains a customized Hyperledger Fabric test network used as the blockchain backend for the Blockchain-Distributed-IDS project.

## Purpose

This Fabric network is used to:
- Enable secure logging of IDS model updates using Hyperledger Fabric
- Simulate a permissioned blockchain across multiple nodes (e.g., `node-alpha`, `node-beta`)
- Support federated learning scenarios where model integrity and trust are critical

## Structure

Based on the official Fabric `test-network`, this setup includes:
- Two organizations (Org1 and Org2), each with one peer
- A single Raft ordering service
- Certificate Authorities for both orgs
- A default channel named `idschannel`
- CLI scripts to start the network and deploy chaincode

## Usage

### Start the network (with channel and CAs):
```bash
./network.sh up createChannel -c idschannel -ca

