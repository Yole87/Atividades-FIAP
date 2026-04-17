# FarmTech Solutions

# Sistema de Gestão e Diagnóstico de Perdas no Agronegócio

### 👨‍🎓 Integrantes: 
- **Nome:** Alan Robin - **RM:** RM567437
- **Nome:** Lucas Amorim - **RM:** RM567505

### 👩‍🏫 Professores:
### Tutor(a) 
- Sabrina Otoni
### Coordenador(a)
- André Godoi


### 📜 Descrição

Este projeto aborda uma das "dores" mais significativas do agronegócio brasileiro, especificamente na cultura da cana-de-açúcar: as **perdas financeiras durante o processo de colheita mecanizada**. Estudos indicam que até 15% da produção pode ser perdida nesta etapa, representando um prejuízo de milhões de reais para os produtores.

Esta aplicação em Python foi desenvolvida como uma ferramenta de **apoio à decisão (Decision Support System - DSS)**. Ela vai além de uma simples calculadora, atuando como um sistema de diagnóstico completo que ajuda o produtor a:
1.  **Quantificar** o prejuízo financeiro exato de cada colheita.
2.  **Diagnosticar** as possíveis causas operacionais e de processo através de um checklist de boas práticas.
3.  **Receber orientações** e recomendações instantâneas para mitigar essas perdas em colheitas futuras.

O sistema persiste todos os dados em um banco de dados **Oracle**, permitindo a criação de um histórico robusto para análises de longo prazo e gestão contínua da eficiência operacional.

### 📁 Estrutura de pastas

A estrutura de arquivos do projeto foi simplificada para focar nos elementos essenciais do desenvolvimento:

- <b>main.py</b>: Ponto de entrada da aplicação. Contém a interface com o usuário (menu), o fluxo principal do programa e as funções de lógica de negócio.

- <b>db_operations.py</b>: Módulo dedicado a centralizar todas as funções de interação com o banco de dados Oracle (conectar, inserir, consultar e excluir dados).

- <b>DataBase_Agro.sql</b>: Script SQL contendo o comando `CREATE TABLE` para gerar a estrutura da tabela `ANALISES_PERDAS` no banco de dados.

- <b>README.md</b>: Arquivo que serve como guia e explicação geral sobre o projeto (o mesmo que você está lendo agora).

## 🔧 Como executar o código

Para executar este projeto em sua máquina local, siga os passos abaixo.

### Pré-requisitos
- Python 3.x instalado.
    - <https://www.python.org/downloads>
- Acesso a um ambiente de banco de dados Oracle. 
    - <https://www.oracle.com/br/database/sqldeveloper/technologies/download>

### 1. Clonar o Repositório
* git clone <https://github.com/Yole87/MeuProjeto>
* cd <Cap 6 - Python e além>

### 2. Instalar Dependências
- O projeto utiliza a biblioteca oracledb. Instale-a usando o pip:
* pip install oracledb (exemplo de comando utiliznado VSCode)

### 3. Configurar o Banco de Dados
- A estrutura da tabela precisa ser criada no seu ambiente Oracle.

* Execute o script SQL contido no arquivo DataBase_Agro.sql em sua ferramenta de gerenciamento Oracle (como Oracle SQL Developer). Isso criará a tabela ANALISES_PERDAS.

### 4. Configurar a Conexão
* Abra o arquivo db_operations.py.

* Insira suas credenciais de acesso ao Oracle nas variáveis indicadas:

* DB_USER = "seu_usuario_oracle"
* DB_PASSWORD = "sua_senha_oracle"
* DB_DSN = "hostname:porta/service_name" # Ex: oracle.fiap.com.br:0000/ORCL

### 5. Executar a Aplicação
- Após a configuração, execute o programa principal a partir do terminal:

* python main.py
* O sistema exibirá o menu principal, pronto para uso.

### 🗃 Histórico de lançamentos
- 1.0.0 - 14/10/2025

- Lançamento da versão inicial do Sistema de Gestão de Perdas.

- Funcionalidades implementadas:

    - Módulo de cálculo de perdas financeiras.

    - Menu interativo para navegação.

    - Integração com banco de dados Oracle para persistência de dados (CRUD: Create, Read, Delete).

    - Módulo de diagnóstico com checklist de 8 fatores de perda.

    - Geração de relatório de recomendações instantâneo.

    - Visualização de histórico resumido e detalhado.

