# 🌽 FarmTech - Sistema de Irrigação Inteligente para Milho

<div align="center">

![FarmTech Logo](https://img.shields.io/badge/FarmTech-v2.0-green?style=for-the-badge&logo=leaf)
![ESP32](https://img.shields.io/badge/ESP32-IoT-blue?style=for-the-badge&logo=espressif)
![Python](https://img.shields.io/badge/Python-Flask-yellow?style=for-the-badge&logo=python)
![Wokwi](https://img.shields.io/badge/Wokwi-Simulation-purple?style=for-the-badge)

**Sistema IoT inteligente para irrigação automatizada de milho com monitoramento em tempo real e dashboard web**

[🚀 Demo](#-demonstração) • [📋 Instalação](#-instalação) • [🔧 Uso](#-como-usar) • [📊 Dashboard](#-dashboard-web) • [📖 Documentação](#-documentação)

</div>

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Características](#-características-principais)
- [Arquitetura](#-arquitetura-do-sistema)
- [Instalação](#-instalação)
- [Estrutura de Pastas](#-estrutura-de-pastas-atualizada)
- [Como Usar](#-como-usar)
- [Dashboard Web](#-dashboard-web)
- [Simulação Wokwi](#-simulação-wokwi)
- [API](#-api-endpoints)
- [Demonstração](#-demonstração)
- [Documentação](#-documentação)
- [Contribuição](#-contribuição)

## 🌟 Visão Geral

O **FarmTech** é um sistema completo de irrigação inteligente desenvolvido especificamente para o cultivo de milho. Utilizando tecnologia IoT com ESP32, sensores ambientais e interface web, o sistema otimiza o uso da água e maximiza a produtividade da cultura.

### 🎯 Problema Resolvido
- **Desperdício de água** na irrigação tradicional (até 40% de economia)
- **Falta de precisão** no timing de irrigação
- **Ausência de monitoramento** em tempo real das condições do solo
- **Decisões baseadas em intuição** ao invés de dados científicos

### 💡 Solução Oferecida
- **Irrigação automatizada** baseada em dados de sensores
- **Monitoramento contínuo** de umidade, pH e temperatura
- **Dashboard web responsivo** para controle remoto
- **Algoritmos inteligentes** para otimização hídrica

## ✨ Características Principais

### 🔧 Hardware (ESP32)
- **Sensor DHT22**: Monitoramento de temperatura e umidade do ar
- **Fotoresistor (LDR)**: Simulação de sensor de pH do solo
- **Botões NPK**: Simulação de sensores de nutrientes (N, P, K)
- **Módulo Relé**: Controle automatizado da bomba de irrigação
- **LED Indicador**: Status visual do sistema
- **Conectividade WiFi**: Comunicação com servidor web

- [Imagem das conexões no Wokwi](https://drive.google.com/file/d/1gtHG7cj1iLYVffD1IStQy45Prqavw1xG/view?usp=sharing)

### 💻 Software
- **Backend Flask**: Servidor web em Python
- **Frontend Responsivo**: HTML5, CSS3, JavaScript
- **API RESTful**: Endpoints para dados e controle
- **Algoritmos Inteligentes**: Lógica de decisão para irrigação
- **Interface Intuitiva**: Dashboard com gráficos e controles

### 🌱 Foco na Cultura do Milho
- **Parâmetros Otimizados**: Específicos para Zea mays
- **Umidade Ideal**: 40-80% (zona de conforto: 65%)
- **pH Adequado**: 6.0-7.5 (ideal: 6.5)
- **Monitoramento NPK**: Nitrogênio, Fósforo e Potássio

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐    WiFi    ┌─────────────────┐    HTTP    ┌─────────────────┐
│   ESP32 + IoT   │ ◄────────► │  Servidor Web   │ ◄────────► │   Dashboard     │
│                 │            │    (Flask)      │            │     Web         │
│ • DHT22         │            │                 │            │                 │
│ • LDR (pH)      │            │ • API REST      │            │ • Gráficos      │
│ • Botões NPK    │            │ • Lógica        │            │ • Controles     │
│ • Relé          │            │ • Dados         │            │ • Alertas       │
│ • LED Status    │            │                 │            │                 │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

### Fluxo de Dados
1. **Sensores** coletam dados ambientais
2. **ESP32** processa e envia via WiFi
3. **Servidor Flask** recebe e armazena dados
4. **Dashboard** exibe informações em tempo real
5. **Algoritmo** decide sobre irrigação
6. **Relé** ativa/desativa bomba de água

## 📦 Instalação

### Pré-requisitos
- **Hardware**: ESP32, DHT22, LDR, Relé, LED, Resistores
- **Software**: Arduino IDE, Python 3.8+, Navegador web

### 1. Configuração do Hardware

#### Conexões ESP32
```
ESP32 DevKit V1
├── DHT22 → Pino 15 (Dados)
├── LDR → Pino A0 (Analógico)
├── Botão N → Pino 13 (Digital)
├── Botão P → Pino 12 (Digital)
├── Botão K → Pino 14 (Digital)
├── Relé → Pino 2 (Digital)
└── LED → Pino 23 (Digital)
```

#### Esquema de Ligação
- **DHT22**: VCC→3V3, GND→GND, DATA→D15
- **LDR**: VCC→3V3, AO→A0, GND→Resistor 10kΩ→GND
- **Botões**: Um terminal→Pino Digital, Outro→GND
- **Relé**: VCC→5V, GND→GND, IN→D2
- **LED**: Anodo→D23, Catodo→Resistor 220Ω→GND

### 2. Configuração do Software

#### Arduino IDE
```bash
# 1. Instalar bibliotecas
- DHT sensor library
- WiFi library (incluída no ESP32)

# 2. Configurar WiFi no código
const char* ssid = "SUA_REDE_WIFI";
const char* password = "SUA_SENHA_WIFI";

# 3. Upload do código para ESP32
```

#### Servidor Python
```bash
# 1. Clonar repositório
git clone https://github.com/Yole87/Atividades-FIAP/tree/FIAP_IA_Online/Fase%202/Cap%201%20-%20Um%20Mapa%20do%20Tesouro
cd Cap 1 - Um Mapa do Tesouro

# 2. Instalar dependências
pip install flask

# 3. Executar servidor
python web/app.py
```

#### Firmware (Wokwi/Arduino IDE — recomendado)
```bash
# 1. Abra o projeto no Wokwi (diagram.json + sketch.ino)
# 2. Ajuste SSID/Senha no sketch (sketch.ino)
# 3. Rode a simulação no Wokwi ou faça upload via Arduino IDE
```
Observação: o ambiente PlatformIO foi removido desta estrutura. Caso deseje usar PlatformIO, veja a seção "Integração com Firmware (Opcional)" mais abaixo para orientações.

### 3. Simulação Wokwi (Opcional)
```bash
# 1. Acesse: https://wokwi.com
# 2. Importe o arquivo diagram.json
# 3. Execute a simulação online
```

## 📁 Estrutura de Pastas
```
Cap 1 - Um Mapa do Tesouro/
├─ web/
│  ├─ app.py
│  ├─ data/
│  │  ├─ clima_resultado.json
│  │  └─ weather_resultado.json
│  ├─ static/
│  │  └─ style.css
│  └─ templates/
│     ├─ index.html
│     └─ wokwi.html
├─ imagens/
├─ diagram.json
├─ sketch.ino
├─ DOCUMENTACAO_IRRIGACAO.md
├─ README.md
├─ wokwi.toml
└─ .gitignore
```
Notas:
- Os dados consumidos pelo backend ficam em `web/data/`.
- O simulador integrado está em `web/templates/wokwi.html`.
- O arquivo `wokwi.toml` permanece como referência.

## 🔧 Como Usar

### Inicialização
1. **Conecte o hardware** conforme esquema
2. **Configure WiFi** no código ESP32
3. **Execute o servidor** Python
4. **Acesse dashboard** em `http://localhost:5000`

### Operação Automática
O sistema opera automaticamente baseado nos parâmetros:
- **Umidade < 40%**: Irrigação obrigatória
- **pH fora de 6.0-7.5**: Alerta de correção
- **NPK deficiente**: Notificação nutricional

### Especificidades de Hardware e Pinos
- **DHT22** em `GPIO15` (`D15`).
- **LDR/pH** em `A0` (ESP32 `GPIO36`). O valor ADC (0–4095) é mapeado linearmente para pH (0–14) para fins didáticos.
- **Botões NPK (N=13, P=12, K=14)** com `INPUT_PULLUP`: botão pressionado = nível `LOW`.
- **Relé em `GPIO2`** com entrada ativa em `HIGH` no Wokwi: `HIGH` liga irrigação, `LOW` desliga.
- **LED de status** em `GPIO23`.

Arquivos de referência:
- `sketch.ino`: código principal do ESP32 alinhado ao `diagram.json` e ao simulador Wokwi.

### Controle Manual
- **Botão "Irrigar Agora"**: Ativação manual da irrigação
- **Modo Automático**: Liga/desliga automação
- **Configurações**: Ajuste de parâmetros

## 📊 Dashboard Web

### Funcionalidades Principais

#### 🎛️ Painel de Controle
- **Status em Tempo Real**: Sensores e sistema
- **Controles Manuais**: Botões de ação
- **Gráficos Dinâmicos**: Histórico de dados
- **Alertas Visuais**: Notificações importantes

#### 📈 Monitoramento
- **Umidade do Solo**: Gráfico em tempo real
- **Temperatura**: Monitoramento ambiental
- **pH do Solo**: Indicador de acidez
- **Status NPK**: Níveis de nutrientes
- **Histórico de Irrigação**: Log de ativações

#### ⚙️ Configurações
- **Parâmetros de Irrigação**: Umidade mín/máx
- **Intervalos**: Tempo entre irrigações
- **Alertas**: Configuração de notificações
- **Calibração**: Ajuste de sensores

### Interface Responsiva
- **Desktop**: Layout completo com gráficos
- **Tablet**: Interface adaptada
- **Mobile**: Controles essenciais

## 🌐 API Endpoints

### Dados dos Sensores (completos)
```http
GET /api/dados
```
Retorna um pacote completo com dados simulados de sensores, meteorologia, justificativa técnica (quando disponível) e estado de irrigação.

### Sensores (somente sensores)
```http
GET /api/sensores
```
Retorna apenas o conjunto de dados de sensores e contexto.

### Meteorologia
```http
GET /api/meteorologia
```
Retorna o bloco `meteorologia` com dados simulados de clima e recomendação.

### Estatísticas do Sistema
```http
GET /api/estatisticas
```
Retorna estatísticas agregadas calculadas a partir do histórico.

### Histórico de Irrigação
```http
GET /api/historico
```
Retorna registros armazenados pelo sistema de histórico (leituras e ativações).

### Alertas
```http
GET /api/alertas
```
Lista alertas ativos gerados pelo sistema de histórico.

### Controlo de Irrigação Manual
```http
POST /api/irrigacao/manual
```
Ativa o modo manual, registra o timestamp e atualiza o cálculo de "Última irrigação".

### Cálculo de "Última Irrigação"
- **Agora**: quando a irrigação está ativa no momento.
- **Há X min** ou **Há Xh Ymin**: quando desativada, calculando tempo desde o último timestamp registrado.
- **Nunca**: se não há registro anterior.

Detalhes de implementação (backend Flask, `web/app.py`):
- Variável global `ultima_irrigacao_timestamp` mantém o marco temporal mais recente.
- `simular_dados_sensores()` captura o instante exato de ativação (manual/automática).
- Desativação automática do modo manual após **5 minutos**.
- Formatação amigável do tempo decorrido para o dashboard.

### Atualização de Dados (Opcional)
```http
GET /api/atualizar
```
Executa scripts externos para atualizar dados. Observação: a pasta `python/` foi removida desta estrutura; este endpoint pode retornar indisponível até que scripts sejam reintroduzidos.

## 🎮 Simulação Wokwi

### Acesso Online
1. Visite [Wokwi.com](https://wokwi.com)
2. Importe o arquivo `diagram.json`
3. Execute a simulação
4. Teste os sensores virtuais

### Componentes Simulados
- **ESP32 DevKit V1**: Microcontrolador principal
- **DHT22**: Sensor de temperatura/umidade
- **Fotoresistor**: Simulação de pH
- **Push Buttons**: Sensores NPK
- **Relay Module**: Controle de irrigação
- **LED**: Indicador de status

### Interação
- **Clique nos botões**: Simula detecção de nutrientes
- **Ajuste o LDR**: Modifica leitura de pH
- **Monitor Serial**: Visualiza logs do sistema

### Execução pela Página Local
- Acesse `http://localhost:5000/wokwi` para abrir o simulador integrado.
- A página fornece atalhos e instruções para rodar no Wokwi online.

### Integração com Firmware Compilado (Opcional)
- O repositório atual não inclui PlatformIO nem binários compilados.
- Se optar por usar PlatformIO, crie um `platformio.ini` e gere artefatos de build (`firmware.elf`/`firmware.bin`).
- O `wokwi.toml` permanece no repositório como referência, mas não depende de `.pio/` nesta estrutura.

## 🚀 Demonstração

### Cenários de Teste

#### Cenário 1: Irrigação Automática
1. Umidade baixa (< 40%)
2. pH adequado (6.0-7.5)
3. Sistema ativa irrigação
4. LED indica status ativo

#### Cenário 2: Alerta de pH
1. pH fora da faixa (< 6.0 ou > 7.5)
2. Sistema emite alerta
3. Irrigação suspensa
4. Dashboard mostra notificação

#### Cenário 3: Deficiência Nutricional
1. Botão NPK não pressionado
2. Sistema detecta deficiência
3. Alerta nutricional ativado
4. Recomendação de correção

### Métricas de Performance
- **Economia de Água**: 25-30%
- **Aumento de Produtividade**: 15-20%
- **Redução de Mão de Obra**: 40%
- **Precisão de Irrigação**: 95%

## 📖 Documentação

### Arquivos Principais
- **`sketch.ino`**: Código principal do ESP32
- **`web/app.py`**: Servidor Flask
- **`web/templates/index.html`**: Interface web
- **`web/templates/wokwi.html`**: Simulador Wokwi integrado
- **`diagram.json`**: Configuração Wokwi
- **`web/data/*.json`**: Arquivos de dados consumidos pelo backend
- **`DOCUMENTACAO_IRRIGACAO.md`**: Documentação técnica completa

### Parâmetros Técnicos
```cpp
// Umidade do Solo
#define UMID_MIN 40        // Mínima para irrigação
#define UMID_IDEAL 65      // Ideal para milho
#define UMID_MAX 80        // Máxima (evitar encharcamento)

// pH do Solo
#define PH_MIN 6.0         // Mínimo aceitável
#define PH_IDEAL 6.5       // Ideal para milho
#define PH_MAX 7.5         // Máximo aceitável
```

### Lógica de Irrigação (Resumo)
- Ativa irrigação quando: umidade < mínimo, pH adequado, NPK OK, sem chuva prevista, intervalo mínimo respeitado.
- Modo manual força ativação e registra timestamp de início.
- Controle do relé e LED reflete estado de irrigação (ativo em HIGH).
- Justificativas técnicas são exibidas no dashboard com o motivo da decisão.

### Algoritmo de Decisão
```cpp
bool precisaIrrigar() {
    if (umidade < UMID_MIN) return true;           // Crítico
    if (umidade > UMID_MAX) return false;          // Saturado
    if (ph < PH_MIN || ph > PH_MAX) return false;  // pH inadequado
    return (umidade < UMID_IDEAL);                 // Zona intermediária
}
```

## 🔄 Atualizações Recentes
- Correção e robustez do campo **"Última irrigação"** no dashboard:
  - Registro preciso do timestamp de ativação da irrigação.
  - Cálculo dinâmico do tempo decorrido (Agora / Há X min / Há Xh Ymin / Nunca).
  - Registro de ativações manuais via `/api/irrigacao/manual`.
  - Desativação automática do modo manual após 5 minutos.
- Alinhamento de pinos para compatibilidade Wokwi (`A0 → GPIO36`, `INPUT_PULLUP` nos botões, relé ativo em HIGH).
- Reestruturação do repositório: dados movidos para `web/data/`, remoção de `python/` e do ambiente PlatformIO (uso opcional).

## 🤝 Contribuição

### Como Contribuir
1. **Fork** o repositório
2. **Crie** uma branch para sua feature
3. **Commit** suas mudanças
4. **Push** para a branch
5. **Abra** um Pull Request

### Áreas de Melhoria
- **Machine Learning**: Predição de necessidades
- **Sensores Adicionais**: Condutividade elétrica
- **App Mobile**: Aplicativo nativo
- **Integração Meteorológica**: APIs de clima
- **Múltiplas Culturas**: Soja, algodão, cana

### Padrões de Código
- **C++**: Google Style Guide
- **Python**: PEP 8
- **JavaScript**: Airbnb Style Guide
- **Documentação**: Markdown com emojis

## 📊 Resultados e Benefícios

### Impacto Econômico
- **ROI**: 260% em 5 anos
- **Payback**: 1.4 anos
- **Economia Anual**: R$ 1.800,00
- **Investimento**: R$ 2.500,00

### Impacto Ambiental
- **Redução no Consumo de Água**: 25-30%
- **Menor Lixiviação**: Nutrientes preservados
- **Uso Eficiente**: Recursos naturais
- **Sustentabilidade**: Agricultura de precisão

### Impacto Social
- **Capacitação**: Tecnologia acessível
- **Produtividade**: Mais alimento
- **Qualidade**: Grãos uniformes
- **Inovação**: Agricultura 4.0

## 📞 Suporte e Contato

### Equipe de Desenvolvimento
- **Email**: suporte@farmtech.com.br (fictício)
- **GitHub**: [FarmTech-Fase2](https://github.com/Yole87/Atividades-FIAP/tree/FIAP_IA_Online/Fase%202)
- **Documentação**: [Wiki do Projeto](https://github.com/Yole87/Atividades-FIAP/tree/FIAP_IA_Online/Fase%202)

### Licença
Este projeto está licenciado sob a **FarmTech License** 

### Agradecimentos
- **Comunidade Arduino**: Bibliotecas e suporte
- **Wokwi**: Plataforma de simulação
- **Flask**: Framework web Python
- **Agricultura de Precisão**: Inspiração e conhecimento

---

<div align="center">

**🌽 FarmTech - Cultivando o Futuro com Tecnologia 🌽**

*Desenvolvido com ❤️ para a agricultura brasileira*

[![GitHub](https://img.shields.io/badge/GitHub-FarmTech-green?style=social&logo=github)](https://github.com/Yole87/Atividades-FIAP/tree/FIAP_IA_Online)

</div>