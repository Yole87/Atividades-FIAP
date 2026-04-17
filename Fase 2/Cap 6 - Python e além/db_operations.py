import oracledb
from datetime import datetime
import json

# --- CONFIGURAÇÃO DA CONEXÃO ---
# IMPORTANTE: Lembre-se de colocar suas credenciais aqui.
DB_USER = "RM567437"
DB_PASSWORD = "300587"
DB_DSN = "oracle.fiap.com.br:1521/ORCL"

def salvar_analise_db(registro):
    """Conecta ao banco Oracle e insere um novo registro de análise."""
    sql = """
        INSERT INTO ANALISES_PERDAS (
            data_analise, potencial_toneladas, colhido_toneladas, preco_tonelada,
            perda_toneladas, perda_percentual, prejuizo_financeiro, observacoes_checklist
        ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
    """
    checklist_json = json.dumps(registro.get('checklist', {}))
    dados_para_inserir = (
        datetime.strptime(registro['data'], "%d/%m/%Y %H:%M:%S"),
        registro['potencial_colheita_t'],
        registro['real_colhido_t'],
        registro['preco_tonelada_rs'],
        registro['analise_resultado']['toneladas_perdidas'],
        registro['analise_resultado']['percentual_perda'],
        registro['analise_resultado']['prejuizo_financeiro'],
        checklist_json
    )
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, dados_para_inserir)
                connection.commit()
        return True
    except oracledb.Error as error:
        print(f"Erro ao salvar no banco de dados: {error}")
        return False

def carregar_historico_db():
    """Conecta ao banco Oracle e busca todos os registros de análises, incluindo o ID."""
    sql = "SELECT id, data_analise, potencial_toneladas, colhido_toneladas, preco_tonelada, perda_toneladas, perda_percentual, prejuizo_financeiro, observacoes_checklist FROM ANALISES_PERDAS ORDER BY data_analise DESC"
    historico = []
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                colunas = [desc[0].lower() for desc in cursor.description]
                for linha in cursor.fetchall():
                    registro = dict(zip(colunas, linha))
                    historico.append(registro)
        return historico
    except oracledb.Error as error:
        print(f"Erro ao carregar histórico do banco de dados: {error}")
        return []

# <-- A FUNÇÃO QUE FALTAVA ESTÁ AQUI ---
def excluir_analise_db(analise_id):
    """Conecta ao banco e exclui uma análise pelo seu ID."""
    sql = "DELETE FROM ANALISES_PERDAS WHERE id = :1"
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, [analise_id])
                connection.commit() # Confirma a exclusão
        return True
    except oracledb.Error as error:
        print(f"Erro ao excluir análise do banco de dados: {error}")
        return False