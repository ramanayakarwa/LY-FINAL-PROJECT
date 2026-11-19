/*
  ARES ESP32: real sensor telemetry to FastAPI via MQTT/TLS and signed LAN CoAP (plaintext).
  Adapted from the project's sensor/GPS/IBT-2 sketch.

  SAFETY: Physical navigation is deliberately disabled during first network
  commissioning. Do NOT re-enable without hardware emergency-stop, safe
  power distribution, and independent obstacle-fail-safe verification.

  ESP32 classic DevKit pins:
    DHT22 GPIO4; soil ADC1 GPIO34; HC-SR04 TRIG27/ECHO26 (divider!);
    GPS TX->GPIO16; IBT-2 PWM: left 25/33, right 18/19.

  Libraries: DHT sensor library, TinyGPSPlus, PubSubClient, ESP32 Arduino core.
*/
#include <Arduino.h>
#include <DHT.h>
#include <TinyGPSPlus.h>
#include <math.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include <time.h>
#include <mbedtls/md.h>

// === WIFI + MQTT ===
const char *WIFI_SSID = "YOUR_2_4_GHZ_WIFI_NAME";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char *MQTT_HOST = "YOUR_TLS_MQTT_BROKER_HOSTNAME";
constexpr uint16_t MQTT_PORT = 8883;
const char *MQTT_USERNAME = "YOUR_ESP32_MQTT_USERNAME";
const char *MQTT_PASSWORD = "YOUR_ESP32_MQTT_PASSWORD";
const char *DEVICE_ID = "ARES_ROVER_01";
const char *DEVICE_HMAC_SECRET = "PASTE_LONG_RANDOM_SECRET_SAME_AS_BACKEND";
const char *MQTT_TOPIC = "ares/rover/telemetry";

// Laptop LAN IP from `ipconfig`, NOT 127.0.0.1. Same Wi-Fi network.
const char *COAP_SERVER_IP = "192.168.1.100"; // CHANGE ME
constexpr uint16_t COAP_SERVER_PORT = 5683;

// Obtain the CA used to verify your actual broker's certificate.
// This MUST be replaced; do not use setInsecure().
const char MQTT_ROOT_CA[] PROGMEM = R"PEM(
-----BEGIN CERTIFICATE-----
PASTE_ACTUAL_TRUSTED_CA_CERTIFICATE_HERE
-----END CERTIFICATE-----
)PEM";

// === PIN MAP (unchanged from user's sketch) ===
constexpr int DHT_PIN = 4;
constexpr int SOIL_PIN = 34;
constexpr int TRIG_PIN = 27;
constexpr int ECHO_PIN = 26;       // 5V HC-SR04 ECHO -> level shifter/divider
constexpr int GPS_RX = 16;         // GPS TX -> ESP32 GPIO16
constexpr int LEFT_RPWM = 25;
constexpr int LEFT_LPWM = 33;
constexpr int RIGHT_RPWM = 18;
constexpr int RIGHT_LPWM = 19;
constexpr bool LEFT_REVERSED = false;
constexpr bool RIGHT_REVERSED = false;

// Set false during network commissioning to prevent accidental rover motion.
constexpr bool ENABLE_WAYPOINT_MOTION = false;

// Navigation placeholders retained from original sketch.
const double TARGET_LAT = NAN;
const double TARGET_LON = NAN;

constexpr int SOIL_DRY_RAW = 3000; // Calibrate against actual dry sample
constexpr int SOIL_WET_RAW = 1450; // Calibrate against actual wet sample
constexpr float STOP_DISTANCE_CM = 50.0f;
constexpr double ARRIVAL_RADIUS_M = 5.0;
constexpr double MIN_SPEED_MPS = 0.6;
constexpr int DRIVE_PWM = 115;
constexpr int TURN_PWM = 65;
constexpr unsigned long REPORT_MS = 2000;
constexpr unsigned long PING_MS = 80;
constexpr unsigned long MAX_FIX_AGE_MS = 1800;
constexpr unsigned long START_WINDOW_MS = 3500;
constexpr unsigned long MQTT_REPORT_MS = 5000;

DHT dht(DHT_PIN, DHT22);
TinyGPSPlus gps;
HardwareSerial gpsPort(2);
WiFiClientSecure tlsClient;
PubSubClient mqtt(tlsClient);
WiFiUDP coapUdp;

bool driving = false;
bool acquiringCourse = false;
bool frontClear = false;
bool receivedGpsData = false;
float distanceCm = NAN;
unsigned long lastGpsByteAt = 0;
unsigned long lastPingAt = 0;
unsigned long lastReportAt = 0;
unsigned long driveStartedAt = 0;
unsigned long lastWiFiAttemptAt = 0;
unsigned long lastMQTTAttemptAt = 0;
unsigned long lastPublishAt = 0;
uint32_t lastSequence = 0;
uint16_t lastCoapMid = 0;
bool coapUdpReady = false;

// === Motors: original functions, held at zero during network commissioning ===
void setMotor(int rpwm, int lpwm, bool reversed, int speed) {
  int forwardPin = reversed ? lpwm : rpwm;
  int otherPin = reversed ? rpwm : lpwm;
  analogWrite(otherPin, 0);
  analogWrite(forwardPin, speed);
}
void driveMotors(int leftSpeed, int rightSpeed) {
  setMotor(LEFT_RPWM, LEFT_LPWM, LEFT_REVERSED, leftSpeed);
  setMotor(RIGHT_RPWM, RIGHT_LPWM, RIGHT_REVERSED, rightSpeed);
}
void stopRover(const char *message) {
  driveMotors(0, 0);
  driving = false;
  acquiringCourse = false;
  Serial.println(message);
}

// === GPS: original logic ===
void readGps() {
  while (gpsPort.available() > 0) {
    gps.encode(gpsPort.read());
    receivedGpsData = true;
    lastGpsByteAt = millis();
  }
}
bool targetReady() {
  return isfinite(TARGET_LAT) && isfinite(TARGET_LON) &&
         fabs(TARGET_LAT) <= 90.0 && fabs(TARGET_LON) <= 180.0;
}
bool fixReady() {
  return gps.location.isValid() &&
         gps.location.age() < MAX_FIX_AGE_MS &&
         gps.satellites.isValid() &&
         gps.satellites.age() < 3000 &&
         gps.satellites.value() >= 4 &&
         gps.hdop.isValid() &&
         gps.hdop.age() < 3000 &&
         gps.hdop.hdop() > 0.0 &&
         gps.hdop.hdop() <= 3.0;
}

// === Ultrasonic: fail closed on missing echo ===
void checkFront() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long echoTime = pulseIn(ECHO_PIN, HIGH, 25000UL);
  if (echoTime == 0) {
    distanceCm = NAN;
    frontClear = false;
    if (driving) stopRover("STOP: no ultrasonic echo.");
    return;
  }
  distanceCm = echoTime * 0.0343f / 2.0f;
  frontClear = distanceCm > STOP_DISTANCE_CM;
  if (driving && !frontClear) stopRover("STOP: obstacle ahead.");
}

// === Serial monitor: original sensor readings ===
void printMeasurements() {
  Serial.println("\n========== ROVER SENSOR DATA ==========");
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  if (isnan(temperature)) Serial.println("Temperature: DHT22 read failed");
  else Serial.printf("Temperature: %.1f C | %s\n", temperature,
                     temperature > 35.0f ? "HIGH" : "NORMAL");
  if (isnan(humidity)) Serial.println("Humidity: DHT22 read failed");
  else {
    const char *status = "NORMAL";
    if (humidity < 50.0f) status = "LOW";
    if (humidity > 85.0f) status = "HIGH";
    Serial.printf("Humidity: %.1f %% | %s\n", humidity, status);
  }
  int soilRaw = analogRead(SOIL_PIN);
  long soilPercent = map(soilRaw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100);
  soilPercent = constrain(soilPercent, 0L, 100L);
  const char *soilStatus = "NORMAL";
  if (soilPercent < 35) soilStatus = "DRY";
  if (soilPercent > 70) soilStatus = "WET";
  Serial.printf("Soil moisture: %ld %% | Raw: %d | %s\n",
                soilPercent, soilRaw, soilStatus);
  if (isnan(distanceCm)) Serial.println("Ultrasonic distance: No echo");
  else Serial.printf("Ultrasonic distance: %.1f cm | %s\n",
                     distanceCm, frontClear ? "CLEAR" : "OBSTACLE");
  if (fixReady()) {
    Serial.printf("GPS: %.6f, %.6f | Satellites: %lu\n",
                  gps.location.lat(), gps.location.lng(),
                  (unsigned long)gps.satellites.value());
    if (targetReady()) {
      double remaining = TinyGPSPlus::distanceBetween(
        gps.location.lat(), gps.location.lng(), TARGET_LAT, TARGET_LON);
      Serial.printf("Distance to destination: %.1f m\n", remaining);
    }
  } else if (!receivedGpsData) Serial.println("GPS: No data received on GPIO 16 yet");
  else if (millis() - lastGpsByteAt > 3000) Serial.println("GPS: Data stream stopped");
  else if (gps.passedChecksum() == 0) Serial.println("GPS: Waiting for valid messages");
  else Serial.println("GPS: Waiting for reliable fix");
  Serial.printf("Rover: %s\n", driving ? "DRIVING" : "STOPPED");
  Serial.println("=======================================");
}

// === Navigation preserved but cannot be armed in commissioning build ===
void handleCommand(char command) {
  if (command == 'X' || command == 'x') {
    stopRover("Stopped by user.");
    return;
  }
  if ((command != 'G' && command != 'g') || driving) return;
  if (!ENABLE_WAYPOINT_MOTION) {
    Serial.println("Motor navigation DISABLED during live telemetry commissioning.");
    return;
  }
  if (!targetReady()) {
    Serial.println("Sensor mode: set TARGET_LAT and TARGET_LON to drive.");
    return;
  }
  if (!fixReady()) {
    Serial.println("Cannot start: waiting for a reliable GPS fix.");
    return;
  }
  checkFront();
  if (!frontClear) {
    Serial.println("Cannot start: obstacle ahead or no ultrasonic echo.");
    return;
  }
  driving = true;
  acquiringCourse = true;
  driveStartedAt = millis();
  Serial.println("Navigation started.");
}
void navigate() {
  if (!fixReady()) {
    stopRover("STOP: GPS fix lost.");
    return;
  }
  double lat = gps.location.lat();
  double lon = gps.location.lng();
  double remaining = TinyGPSPlus::distanceBetween(lat, lon, TARGET_LAT, TARGET_LON);
  if (remaining <= ARRIVAL_RADIUS_M) {
    stopRover("STOP: reached waypoint area.");
    return;
  }
  unsigned long elapsed = millis() - driveStartedAt;
  bool courseReady = gps.course.isValid() &&
                     gps.course.age() < MAX_FIX_AGE_MS &&
                     gps.speed.isValid() &&
                     gps.speed.age() < MAX_FIX_AGE_MS &&
                     gps.speed.mps() >= MIN_SPEED_MPS;
  if (acquiringCourse) {
    if (courseReady && gps.course.age() < elapsed) acquiringCourse = false;
    else if (elapsed >= START_WINDOW_MS) {
      stopRover("STOP: could not establish direction of travel.");
      return;
    } else {
      driveMotors(DRIVE_PWM, DRIVE_PWM);
      return;
    }
  }
  if (!courseReady) {
    stopRover("STOP: GPS direction unreliable.");
    return;
  }
  double bearing = TinyGPSPlus::courseTo(lat, lon, TARGET_LAT, TARGET_LON);
  double turn = fmod(bearing - gps.course.deg() + 540.0, 360.0) - 180.0;
  if (turn > 15.0) driveMotors(DRIVE_PWM, TURN_PWM);
  else if (turn < -15.0) driveMotors(TURN_PWM, DRIVE_PWM);
  else driveMotors(DRIVE_PWM, DRIVE_PWM);
}

// === NEW: HMAC SHA256 of the exact canonical JSON expected by FastAPI ===
String hmacHex(const String &canonical) {
  unsigned char digest[32];
  const mbedtls_md_info_t *md = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  if (md == nullptr) return "";
  int err = mbedtls_md_hmac(
    md,
    (const unsigned char*)DEVICE_HMAC_SECRET,
    strlen(DEVICE_HMAC_SECRET),
    (const unsigned char*)canonical.c_str(),
    canonical.length(),
    digest
  );
  if (err != 0) return "";
  const char *hexDigits = "0123456789abcdef";
  char result[65];
  for (int i = 0; i < 32; ++i) {
    result[2*i] = hexDigits[digest[i] >> 4];
    result[2*i+1] = hexDigits[digest[i] & 0x0F];
  }
  result[64] = 0;
  return String(result);
}

// Python canonical JSON sorts keys and uses compact separators. Floats in the
// backend are encoded as x.0 or x.y; preserve that with String(..., 1).
void appendFloat(String &json, bool &first, const char *key, float value) {
  if (!isfinite(value)) return;
  if (!first) json += ',';
  first = false;
  json += '"'; json += key; json += "\":"; json += String(value, 1);
}
void appendBool(String &json, bool &first, const char *key, bool value) {
  if (!first) json += ',';
  first = false;
  json += '"'; json += key; json += "\":"; json += value ? "true" : "false";
}

// A tiny RFC7252 CoAP CON POST /telemetry encoder (content format 50: JSON).
// CoAP is LAN-only and is NOT encrypted. The message is HMAC-signed.
void sendCoapPacket(const String &json) {
  if (!coapUdpReady) return;
  IPAddress destination;
  if (!destination.fromString(COAP_SERVER_IP)) {
    Serial.println("CoAP: invalid laptop LAN IP");
    return;
  }
  const size_t dataLength = json.length();
  if (dataLength > 1100) {
    Serial.println("CoAP: JSON too large");
    return;
  }
  uint8_t packet[1200];
  uint16_t mid = ++lastCoapMid;
  size_t i = 0;
  packet[i++] = 0x42; // CoAP v1, CON, token length 2
  packet[i++] = 0x02; // POST
  packet[i++] = (uint8_t)(mid >> 8);
  packet[i++] = (uint8_t)(mid & 0xff);
  packet[i++] = (uint8_t)(mid >> 8); // Token echoes message ID
  packet[i++] = (uint8_t)(mid & 0xff);
  packet[i++] = 0xB9; // Uri-Path (#11), 9-byte string
  const char *path = "telemetry";
  for (int j = 0; j < 9; ++j) packet[i++] = path[j];
  packet[i++] = 0x11; // Content-Format (#12), 1-byte value
  packet[i++] = 50;   // application/json
  packet[i++] = 0xFF; // Payload marker
  memcpy(packet + i, json.c_str(), dataLength);
  i += dataLength;

  if (!coapUdp.beginPacket(destination, COAP_SERVER_PORT)) {
    Serial.println("CoAP: beginPacket failed");
    return;
  }
  coapUdp.write(packet, i);
  bool sent = coapUdp.endPacket() == 1;
  Serial.printf("CoAP: %s (LAN UDP, message=%u)\n",
                sent ? "sent" : "send failed", mid);
}

// Print the server response, if it arrives. Server's API status is authoritative.
void checkCoapReply() {
  if (!coapUdpReady) return;
  int packetSize = coapUdp.parsePacket();
  if (packetSize <= 0) return;
  uint8_t response[128];
  int n = coapUdp.read(response, sizeof(response));
  if (n >= 6 && (response[0] >> 6) == 1) {
    int codeClass = response[1] >> 5;
    int codeDetail = response[1] & 31;
    Serial.printf("CoAP: response %d.%02d (confirm backend /system/status)\n",
                  codeClass, codeDetail);
  }
}

String buildSignedPayload(const String &data, uint32_t seq, uint32_t now) {
  // HMAC canonical order: data, device_id, issued_at, sequence.
  // All float fields use one decimal, GPS coordinates use integer microdegrees.
  String canonical = String("{\"data\":") + data +
    ",\"device_id\":\"" + String(DEVICE_ID) + "\"" +
    ",\"issued_at\":" + String(now) + ".0" +
    ",\"sequence\":" + String(seq) + "}";
  String signature = hmacHex(canonical);
  if (signature.length() != 64) return "";
  return canonical.substring(0, canonical.length() - 1) +
    ",\"signature\":\"" + signature + "\"}";
}

void publishSensorTelemetry() {
  time_t current = time(nullptr);
  if (current < 1700000000) {
    Serial.println("Network: waiting for NTP time");
    return;
  }
  const uint32_t now = (uint32_t)current;
  // Distinct sequences for MQTT and CoAP to prevent cross-protocol replay.
  // With 32-bit sequence this time-based demonstration format lasts until 2038.
  if (now > 2147483640UL || now <= lastSequence) return;

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int soilRaw = analogRead(SOIL_PIN);
  long soilPercent = map(soilRaw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100);
  soilPercent = constrain(soilPercent, 0L, 100L);

  // IMPORTANT: Sensor keys in alphabetical order for Python HMAC canonical JSON.
  String data = "{";
  bool first = true;
  if (isfinite(distanceCm) && distanceCm >= 0)
    appendFloat(data, first, "distance_cm", distanceCm);
  if (fixReady()) {
    long latE6 = lround(gps.location.lat() * 1000000.0);
    long lonE6 = lround(gps.location.lng() * 1000000.0);
    if (!first) data += ',';
    first = false;
    data += "\"gps_lat_e6\":" + String(latE6);
    data += ",\"gps_lon_e6\":" + String(lonE6);
    data += ",\"gps_satellites\":" + String(gps.satellites.value());
  }
  if (isfinite(humidity) && humidity >= 0 && humidity <= 100)
    appendFloat(data, first, "humidity", humidity);
  appendBool(data, first, "obstacle_stop", !frontClear);
  appendFloat(data, first, "soil_moisture", (float)soilPercent);
  if (isfinite(temperature) && temperature >= -20 && temperature <= 70)
    appendFloat(data, first, "temperature", temperature);
  data += "}";

  String mqttPayload = buildSignedPayload(data, now * 2, now);
  String coapPayload = buildSignedPayload(data, now * 2 + 1, now);
  if (mqttPayload.length() == 0 || coapPayload.length() == 0) {
    Serial.println("HMAC signing failed");
    return;
  }
  lastSequence = now;

  // CoAP works independently, even when the MQTT broker is temporarily down.
  sendCoapPacket(coapPayload);

  if (mqtt.connected()) {
    bool sent = mqtt.publish(MQTT_TOPIC, mqttPayload.c_str());
    Serial.printf("MQTT: %s | soil=%ld%% | DHT=%s\n",
                  sent ? "published" : "failed", soilPercent,
                  isfinite(temperature) ? String(temperature, 1).c_str() : "missing");
  } else {
    Serial.println("MQTT: disconnected; CoAP still attempted");
  }
}

void setupNetworkTelemetry() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWiFiAttemptAt = millis();
  configTime(0, 0, "pool.ntp.org", "time.google.com");
  tlsClient.setCACert(MQTT_ROOT_CA);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setKeepAlive(30);
  mqtt.setBufferSize(2048);
  Serial.println("Network telemetry initialized (device must use valid broker certificate).");
}

void networkTelemetryTick() {
  // Network operations may block on reconnection. Movement is disabled in
  // this firmware; do not enable it for physical driving without redesign.
  if (driving) return;
  unsigned long ms = millis();
  if (WiFi.status() != WL_CONNECTED) {
    if (ms - lastWiFiAttemptAt >= 10000) {
      lastWiFiAttemptAt = ms;
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }
    return;
  }
  if (!coapUdpReady) {
    coapUdpReady = (coapUdp.begin(49152) == 1);
    Serial.println(coapUdpReady ? "CoAP UDP ready" : "CoAP UDP failed");
  }
  checkCoapReply();
  if (time(nullptr) < 1700000000) return;
  if (!mqtt.connected() && ms - lastMQTTAttemptAt >= 5000) {
    lastMQTTAttemptAt = ms;
    bool ok = mqtt.connect(DEVICE_ID, MQTT_USERNAME, MQTT_PASSWORD);
    Serial.printf("MQTT TLS: %s\n", ok ? "connected" : "not connected");
  }
  if (mqtt.connected()) mqtt.loop();
  if (ms - lastPublishAt >= MQTT_REPORT_MS) {
    lastPublishAt = ms;
    publishSensorTelemetry();
  }
}

// === Setup and loop ===
void setup() {
  Serial.begin(115200);
  pinMode(LEFT_RPWM, OUTPUT); pinMode(LEFT_LPWM, OUTPUT);
  pinMode(RIGHT_RPWM, OUTPUT); pinMode(RIGHT_LPWM, OUTPUT);
  driveMotors(0, 0);
  pinMode(TRIG_PIN, OUTPUT); digitalWrite(TRIG_PIN, LOW);
  pinMode(ECHO_PIN, INPUT);
  dht.begin();
  analogReadResolution(12);
  analogSetPinAttenuation(SOIL_PIN, ADC_11db);
  gpsPort.begin(9600, SERIAL_8N1, GPS_RX, -1);
  setupNetworkTelemetry();
  Serial.println("ARES ready: real sensors + MQTT telemetry; MOTOR NAVIGATION DISABLED.");
}

void loop() {
  readGps();
  if (millis() - lastPingAt >= PING_MS) {
    lastPingAt = millis();
    checkFront();
  }
  while (Serial.available() > 0) handleCommand(Serial.read());
  if (driving) navigate();
  if (millis() - lastReportAt >= REPORT_MS) {
    lastReportAt = millis();
    printMeasurements();
  }
  networkTelemetryTick();
}
