/*
  IoT-Enabled Smart Agriculture Monitoring System
  ------------------------------------------------
  Board: ESP32 (works in Wokwi simulator)
  Sensors:
    - DHT22       -> Temperature & Humidity (GPIO 4)
    - Soil Moisture (analog) -> GPIO 34
    - LDR (analog, light)    -> GPIO 35
  Actuator:
    - Relay (water pump)     -> GPIO 25
  Connectivity:
    - WiFi + MQTT (broker.hivemq.com - public test broker)

  This sketch reads sensors every 5 seconds, prints values to the
  Serial Monitor, applies a simple irrigation threshold rule, and
  publishes JSON data to an MQTT topic.

  Wokwi project: create a new ESP32 project, add DHT22, a
  potentiometer (as soil moisture / LDR analog source), and a relay
  module, then wire as commented below.
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

// ---------- Pin Definitions ----------
#define DHTPIN   4
#define DHTTYPE  DHT22
#define SOIL_PIN 34   // Analog input (soil moisture sensor)
#define LDR_PIN  35   // Analog input (light sensor)
#define RELAY_PIN 25  // Digital output (pump relay)

DHT dht(DHTPIN, DHTTYPE);

// ---------- WiFi & MQTT ----------
const char* ssid     = "Wokwi-GUEST";   // Wokwi simulator default network
const char* password = "";
const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

// ---------- Thresholds ----------
const int SOIL_DRY_THRESHOLD = 1500;   // below this -> turn pump ON
const int SOIL_WET_THRESHOLD = 2800;   // above this -> turn pump OFF
const float TEMP_HIGH_THRESHOLD = 35.0;

bool pumpState = false;

void setup_wifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("esp32SmartFarmClient")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2 seconds");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Relay OFF (active-low module assumption)

  dht.begin();

  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // ---- Read sensors ----
  float temperature = dht.readTemperature();
  float humidity    = dht.readHumidity();
  int soilValue     = analogRead(SOIL_PIN);
  int lightValue    = analogRead(LDR_PIN);

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }

  // ---- Irrigation logic ----
  if (soilValue < SOIL_DRY_THRESHOLD) {
    pumpState = true;
  } else if (soilValue > SOIL_WET_THRESHOLD) {
    pumpState = false;
  }

  digitalWrite(RELAY_PIN, pumpState ? LOW : HIGH); // active-low relay

  // ---- Serial Monitor Output ----
  Serial.println("---------------------------------");
  Serial.printf("Soil Moisture : %d\n", soilValue);
  Serial.printf("Temperature   : %.1f C\n", temperature);
  Serial.printf("Humidity      : %.1f %%\n", humidity);
  Serial.printf("Light         : %d\n", lightValue);
  Serial.printf("Pump Status   : %s\n", pumpState ? "ON" : "OFF");

  if (soilValue < SOIL_DRY_THRESHOLD) {
    Serial.println("ALERT: Low soil moisture - irrigation started");
  }
  if (temperature > TEMP_HIGH_THRESHOLD) {
    Serial.println("ALERT: High temperature detected");
  }

  // ---- Publish to MQTT ----
  char payload[150];
  snprintf(payload, sizeof(payload),
           "{\"soil\":%d,\"temp\":%.1f,\"hum\":%.1f,\"light\":%d,\"pump\":\"%s\"}",
           soilValue, temperature, humidity, lightValue, pumpState ? "ON" : "OFF");

  client.publish("farm/node1/data", payload);

  delay(5000);
}
