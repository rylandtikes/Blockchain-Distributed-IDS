#!/bin/bash

set -e

sudo apt update
sudo apt install -y prometheus curl

sudo mv /etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml.bak || true

CUSTOM_CONFIG=./prometheus.yml
if [ ! -f "$CUSTOM_CONFIG" ]; then
  echo "❌ ERROR: $CUSTOM_CONFIG not found. Please check the path."
  exit 1
fi
sudo cp "$CUSTOM_CONFIG" /etc/prometheus/prometheus.yml

sudo systemctl restart prometheus
sudo systemctl enable prometheus

