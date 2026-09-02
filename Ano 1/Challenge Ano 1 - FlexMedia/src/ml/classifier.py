import sqlite3
import pandas as pd
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# --- CONFIGURAÇÃO ROBUSTA DE CAMINHOS ---
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "totem_data.db"
MODEL_PATH = BASE_DIR / "ml" / "interaction_model.pkl"

def load_rich_data():
    """Busca os dados normalizados juntando as tabelas de interações e perfil do visitante."""
    if not DB_PATH.exists():
        print("❌ Erro: Banco de dados não encontrado.")
        return None

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT i.duration_seconds, i.interaction_type, i.success,
               v.age_group, v.preferred_language
        FROM interactions i
        JOIN visitors v ON i.user_id_anon = v.user_id_anon
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def train_advanced_model():
    print("🧠 [VÊNUS IA] Iniciando treinamento avançado (Sprint 4)...")
    df = load_rich_data()

    if df is None or len(df) < 20:
        print("⚠️ Poucos dados para treinar. Deixe o simulador rodar mais tempo.")
        return

    # 1. Pré-processamento: Transformando texto em números para a IA entender
    le_interaction = LabelEncoder()
    le_age = LabelEncoder()
    le_lang = LabelEncoder()

    df['interaction_encoded'] = le_interaction.fit_transform(df['interaction_type'])
    df['age_encoded'] = le_age.fit_transform(df['age_group'])
    df['lang_encoded'] = le_lang.fit_transform(df['preferred_language'])

    # 🚀 O SEGREDINHO DA SPRINT 4: Agora a IA analisa 4 dimensões (Features)
    X = df[['duration_seconds', 'interaction_encoded', 'age_encoded', 'lang_encoded']]
    y = df['success']

    # 2. Divisão de Treino e Teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Treinamento do Modelo
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # 4. Avaliação de Desempenho
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✅ Modelo treinado com sucesso processando {len(df)} registros complexos!")
    print(f"🎯 Acurácia Geral do Sistema: {accuracy * 100:.2f}%\n")
    print("📊 RELATÓRIO DE CLASSIFICAÇÃO:")
    print(classification_report(y_test, y_pred, target_names=["Falha", "Sucesso"]))

    # 5. Gerar Gráficos de Inteligência de Negócio
    print("\n📈 Gerando mapas de calor e análise de features...")
    
    plt.figure(figsize=(6, 4))
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Falha', 'Sucesso'], yticklabels=['Falha', 'Sucesso'])
    plt.title('Matriz de Confusão (IA Enriquecida)')
    plt.ylabel('Real')
    plt.xlabel('Previsto')
    plt.tight_layout()
    plt.savefig(BASE_DIR / 'ml' / 'matriz_confusao.png')
    plt.close()

    plt.figure(figsize=(8, 5))
    importances = clf.feature_importances_
    features = ['Duração (s)', 'Tipo Interação', 'Faixa Etária', 'Idioma']
    sns.barplot(x=features, y=importances, palette='viridis')
    plt.title('Peso das Variáveis para o Sucesso da Interação')
    plt.ylabel('Relevância (0 a 1)')
    plt.tight_layout()
    plt.savefig(BASE_DIR / 'ml' / 'feature_importance.png')
    plt.close()

    joblib.dump(clf, MODEL_PATH)
    print("💾 Modelo avançado V2 exportado com sucesso para a FlexMedia.")

if __name__ == "__main__":
    train_advanced_model()