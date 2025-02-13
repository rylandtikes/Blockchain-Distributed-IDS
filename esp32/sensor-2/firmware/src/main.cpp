#include <Arduino.h>
#include "sensor.h"

#define NODE_NAME "Sensor-2"

void setup() {
    Serial.begin(115200);
    Serial.println();
    Serial.print("Booting Node: ");
    Serial.println(NODE_NAME);

    initSensor();
}

void loop() {
    readSensor();
    delay(1000);
}
