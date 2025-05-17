#include <WiFi.h>

const char* ssid     = "DroneController - Server ESP32";
const char* password = "@jajalmao@";
WiFiServer server(80);

// Pines PWM
int fanPin    = 2;  // PWM original
int fanPin2   = 12; // Nuevo PWM
int fanPin3   = 13; // Nuevo PWM
int fanPin4   = 14; // Nuevo PWM

// Pines LED estroboscópicos
int led1Pin   = 4;
int led2Pin   = 5;

// Parpadeo
const unsigned long STROBE_INTERVAL = 300;
unsigned long previousMillis = 0;
int strobePhase = 0;

void setup() {
  Serial.begin(115200);

  // Pines de salida
  pinMode(fanPin, OUTPUT);
  pinMode(fanPin2, OUTPUT);
  pinMode(fanPin3, OUTPUT);
  pinMode(fanPin4, OUTPUT);
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);

  WiFi.softAP(ssid, password);
  server.begin();
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= STROBE_INTERVAL) {
    previousMillis = currentMillis;
    switch (strobePhase) {
      case 0: digitalWrite(led1Pin, HIGH); digitalWrite(led2Pin, LOW); break;
      case 1: digitalWrite(led1Pin, LOW); break;
      case 2: digitalWrite(led2Pin, HIGH); break;
      case 3: digitalWrite(led2Pin, LOW); break;
    }
    strobePhase = (strobePhase + 1) % 4;
  }

  WiFiClient client = server.available();
  if (client) {
    if (client.connected()) {
      if (client.available()) {
        String line = client.readStringUntil('\n');
        int pwm = line.toInt();
        pwm = constrain(pwm, 0, 255);

        // Aplicar PWM a los 4 pines
        analogWrite(fanPin, pwm);
        analogWrite(fanPin2, pwm);
        analogWrite(fanPin3, pwm);
        analogWrite(fanPin4, pwm);
      }
    }
    client.stop();
  }
}
