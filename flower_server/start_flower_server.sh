#!/bin/bash

export TF_CPP_MIN_LOG_LEVEL=2
export XLA_FLAGS=--xla_gpu_cuda_data_dir=/usr/local/cuda
echo "checking GPU"
python -c "import tensorflow as tf; print('TensorFlow GPU:', tf.test.gpu_device_name())"
echo "starting Flowerserver"
flower-superlink --insecure

