# Experiment E7: ESP32 Data Forwarding Demo (Integration Validation)

**Date:** 2025-05-11  
**Goal:** Validate that the ESP32 sensor node can send telemetry over MQTT to a Raspberry Pi MQTT broker.  
**Broker:** Mosquitto running on `node-beta` (192.168.8.215)

## Procedure

- ESP32 firmware was flashed using `arduino-cli`.
- Firmware connects to WiFi and publishes mock telemetry JSON to the topic `esp32/telemetry` once per second.
- On another node (`odroid`), `mosquitto_sub` was used to verify messages are received from the broker.

## Observed Output

Example MQTT message received:

```json
{"node":"esp32","anomaly":0.42,"ts":"2025-05-11T20:01:00Z"}

