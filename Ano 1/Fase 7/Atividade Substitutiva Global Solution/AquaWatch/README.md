# AquaWatch — Monitoramento de Qualidade da Agua via Satelite + ML

**FIAP — Graduacao em Inteligencia Artificial | Fase 7 — Sub GS 2026.1**
**Aluno:** Lucas Alberto da Silva Amorim | **RM:** 567505

---

## Proposta

O AquaWatch e um sistema inteligente de monitoramento de qualidade da agua que combina:
- Dados de satelite (analise espectral NDWI de imagens multiespectrais)
- Machine Learning (LSTM Bidirecional + Isolation Forest)
- IoT em campo (ESP32 + sensores TDS/turbidez/temperatura)
- Cloud serverless (Firebase Cloud Function simulada)
- Dashboard interativo (Dash + Plotly)
- Banco NoSQL (MongoDB simulado via JSON)
- API publica real (USGS Water Quality Web Service)

**Pergunta respondida:** Como a IA e tecnologias digitais podem transformar a nova economia espacial e gerar impacto positivo na Terra?

---

## Arquitetura

```
Satelite (Sentinel-2 simulado)
        -> vision/analisar_imagem.py
           -> NDWI + analise de bandas RGB
           -> Classificacao de 4 zonas de qualidade

ESP32 (TDS + Turbidez + DS18B20)
        -> MQTT / HiveMQ
           -> cloud/firebase_sim.py
              -> LSTM Bidirecional classifica serie temporal
              -> Isolation Forest detecta anomalias
              -> USGS API enriquece com dados reais
              -> MongoDB (JSON local) armazena historico

dashboard/app.py (Dash + Plotly)
        -> Mapa de pontos de monitoramento
        -> Classificador LSTM ao vivo (sliders)
        -> Historico MongoDB
        -> Curvas de treinamento
```

---

## Estrutura de Pastas

```
AquaWatch/
├── ml/
│   ├── gerar_dataset.py        # Dataset sintetico com overlap entre classes
│   ├── treinar_lstm.py         # LSTM Bidirecional + Atencao (PyTorch)
│   └── isolation_forest.py     # Isolation Forest (scikit-learn)
├── vision/
│   └── analisar_imagem.py      # NDWI + analise espectral de imagem de satelite
├── dashboard/
│   └── app.py                  # Dashboard interativo (Dash + Plotly)
├── cloud/
│   └── firebase_sim.py         # Firebase Cloud Function + USGS API + MongoDB
├── sensor/
│   └── aquawatch.ino           # Firmware ESP32 (TDS + Turbidez + DS18B20 + MQTT)
├── dados/                      # Gerado automaticamente
├── modelos/                    # Pesos LSTM + pickle IF
├── db/                         # historico.json (MongoDB simulado)
├── requirements.txt
└── README.md
```

---

## Como Executar (ordem obrigatoria)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Gerar dataset sintetico
python ml/gerar_dataset.py

# 3. Treinar LSTM Bidirecional (40 epocas)
python ml/treinar_lstm.py

# 4. Treinar Isolation Forest
python ml/isolation_forest.py

# 5. Analise espectral de imagem de satelite
python vision/analisar_imagem.py

# 6. Firebase Cloud Function + USGS API (4 cenarios)
python cloud/firebase_sim.py

# 7. Dashboard interativo
python dashboard/app.py
# Acesse: http://localhost:8050
```

Todos os comandos devem ser executados da raiz do projeto (AquaWatch/).

---

## Tecnologias

| Camada | Tecnologia | Diferencial |
|--------|-----------|------------|
| ML Temporal | LSTM Bidirecional + Atencao (PyTorch) | Series temporais 24h x 6 parametros |
| ML Anomalia | Isolation Forest (scikit-learn) | Deteccao nao-supervisionada |
| Visao | NDWI + Analise Espectral (scikit-image) | Indice de agua em imagens multiespectrais |
| API | USGS Water Quality Web Service | Dados reais de qualidade de rios |
| Cloud | Firebase Cloud Function (simulada) | Serverless diferente de AWS Lambda |
| Dashboard | Dash + Plotly | Callbacks reativos |
| IoT | ESP32 + TDS + Turbidez + DS18B20 | Sensores de qualidade da agua |
| Banco | MongoDB (simulado) | NoSQL diferente de SQLite e TinyDB |

---

## Resultados

| Modulo | Resultado |
|--------|-----------|
| LSTM Acuracia (teste) | **86,67%** |
| LSTM Melhor val_acc | 93,33% |
| Isolation Forest F1 | **0,9696** |
| Isolation Forest Precision | 0,9829 |
| Isolation Forest Recall | 0,9567 |
| Visao Computacional NDWI | **4/4 zonas corretas** |
| Firebase + USGS API | HTTP 200 — dados reais |
| Dashboard | localhost:8050 |

---

## Links

- **Repositorio GitHub:** [LINK](https://github.com/lucasamorim1995/FIAP_Entregas)
- **Video demonstrativo:** [YouTube Nao Listado](https://youtu.be/8ZgepqTG-zs)
