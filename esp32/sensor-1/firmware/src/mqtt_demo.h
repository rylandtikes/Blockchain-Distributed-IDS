#ifndef MQTT_DEMO_H
#define MQTT_DEMO_H

#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "";
const char* password = "";
const char* mqtt_server = "192.168.8.215";

WiFiClient espClient;
PubSubClient client(espClient);

void connectWiFiAndMQTT() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected");

    client.setServer(mqtt_server, 1883);
    while (!client.connected()) {
        client.connect("ESP32Client");
    }

    Serial.println("MQTT connected.");
}

void publishMockTelemetry() {
    if (!client.connected()) {
        client.connect("ESP32Client");
    }
    client.loop();

    String payload = "{\"node\":\"esp32\",\"anomaly\":0.42,\"ts\":\"2025-05-11T20:01:00Z\"}";
    client.publish("esp32/telemetry", payload.c_str());
    Serial.println("Published mock telemetry: " + payload);
}

#endif
