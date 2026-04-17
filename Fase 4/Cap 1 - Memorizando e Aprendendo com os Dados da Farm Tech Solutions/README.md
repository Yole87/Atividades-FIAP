# FIAP - Faculdade de Informática e Administração Paulista

# Fase 4 (Cap 1): Assistente Agrícola Inteligente

## 👨‍🎓 Integrantes: 
- **Nome:** Alan Robin Santos - **RM:** 567437
- **Nome:** Lucas Alberto da Silva Amorim - **RM:** 567505

## 👩‍🏫 Professores:
### Tutor(a) 
- [Sabrina Otoni]
### Coordenador(a)
- [André Godoi]

## 📜 Descrição

Este projeto representa a consolidação da inteligência da **FarmTech Solutions**. Desenvolvemos um **Dashboard Analítico Interativo** que utiliza Machine Learning para apoiar a tomada de decisão no campo.

O sistema simula um ambiente de IoT (sensores) e utiliza um modelo de **Regressão (Random Forest)** treinado com dados históricos para prever a umidade do solo em tempo real e sugerir ações automáticas de irrigação e fertilização.

**Funcionalidades Principais:**
1.  **Previsão de Umidade:** Uma Inteligência Artificial analisa Temperatura, Chuva e pH para estimar a umidade atual do solo.
2.  **Sistema de Recomendação:**
    * **Irrigação:** Sugere ligar/desligar a bomba baseado na previsão da IA (e não apenas em regras fixas). Se a umidade prevista cair abaixo de 40%, o sistema emite um alerta crítico.
    * **Nutrição:** Monitora os níveis de Nitrogênio (N), Fósforo (P) e Potássio (K) e alerta sobre deficiências específicas.
3.  **Interface Visual:** Dashboard interativo construído com **Streamlit**, exibindo KPIs, gráficos de dispersão e métricas de performance do modelo (R², MAE, MSE) em tempo real.

## 📁 Estrutura de pastas
GitHub
https://github.com/Yole87/Atividades-FIAP/tree/FIAP_IA_Online/Fase%204/Cap%201%20-%20Memorizando%20e%20Aprendendo%20com%20os%20Dados%20da%20Farm%20Tech%20Solutions

- <b><code>dashboard_farmtech.py</code></b>: A aplicação principal (Streamlit). Contém a interface do usuário, o treinamento do modelo de Machine Learning e a lógica de decisão para irrigação.
- <b><code>gerar_dataset.py</code></b>: Script auxiliar responsável por criar a massa de dados históricos simulados (CSV). Ele utiliza uma lógica agronômica realista (ex: chuva aumenta umidade, calor diminui) para treinar a IA corretamente.
- <b><code>dados_historicos_irrigacao.csv</code></b>: O dataset gerado, contendo 1000 registros de condições climáticas e de solo.
- <b><code>db_operations.py</code></b>: Módulo de conexão com Oracle (herdado da Fase 3 para manter a integridade do sistema).
- <b><code>README.md</code></b>: Este arquivo de documentação.

## 🔧 Como executar o código

### Pré-requisitos
- Python 3.x instalado.
- Bibliotecas necessárias: `streamlit`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`.

### 1. Instalação das Dependências
No terminal, dentro da pasta do projeto, execute:
```bash
pip install streamlit pandas scikit-learn matplotlib seaborn
```

### 2. Geração de Dados (Treinamento)
Antes de iniciar o dashboard, é necessário garantir que o modelo tenha dados para aprender. Execute o script gerador:
```bash
python gerar_dataset.py
```
*Isso criará o arquivo `dados_historicos_irrigacao.csv` com a lógica realista implementada.*

### 3. Executar o Dashboard
Inicie a aplicação web com o comando do Streamlit:
```bash
streamlit run dashboard_farmtech.py
```
O navegador abrirá automaticamente no endereço local (geralmente `http://localhost:8501`), exibindo o painel de controle.

---

## 👨‍💻 Autor

* **Nome:** Alan Robin Santos - **RM:** 567437
* **Nome:** Lucas Alberto da Silva Amorim - **RM:** 567505