import sqlite3
from pathlib import Path

# 🚀 CORREÇÃO SPRINT 4: Usando pathlib para os caminhos funcionarem em qualquer PC!
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "totem_data.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Ativa o suporte a Chaves Estrangeiras (Foreign Keys) no SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Garante que as tabelas normalizadas existam antes da API receber dados."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 📊 TABELA 1: Totens (Hardware)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS totems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    ''')

    # 👤 TABELA 2: Visitantes Anonimizados (Para IA gerar insights de perfil)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            user_id_anon TEXT PRIMARY KEY,
            age_group TEXT,
            preferred_language TEXT
        )
    ''')

    # 🔗 TABELA 3: Interações (Com as Foreign Keys que o professor pediu)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            totem_id INTEGER,
            user_id_anon TEXT,
            interaction_type TEXT NOT NULL,
            duration_seconds REAL,
            success BOOLEAN,
            FOREIGN KEY (totem_id) REFERENCES totems(id),
            FOREIGN KEY (user_id_anon) REFERENCES visitors(user_id_anon)
        )
    ''')
    
    # Inserir um Totem padrão para o nosso simulador funcionar de cara
    cursor.execute("INSERT OR IGNORE INTO totems (id, location) VALUES (1, 'Zona dos Felinos - Zoológico')")

    conn.commit()
    conn.close()
    print("✅ Banco de Dados Normalizado e Atualizado para a Sprint 4!")

if __name__ == "__main__":
    init_db()