/*
  OrbitalGuard — Sensor de Vibração Orbital
  Hardware: ESP32 DevKit V1 + MPU6050 (acelerômetro/giroscópio)
  Função: Detecta padrões de vibração simulando impacto de microdetritos
          em estruturas de satélites ou estações espaciais.
  Protocolo: MQTT via HiveMQ (broker público)
  Tópico: orbitalguard/sensor/vibration01

  Dependências (Arduino IDE):
    - Adafruit MPU6050 (by Adafruit)
    - Adafruit Unified Sensor (by Adafruit)
    - ArduinoJson (by Benoit Blanchon)
    - PubSubClient (by Nick O'Leary)
    - Wire.h (nativa)

  Pinagem:
    MPU6050 SDA → GPIO 21
    MPU6050 SCL → GPIO 22
    LED Alerta  → GPIO 2 (LED embutido)
*/

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ─── Configurações WiFi e MQTT ──────────────────────────────────────────────
const char* SSID         = "SUA_REDE_WIFI";
const char* WIFI_PASS    = "SUA_SENHA_WIFI";
const char* MQTT_SERVER  = "broker.hivemq.com";
const int   MQTT_PORT    = 1883;
const char* MQTT_TOPIC   = "orbitalguard/sensor/vibration01";
const char* CLIENT_ID    = "OrbitalGuard-ESP32-001";

// ─── Thresholds de detecção ─────────────────────────────────────────────────
const float ACCEL_LIMITE_ALTO   = 3.5;   // m/s² — impacto severo
const float ACCEL_LIMITE_MEDIO  = 1.8;   // m/s² — vibração moderada
const float GYRO_LIMITE         = 0.8;   // rad/s — rotação anômala
const int   INTERVALO_MS        = 2000;  // Leitura a cada 2 segundos
const int   LED_PIN             = 2;     // LED embutido

// ─── Objetos ────────────────────────────────────────────────────────────────
Adafruit_MPU6050 mpu;
WiFiClient       espClient;
PubSubClient     mqttClient(espClient);

// ─── Variáveis de estado ─────────────────────────────────────────────────────
unsigned long ultimaLeitura  = 0;
int           contImpactos   = 0;
float         accelMaxSessao = 0.0;


// ════════════════════════════════════════════════════════════════════════════
//  Funções auxiliares
// ════════════════════════════════════════════════════════════════════════════

float calcularMagnitude(float ax, float ay, float az) {
  return sqrt(ax * ax + ay * ay + az * az);
}

String classificarImpacto(float magnitude, float gyroMag) {
  if (magnitude > ACCEL_LIMITE_ALTO || gyroMag > GYRO_LIMITE) {
    return "CRITICO";
  } else if (magnitude > ACCEL_LIMITE_MEDIO) {
    return "MODERADO";
  }
  return "NORMAL";
}

String nivelRisco(String classificacao) {
  if (classificacao == "CRITICO")  return "ALTO";
  if (classificacao == "MODERADO") return "MEDIO";
  return "BAIXO";
}

void piscarLED(int vezes, int ms) {
  for (int i = 0; i < vezes; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(ms);
    digitalWrite(LED_PIN, LOW);
    delay(ms);
  }
}

// ════════════════════════════════════════════════════════════════════════════
//  Conexões WiFi e MQTT
// ════════════════════════════════════════════════════════════════════════════

void conectarWiFi() {
  Serial.print("[WiFi] Conectando a ");
  Serial.print(SSID);
  WiFi.begin(SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("[WiFi] Conectado! IP: ");
  Serial.println(WiFi.localIP());
}

void conectarMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Conectando ao broker...");
    if (mqttClient.connect(CLIENT_ID)) {
      Serial.println(" OK");
      mqttClient.publish("orbitalguard/status", "{\"status\":\"online\",\"sensor\":\"MPU6050\"}");
    } else {
      Serial.print(" Falha, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" | Tentando novamente em 3s...");
      delay(3000);
    }
  }
}

// ════════════════════════════════════════════════════════════════════════════
//  Setup
// ════════════════════════════════════════════════════════════════════════════

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  Serial.println("========================================");
  Serial.println("  OrbitalGuard — Sensor de Vibração");
  Serial.println("  ESP32 + MPU6050 | Sistema Orbital");
  Serial.println("========================================");

  // Inicializar MPU6050
  Wire.begin();
  if (!mpu.begin()) {
    Serial.println("[ERRO] MPU6050 não encontrado. Verifique a fiação (SDA=21, SCL=22).");
    while (1) {
      piscarLED(3, 100);
      delay(1000);
    }
  }
  Serial.println("[MPU6050] Sensor inicializado com sucesso!");

  // Configurar faixas do sensor
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("[MPU6050] Range: ±8g | Gyro: ±500°/s | Filtro: 21Hz");

  conectarWiFi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  conectarMQTT();

  piscarLED(3, 200);
  Serial.println("[OK] Sistema pronto. Monitorando detritos orbitais...\n");
}

// ════════════════════════════════════════════════════════════════════════════
//  Loop principal
// ════════════════════════════════════════════════════════════════════════════

void loop() {
  if (!mqttClient.connected()) conectarMQTT();
  mqttClient.loop();

  unsigned long agora = millis();
  if (agora - ultimaLeitura < INTERVALO_MS) return;
  ultimaLeitura = agora;

  // ── Leitura do MPU6050 ─────────────────────────────────────────────────
  sensors_event_t accel, gyro, temp;
  mpu.getEvent(&accel, &gyro, &temp);

  float ax = accel.acceleration.x;
  float ay = accel.acceleration.y;
  float az = accel.acceleration.z;
  float gx = gyro.gyro.x;
  float gy = gyro.gyro.y;
  float gz = gyro.gyro.z;

  float accelMag = calcularMagnitude(ax, ay, az);
  float gyroMag  = calcularMagnitude(gx, gy, gz);
  float tempC    = temp.temperature;

  String classificacao = classificarImpacto(accelMag, gyroMag);
  String risco         = nivelRisco(classificacao);

  if (classificacao != "NORMAL") contImpactos++;
  if (accelMag > accelMaxSessao) accelMaxSessao = accelMag;

  // ── Feedback visual ────────────────────────────────────────────────────
  if (classificacao == "CRITICO")       piscarLED(5, 80);
  else if (classificacao == "MODERADO") piscarLED(2, 150);
  else                                  digitalWrite(LED_PIN, LOW);

  // ── Log serial ─────────────────────────────────────────────────────────
  Serial.printf("[LEITURA] Accel: %.2f m/s² | Gyro: %.2f rad/s | Temp: %.1f°C | %s | Risco: %s\n",
                accelMag, gyroMag, tempC, classificacao.c_str(), risco.c_str());

  // ── Payload MQTT ───────────────────────────────────────────────────────
  StaticJsonDocument<384> doc;
  doc["sensor_id"]          = CLIENT_ID;
  doc["timestamp_ms"]       = agora;
  doc["accel_x_ms2"]        = round(ax * 100) / 100.0;
  doc["accel_y_ms2"]        = round(ay * 100) / 100.0;
  doc["accel_z_ms2"]        = round(az * 100) / 100.0;
  doc["accel_magnitude"]    = round(accelMag * 1000) / 1000.0;
  doc["gyro_magnitude"]     = round(gyroMag * 1000) / 1000.0;
  doc["temperatura_c"]      = round(tempC * 10) / 10.0;
  doc["classificacao"]      = classificacao;
  doc["nivel_risco"]        = risco;
  doc["impactos_sessao"]    = contImpactos;
  doc["accel_max_sessao"]   = round(accelMaxSessao * 1000) / 1000.0;
  doc["uptime_s"]           = agora / 1000;

  char payload[512];
  serializeJson(doc, payload);
  mqttClient.publish(MQTT_TOPIC, payload);

  Serial.printf("[MQTT] Publicado em %s\n", MQTT_TOPIC);
}
