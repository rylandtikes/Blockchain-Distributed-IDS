#include <Arduino.h>
#include "sensor.h"
#include "mqtt_demo.h"

#define NODE_NAME "Sensor-1"

void setup() {
    Serial.begin(115200);
    Serial.println();
    Serial.print("Booting Node: ");
    Serial.println(NODE_NAME);

    connectWiFiAndMQTT();
    initSensor();
}

void loop() {
    publishMockTelemetry();   
    readSensor();
    delay(5000);
}

