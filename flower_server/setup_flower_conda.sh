#!/bin/bash
conda create --name flower-env python=3.11 -y
conda activate flower-env
pip install --upgrade pip
pip install flwr torch torchvision torchaudio tensorflow numpy pandas
python -c "import flwr; print('Flower version:', flwr.__version__)"


