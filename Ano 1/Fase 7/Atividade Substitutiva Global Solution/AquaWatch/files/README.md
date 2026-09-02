# 💧 AquaWatch — Monitoramento de Qualidade da Água via Satélite + ML

**FIAP — Graduação em Inteligência Artificial | Fase 7 — Sub GS 2026.1**  
**Aluno:** Lucas Alberto da Silva Amorim | **RM:** 567505

---

## 🎯 Proposta

O AquaWatch é um sistema inteligente de monitoramento de qualidade da água que combina:
- Dados de satélite (análise espectral NDWI de imagens multiespectrais)
- Machine Learning (LSTM Bidirecional + Isolation Forest)
- IoT em campo (ESP32 + sensores TDS/turbidez/temperatura)
- Cloud serverless (Firebase Cloud Function simulada)
- Dashboard interativo (Dash + Plotly)
- Banco NoSQL (MongoDB simulado via JSON)
- API pública real (USGS Water Quality Web Service)

**Pergunta respondida:** Como a IA e tecnologias digitais podem transformar a nova economia espacial e gerar impacto positivo na Terra?

---

## 🏗️ Arquitetura

```
Satélite (Sentinel-2 simulado)
        ↓ imagem multiespectral
vision/analisar_imagem.py
  → NDWI + análise de bandas RGB
  → Classificação de 4 zonas de qualidade

ESP32 (TDS + Turbidez + DS18B20)
        ↓ MQTT / HiveMQ
cloud/firebase_sim.py
  → LSTM Bidirecional classifica série temporal
  → Isolation Forest detecta anomalias em tempo real
  → USGS API enriquece com dados reais de rios
  → MongoDB (JSON local) armazena histórico

dashboard/app.py (Dash + Plotly)
  → Mapa de pontos de monitoramento
  → Classificador LSTM ao vivo (sliders interativos)
  → Histórico de predições MongoDB
  → Curvas de treinamento LSTM
```

---

## 📁 Estrutura de Pastas

```
AquaWatch/
├── ml/
│   ├── gerar_dataset.py        # Dataset sintético (séries temporais 24h × 6 parâmetros)
│   ├── treinar_lstm.py         # LSTM Bidirecional + Atenção (PyTorch)
│   └── isolation_forest.py     # Isolation Forest não-supervisionado (scikit-learn)
├── vision/
│   └── analisar_imagem.py      # NDWI + análise espectral de imagem de satélite
├── dashboard/
│   └── app.py                  # Dashboard interativo (Dash + Plotly)
├── cloud/
│   └── firebase_sim.py         # Firebase Cloud Function + USGS API + MongoDB
├── sensor/
│   └── aquawatch.ino           # Firmware ESP32 (TDS + Turbidez + DS18B20 + MQTT)
├── dados/                      # Gerado automaticamente ao rodar os scripts
├── modelos/                    # Pesos do LSTM + pickle do IF
├── db/                         # Banco MongoDB (historico.json)
├── vision/                     # Imagem de análise espectral gerada
├── requirements.txt
└── README.md
```

---

## ▶️ Como Executar (ordem obrigatória)

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Gerar dataset sintético
python ml/gerar_dataset.py

# 3. Treinar LSTM Bidirecional (40 épocas)
python ml/treinar_lstm.py

# 4. Treinar Isolation Forest
python ml/isolation_forest.py

# 5. CNN para classificação de imagem de satélite (Visão Computacional)
python vision/cnn_satelite.py

# 6. Análise espectral de imagem de satélite (NDWI)
python vision/analisar_imagem.py

# 7. Firebase Cloud Function + USGS API (4 cenários)
python cloud/firebase_sim.py

# 8. Dashboard interativo (acesse http://localhost:8050)
python dashboard/app.py
```

**Importante:** Todos os comandos devem ser executados da raiz do projeto (`AquaWatch/`).

---

## 🤖 Tecnologias

| Camada | Tecnologia | Diferencial |
|--------|-----------|------------|
| ML Temporal | **LSTM Bidirecional + Atenção** (PyTorch) | Aprende padrões em 24h de série temporal |
| ML Anomalia | **Isolation Forest** (scikit-learn) | Detecção não-supervisionada em tempo real |
| Visão | **CNN (PyTorch) + NDWI + Análise Espectral** | CNN classifica patches de satélite; NDWI detecta água limpa |
| API | **USGS Water Quality Web Service** | Dados reais de qualidade de rios dos EUA |
| Cloud | **Firebase Cloud Function** (simulada) | Serverless diferente de AWS Lambda |
| Dashboard | **Dash + Plotly** | Callbacks reativos sem recarregar página |
| IoT | **ESP32 + TDS + Turbidez + DS18B20** | Sensores de qualidade da água real |
| Banco | **MongoDB** (simulado) | NoSQL diferente de SQLite e TinyDB |

---

## 📊 Resultados do Modelo

- **LSTM Acurácia (teste):** 86,67% | Melhor val_acc: 93,33%
- **Isolation Forest F1:** 0.9696 | Precision: 0.9829 | Recall: 0.9567
- **CNN Visão Computacional:** classificação de patches de imagem de satélite (PyTorch)
- **Análise Espectral NDWI:** 4/4 zonas classificadas corretamente
- **Épocas de treinamento LSTM:** 40 com scheduler adaptativo
- **Nota:** dataset sintético com 30% de amostras em zona de transição entre classes, seguindo parâmetros da CONAMA 357/2005 — acurácia abaixo de 100% é esperada e reflete dificuldade real.

---

## 🔗 Links

- **Repositório GitHub:** [a preencher]
- **Vídeo demonstrativo:** [a preencher — YouTube Não Listado]
