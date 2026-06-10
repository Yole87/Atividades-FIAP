/*
 * AgroSat — Nó de Sensor de Campo
 * Hardware: ESP32 DevKit V1
 * Sensores: DHT22 (temperatura/umidade), BMP280 (pressão), UV VEML6070
 *
 * Função: coleta dados ambientais em campo e envia via MQTT para a nuvem.
 * Esses dados complementam as leituras de satélite (NASA POWER) com
 * medições locais em tempo real, aumentando a precisão do modelo de ML.
 *
 * Bibliotecas necessárias (Arduino IDE / PlatformIO):
 *   - DHT sensor library (Adafruit)
 *   - Adafruit BMP280
 *   - PubSubClient (MQTT)
 *   - ArduinoJson
 *   - WiFi (built-in ESP32)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>

// ─────────────────────────────────────────────
// CONFIGURAÇÕES — ajuste para seu ambiente
// ─────────────────────────────────────────────

// WiFi
const char* WIFI_SSID     = "SEU_WIFI";
const char* WIFI_PASSWORD = "SUA_SENHA";

// Broker MQTT (pode usar HiveMQ público ou AWS IoT Core)
const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "agrosat/sensor/campo01";
const char* CLIENT_ID     = "agrosat-esp32-campo01";

// Pinos
#define DHT_PIN       4
#define DHT_TYPE      DHT22
#define LED_STATUS    2   // LED built-in do ESP32

// Intervalo de envio (ms)
#define INTERVALO_MS  30000   // 30 segundos

// ─────────────────────────────────────────────
// INICIALIZAÇÃO
// ─────────────────────────────────────────────

DHT           dht(DHT_PIN, DHT_TYPE);
Adafruit_BMP280 bmp;
WiFiClient    wifiClient;
PubSubClient  mqttClient(wifiClient);

unsigned long ultimoEnvio = 0;
int           leituraSeq  = 0;

// ─────────────────────────────────────────────
// FUNÇÕES AUXILIARES
// ─────────────────────────────────────────────

void conectarWiFi() {
    Serial.print("[WiFi] Conectando a ");
    Serial.print(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int tentativas = 0;
    while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
        delay(500);
        Serial.print(".");
        tentativas++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WiFi] Conectado!");
        Serial.print("[WiFi] IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n[WiFi] Falha na conexão. Reiniciando...");
        ESP.restart();
    }
}

void conectarMQTT() {
    while (!mqttClient.connected()) {
        Serial.print("[MQTT] Conectando ao broker...");
        if (mqttClient.connect(CLIENT_ID)) {
            Serial.println(" conectado!");
            // Publica mensagem de presença
            mqttClient.publish("agrosat/status", "{\"status\":\"online\",\"device\":\"campo01\"}");
        } else {
            Serial.print(" falhou. Código: ");
            Serial.print(mqttClient.state());
            Serial.println(" — tentando novamente em 5s");
            delay(5000);
        }
    }
}

float lerUV() {
    /*
     * Simulação do sensor UV VEML6070.
     * Em produção: use Wire.requestFrom(VEML6070_ADDR, 1) via I2C.
     * Retorna índice UV (0-11+)
     */
    return random(0, 8) / 10.0 + 2.0;
}

// ─────────────────────────────────────────────
// COLETA E ENVIO DE DADOS
// ─────────────────────────────────────────────

void coletarEEnviar() {
    // Lê sensores
    float temperatura = dht.readTemperature();
    float umidade     = dht.readHumidity();
    float pressao     = bmp.readPressure() / 100.0F;  // hPa
    float altitude    = bmp.readAltitude(1013.25);     // metros
    float uv          = lerUV();
    int   rssi        = WiFi.RSSI();

    // Valida leituras do DHT22
    if (isnan(temperatura) || isnan(umidade)) {
        Serial.println("[SENSOR] Erro na leitura DHT22. Pulando envio.");
        return;
    }

    // Monta JSON
    StaticJsonDocument<256> doc;
    doc["device"]       = CLIENT_ID;
    doc["seq"]          = ++leituraSeq;
    doc["timestamp"]    = millis();
    doc["temperatura"]  = round(temperatura * 10) / 10.0;
    doc["umidade"]      = round(umidade * 10) / 10.0;
    doc["pressao_hpa"]  = round(pressao * 10) / 10.0;
    doc["altitude_m"]   = round(altitude);
    doc["indice_uv"]    = uv;
    doc["rssi_dbm"]     = rssi;

    // Calcula índice de stress hídrico (simplificado)
    // Baseado em relação temperatura × umidade
    float vpd = (1 - umidade / 100.0) * 0.6108 * exp(17.27 * temperatura / (temperatura + 237.3));
    doc["vpd_kpa"]      = round(vpd * 100) / 100.0;   // Déficit de pressão de vapor
    doc["stress_hidrico"] = vpd > 2.0 ? "alto" : vpd > 1.0 ? "moderado" : "baixo";

    char payload[256];
    serializeJson(doc, payload);

    // Publica
    if (mqttClient.publish(MQTT_TOPIC, payload)) {
        Serial.print("[MQTT] Publicado #");
        Serial.print(leituraSeq);
        Serial.print(" — Temp: ");
        Serial.print(temperatura, 1);
        Serial.print("°C | Umid: ");
        Serial.print(umidade, 1);
        Serial.print("% | UV: ");
        Serial.print(uv, 1);
        Serial.print(" | VPD: ");
        Serial.print(vpd, 2);
        Serial.println(" kPa");
        digitalWrite(LED_STATUS, HIGH);
        delay(100);
        digitalWrite(LED_STATUS, LOW);
    } else {
        Serial.println("[MQTT] Falha ao publicar.");
    }
}

// ─────────────────────────────────────────────
// SETUP & LOOP
// ─────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    pinMode(LED_STATUS, OUTPUT);

    Serial.println("\n============================");
    Serial.println("  AgroSat — Sensor de Campo");
    Serial.println("============================\n");

    // Inicializa DHT22
    dht.begin();
    Serial.println("[SENSOR] DHT22 inicializado.");

    // Inicializa BMP280
    if (!bmp.begin(0x76)) {
        Serial.println("[SENSOR] BMP280 não encontrado! Verificar endereço I2C.");
    } else {
        bmp.setSampling(
            Adafruit_BMP280::MODE_NORMAL,
            Adafruit_BMP280::SAMPLING_X2,
            Adafruit_BMP280::SAMPLING_X16,
            Adafruit_BMP280::FILTER_X16,
            Adafruit_BMP280::STANDBY_MS_500
        );
        Serial.println("[SENSOR] BMP280 inicializado.");
    }

    // Conecta WiFi e MQTT
    conectarWiFi();
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

    Serial.println("\n[OK] Sistema pronto. Enviando a cada 30 segundos.\n");
}

void loop() {
    // Mantém conexão MQTT
    if (!mqttClient.connected()) {
        conectarMQTT();
    }
    mqttClient.loop();

    // Coleta e envia dados no intervalo definido
    unsigned long agora = millis();
    if (agora - ultimoEnvio >= INTERVALO_MS) {
        ultimoEnvio = agora;
        coletarEEnviar();
    }
}

/*
 * ──────────────────────────────────────────────
 * DIAGRAMA DE CONEXÃO
 * ──────────────────────────────────────────────
 *
 *  ESP32          DHT22          BMP280 (I2C)
 *  ─────          ─────          ────────────
 *  GPIO 4    ──→  DATA
 *  3.3V      ──→  VCC            VCC
 *  GND       ──→  GND            GND
 *  GPIO 21   ────────────────→   SDA
 *  GPIO 22   ────────────────→   SCL
 *
 *  Tópico MQTT: agrosat/sensor/campo01
 *  Payload exemplo:
 *  {
 *    "device": "agrosat-esp32-campo01",
 *    "seq": 42,
 *    "temperatura": 28.5,
 *    "umidade": 65.2,
 *    "pressao_hpa": 1012.3,
 *    "altitude_m": 420,
 *    "indice_uv": 3.2,
 *    "vpd_kpa": 1.23,
 *    "stress_hidrico": "moderado"
 *  }
 * ──────────────────────────────────────────────
 */
