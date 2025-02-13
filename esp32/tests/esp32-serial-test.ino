void setup() {
    Serial.begin(115200);
    Serial.println("ESP32 basic test");
}

void loop() {
    Serial.println("Hello ESP32");
    delay(1000);
}