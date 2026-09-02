# FIAP - Faculdade de Informática e Administração Paulista

# Fase 5 (Cap 1): FarmTech na Era da Cloud Computing

## 👨‍🎓 Integrantes: 
- **Nome:** Alan Robin Santos - **RM:** 567437
- **Nome:** Lucas Alberto da Silva Amorim - **RM:** 567505

## 👩‍🏫 Professores:
### Tutor(a) 
- [Sabrina Otoni]
### Coordenador(a)
- [André Godoi]

## 📜 Descrição

Este projeto representa a evolução da **FarmTech Solutions**. Após a consolidação do painel interativo na Fase 4, a plataforma agora dá um salto de maturidade técnica: substituímos dados simulados por dados reais de safra e preparamos nossa infraestrutura de Inteligência Artificial para operar na nuvem (Cloud Computing).

O projeto é dividido em duas frentes tecnológicas principais: **Machine Learning Avançado** (identificação de padrões e testes múltiplos de regressão) e **Arquitetura AWS** (estimativa de viabilidade técnica e financeira para hospedagem da solução).

---

## 🚀 Entregas e Funcionalidades Principais

### 🤖 Entrega 1: Inteligência de Dados (Machine Learning)
1. **Análise Exploratória (EDA):** Mapeamento de correlações climáticas (Temperatura, Umidade, Chuva) com o rendimento da safra através de Mapas de Calor (Heatmaps).
2. **Clusterização (Aprendizado Não Supervisionado):** Utilização do algoritmo **K-Means** para segmentar as fazendas em 3 perfis de produtividade, permitindo identificar tendências climáticas e *outliers* (cenários de risco que fogem do padrão).
3. **Batalha de Algoritmos (Preditivo):** Treinamento e avaliação simultânea de 5 modelos de regressão:
   - *Regressão Linear, Árvore de Decisão, Random Forest, Gradient Boosting e SVR.*
   - **O Campeão:** Após aplicarmos a técnica de *One-Hot Encoding* para ensinar ao modelo as categorias das culturas agrícolas, o modelo de **Regressão Linear** assumiu a liderança com um impressionante R² de **99.50%**. A Árvore de Decisão e Random Forest também mantiveram precisões acima de 99%, provando a alta qualidade do dataset tratado.
4. **Deploy Ready:** O modelo vencedor foi exportado em formato binário (`.joblib`), permitindo sua execução rápida em servidores via API sem necessidade de retreinamento.

### ☁️ Entrega 2: Estratégia de Cloud Computing (AWS)
Planejamento da infraestrutura para hospedar a API de Machine Learning e processar os dados dos sensores IoT.
- **Configuração da Instância (EC2):** Linux, 2 vCPUs, 1 GiB de RAM, Rede até 5 Gigabit, Armazenamento EBS de 50 GB. (Estratégia: On-Demand 100%).
- **Comparativo Financeiro:**
  - 🇺🇸 **US East (N. Virginia):** US$ 10.13 / mês - [Orçamento Virgínia](<Orçamento_Servidor_AWS_Virgínia do Norte (EUA).pdf>)
  - 🇧🇷 **South America (São Paulo):** US$ 17.38 / mês - [Orçameto SP](<Orçamento_Servidor_AWS_São Paulo (BR).pdf>)
- **Decisão Arquitetural:** Optamos por hospedar os servidores em **São Paulo (sa-east-1)**. Apesar do custo ligeiramente maior, garantimos **latência ultrabaixa** para comunicação em tempo real com os sensores nas fazendas brasileiras e garantimos total conformidade legal com a **LGPD** (manutenção de dados confidenciais em território nacional).
- 💡 **Visão de Futuro:** Em cenário de operação escalada, migraremos do modelo *On-Demand* para os planos de *Savings Plans (Convertible)*, garantindo grandes descontos mediante contratos de 1 a 3 anos com a AWS, mantendo a flexibilidade de trocar a família da máquina no futuro.

---

## 🎥 Apresentação em Vídeo

- **Vídeo Explicação do Código e Modelos e Estimativa de Custos AWS :** [Video YouTube](https://youtu.be/iliNkw9J9LQ)

---

## 📁 Estrutura de Pastas e Arquivos

- <b><code>AlanRobin_rm567437_LucasAmorin_rm567505_pbl_fase4.ipynb</code></b>: Notebook Jupyter principal contendo toda a Análise Exploratória, K-Means, treinamento dos 5 modelos e as métricas de validação.
- <b><code>crop_yield.csv</code></b>: O dataset com dados reais das safras utilizado para treinar os algoritmos.
- <b><code>melhor_modelo_farmtech.joblib</code></b>: Arquivo binário gerado automaticamente contendo o modelo vencedor (Gradient Boosting) pronto para produção.
- <b><code>print_virginia.png</code></b> / <b><code>print_sp.png</code></b>: Imagens comprobatórias da cotação realizada na calculadora oficial da AWS.
- <b><code>README.md</code></b>: Este arquivo de documentação.

---

## 🔧 Como executar o código

### Pré-requisitos
- Python 3.13.x instalado.
- Visual Studio Code com a extensão "Jupyter" instalada.

### 1. Instalação das Dependências
Abra o terminal do seu VS Code na pasta do projeto e instale as bibliotecas científicas necessárias:
```bash
pip install pandas seaborn matplotlib scikit-learn joblib
```

### 2. Executando o Notebook
Abra o arquivo <b><code>AlanRobin_rm567437_LucasAmorin_rm567505_pbl_fase4.ipynb</code></b> no VS Code. [Atalho aqui](AlanRobin_rm567437_LucasAmorin_rm567505_pbl_fase4.ipynb)

No canto superior direito, clique em "Select Kernel" -> "Python Environments" e escolha o seu Python Global (o mesmo onde as dependências foram instaladas).

Clique em "Run All" (ou execute as células uma a uma com Ctrl + Enter).

Os gráficos (Heatmap e Clusterização) serão renderizados diretamente na tela, e o "boletim" com as notas dos 5 modelos será impresso no final, gerando o arquivo .joblib automaticamente.

👨‍💻 Autores

Nome: Alan Robin Santos - RM: 567437

Nome: Lucas Alberto da Silva Amorim - RM: 567505