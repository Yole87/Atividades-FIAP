# 🎯 Challenge FIAP – Totem de IA Interativo | FlexMedia (Sprint 4 - Final)

#### FIAP Turma 1TIAOS - 1º Ano | Artificial Intelligence
#### Integrantes: 
- **Alan Robin** (RM: 567437) – Engenharia de Software, Cloud e Inteligência Artificial
- **Lucas Amorim** (RM: 567505) – Hardware, IoT e Integração de Sensores

---

## 📋 Visão Geral do Projeto (Fase 6)

Este projeto consiste no desenvolvimento de um **Totem Interativo Inteligente** para a empresa **FlexMedia**. O objetivo é transformar a experiência de visitação em museus e zoológicos através de um assistente virtual capaz de interagir por voz, responder curiosidades e coletar métricas de engajamento em tempo real.

Nesta **Sprint 4 (Entrega Final)**, o sistema deixou de ser apenas um coletor de dados para se tornar uma **solução digital interativa avançada**. Implementamos simulação de **Visão Computacional** (detecção de faixa etária e idioma), um **Mecanismo de IA para Interação** (LLM simulado para respostas contextuais) e um **Banco de Dados Relacional Normalizado** para extrair métricas ricas.

---

## 🏗️ Estrutura do Projeto

O projeto está estruturado seguindo princípios de engenharia de software, agora utilizando `pathlib` para portabilidade universal (eliminando caminhos hardcoded):

```text
/ (Raiz)
├── docs/                 # Documentação e diagramas
├── src/
│   ├── backend/          # API FastAPI + Autenticação + Rotas de IA (Chat NLP)
│   ├── dashboard/        # Dashboard Analítico (Streamlit) cruzando perfil e uso
│   ├── database/         # Banco relacional normalizado (SQLite) com Foreign Keys
│   ├── ml/               # Modelos RandomForest aprimorados (Análise multidimensional)
│   └── simulator/        # Mock avançado (Visão Computacional simulada e interações)
```

### 🔐 Segurança e Compliance (Cognitive CyberSecurity & LGPD)
- **API Key Authentication:** A comunicação entre o totem (ESP32/Mock) e o backend é protegida por um header `X-API-Key`, garantindo que apenas dispositivos autorizados enviem dados.
- **Anonimização (LGPD):** Todos os registros de interações são gravados de forma anônima (ex: `Visitor_492`), protegendo a privacidade dos visitantes.

---

## 🧠 Inteligência Artificial & Machine Learning (Novidades Sprint 4)

1. **Processamento de Linguagem Natural (NLP):** O backend agora possui uma rota `/api/ai/chat` que simula um LLM, capaz de interpretar perguntas do visitante sobre o espaço (ex: "Onde tem banheiro?") e gerar respostas contextuais.
2. **Machine Learning Enriquecido:** O modelo `RandomForestClassifier` foi refinado para prever o sucesso da interação usando novas dimensões. A IA provou (via *Feature Importance*) que a **Faixa Etária** e o **Idioma** detectados afetam drasticamente o engajamento, sanando análises rasas.

---

## 🚀 Como Executar o Projeto Localmente

Para testar o ecossistema completo, abra **terminais separados** na raiz do projeto e execute rigorosamente nesta ordem:

**1. Inicie a API Backend (FastAPI):**
*(Crucial: A API deve rodar primeiro para criar o banco normalizado e habilitar as rotas)*
```bash
uvicorn src.backend.main:app --reload
```
*(Acesse a documentação Swagger em: http://127.0.0.1:8000/docs)*

**2. Inicie o Simulador Avançado (Visão Computacional & Mock):**
```bash
python src/simulator/sensor_mock.py
```

**3. Abra o Relatório Analítico Final (Dashboard):**
```bash
python -m streamlit run src/dashboard/app.py
```

**4. Treine e Avalie o Modelo de IA:**
```bash
python src/ml/classifier.py
```

---

## 🎥 Pitch e Demonstração

**[[VÍDEO DO YOUTUBE AQUI](https://youtu.be/NiRXOeUnG5c)]**

---

## 🗺️ Mapa Arquitetural

[Arquitetura do Totem](docs/Sprint_1/diagram_final.png)

> _"Projeto acadêmico desenvolvido para a FIAP 2026 - Consolidando o mundo físico ao digital com Inteligência Artificial."_