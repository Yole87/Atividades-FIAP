# FIAP - Faculdade de Informática e Administração Paulista

[![FIAP - Faculdade de Informática e Admnistração Paulista](https://github.com/agodoi/templateFiapVfinal/raw/main/assets/logo-fiap.png)](https://www.fiap.com.br/)

# CardioIA — Fase 1: A Busca de Dados

## Grupo CardioIA

## 👨‍🎓 Integrantes:

- Alan Robin Santos RM: 567437
- Lucas Alberto da Silva Amorim RM: 567505

## 👩‍🏫 Professores:

### Tutor(a)

- Leonardo Ruiz Orabona

### Coordenador(a)

- Andre Godoi

## 📜 Descrição

O **CardioIA** é um projeto acadêmico que simula o ecossistema de uma clínica de cardiologia moderna, integrando dados clínicos, modelos de Machine Learning, Visão Computacional, IoT e agentes inteligentes para lidar com triagem, diagnósticos, monitoramento, assistência remota e previsões médicas.

Nesta **Fase 1 — Batimentos de Dados**, assumimos o papel de cientistas de dados hospitalares. O objetivo é levantar, organizar e documentar três tipos de dados fundamentais que alimentarão os módulos inteligentes do CardioIA nas fases seguintes:

**Parte 1 — Dados Numéricos (IoT):** Utilizamos o Cleveland Heart Disease Dataset, disponibilizado pelo UCI Machine Learning Repository, com 297 linhas válidas e 14 variáveis clínicas como idade, sexo, pressão arterial, colesterol, frequência cardíaca e diagnóstico de doença cardíaca. Os dados são reais, coletados em ambiente hospitalar, e servirão para treinar modelos preditivos de risco cardiovascular.

**Parte 2 — Dados Textuais (NLP):** Coletamos dois artigos científicos dos Arquivos Brasileiros de Cardiologia (SciELO): a Estatística Cardiovascular Brasil 2023 e um estudo sobre Estratégia Fármaco-Invasiva no Infarto do Miocárdio. Esses textos serão explorados por algoritmos de NLP para extração de entidades médicas, classificação de tópicos, sumarização automática e identificação de sintomas para triagem digital.

**Parte 3 — Dados Visuais (Visão Computacional):** Reunimos 234 imagens de raio-X torácico da classe NORMAL, provenientes do Chest X-Ray Images Dataset (Kaggle/Guangzhou Women and Children's Medical Center). Essas imagens estabelecem a linha de base para que modelos de Visão Computacional identifiquem anomalias cardiopulmonares como cardiomegalia, derrame pleural e congestão pulmonar nas fases seguintes.

A coleta considerou os princípios de Governança de Dados em IA, identificando vieses presentes nos datasets (geográfico, de gênero e temporal) que deverão ser mitigados nas fases seguintes do projeto.

---

## 📁 Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- **assets**: aqui estão as imagens de raio-X torácico utilizadas na Parte 3 — Dados Visuais. Na subpasta `imagens_raio_x`, encontram-se as 234 imagens `.jpeg` da classe NORMAL.

- **docs**: aqui estão os arquivos de texto utilizados na Parte 2 — Dados Textuais. Contém os dois artigos científicos em formato `.txt` obtidos do SciELO.

- **notebooks**: pasta reservada para os notebooks Jupyter/Colab que serão desenvolvidos nas fases seguintes do CardioIA para consumir e processar os dados coletados.

- **heart_disease_cleveland.csv**: dataset numérico principal com 297 linhas e 14 variáveis clínicas de pacientes cardíacos, utilizado na Parte 1 — Dados Numéricos.

- **README.md**: arquivo que serve como guia e explicação geral sobre o projeto (o mesmo que você está lendo agora).

```
Fase 1/
├── README.md
├── heart_disease_cleveland.csv
├── docs/
│   ├── texto1_estatistica_cardiovascular_brasil_2023.txt
│   └── texto2_infarto_miocardio_sintomas_mortalidade.txt
├── assets/
│   └── imagens_raio_x/
│       └── (234 imagens .jpeg de raio-X torácico)
└── notebooks/
    └── (notebooks Jupyter/Colab das fases seguintes)
```

---

## 📊 Parte 1 — Dados Numéricos (IoT)

### Fonte dos Dados

Utilizamos o **Cleveland Heart Disease Dataset**, disponibilizado pelo **UCI Machine Learning Repository** — uma das fontes acadêmicas mais respeitadas no campo de IA aplicada à saúde, amplamente utilizada em pesquisas e publicações científicas desde 1988.

- 🔗 **Fonte original:** [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/45/heart+disease)
- 🔗 **Download do dataset tratado:** [heart_disease_cleveland.csv — Google Drive](https://drive.google.com/file/d/1mG9rDA_t4UILysb804DoJHQonTE7ucN7/view?usp=sharing)
- 📁 **Formato:** `.csv`
- 📏 **Volume:** 297 linhas válidas × 14 colunas

> Os dados são **reais**, coletados em ambiente hospitalar. Das 303 linhas originais, 6 foram removidas por conterem valores ausentes, o que é esperado em dados clínicos reais e faz parte do processo de governança e limpeza de dados em projetos de IA.

### Variáveis do Dataset

| Variável | Descrição | Tipo |
|---|---|---|
| `age` | Idade do paciente (anos) | Numérico |
| `sex` | Sexo (1 = masculino, 0 = feminino) | Categórico |
| `cp` | Tipo de dor no peito (1 a 4) | Categórico |
| `trestbps` | Pressão arterial em repouso (mmHg) | Numérico |
| `chol` | Colesterol sérico (mg/dl) | Numérico |
| `fbs` | Glicemia em jejum > 120 mg/dl (1 = sim) | Categórico |
| `restecg` | Resultado do ECG em repouso (0 a 2) | Categórico |
| `thalach` | Frequência cardíaca máxima atingida | Numérico |
| `exang` | Angina induzida por exercício (1 = sim) | Categórico |
| `oldpeak` | Depressão do segmento ST pelo exercício | Numérico |
| `slope` | Inclinação do segmento ST no pico | Categórico |
| `ca` | Número de vasos principais coloridos por fluoroscopia | Numérico |
| `thal` | Talassemia (3 = normal, 6 = fixo, 7 = reversível) | Categórico |
| `target` | Diagnóstico de doença cardíaca (0 = ausente, 1-4 = presente) | Categórico |

### Variáveis Mais Relevantes e Justificativa Clínica

**1. `target` — Variável alvo**  
É a variável que os modelos de IA irão aprender a prever. Indica a presença ou ausência de doença cardíaca, sendo o centro de todo o projeto preditivo.

**2. `cp` — Tipo de dor no peito**  
A dor torácica é um dos sintomas mais importantes na triagem cardiológica. Sua classificação (típica, atípica, não-anginosa ou assintomática) tem alta correlação com o diagnóstico de doença cardíaca.

**3. `thalach` — Frequência cardíaca máxima**  
Pacientes com doença cardíaca frequentemente apresentam frequência cardíaca máxima reduzida durante esforço. Essa variável é essencial para modelos de monitoramento em tempo real via IoT.

**4. `trestbps` — Pressão arterial em repouso**  
A hipertensão é um dos principais fatores de risco cardiovascular. Pressão elevada em repouso sinaliza risco aumentado de eventos cardíacos.

**5. `chol` — Colesterol sérico**  
Níveis elevados de colesterol estão diretamente associados à aterosclerose, principal causa de infarto do miocárdio. É uma variável fundamental em qualquer modelo preditivo cardiovascular.

**6. `age` e `sex`**  
Idade e sexo são determinantes clássicos de risco cardiovascular. Homens acima de 45 anos e mulheres acima de 55 anos têm risco significativamente maior, o que torna essas variáveis indispensáveis em qualquer análise.

**7. `exang` — Angina induzida por exercício**  
A angina ao esforço é um sinal clínico direto de isquemia miocárdica — condição em que o coração não recebe oxigênio suficiente. Variável de alto valor preditivo.

### Considerações sobre Governança de Dados e Viés

Este dataset, embora robusto academicamente, apresenta **limitações que devem ser consideradas em projetos de IA responsável**:

- **Viés de gênero:** a maioria dos pacientes é do sexo masculino, o que pode prejudicar a performance do modelo para mulheres
- **Viés geográfico:** os dados são provenientes exclusivamente de Cleveland (EUA), não representando a população brasileira
- **Dados históricos:** coletados na década de 1980, podendo não refletir o perfil atual de pacientes cardíacos

Essas questões de governança serão consideradas nas fases seguintes ao treinar e avaliar os modelos de IA.

---

## 📝 Parte 2 — Dados Textuais (NLP)

Os textos foram obtidos dos **Arquivos Brasileiros de Cardiologia (ABC Cardiol)**, publicação científica indexada no SciELO. Os arquivos estão disponíveis na pasta `docs/` do repositório e também hospedados no Google Drive para acesso direto.

### Texto 1 — Estatística Cardiovascular Brasil 2023

- **Arquivo:** `docs/texto1_estatistica_cardiovascular_brasil_2023.txt`
- **Fonte:** Arquivos Brasileiros de Cardiologia, Vol. 121, Nº 2, Fev. 2024
- **DOI:** 10.36660/abc.20240079
- **Link SciELO:** [Estatística Cardiovascular Brasil 2023](https://www.scielo.br/j/abc/a/jzFMcdN5y3w6CtjVgdJdSdR/?lang=pt)
- **Link Drive:** [texto1_estatistica_cardiovascular_brasil_2023.txt](https://drive.google.com/file/d/1zarzA6NWpioNbuoUqtj6N0xe3rk593uP/view?usp=sharing)

Documento de referência nacional sobre epidemiologia cardiovascular no Brasil, compilando dados do Ministério da Saúde, GBD e diversas coortes. Abrange mortalidade, incidência, prevalência e custos de doenças como infarto, AVC, insuficiência cardíaca e hipertensão.

### Texto 2 — Estratégia Fármaco-Invasiva no Infarto do Miocárdio

- **Arquivo:** `docs/texto2_infarto_miocardio_sintomas_mortalidade.txt`
- **Fonte:** Arquivos Brasileiros de Cardiologia, Vol. 119, Nº 5, 2022
- **DOI:** 10.36660/abc.20211055
- **Link SciELO:** [Infarto do Miocárdio: Sintomas e Mortalidade](https://www.scielo.br/j/abc/a/t5HQYqt97zKc6wPfxQFscxh/?lang=pt)
- **Link Drive:** [texto2_infarto_miocardio_sintomas_mortalidade.txt](https://drive.google.com/file/d/1m0qAG9uen7An9u0OQrfMQPJ6umKEm2pU/view?usp=sharing)

Estudo com 2.290 pacientes analisando a apresentação de sintomas isquêmicos, métricas temporais de atendimento e preditores de mortalidade hospitalar no infarto com supradesnivelamento do segmento ST (IAMCSST).

### Como Esses Textos Podem Ser Explorados por Algoritmos de NLP

**1. Extração de Entidades Médicas (NER)**  
Identificar automaticamente termos clínicos relevantes como nomes de doenças, medicamentos, exames e procedimentos. Isso permite estruturar informações não estruturadas de prontuários e laudos médicos.

**2. Classificação de Tópicos**  
Algoritmos de classificação podem categorizar automaticamente trechos dos textos por tema: fatores de risco, sintomas, tratamentos, prognóstico.

**3. Análise de Sentimentos e Gravidade Clínica**  
Modelos de NLP podem inferir o grau de gravidade de condições descritas em textos médicos, distinguindo situações críticas de condições controladas.

**4. Sumarização Automática**  
Gerar resumos automáticos de artigos e relatórios clínicos extensos para facilitar a tomada de decisão médica em tempo real.

**5. Extração de Sintomas para Triagem**  
Identificar padrões de sintomas descritos nos textos e associá-los a diagnósticos — base para um sistema de triagem digital inteligente nas fases futuras do CardioIA.

---

## 🖼️ Parte 3 — Dados Visuais (Visão Computacional)

### Fonte das Imagens

Utilizamos o **Chest X-Ray Images (Pneumonia) Dataset**, disponibilizado no **Kaggle** pelo pesquisador Paul Mooney, originalmente publicado pelo **Guangzhou Women and Children's Medical Center** e referenciado na revista científica Cell.

- 🔗 **Fonte original:** [Kaggle — Chest X-Ray Images](https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia)
- 🔗 **Imagens hospedadas:** [Google Drive — imagens_raio_x](https://drive.google.com/drive/folders/1QrJ0G5MwkoLYCjC2ylIjczYZKjvc8q1D?usp=sharing)
- 📁 **Formato:** `.jpeg`
- 📏 **Volume:** 234 imagens de raio-X torácico
- 🏥 **Tipo de exame:** Radiografia torácica (Chest X-Ray)
- 👥 **Pacientes:** Pediátricos (1 a 5 anos)
- 🏷️ **Classe selecionada:** NORMAL — raio-X de pulmões saudáveis

> Selecionamos exclusivamente imagens da classe **NORMAL** para estabelecer a linha de base que os modelos de Visão Computacional utilizarão para identificar anomalias cardiopulmonares nas fases seguintes do CardioIA.

### Como Essas Imagens Podem Ser Analisadas por Visão Computacional

**1. Detecção de Padrões e Anomalias**  
Redes neurais convolucionais (CNNs) são capazes de identificar padrões visuais sutis em raio-X torácico que indicam alterações cardíacas, como cardiomegalia, derrame pleural ou congestão pulmonar.

**2. Identificação de Bordas e Estruturas Anatômicas**  
Técnicas como detecção de bordas (Canny, Sobel) e segmentação permitem isolar estruturas como o contorno cardíaco, a silhueta pulmonar e o mediastino, auxiliando no cálculo do índice cardiotorácico.

**3. Classificação Binária Normal vs. Anormal**  
Com as imagens normais como referência, os modelos poderão ser treinados para classificar automaticamente novas imagens como normais ou suspeitas, acelerando a triagem radiológica.

**4. Transfer Learning com Modelos Pré-treinados**  
Modelos como ResNet, VGG e EfficientNet podem ser ajustados (fine-tuning) com este dataset para criar um classificador cardiológico especializado.

**5. Apoio ao Diagnóstico Assistido por IA**  
A análise automatizada de raio-X torácico pode reduzir o tempo de diagnóstico e apoiar radiologistas em regiões com escassez de especialistas.

---

## 🔧 Como executar o código

Esta fase não possui código executável — trata-se de coleta, organização e documentação de dados. Os notebooks que consumirão esses dados serão desenvolvidos nas fases seguintes e disponibilizados na pasta `notebooks/`.

Para acessar os dados diretamente:

| Tipo | Descrição | Link |
|---|---|---|
| 📊 Numérico | Cleveland Heart Disease Dataset (.csv) | [Google Drive](https://drive.google.com/file/d/1mG9rDA_t4UILysb804DoJHQonTE7ucN7/view?usp=sharing) |
| 📝 Texto 1 | Estatística Cardiovascular Brasil 2023 (.txt) | [Google Drive](https://drive.google.com/file/d/1zarzA6NWpioNbuoUqtj6N0xe3rk593uP/view?usp=sharing) |
| 📝 Texto 2 | Infarto do Miocárdio: Sintomas e Mortalidade (.txt) | [Google Drive](https://drive.google.com/file/d/1m0qAG9uen7An9u0OQrfMQPJ6umKEm2pU/view?usp=sharing) |
| 🖼️ Visual | 234 Raio-X Torácico — Classe NORMAL (.jpeg) | [Google Drive](https://drive.google.com/drive/folders/1QrJ0G5MwkoLYCjC2ylIjczYZKjvc8q1D?usp=sharing) |

---

## 🗃 Histórico de lançamentos

- 1.0.0 - 02/09/2026 — Entrega da Fase 1: coleta e organização dos dados numéricos, textuais e visuais
---
