#include <DHT.h>

/* ======= Configuração de pinos conforme seu diagram.json ======= */
#define DHTPIN        15        // DHT22 no GPIO15 (D15)
#define DHTTYPE       DHT22

#define RELAY_PIN      2        // IN do relé no GPIO2 (D2) - Wokwi
// BOTÕES NPK (cada botão tem a outra perna no GND)
#define BTN_N         13        // Nitrogênio  (D13)
#define BTN_P         12        // Fósforo     (D12)
#define BTN_K         14        // Potássio    (D14)

// LDR (pH simulado) ligado na entrada analógica "A0" do Wokwi -> GPIO36 no ESP32
#define PH_PIN        36        // ADC1_CH0

/* ======= Regras de acionamento ======= */
const float LIMIAR_UMIDADE = 50.0;  // abaixo disso, liga irrigação

/* ======= Relé do Wokwi é ATIVO em HIGH ======= */
#define RELAY_ACTIVE   HIGH
#define RELAY_ON()     digitalWrite(RELAY_PIN, RELAY_ACTIVE)
#define RELAY_OFF()    digitalWrite(RELAY_PIN, !RELAY_ACTIVE)

/* ======= Instâncias ======= */
DHT dht(DHTPIN, DHTTYPE);

/* ======= Funções utilitárias ======= */
static inline float mapPhFromAdc(int adc) {
  // Converte 0..4095 (ADC) para faixa de pH 0..14 apenas para exibição didática
  return (adc / 4095.0f) * 14.0f;
}

void setup() {
  Serial.begin(115200);
  dht.begin();

  // Relé
  pinMode(RELAY_PIN, OUTPUT);
  RELAY_OFF();  // começa DESLIGADO

  // Botões com PULLUP interno (porque a outra perna está no GND)
  pinMode(BTN_N, INPUT_PULLUP);
  pinMode(BTN_P, INPUT_PULLUP);
  pinMode(BTN_K, INPUT_PULLUP);

  // ADC do pH (LDR)
  // No ESP32, não precisa pinMode para entrada analógica, mas não custa documentar:
  // pinMode(PH_PIN, INPUT);

  Serial.println("Sistema iniciado. Aguarde leituras...");
}

void loop() {
  // ---- Leituras dos sensores ----
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (isnan(h) || isnan(t)) {
    Serial.println("Falha na leitura do DHT22");
    delay(1000);
    return;
  }

  // LDR -> valor ADC
  int adcPh = analogRead(PH_PIN);       // 0..4095
  float ph   = mapPhFromAdc(adcPh);     // 0..14 (didático)

  // Botões (com PULLUP): pressionado = LOW, solto = HIGH
  bool n_on = (digitalRead(BTN_N) == LOW);
  bool p_on = (digitalRead(BTN_P) == LOW);
  bool k_on = (digitalRead(BTN_K) == LOW);

  // ---- Lógica de irrigação (BÁSICA por umidade) ----
  // Ajuste aqui se quiser combinar NPK/pH também.
  if (h < LIMIAR_UMIDADE) {
    RELAY_ON();
    Serial.println("Irrigacao LIGADA (rele ON)");
  } else {
    RELAY_OFF();
    Serial.println("Irrigacao DESLIGADA (rele OFF)");
  }

  // ---- Logs de depuração ----
  Serial.printf("Umidade: %.2f%% | Temp: %.2f C | pH*~: %.2f (ADC=%d)\n", h, t, ph, adcPh);
  Serial.printf("N=%s  P=%s  K=%s | GPIO%d nivel=%d (LED1 do rele deve refletir)\n",
                n_on ? "ON" : "OFF",
                p_on ? "ON" : "OFF",
                k_on ? "ON" : "OFF",
                RELAY_PIN, digitalRead(RELAY_PIN));

  delay(1500);
}