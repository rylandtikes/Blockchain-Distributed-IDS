#!/bin/bash

wget -q https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_ARM64.tar.gz -O /tmp/arduino-cli.tar.gz || { echo "Failed to download Arduino CLI"; exit 1; }
tar -xzf /tmp/arduino-cli.tar.gz -C /tmp || { echo "Failed to extract Arduino CLI"; exit 1; }
sudo mv /tmp/arduino-cli /usr/local/bin/arduino-cli || { echo "Failed to move Arduino CLI binary"; exit 1; }
sudo chmod +x /usr/local/bin/arduino-cli
rm -f /tmp/arduino-cli.tar.gz
arduino-cli version || { echo "installation failed"; exit 1; }
echo "installed successfully!"
echo "Updating core index"
arduino-cli core update-index
echo "Installing ESP32 board support..."
arduino-cli core install esp32:esp32 || { echo "Failed to install ESP32 board support"; exit 1; }
echo "ESP32 board support installed"
arduino-cli core list
mkdir -p ~/.arduino15
arduino-cli config init
echo "Arduino CLI setup is complete"
