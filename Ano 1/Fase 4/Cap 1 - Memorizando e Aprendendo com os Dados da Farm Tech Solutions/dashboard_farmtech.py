import streamlit as st  # Cria a interface web (dashboard, botões, gráficos)
import pandas as pd     # Manipula a tabela de dados (carrega o CSV)
import numpy as np      # Realiza cálculos matemáticos avançados (arrays/matrizes)

# --- MACHINE LEARNING (O Cérebro da IA) ---
from sklearn.model_selection import train_test_split # Divide os dados em Treino (estudar) e Teste (prova)
from sklearn.ensemble import RandomForestRegressor   # O algoritmo de IA principal (Floresta Aleatória)
from sklearn.linear_model import LinearRegression    # Outro algoritmo de IA (Regressão Linear - alternativa)
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score # Calculam a nota/precisão da IA

# --- VISUALIZAÇÃO (Gráficos) ---
import matplotlib.pyplot as plt # Cria a figura/base do gráfico
import seaborn as sns           # Desenha o gráfico de dispersão bonito e estilizado

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="FarmTech AI Assistant", layout="wide")

st.title("🚜 FarmTech Solutions - Assistente Agrícola Inteligente")
st.markdown("""
Este sistema utiliza **Machine Learning (Regressão)** para analisar dados históricos 
e prever a **Umidade do Solo** atual, sugerindo ações de irrigação automatizadas.
""")

# --- 1. CARGA E TREINAMENTO DO MODELO ---
@st.cache_data # Para o site ficar rápido, não recarrega o modelo toda hora
def treinar_modelo():
    try:
        df = pd.read_csv('dados_historicos_irrigacao.csv')
    except:
        st.error("Arquivo de dados não encontrado. Rode o script de geração primeiro.")
        return None, None, None, None

    # Features (Entradas) e Target (O que queremos prever: Umidade)
    X = df[['Temperatura', 'Precipitacao', 'pH', 'N', 'P', 'K']]
    y = df['Umidade_Solo']

    # Divisão Treino/Teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Modelo: Random Forest Regressor (Geralmente melhor que Linear para o que precisamos)
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)

    return modelo, X_test, y_test, df

modelo, X_test, y_test, df_total = treinar_modelo()

if modelo is not None:
    # --- 2. BARRA LATERAL (SIMULAÇÃO DOS SENSORES) ---
    st.sidebar.header("📡 Simulação de Sensores (IoT)")
    st.sidebar.markdown("Ajuste os valores como se fossem lidos do ESP32:")

    temp_input = st.sidebar.slider("Temperatura (°C)", 15.0, 45.0, 28.0)
    precip_input = st.sidebar.slider("Precipitação/Chuva (mm)", 0.0, 50.0, 5.0)
    ph_input = st.sidebar.slider("pH do Solo", 4.0, 9.0, 6.5)
    
    st.sidebar.subheader("Nutrientes (0=Bom, 1=Baixo)")
    n_input = st.sidebar.selectbox("Nitrogênio (N)", [0, 1])
    p_input = st.sidebar.selectbox("Fósforo (P)", [0, 1])
    k_input = st.sidebar.selectbox("Potássio (K)", [0, 1])

    # --- 3. PREVISÃO E DECISÃO ---
    # Cria um dataframe com os dados de entrada do usuário
    entrada_usuario = pd.DataFrame([[temp_input, precip_input, ph_input, n_input, p_input, k_input]], 
                                   columns=['Temperatura', 'Precipitacao', 'pH', 'N', 'P', 'K'])
    
    # A IA faz a previsão
    umidade_prevista = modelo.predict(entrada_usuario)[0]

    # --- 4. EXIBIÇÃO NO DASHBOARD ---
    
    # Colunas para KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="🌡️ Temperatura", value=f"{temp_input} °C")
    with col2:
        st.metric(label="💧 Chuva Recente", value=f"{precip_input} mm")
    with col3:
        # Cor dinâmica dependendo da umidade
        delta_color = "normal" if umidade_prevista > 40 else "inverse"
        st.metric(label="🤖 Umidade Prevista (IA)", value=f"{umidade_prevista:.2f}%", delta_color=delta_color)

    st.divider()

    # Lógica de Sugestão (O "Cérebro" da decisão)
    col_acao, col_grafico = st.columns([1, 2])

    with col_acao:
        st.subheader("📢 Recomendações do Sistema")
        
        # Decisão de Irrigação
        if umidade_prevista < 40:
            st.error("🚨 **AÇÃO CRÍTICA: LIGAR IRRIGAÇÃO**")
            st.write("A umidade prevista está abaixo do ideal (40%). O sistema ativaria o Relé automaticamente.")
        elif umidade_prevista < 60:
            st.warning("⚠️ **ATENÇÃO: Monitorar Solo**")
            st.write("Umidade aceitável, mas fique atento. Não é necessário irrigar agora.")
        else:
            st.success("✅ **SOLO SAUDÁVEL: Irrigação Desligada**")
            st.write("Níveis de umidade ótimos. Economize água.")

        # Decisão de Nutrientes
        if n_input == 1 or p_input == 1 or k_input == 1:
            st.info("💊 **FERTILIZAÇÃO NECESSÁRIA**")
            if n_input == 1: st.write("- Repor Nitrogênio (N)")
            if p_input == 1: st.write("- Repor Fósforo (P)")
            if k_input == 1: st.write("- Repor Potássio (K)")

    with col_grafico:
        st.subheader("📊 Performance do Modelo (Métricas)")
        # Calcula métricas em tempo real com os dados de teste
        y_pred_test = modelo.predict(X_test)
        
        tab1, tab2 = st.tabs(["Métricas", "Gráfico de Dispersão"])
        
        with tab1:
            mae = mean_absolute_error(y_test, y_pred_test)
            mse = mean_squared_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)
            
            st.write(f"**R² (Coeficiente de Determinação):** {r2:.4f} (Quanto mais perto de 1.0, melhor)")
            st.write(f"**MAE (Erro Médio Absoluto):** {mae:.2f}")
            st.write(f"**MSE (Erro Quadrático Médio):** {mse:.2f}")
            st.progress(r2)

        with tab2:
            # Gráfico Real vs Previsto
            fig, ax = plt.subplots()
            sns.scatterplot(x=y_test, y=y_pred_test, alpha=0.5)
            plt.plot([0, 100], [0, 100], '--r') # Linha ideal
            plt.xlabel("Umidade Real (Histórico)")
            plt.ylabel("Umidade Prevista (Modelo)")
            plt.title("Precisão do Modelo: Real vs Previsto")
            st.pyplot(fig)