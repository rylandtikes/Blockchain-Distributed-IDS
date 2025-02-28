#!/bin/bash

source /home/rtikes/anaconda3/bin/activate flower-env

export TF_CPP_MIN_LOG_LEVEL=3
export XLA_FLAGS=--xla_gpu_cuda_data_dir=/usr/local/cuda
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH
export PATH=$CUDA_HOME/bin:$PATH
export CUDA_VISIBLE_DEVICES=0
export TF_FORCE_GPU_ALLOW_GROWTH=true
export TF_ENABLE_AUTO_MIXED_PRECISION=0
export TF_ENABLE_CUBLAS=0
export TF_ENABLE_CUDNN=0
export TF_ENABLE_CUFFT=0
export TF_DISABLE_MLIR_CUDA_ALLOWLIST=1
export FORCE_PYTHON_IP_VERSION=4
export GUNICORN_CMD_ARGS="--bind 0.0.0.0"

python3 /home/rtikes/Blockchain-Distributed-IDS/flower_server/flower_server.py

