# 🎯 Challenge FIAP – Totem de IA Interativo | FlexMedia

#### FIAP Turma 1TIAOS - 1 Trimestre em Inteligência Artificial Online Turma S
#### Coordenador: André Godoi
#### Tutora turma S: Sabrina Otoni
#### Integrantes: Alan Robin RM: 567437 | Lucas Amorim RM: 567505

---

Este repositório contém o planejamento e a documentação do projeto desenvolvido para o **Challenge FIAP**, em parceria com a **FlexMedia**.  
O objetivo desta primeira Sprint (Fase 3) é apresentar a **arquitetura inicial**, a **definição das tecnologias** e o **plano de desenvolvimento** do projeto.

---

## 🧩 1. Justificativa do Problema e Descrição da Solução

### A. Justificativa do Problema

Em locais de visitação cultural ou de lazer (museus, zoológicos ou parques), visitantes buscam experiências **mais imersivas e interativas**, que vão além da simples observação.

Três problemas principais foram identificados:

1. **Falta de Interatividade:** a visita passiva é pouco envolvente, especialmente para o público jovem.
2. **Barreiras de Acesso:** idiomas e deficiências sensoriais limitam a experiência de muitos visitantes.
3. **Curiosidade Não Atendida:** perguntas espontâneas surgem durante a visita, mas não há meios práticos de obter respostas imediatas.

### B. Descrição da Solução

A proposta é o **Totem de IA Interativo**, equipado com **assistentes inteligentes especializados**, capazes de entender e responder perguntas por voz, de forma natural e acessível.

Os agentes de IA são organizados em personas:

- **Agente “Guia Principal”** — Responde perguntas operacionais e gerais do local.
- **Agente “Mestre das Curiosidades”** — Engaja o visitante com fatos e quizzes.
- **Agente “Planejador de Visita”** — Sugere rotas e experiências personalizadas.

O objetivo é transformar a visitação em uma experiência **interativa, educativa e inclusiva**.

---

## ⚙️ 2. Definição das Tecnologias

### 🧠 Arquitetura de Componentes

| Camada | Tecnologia | Descrição |
|--------|-------------|-----------|
| **Hardware (Totem)** | ESP32-CAM + INMP441 + Alto-falante | Captura de áudio, reprodução de voz e detecção de presença |
| **Firmware** | MicroPython | Comunicação com o backend via HTTPS |
| **Backend (Nuvem)** | Python 3 + FastAPI | Orquestrador das APIs de IA |
| **Banco de Dados** | PostgreSQL ou Firestore | Armazenamento de métricas de uso |
| **APIs de IA** | Google Speech-to-Text (STT), OpenAI GPT (LLM), Google Text-to-Speech (TTS) | Processamento de fala, linguagem e áudio |

---

## 🔄 3. Fluxo da Arquitetura

### Pipeline Completo de Interação

#### **1️⃣ Início da Interação**
1. O **usuário fala** com o totem.  
2. O **microfone INMP441** captura o áudio.  
3. O **ESP32-CAM** envia o áudio ao **Backend (FastAPI)** via HTTPS.

#### **2️⃣ Processamento em Nuvem**
4. O Backend envia o áudio à **API Google STT**, que converte fala → texto.  
5. O texto transcrito retorna ao Backend.  
6. O Backend envia o texto à **API OpenAI LLM**, que gera a resposta.  
7. A resposta em texto retorna ao Backend.  
8. O Backend envia essa resposta textual à **API Google TTS**, que converte texto → fala.  
9. O áudio sintetizado retorna ao Backend.

#### **3️⃣ Retorno ao Dispositivo**
10. O Backend envia o **áudio da resposta** (e opcionalmente o texto) de volta ao **ESP32-CAM**.  
11. O **alto-falante** reproduz o áudio da resposta para o visitante.

#### **4️⃣ Coleta de Métricas**
Durante esse processo (etapa 7 em diante), o **Backend grava as métricas** no banco de dados:
- Horário de início e fim da interação.  
- Duração total (ms).  
- Texto da pergunta (anonimizado).  
- Agente IA utilizado.  
- Idioma detectado.  
- Tipo de consulta (informativa, curiosidade, planejamento).  

📍 As métricas são gravadas **após o recebimento da resposta textual da LLM** (etapa 7), antes do envio ao TTS, garantindo que cada interação completa seja registrada.

---

## 🧱 4. Estratégia de Segurança e Privacidade

- **Privacidade:** nenhum áudio ou imagem é armazenado. O processamento é temporário e descartado após o uso.  
- **Comunicação Segura:** todas as conexões utilizam **HTTPS (SSL/TLS)**.  
- **Autenticação:** o ESP32 utiliza uma **API Key exclusiva** para autenticação no Backend.  
- **LGPD:** todas as métricas são **anonimizadas** e não identificam usuários.

---

## 🧭 5. Plano de Desenvolvimento (Sprints)

| Sprint | Fase | Entrega | Responsável | Objetivo |
|--------|------|----------|--------------|-----------|
| **Sprint 1** | Fase 3 | 31/10/2025 | Alan Robin e Lucas Amorim | Planejamento e arquitetura do sistema |
| **Sprint 2** | Fase 4 | 28/11/2025 | Alan Robin | Desenvolvimento do backend e integração com APIs |
| **Sprint 3** | Fase 5 | 06/03/2026 | Lucas Amorim | Desenvolvimento do firmware e hardware do ESP32 |
| **Sprint 4** | Fase 6 | 17/04/2026 | Alan Robin e Lucas Amorim | Integração e testes do MVP funcional |

---

## 🗺️ 6. Diagrama de Arquitetura

O diagrama abaixo representa o fluxo de ponta a ponta, incluindo as APIs de IA e o ponto de coleta de métricas.

📁 Arquivo original do diagrama:  
[`diagram_final.drawio`](./diagram_final.drawio)

Arquitetura Totem de IA![`desenho de arquitetura`](diagram_final.png)

---

## 🧩 7. Siglas Técnicas

| Sigla | Nome Completo | Função |
|--------|----------------|--------|
| **STT** | Speech-to-Text | Converte fala em texto |
| **LLM** | Large Language Model | Interpreta e gera respostas textuais |
| **TTS** | Text-to-Speech | Converte texto em fala |

---

## 🧠 8. Equipe

| Nome | Função |
|------|---------|
| **Alan Robin** | Backend & Cloud Specialist |
| **Lucas Amorim** | Hardware & Firmware Specialist |

---

## 🏁 9. Licença
Projeto acadêmico desenvolvido no contexto do **Challenge FIAP 2025**, não destinado a uso comercial.

---

> _“Transformando curiosidade em interação com o poder da Inteligência Artificial.”_
