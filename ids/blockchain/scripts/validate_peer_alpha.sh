#!/bin/bash

PEER_ID="peer0.node-alpha.idsnet.local"
ORG_MSP="NodeAlphaOrgMSP"
MSP_PATH="/home/rtikes/Blockchain-Distributed-IDS/ids/blockchain/artifacts/crypto-config/peerOrganizations/node-alpha.idsnet.local/users/Admin@node-alpha.idsnet.local/msp"
FABRIC_CFG="/home/rtikes/Blockchain-Distributed-IDS/ids/blockchain/config-beta"
LEDGER_PATH="/home/rtikes/Blockchain-Distributed-IDS/ids/blockchain/ledgers/peer"
KEYSTORE_PATH="${MSP_PATH}/keystore"
PEER_ADDRESS="${PEER_ID}:8051"

export CORE_PEER_ID="$PEER_ID"
export CORE_PEER_ADDRESS="$PEER_ADDRESS"
export CORE_PEER_LISTENADDRESS="0.0.0.0:8051"
export CORE_PEER_LOCALMSPID="$ORG_MSP"
export CORE_PEER_MSPCONFIGPATH="$MSP_PATH"
export CORE_PEER_FILESYSTEMPATH="$LEDGER_PATH"
export CORE_PEER_BCCSP_DEFAULT=SW
export CORE_PEER_BCCSP_SW_FILEKEYSTORE_KEYSTORE="$KEYSTORE_PATH"
export CORE_VM_ENDPOINT=unix:///var/run/docker.sock
export FABRIC_CFG_PATH="$FABRIC_CFG"
export FABRIC_LOGGING_SPEC=INFO

echo " Validating peer: $PEER_ID"
peer lifecycle chaincode queryinstalled

