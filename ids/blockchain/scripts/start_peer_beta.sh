#!/bin/bash

export FABRIC_CFG_PATH=/home/rtikes/Blockchain-Distributed-IDS/ids/blockchain/config-beta/
export CORE_PEER_ID=peer0.node-beta.idsnet.local
export CORE_PEER_ADDRESS=peer0.node-beta.idsnet.local:8051
export CORE_PEER_LISTENADDRESS=0.0.0.0:8051
export CORE_PEER_LOCALMSPID=NodeBetaOrgMSP
export CORE_PEER_MSPCONFIGPATH=/home/rtikes/Blockchain-Distributed-IDS/ids/blockchain/artifacts/crypto-config/peerOrganizations/node-beta.idsnet.local/peers/peer0.node-beta.idsnet.local/msp
export CORE_PEER_FILESYSTEMPATH=/home/rtikes/Blockchain-Distributed-IDS/ids/blockchain/ledgers/peer
export FABRIC_LOGGING_SPEC=INFO
export CORE_PEER_BCCSP_DEFAULT=SW
export CORE_PEER_BCCSP_SW_FILEKEYSTORE_KEYSTORE=/home/rtikes/Blockchain-Distributed-IDS/ids/blockchain/artifacts/crypto-config/peerOrganizations/node-beta.idsnet.local/peers/peer0.node-beta.idsnet.local/msp/keystore
export CORE_VM_ENDPOINT=unix:///var/run/docker.sock

/home/rtikes/bin/peer node start

