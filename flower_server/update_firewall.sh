#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exit 1
fi

ufw allow 9091/tcp
ufw allow 9092/tcp
ufw allow 9093/tcp
ufw reload

systemctl restart fl_server.service

sleep 5

netstat -tulnp | grep python

