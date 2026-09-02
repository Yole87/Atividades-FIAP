/*
 * AquaWatch — Firmware ESP32 — Sensor de Qualidade da Água
 * =========================================================
 * Hardware:
 *   - ESP32 DevKit V1
 *   - Sensor TDS (Total Dissolved Solids) — SEN0189 / Gravity TDS
 *     → GPIO 34 (ADC1_CH6) — entrada analógica
 *   - Sensor de Turbidez — SEN0189 analógico
 *     → GPIO 35 (ADC1_CH7) — entrada analógica
 *   - Sensor de Temperatura — DS18B20 (OneWire)
 *     → GPIO 4 — OneWire data
 *   - LED indicador de alerta
 *     → GPIO 2 (LED embutido)
 *   - WiFi integrado → MQTT via HiveMQ público
 *
 * Por que diferente do OrbitalGuard?
 *   OrbitalGuard: MPU6050 (acelerômetro/giroscópio) → detecção de vibração orbital
 *   AquaWatch:    TDS + Turbidez + DS18B20 → sensores de QUALIDADE DA ÁGUA
 *
 * Protocolo MQTT:
 *   Broker:  broker.hivemq.com (público, porta 1883)
 *   Tópico:  aquawatch/sensor/{SENSOR_ID}
 *   Payload: JSON com todas as leituras + classificação local
 *
 * Classificação local no ESP32 (sem cloud):
 *   O firmware calcula um score de qualidade local baseado em limites de referência
 *   da CONAMA 357/2005 (Classe II — rios para abastecimento humano com tratamento).
 *
 * Pinagem:
 *   ┌──────────────┬──────────┬───────────────────────────┐
 *   │ Componente   │ GPIO     │ Protocolo                 │
 *   ├──────────────┼──────────┼───────────────────────────┤
 *   │ TDS Sensor   │ GPIO 34  │ ADC Analógico             │
 *   │ Turbidez     │ GPIO 35  │ ADC Analógico             │
 *   │ DS18B20      │ GPIO 4   │ OneWire + DallasTemp      │
 *   │ LED Alerta   │ GPIO 2   │ Digital Output            │
 *   │ WiFi         │ Embutido │ TCP/IP → MQTT             │
 *   └──────────────┴──────────┴───────────────────────────┘
 *
 * Bibliotecas necessárias (Arduino IDE / PlatformIO):
 *   - PubSubClient    (MQTT)
 *   - OneWire         (DS18B20)
 *   - DallasTemperature (DS18B20)
 *   - ArduinoJson     (payload JSON)
 *
 * Instalar via Arduino IDE → Gerenciar Bibliotecas:
 *   PubSubClient by Nick O'Leary
 *   DallasTemperature by Miles Burton
 *   OneWire by Paul Stoffregen
 *   ArduinoJson by Benoit Blanchon
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>

// ─── Configuração WiFi ────────────────────────────────────────────────────────
const char* WIFI_SSID     = "SUA_REDE_WIFI";
const char* WIFI_PASSWORD = "SUA_SENHA_WIFI";

// ─── Configuração MQTT ────────────────────────────────────────────────────────
const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "aquawatch/sensor/ESP32-001";
const char* CLIENT_ID     = "AquaWatch-ESP32-001";

// ─── Pinos ────────────────────────────────────────────────────────────────────
const int PIN_TDS       = 34;   // ADC1 — sensor TDS (analógico 0-3.3V)
const int PIN_TURBIDEZ  = 35;   // ADC1 — sensor turbidez (analógico)
const int PIN_DS18B20   = 4;    // OneWire — temperatura da água
const int PIN_LED_ALERTA = 2;   // LED embutido

// ─── Constantes de calibração ─────────────────────────────────────────────────
// Calibração TDS: fator empírico para conversão ADC → TDS (mg/L)
// Ref: DFRobot SEN0189 datasheet
const float TDS_K_VALUE     = 1.6;       // fator de calibração
const float VREF            = 3.3;       // tensão de referência ADC
const int   ADC_RESOLUTION  = 4096;      // 12-bit ADC do ESP32

// Limites de qualidade — CONAMA 357/2005 Classe II
const float LIMITE_TDS_ALERTA    = 500.0;   // mg/L
const float LIMITE_TDS_CRITICO   = 1000.0;
const float LIMITE_TURB_ALERTA   = 40.0;    // NTU
const float LIMITE_TURB_CRITICO  = 100.0;
const float LIMITE_TEMP_ALERTA   = 30.0;    // °C
const float LIMITE_TEMP_CRITICO  = 35.0;

// ─── Intervalo de leitura ─────────────────────────────────────────────────────
const unsigned long INTERVALO_MS = 5000;    // 5 segundos (IoT stream em tempo real)

// ─── Objetos ──────────────────────────────────────────────────────────────────
WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);
OneWire      oneWire(PIN_DS18B20);
DallasTemperature ds18b20(&oneWire);

unsigned long lastSend    = 0;
int           impactos    = 0;        // contador de leituras críticas na sessão
String        sensor_id   = "AquaWatch-ESP32-001";

// ─── Funções auxiliares ───────────────────────────────────────────────────────

/**
 * Lê tensão média do ADC (oversampling 16x para reduzir ruído).
 */
float lerADC_V(int pino) {
    long soma = 0;
    for (int i = 0; i < 16; i++) {
        soma += analogRead(pino);
        delayMicroseconds(100);
    }
    float media = soma / 16.0;
    return media * VREF / ADC_RESOLUTION;
}

/**
 * Converte tensão ADC para TDS (mg/L).
 * Fórmula: DFRobot SEN0189 + correção de temperatura.
 * Ref: https://www.dfrobot.com/wiki/index.php/Gravity:_TDS_Meter_V1.0_SKU:_SEN0244
 */
float calcularTDS(float tensao_V, float temperatura_C) {
    float comp = 1.0 + 0.02 * (temperatura_C - 25.0);   // coef. temperatura
    float tensaoComp = tensao_V / comp;
    // Equação polinomial do datasheet
    float tds = (133.42 * pow(tensaoComp, 3)
               - 255.86 * pow(tensaoComp, 2)
               + 857.39 * tensaoComp) * TDS_K_VALUE;
    return max(tds, 0.0f);
}

/**
 * Converte tensão ADC do sensor de turbidez para NTU.
 * Sensor analógico: tensão alta = água limpa, tensão baixa = turva.
 * Fórmula inversa calibrada empiricamente.
 */
float calcularTurbidez(float tensao_V) {
    // Relação inversa: 4.5V = 0 NTU (água limpa), 0.5V = 3000 NTU (muito turva)
    if (tensao_V >= 4.2) return 0.0;
    float ntu = -1120.4 * pow(tensao_V, 2) + 5742.3 * tensao_V - 4353.8;
    return max(ntu, 0.0f);
}

/**
 * Determina classificação de qualidade local (CONAMA 357/2005).
 * Retorna: "normal", "alerta", "critico" ou "toxico"
 */
String classificarQualidade(float tds, float turbidez, float temp) {
    // Qualquer parâmetro crítico → status crítico
    if (tds > LIMITE_TDS_CRITICO || turbidez > LIMITE_TURB_CRITICO || temp > LIMITE_TEMP_CRITICO) {
        return "toxico";
    }
    if (tds > LIMITE_TDS_ALERTA || turbidez > LIMITE_TURB_ALERTA || temp > LIMITE_TEMP_ALERTA) {
        return "critico";
    }
    // Verificação combinada (degradação sinérgica)
    int pontos_alerta = 0;
    if (tds > 300.0)       pontos_alerta++;
    if (turbidez > 15.0)   pontos_alerta++;
    if (temp > 26.0)       pontos_alerta++;
    if (pontos_alerta >= 2) return "alerta";

    return "normal";
}

/**
 * Controla LED de alerta:
 *   normal  → LED apagado
 *   alerta  → pisca lento (1Hz)
 *   critico → pisca rápido (5Hz)
 *   toxico  → LED aceso contínuo
 */
void controlarLED(String classificacao) {
    if (classificacao == "normal") {
        digitalWrite(PIN_LED_ALERTA, LOW);
    } else if (classificacao == "alerta") {
        digitalWrite(PIN_LED_ALERTA, millis() % 1000 < 500 ? HIGH : LOW);
    } else if (classificacao == "critico") {
        digitalWrite(PIN_LED_ALERTA, millis() % 200 < 100 ? HIGH : LOW);
    } else {  // toxico
        digitalWrite(PIN_LED_ALERTA, HIGH);
    }
}

// ─── WiFi ────────────────────────────────────────────────────────────────────
void conectarWiFi() {
    Serial.print("[WiFi] Conectando a ");
    Serial.print(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n[WiFi] Conectado! IP: " + WiFi.localIP().toString());
}

// ─── MQTT ─────────────────────────────────────────────────────────────────────
void conectarMQTT() {
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    while (!mqttClient.connected()) {
        Serial.print("[MQTT] Conectando... ");
        if (mqttClient.connect(CLIENT_ID)) {
            Serial.println("OK!");
            // Publica mensagem de handshake
            String handshake = "{\"evento\":\"conexao\",\"sensor\":\"" + sensor_id + "\","
                               "\"projeto\":\"AquaWatch\",\"fiap_rm\":\"567505\"}";
            mqttClient.publish("aquawatch/status", handshake.c_str());
        } else {
            Serial.println("Falhou. Tentando em 3s...");
            delay(3000);
        }
    }
}

// ─── Setup ───────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n╔══════════════════════════════════════╗");
    Serial.println("║        AquaWatch — ESP32             ║");
    Serial.println("║  Sensor TDS + Turbidez + DS18B20    ║");
    Serial.println("║  FIAP IA — Fase 7 — Sub GS 2026.1  ║");
    Serial.println("╚══════════════════════════════════════╝\n");

    pinMode(PIN_LED_ALERTA, OUTPUT);
    analogReadResolution(12);    // 12-bit ADC (ESP32)
    analogSetAttenuation(ADC_11db);  // suporte a 0-3.3V

    ds18b20.begin();
    Serial.println("[DS18B20] Sensores encontrados: " + String(ds18b20.getDeviceCount()));

    conectarWiFi();
    conectarMQTT();

    Serial.println("[AquaWatch] Iniciando leituras a cada " + String(INTERVALO_MS/1000) + "s...\n");
}

// ─── Loop ────────────────────────────────────────────────────────────────────
void loop() {
    if (!mqttClient.connected()) conectarMQTT();
    mqttClient.loop();

    unsigned long agora = millis();
    if (agora - lastSend >= INTERVALO_MS) {
        lastSend = agora;

        // ── Leituras dos sensores ─────────────────────────────────────────────
        // Temperatura (DS18B20)
        ds18b20.requestTemperatures();
        float temperatura = ds18b20.getTempCByIndex(0);
        if (temperatura == DEVICE_DISCONNECTED_C) temperatura = 22.0;   // fallback

        // TDS (SEN0189 via ADC)
        float tensao_tds = lerADC_V(PIN_TDS);
        float tds        = calcularTDS(tensao_tds, temperatura);

        // Turbidez (analógico)
        float tensao_turb = lerADC_V(PIN_TURBIDEZ);
        float turbidez    = calcularTurbidez(tensao_turb);

        // OD simulado (correlação inversa com temperatura — simplificação POC)
        float OD = max(0.0f, 14.6f - 0.39f * temperatura);

        // Condutividade estimada (TDS / 0.64 — relação empírica)
        float condutividade = tds / 0.64f;

        // pH — seria necessário sensor pH (SEN0161), aqui estimado
        // Correlação inversa com condutividade (indicativa)
        float pH_estimado = max(4.0f, 8.5f - condutividade / 2000.0f);

        // ── Classificação local ───────────────────────────────────────────────
        String classificacao = classificarQualidade(tds, turbidez, temperatura);
        controlarLED(classificacao);
        if (classificacao == "critico" || classificacao == "toxico") impactos++;

        // ── Monta payload JSON ────────────────────────────────────────────────
        StaticJsonDocument<512> doc;
        doc["sensor_id"]          = sensor_id;
        doc["timestamp_ms"]       = agora;
        doc["TDS_mgL"]            = round(tds * 10) / 10.0;
        doc["turbidez_NTU"]       = round(turbidez * 10) / 10.0;
        doc["temperatura_C"]      = round(temperatura * 10) / 10.0;
        doc["OD_mgL"]             = round(OD * 100) / 100.0;
        doc["condutividade_uScm"] = round(condutividade);
        doc["pH_estimado"]        = round(pH_estimado * 10) / 10.0;
        doc["tensao_TDS_V"]       = round(tensao_tds * 1000) / 1000.0;
        doc["tensao_turb_V"]      = round(tensao_turb * 1000) / 1000.0;
        doc["classificacao_local"] = classificacao;
        doc["nivel_alerta"]       = (classificacao == "normal")  ? "BAIXO"   :
                                    (classificacao == "alerta")  ? "MEDIO"   :
                                    (classificacao == "critico") ? "ALTO"    : "CRITICO";
        doc["alertas_sessao"]     = impactos;
        doc["protocolo"]          = "MQTT_HIVEMQ";
        doc["projeto"]            = "AquaWatch_FIAP_RM567505";

        // ── Publica no MQTT ───────────────────────────────────────────────────
        char buffer[512];
        serializeJson(doc, buffer);

        bool publicado = mqttClient.publish(MQTT_TOPIC, buffer, false);

        // ── Log Serial ────────────────────────────────────────────────────────
        Serial.println("─────────────────────────────────────────");
        Serial.println("[SENSOR] Leitura #" + String(impactos + 1));
        Serial.println("  TDS         : " + String(tds, 1) + " mg/L (V=" + String(tensao_tds, 3) + ")");
        Serial.println("  Turbidez    : " + String(turbidez, 1) + " NTU (V=" + String(tensao_turb, 3) + ")");
        Serial.println("  Temperatura : " + String(temperatura, 1) + " °C");
        Serial.println("  OD          : " + String(OD, 2) + " mg/L");
        Serial.println("  Condut.     : " + String(condutividade, 0) + " μS/cm");
        Serial.println("  pH (estim.) : " + String(pH_estimado, 1));
        Serial.println("  Classif.    : " + classificacao.toUpperCase());
        Serial.println("  MQTT OK     : " + String(publicado ? "SIM ✓" : "FALHOU ✗"));
        Serial.println("  Tópico      : " + String(MQTT_TOPIC));
    }
}

/*
 * Exemplo de payload MQTT publicado pelo ESP32:
 * Tópico: aquawatch/sensor/ESP32-001
 *
 * {
 *   "sensor_id": "AquaWatch-ESP32-001",
 *   "timestamp_ms": 12345678,
 *   "TDS_mgL": 245.3,
 *   "turbidez_NTU": 1.8,
 *   "temperatura_C": 19.5,
 *   "OD_mgL": 7.88,
 *   "condutividade_uScm": 383.0,
 *   "pH_estimado": 8.3,
 *   "tensao_TDS_V": 0.412,
 *   "tensao_turb_V": 3.821,
 *   "classificacao_local": "normal",
 *   "nivel_alerta": "BAIXO",
 *   "alertas_sessao": 0,
 *   "protocolo": "MQTT_HIVEMQ",
 *   "projeto": "AquaWatch_FIAP_RM567505"
 * }
 */
