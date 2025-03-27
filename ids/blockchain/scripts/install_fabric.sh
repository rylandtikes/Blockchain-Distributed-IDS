#!/bin/bash

set -e

sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget unzip build-essential jq docker.io docker-compose

sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker << END
echo "Docker group updated."
END

cd ~
wget https://go.dev/dl/go1.20.14.linux-arm64.tar.gz
sudo tar -C /usr/local -xzf go1.20.14.linux-arm64.tar.gz
rm go1.20.14.linux-arm64.tar.gz

echo 'export GOPATH=$HOME/go' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin' >> ~/.bashrc
source ~/.bashrc

git clone https://github.com/hyperledger/fabric-samples.git
cd fabric-samples
git checkout v2.4.9

wget https://github.com/hyperledger/fabric/releases/download/v2.5.0/hyperledger-fabric-linux-arm64-2.5.0.tar.gz
tar -xvzf hyperledger-fabric-linux-arm64-2.5.0.tar.gz
mkdir -p ~/bin
mv bin/* ~/bin

echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
source ~/.bashrc

peer version
go version
docker version

