sudo apt update
sudo apt install -y apt-transport-https software-properties-common wget gnupg

wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

sudo apt update
sudo apt install grafana -y

sudo systemctl enable grafana-server
sudo systemctl start grafana-server

