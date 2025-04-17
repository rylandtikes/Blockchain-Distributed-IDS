export PATH=$PWD/bin:$PATH
export FABRIC_CFG_PATH=$PWD/config

./network.sh up createChannel -c mychannel -ca

