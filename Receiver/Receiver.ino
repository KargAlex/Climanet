#include <RH_RF22.h>

#define RF22_CS 10
#define RF22_INT 2
#define RF22_RST 9
#define DEVICE 0

RH_RF22 rf22(RF22_CS, RF22_INT);
const int ledPin = 13;

bool rainDetected = false;
float uvIntensity = 0.0;
float temperature = 0.0;
float humidity = 0.0;
float longitude = 0.0;
float latitude = 0.0;
float altitude = 0.0;
String gpsTime = "Unknown";

unsigned long lastPrint = 0;
const unsigned long printInterval = 5000;

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);

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
  Serial.println("RF22 Receiver initialized");
}

void loop() {
  if (rf22.available()) {
    uint8_t buf[RH_RF22_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf22.recv(buf, &len)) {
      buf[len] = '\0';
      String message = String((char*)buf);
      parseMessage(message);

      const char* ackMsg = "ACK";
      rf22.send((uint8_t*)ackMsg, strlen(ackMsg));
      rf22.waitPacketSent();

      digitalWrite(ledPin, HIGH); delay(50); digitalWrite(ledPin, LOW);
    }
  }

  if (millis() - lastPrint > printInterval) {
    lastPrint = millis();
    printAllValues();
  }
}

void parseMessage(String msg) {
  int sep = msg.indexOf('=');
  if (sep == -1) return;

  String key = msg.substring(0, sep);
  String val = msg.substring(sep + 1);

  if (key == "RAIN") {
    rainDetected = (val == "Yes");
  } else if (key == "UV") {
    uvIntensity = val.toFloat();
  } else if (key == "TEMP") {
    temperature = val.toFloat();
  } else if (key == "HUM") {
    humidity = val.toFloat();
  } else if (key == "LON") {
    longitude = val.toFloat();
  } else if (key == "LAT") {
    latitude = val.toFloat();
  } else if (key == "ALT") {
    altitude = val.toFloat();
  } else if (key == "TIME") {
    gpsTime = formatTime(val);
  }
}

String formatTime(String isoTime) {
  if (isoTime.length() < 19) return "Invalid";
  String year = isoTime.substring(0, 4);
  String month = isoTime.substring(5, 7);
  String day = isoTime.substring(8, 10);
  String time = isoTime.substring(11); // HH:MM:SS
  return day + "-" + month + "-" + year + " " + time;
}

void printAllValues() {
  Serial.print("Dev="); Serial.print(DEVICE);
  Serial.print(",Time="); Serial.print(gpsTime);
  Serial.print(",Lon="); Serial.print(longitude, 6);
  Serial.print(",Lat="); Serial.print(latitude, 6);
  Serial.print(",Alt="); Serial.print(altitude, 2);
  Serial.print(",Temp="); Serial.print(temperature, 2);
  Serial.print(",Hum="); Serial.print(humidity, 2);
  Serial.print(",UV="); Serial.print(uvIntensity, 2);
  Serial.print(",Rain="); Serial.print(rainDetected ? 1 : 0);
  Serial.println(",end");
}