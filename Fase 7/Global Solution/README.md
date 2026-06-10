# FIAP - Faculdade de Informática e Administração Paulista

![FIAP Logo](https://www.fiap.com.br/wp-content/themes/fiap2016/images/sharing/fiap.png)

# 🎓 Graduação ON em Inteligência Artificial

## 📚 Global Solution 2 — 2026.1 | Fase 7

---

## 👩🏻‍💻 Integrantes

| Nome Completo | RM |
|---------------|----|
| Alan Robin Santos | RM 567437 |
| Lucas Alberto da Silva Amorim | RM 567505 |
| Gustavo Borges Marinho Peres | RM 567477 |

---

## 🛰️ AgroSat — Previsão de Produtividade Agrícola com Dados de Satélite

### O Problema

O agronegócio brasileiro representa mais de 27% do PIB nacional, mas ainda sofre com alta imprevisibilidade climática que afeta diretamente a produtividade das lavouras. Geadas, secas e excesso de chuva causam perdas bilionárias anualmente — perdas que poderiam ser mitigadas com previsão antecipada baseada em dados.

### A Solução

O **AgroSat** é uma POC que combina **dados reais de satélites da NASA e do Sentinel-2 (ESA)** com **Machine Learning, Visão Computacional e IoT** para prever a produtividade agrícola de lavouras do Cerrado Brasileiro. A solução responde diretamente ao tema da GS:

> *"Como a IA e as tecnologias digitais podem transformar a nova economia espacial e gerar impacto positivo na Terra?"*

---

## 🏗️ Arquitetura da Solução

```
🛰️ SATÉLITE (NASA/ESA)      📡 ESP32 (CAMPO)
        │                          │
        ▼                          ▼
  NASA POWER API           DHT22 + BMP280
  T2M, PRECTOT,            Temp, Umidade,
  ALLSKY_SW_DWN            Pressão, UV, VPD
        │                          │
        └────────────┬─────────────┘
                     ▼
           Feature Engineering
           (agregação mensal · VPD · NDVI)
                     │
                     ▼
          Random Forest Regressor
          R² = 0.9465 | MAE = 225 kg/ha
                     │
                  ┌──┴──┐
                  ▼     ▼
            SQLite    Dashboard
            (histórico) Streamlit+Plotly

🛰️ Sentinel-2 (ESA)    →    YOLO + Classificação Espectral
   Imagem orbital real  →    NDVI · Vegetação · Stress hídrico

☁️ AWS Lambda           →    API REST serverless
   API Gateway + S3     →    Previsão sob demanda
```

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso no Projeto |
|------------|----------------|
| Python 3.x | Linguagem principal |
| scikit-learn | Modelo Random Forest Regressor |
| NASA POWER API | Dados climáticos reais de satélite (temperatura, precipitação, radiação) |
| Sentinel-2 L2A (ESA) | Imagem orbital real do Cerrado para análise espectral |
| YOLOv8 (Ultralytics) | Detecção de objetos em imagens de satélite |
| Classificação Espectral NDVI | Análise de vegetação, stress hídrico e cobertura do solo |
| Pandas / NumPy | Processamento e feature engineering |
| Streamlit | Interface web do dashboard interativo |
| Plotly | Visualizações interativas de dados climáticos e previsões |
| SQLite | Persistência do histórico de previsões e métricas do modelo |
| ESP32 + DHT22 + BMP280 | Sensor IoT de campo (temperatura, umidade, pressão, VPD) |
| MQTT (HiveMQ) | Transmissão de dados IoT para a nuvem |
| AWS Lambda | Função serverless para previsão via API REST |
| AWS API Gateway + S3 | Exposição da API e armazenamento de resultados |
| joblib | Serialização do modelo ML treinado |

---

## 📁 Estrutura do Repositório

```
agrosat-gs2026/
├── model.py                    # Pipeline de ML: NASA API → treino → SQLite → previsão
├── app.py                      # Dashboard Streamlit + Plotly + histórico SQLite
├── sensor_campo.ino            # Firmware ESP32 (C++) — sensor IoT de campo
├── requirements.txt            # Dependências Python
├── README.md
│
├── ml/                         # Artefatos gerados após execução do model.py
│   ├── model.py                # Script principal do pipeline de ML
│   ├── modelo_agrosat.pkl      # Modelo Random Forest serializado
│   ├── scaler_agrosat.pkl      # Scaler de normalização
│   ├── dados_mensais.csv       # Dados históricos processados
│   ├── metricas.json           # R², MAE e métricas do modelo
│   └── agrosat.db              # Banco SQLite com histórico de previsões
│
├── vision/                     # Módulo de Visão Computacional
│   ├── yolo_detector.py        # YOLO + classificação espectral NDVI
│   ├── download_e_detectar.py  # Pipeline completo: imagem real → análise
│   ├── satelite_real_cerrado.jpg  # Imagem real Sentinel-2 (Sorriso/MT)
│   ├── mapa_real_classificacao.png  # Mapa de classificação gerado
│   └── resultado_real.json     # Resultados da análise espectral
│
└── aws/                        # Módulo AWS Serverless
    └── lambda_function.py      # Função Lambda + simulação local
```

---

## 🚀 Instruções de Execução

### Pré-requisitos
- Python 3.10 ou superior
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/agrosat-gs2026
cd agrosat-gs2026

# 2. Instale as dependências
pip install -r requirements.txt
```

### Execução dos módulos

```bash
# 1. Pipeline de ML (treina modelo + cria banco SQLite)
python ml/model.py

# 2. Dashboard interativo (abre no browser)
python -m streamlit run app.py

# 3. Visão Computacional — YOLO + Sentinel-2
python vision/download_e_detectar.py

# 4. AWS Lambda — simulação local
python aws/lambda_function.py
```

Acesse o dashboard em: `http://localhost:8501`

### ESP32
Abra `sensor_campo.ino` no Arduino IDE. Configure `WIFI_SSID`, `WIFI_PASSWORD` e `MQTT_BROKER` antes de gravar no dispositivo.

---

## 📊 Resultados Obtidos

| Métrica | Valor |
|---------|-------|
| R² do modelo | 0.9465 |
| MAE | 225 kg/ha |
| Dados históricos | 60 meses (2019–2023) |
| Fonte dos dados climáticos | NASA POWER API (dados reais de satélite) |
| Imagem orbital analisada | Sentinel-2 L2A — Sorriso/MT (10/02/2026) |
| Vegetação saudável detectada | 46.7% da área analisada |
| Produtividade média prevista | 4.669 kg/ha |
| Previsões persistidas (SQLite) | 5 cenários registrados |

---

## 🔬 Módulo de Visão Computacional

Análise espectral real da imagem Sentinel-2 L2A do Cerrado Brasileiro:

| Classe | Cobertura | NDVI estimado |
|--------|-----------|---------------|
| Vegetação saudável | 46.7% | 0.58 |
| Solo exposto / pousio | 40.8% | 0.08 |
| Área urbana (Sorriso/Sinop) | 12.0% | 0.05 |
| Stress hídrico | 0.2% | 0.21 |
| Corpos d'água | 1.3% | -0.15 |

---

## ☁️ Módulo AWS Serverless

Arquitetura proposta para produção:

```
Cliente → API Gateway → Lambda → NASA POWER API
Lambda  → S3 (resultados) → CloudWatch (logs)

Endpoint: GET https://api.agrosat.io/previsao?lat=-12.55&lon=-55.72&mes=1
```

---

## 🌍 Impacto e Contextualização Espacial

A arquitetura do AgroSat é equivalente à usada por plataformas como Climate FieldView e Solinftec. Nossa solução usa exclusivamente APIs públicas, hardware acessível (ESP32 < R$30) e dados orbitais gratuitos (NASA + ESA), democratizando o acesso à inteligência agronômica baseada em satélite.

---

## 🎥 Vídeo Demonstrativo

[[LINK DO YOUTUBE — NÃO LISTADO](https://youtu.be/j385NOpaXt0)]

---

## 🔗 Links

- **Repositório:** [[LINK DO GITHUB](https://github.com/Yole87/Atividades-FIAP/tree/FIAP_IA_Online/Fase%207/Global%20Solution)]
- **NASA POWER API:** https://power.larc.nasa.gov/
- **Copernicus Browser (Sentinel-2):** https://browser.dataspace.copernicus.eu/

---

## 📋 Licença

*Projeto desenvolvido para a Global Solution 2026.1 — FIAP | Curso de Inteligência Artificial*
