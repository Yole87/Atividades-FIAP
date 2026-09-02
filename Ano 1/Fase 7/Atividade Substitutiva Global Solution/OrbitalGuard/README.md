<p align="center">
<a href="https://www.fiap.com.br/">
<img src="https://upload.wikimedia.org/wikipedia/commons/d/d4/Fiap-logo-novo.jpg" alt="FIAP" width="160px"/>
</a>
</p>

# 🛸 OrbitalGuard
## Classificação de Detritos Espaciais com CNN + Monitoramento Orbital

---

## 👨‍💻 Integrante

| [<img src="https://avatars.githubusercontent.com/u/000000?v=4" width=115><br><sub>Alan Robin Santos</sub>](https://github.com/Yole87) |
| :---: |
| RM 567437 |

---

## 👩‍🏫 Professores

### Tutor(a)
Sabrina Otoni

### Coordenador(a)
André Godoi

---

## 📜 Descrição

O **OrbitalGuard** é uma prova de conceito que responde ao tema da Global Solution 2026.1:

> *"Como a Inteligência Artificial e as tecnologias digitais podem transformar a nova economia espacial e gerar impacto positivo na Terra?"*

A solução aplica uma **CNN (Rede Neural Convolucional com PyTorch)** para classificar tipos de detritos espaciais em imagens orbitais, combinada com monitoramento em tempo real via **ESP32 + MPU6050**, integração com a **API real da ISS (Open Notify)** e arquitetura serverless simulada na **AWS Lambda**.

---

## 🏗️ Arquitetura da Solução
🛸 Imagens Sintéticas → CNN (PyTorch) → Classificação de Detritos → Dashboard

🌐 Open Notify ISS API → Lambda → CNN (PyTorch) → Risco de Colisão Orbital → Dashboard

📡 ESP32 + MPU6050 → MQTT (HiveMQ) → Enriquecimento local

| Módulo | Tecnologia | Função |
|---|---|---|
| **ML — CNN** | PyTorch + scikit-learn | Classifica 4 tipos de objetos orbitais em imagens 64x64 |
| **Dashboard** | Streamlit + Plotly | Interface interativa com simulador de risco orbital |
| **Visão Computacional** | OpenCV + PIL + PyTorch | Classificação em grid de cena orbital sintética |
| **Sensor IoT** | ESP32 + MPU6050 + MQTT | Detecta vibração/impacto de microdetritos em tempo real |
| **Cloud** | AWS Lambda + Open Notify API + CNN | API REST serverless com classificação neural integrada |
| **Banco de Dados** | TinyDB (NoSQL JSON) | Histórico de predições e métricas do modelo |

---

## 🧠 Classes do Modelo CNN

| ID | Classe | Risco |
|---|---|---|
| 0 | `satelite_ativo` | BAIXO |
| 1 | `detrito_metalico` | ALTO |
| 2 | `fragmento_rochoso` | ALTO |
| 3 | `satelite_inativo` | MÉDIO |

---

## 📁 Estrutura do Projeto

OrbitalGuard/
├── ml/
│   ├── model.py              # CNN compartilhada (importada por todos os módulos)
│   ├── gerar_dataset.py      # Gerador de dataset sintético (800 imagens, 4 classes)
│   ├── treinar_cnn.py        # Treinamento da CNN com PyTorch + data augmentation
│   ├── dataset/              # Imagens geradas automaticamente ao rodar gerar_dataset.py
│   ├── modelo_cnn.pth        # Modelo treinado — gerado automaticamente ao rodar treinar_cnn.py
│   ├── metricas.json         # Acurácia e loss — gerado automaticamente ao rodar treinar_cnn.py
│   └── historico_treino.png  # Gráfico de treinamento — gerado automaticamente ao rodar treinar_cnn.py
├── vision/
│   ├── analisar_orbita.py    # Análise de cena orbital + OpenCV
│   ├── mapa_orbital.png      # Mapa com bounding boxes — gerado automaticamente ao rodar analisar_orbita.py
│   └── resultado_visao.json  # Resultados da visão — gerado automaticamente ao rodar analisar_orbita.py
├── aws/
│   ├── lambda_function.py    # AWS Lambda simulada + CNN + Open Notify API
│   └── lambda_resultados.json # Resultados — gerados automaticamente ao rodar lambda_function.py
├── db/
│   └── orbitalguard.json     # Banco TinyDB NoSQL — gerado automaticamente ao rodar treinar_cnn.py
├── app.py                    # Dashboard Streamlit
├── sensor_orbital.ino        # Firmware ESP32 + MPU6050
├── requirements.txt
└── README.md

---

## ⚙️ Como Executar

```bash
# 1. Entre na pasta do projeto
cd OrbitalGuard

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Gere o dataset sintético
python ml/gerar_dataset.py

# 4. Treine a CNN
python ml/treinar_cnn.py

# 5. Analise a cena orbital
python vision/analisar_orbita.py

# 6. Simule a Lambda AWS
python aws/lambda_function.py

# 7. Rode o dashboard
python -m streamlit run app.py
```

---

## 📡 ESP32 — Sensor de Vibração Orbital

**Hardware:** ESP32 DevKit V1 + MPU6050 (acelerômetro/giroscópio I²C)

| Componente | Conexão |
|---|---|
| MPU6050 SDA | GPIO 21 |
| MPU6050 SCL | GPIO 22 |
| LED Alerta | GPIO 2 (embutido) |

**Protocolo:** MQTT via HiveMQ | **Tópico:** `orbitalguard/sensor/vibration01`

---

## ☁️ AWS Lambda

**Endpoint simulado:**
GET https://api.orbitalguard.io/risco?altitude_km=408&inclinacao=51.6
**Arquitetura:** `Cliente → API Gateway → Lambda → CNN (PyTorch) + Open Notify API → S3 + CloudWatch`

---

## 🎯 Resultados Obtidos

| Métrica | Valor |
|---|---|
| Acurácia CNN (teste) | 0.9688 (96.88%) |
| Loss (Cross-Entropy) | 0.0250 |
| Amostras de treino | 512 |
| Épocas | 40 |
| Objetos detectados (visão) | 6/6 corretos |
| Cenários Lambda testados | 4 |

---

## 🔗 Links

- 🎥 **Vídeo Demonstrativo:** [YouTube](https://youtu.be/jC8Nrqa1koA)
- 💻 **Repositório GitHub:** [Github](https://github.com/Yole87/Atividades-FIAP/tree/FIAP_IA_Online/Fase%207/Atividade%20Substitutiva%20Global%20Solution)

---

## 📚 Referências

- Open Notify ISS API: http://api.open-notify.org/
- PyTorch: https://pytorch.org/
- Streamlit: https://docs.streamlit.io/
- Adafruit MPU6050: https://github.com/adafruit/Adafruit_MPU6050
- ESA Space Debris Office: https://www.esa.int/Space_Safety/Space_Debris

---

## 📋 Licença

<img alt="CC BY 4.0" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" height="22">
<img alt="BY" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" height="22">

[FIAP](https://fiap.com.br) — licenciado sob [Attribution 4.0 International](http://creativecommons.org/licenses/by/4.0/).