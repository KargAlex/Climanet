#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include "DHT.h"
#include <RH_RF22.h>

#define DHTPIN A0
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const int rainSensorPin = A1;
const int ledPin = 13;
const int UV_OUT = A2;
const int REF_3V3 = A3;

SoftwareSerial gpsSerial(4, 3); // RX, TX
TinyGPSPlus gps;

#define RF22_CS 10
#define RF22_INT 2
#define RF22_RST 9
RH_RF22 rf22(RF22_CS, RF22_INT);

unsigned long lastSensorRead = 0;
const unsigned long sensorInterval = 10000;

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  gpsSerial.begin(9600);
  dht.begin();
  Serial.println("Initializing");
  
  pinMode(RF22_RST, OUTPUT);
  digitalWrite(RF22_RST, HIGH); delay(10);
  digitalWrite(RF22_RST, LOW); delay(10);
  digitalWrite(RF22_RST, HIGH); delay(10);

  if (!rf22.init()) {
    Serial.println("RF22 init failed");
    while (1);
  }
  rf22.setFrequency(433.0);
  rf22.setTxPower(20);
}

void loop() {
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  if (millis() - lastSensorRead > sensorInterval) {
    lastSensorRead = millis();

    int rainValue = analogRead(rainSensorPin);
    bool rainDetected = (rainValue < 500);
    digitalWrite(ledPin, rainDetected ? HIGH : LOW);

    int uvLevel = analogRead_average(UV_OUT);
    int refLevel = analogRead_average(REF_3V3);
    float outputVoltage = 3.3 / refLevel * uvLevel;
    float uvIntensity = mapfloat(outputVoltage, 0.99, 2.8, 0.0, 15.0);

    float temp = dht.readTemperature();
    float hum = dht.readHumidity();

    sendWithAckAndPrint("RAIN", rainDetected ? "Yes" : "No");
    delay(200);
    sendWithAckAndPrint("UV", String(uvIntensity, 2));
    delay(200);
    sendWithAckAndPrint("TEMP", isnan(temp) ? "NaN" : String(temp, 2));
    delay(200);
    sendWithAckAndPrint("HUM", isnan(hum) ? "NaN" : String(hum, 2));
    delay(200);

    bool gnssFix = gps.location.isValid() && gps.time.isValid();
    Serial.print("GNSS: ");
    Serial.println(gnssFix ? "FIXED" : "NO FIX");

    if (gnssFix) {
      sendWithAckAndPrint("LON", String(gps.location.lng(), 6)); delay(200);
      sendWithAckAndPrint("LAT", String(gps.location.lat(), 6)); delay(200);
      sendWithAckAndPrint("ALT", String(gps.altitude.meters(), 2)); delay(200);

      char timeStr[25];
      snprintf(timeStr, sizeof(timeStr), "%04d-%02d-%02dT%02d:%02d:%02d",
               gps.date.year(), gps.date.month(), gps.date.day(),
               gps.time.hour(), gps.time.minute(), gps.time.second());
      sendWithAckAndPrint("TIME", String(timeStr));
    }
  }
}

bool sendWithAck(String message) {
  rf22.send((uint8_t *)message.c_str(), message.length());
  rf22.waitPacketSent();
  return waitForAck(3000);
}

void sendWithAckAndPrint(String key, String value) {
  String message = key + "=" + value;
  bool ackReceived = sendWithAck(message);
  Serial.print(key); Serial.print(": "); Serial.print(value);
  Serial.print(" , ACK = "); Serial.println(ackReceived ? "YES" : "NO");
}

bool waitForAck(unsigned long timeout) {
  unsigned long start = millis();
  while (millis() - start < timeout) {
    if (rf22.available()) {
      uint8_t buf[108];
      uint8_t len = sizeof(buf);
      if (rf22.recv(buf, &len)) {
        buf[len] = '\0';
        if (String((char*)buf) == "ACK") return true;
      }
    }
  }
  return false;
}

int analogRead_average(int pinToRead) {
  int sum = 0;
  for (int i = 0; i < 8; i++) sum += analogRead(pinToRead);
  return sum / 8;
}

float mapfloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}