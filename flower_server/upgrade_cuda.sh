#!/bin/bash

sudo apt remove --purge -y '^cuda.*' '^nvidia.*' '^libcudnn.*' '^libnccl.*' '^libcufft.*'
sudo apt autoremove -y
sudo rm -rf /usr/local/cuda*

sudo apt update
sudo apt install -y wget gnupg

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-5

echo 'export PATH=/usr/local/cuda-12.5/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.5/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export CUDA_HOME=/usr/local/cuda-12.5' >> ~/.bashrc
source ~/.bashrc

