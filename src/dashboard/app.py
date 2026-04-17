import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Relatório Analítico FlexMedia - IA",
    page_icon="🤖",
    layout="wide"
)

# --- FUNÇÃO PARA CARREGAR DADOS (COM PATHLIB) ---
def load_data():
    BASE_DIR = Path(__file__).resolve().parent.parent
    db_path = BASE_DIR / "database" / "totem_data.db"
    
    if not db_path.exists():
        st.error("⚠️ Banco de dados não encontrado! Rode o simulador primeiro.")
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    # 🚀 JOIN poderoso: Juntando a tabela de interações com o perfil do visitante!
    query = """
        SELECT i.timestamp, i.interaction_type, i.duration_seconds, i.success,
               v.age_group, v.preferred_language
        FROM interactions i
        JOIN visitors v ON i.user_id_anon = v.user_id_anon
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hora'] = df['timestamp'].dt.hour
    return df

# --- CABEÇALHO ---
st.title("🤖 Dashboard Analítico com IA - FlexMedia (Sprint 4)")
st.markdown("Monitoramento avançado cruzando dados de uso com o perfil detectado por Visão Computacional.")

if st.button('🔄 Atualizar Relatório'):
    st.rerun()

df = load_data()

if not df.empty:
    # --- KPIs ---
    st.markdown("### 📈 Indicadores Chave de Desempenho (KPIs)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Interações", f"{len(df)}")
    col2.metric("Tempo Médio (s)", f"{df['duration_seconds'].mean():.1f}s")
    col3.metric("Taxa de Sucesso IA", f"{(df['success'].mean() * 100):.1f}%")
    col4.metric("Idioma Predominante", f"{df['preferred_language'].mode()[0]}")
    st.divider()

    # --- ANÁLISES DEMOGRÁFICAS (Novidade Sprint 4) ---
    st.markdown("### 👁️ Perfil Demográfico Detectado (Visão Computacional)")
    col_demo1, col_demo2 = st.columns(2)

    with col_demo1:
        st.subheader("Distribuição por Faixa Etária")
        fig_age = px.pie(df, names='age_group', hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_age, use_container_width=True)

    with col_demo2:
        st.subheader("Idiomas Identificados")
        lang_counts = df['preferred_language'].value_counts().reset_index()
        lang_counts.columns = ['Idioma', 'Visitantes']
        fig_lang = px.bar(lang_counts, x='Idioma', y='Visitantes', text='Visitantes', color='Idioma')
        st.plotly_chart(fig_lang, use_container_width=True)

    st.divider()

    # --- ANÁLISE DE COMPORTAMENTO ---
    st.markdown("### 📊 Padrões de Interação e Engajamento")
    col_comp1, col_comp2 = st.columns(2)

    with col_comp1:
        st.subheader("Uso por Tipo de Interação")
        type_counts = df['interaction_type'].value_counts().reset_index()
        type_counts.columns = ['Tipo', 'Quantidade']
        fig_type = px.bar(type_counts, x='Quantidade', y='Tipo', orientation='h', color='Tipo')
        st.plotly_chart(fig_type, use_container_width=True)

    with col_comp2:
        st.subheader("Taxa de Sucesso vs Duração")
        fig_scatter = px.scatter(df, x="duration_seconds", y="age_group", color="success", 
                                 title="Influência da Idade e Tempo no Sucesso", symbol="success")
        st.plotly_chart(fig_scatter, use_container_width=True)

else:
    st.warning("Nenhum dado encontrado. O simulador está rodando?")