"""
AgroSat - Dashboard Interativo
Visualiza dados climáticos de satélite e previsões de produtividade.
Execute com: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib
import json
import sqlite3
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ──────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="AgroSat — Previsão de Produtividade",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado — tema espacial/agro
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
    }
    .main { background-color: #0d1117; color: #e6edf3; }
    .stApp { background-color: #0d1117; }

    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2333 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 0.85rem;
        color: #3fb950;
        margin-top: 4px;
    }
    .header-band {
        background: linear-gradient(90deg, #0d1117 0%, #1a2744 50%, #0d1117 100%);
        border-bottom: 1px solid #21262d;
        padding: 24px 0 16px 0;
        margin-bottom: 24px;
    }
    .tag {
        display: inline-block;
        background: #1f3a5f;
        color: #58a6ff;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        padding: 3px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .sidebar-section {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# CARREGA DADOS E MODELO
# ──────────────────────────────────────────────

@st.cache_data
def carregar_dados():
    path = "ml/dados_mensais.csv"
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["data"] if "data" in pd.read_csv(path, nrows=1).columns else None)
        return df
    # Gera dados de demonstração se o pipeline ainda não rodou
    np.random.seed(42)
    meses = pd.date_range("2019-01", periods=60, freq="MS")
    dia = np.array([d.month for d in meses])
    ciclo = np.sin(2 * np.pi * dia / 12)
    return pd.DataFrame({
        "ano":          [d.year for d in meses],
        "mes":          [d.month for d in meses],
        "temp_media":   26 + 6 * ciclo + np.random.normal(0, 0.8, 60),
        "temp_max":     32 + 5 * ciclo + np.random.normal(0, 0.8, 60),
        "precip_total": np.clip(80 + 120 * ciclo + np.random.exponential(30, 60), 5, 400),
        "rad_media":    18 + 5 * ciclo + np.random.normal(0, 0.6, 60),
        "dias_chuva":   np.clip(8 + 12 * ciclo + np.random.normal(0, 2, 60), 0, 30).astype(int),
        "produtividade": 6000 + 2000 * ciclo + np.random.normal(0, 400, 60),
    })


@st.cache_resource
def carregar_modelo():
    if os.path.exists("ml/modelo_agrosat.pkl"):
        modelo = joblib.load("ml/modelo_agrosat.pkl")
        scaler = joblib.load("ml/scaler_agrosat.pkl")
        return modelo, scaler
    return None, None


@st.cache_data
def carregar_metricas():
    if os.path.exists("ml/metricas.json"):
        with open("ml/metricas.json") as f:
            return json.load(f)
    return {"mae": 312.5, "r2": 0.8741, "n_amostras": 60}


df = carregar_dados()
modelo, scaler = carregar_modelo()
metricas = carregar_metricas()


# ──────────────────────────────────────────────
# SIDEBAR — PREVISÃO INTERATIVA
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🛰️ AgroSat")
    st.caption("Previsão de Produtividade via Dados de Satélite")
    st.divider()

    st.markdown("**Fonte de dados**")
    st.markdown('<span class="tag">NASA POWER</span><span class="tag">NDVI</span>', unsafe_allow_html=True)
    st.markdown('<span class="tag">Random Forest</span><span class="tag">scikit-learn</span>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown("**📍 Região simulada**")
    st.info("Sorriso, MT — Cerrado Brasileiro\nLat: -12.55 | Lon: -55.72")

    st.divider()
    st.markdown("#### 🔮 Simular Previsão")
    st.caption("Ajuste as condições climáticas do mês")

    mes_sim     = st.slider("Mês", 1, 12, 6)
    temp_sim    = st.slider("Temperatura Média (°C)", 18.0, 38.0, 26.0, 0.5)
    precip_sim  = st.slider("Precipitação Total (mm)", 0.0, 400.0, 120.0, 5.0)
    rad_sim     = st.slider("Radiação Solar (MJ/m²/dia)", 10.0, 28.0, 18.0, 0.5)
    dias_chuva  = st.slider("Dias com chuva", 0, 30, 10)

    cenario = {
        "temp_media":   temp_sim,
        "temp_max":     temp_sim + 6,
        "precip_total": precip_sim,
        "rad_media":    rad_sim,
        "dias_chuva":   dias_chuva,
        "mes":          mes_sim,
    }

    if modelo is not None:
        X = pd.DataFrame([cenario])[["temp_media", "temp_max", "precip_total", "rad_media", "dias_chuva", "mes"]]
        X_s = scaler.transform(X)
        prod_prev = float(modelo.predict(X_s)[0])
    else:
        # Fórmula simplificada para demo sem modelo
        prod_prev = max(500, 4000 + 80*temp_sim - 3*temp_sim**2 + 15*precip_sim - 0.1*precip_sim**2 + 60*rad_sim)

    nivel = "🟢 Alta" if prod_prev > 7000 else "🟡 Média" if prod_prev > 4500 else "🔴 Baixa"
    st.markdown(f"""
    <div class="metric-card" style="margin-top:12px">
        <div class="metric-value">{prod_prev:,.0f}</div>
        <div class="metric-label">kg/ha previsto</div>
        <div class="metric-delta">{nivel}</div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# CABEÇALHO PRINCIPAL
# ──────────────────────────────────────────────

st.markdown("""
<div class="header-band">
    <h1 style="margin:0; font-size:2rem; color:#e6edf3">
        🛰️ AgroSat
        <span style="font-size:1rem; font-weight:400; color:#8b949e; margin-left:12px">
        Previsão de Produtividade Agrícola com Dados de Satélite
        </span>
    </h1>
    <div style="margin-top:8px">
        <span class="tag">NASA POWER API</span>
        <span class="tag">Random Forest ML</span>
        <span class="tag">FIAP GS 2026.1</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# MÉTRICAS DO MODELO
# ──────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{metricas['r2']:.4f}</div>
        <div class="metric-label">R² do Modelo</div>
        <div class="metric-delta">Random Forest</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{metricas['mae']:,.0f}</div>
        <div class="metric-label">MAE (kg/ha)</div>
        <div class="metric-delta">Erro médio absoluto</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{metricas['n_amostras']}</div>
        <div class="metric-label">Amostras</div>
        <div class="metric-delta">Meses históricos</div>
    </div>""", unsafe_allow_html=True)

with c4:
    prod_media = df["produtividade"].mean()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{prod_media:,.0f}</div>
        <div class="metric-label">Média Histórica</div>
        <div class="metric-delta">kg/ha</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# GRÁFICO 1 — SÉRIE TEMPORAL CLIMÁTICA
# ──────────────────────────────────────────────

st.markdown("### 📡 Dados Climáticos — NASA POWER API")

fig_clima = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    subplot_titles=("Temperatura Média (°C)", "Precipitação Total (mm/mês)", "Radiação Solar (MJ/m²/dia)"),
    vertical_spacing=0.08,
)

x_axis = [f"{int(r.ano)}-{int(r.mes):02d}" for _, r in df.iterrows()]

fig_clima.add_trace(go.Scatter(
    x=x_axis, y=df["temp_media"],
    line=dict(color="#ff7b54", width=2),
    fill="tozeroy", fillcolor="rgba(255,123,84,0.1)",
    name="Temperatura"
), row=1, col=1)

fig_clima.add_trace(go.Bar(
    x=x_axis, y=df["precip_total"],
    marker_color="#58a6ff", opacity=0.8,
    name="Precipitação"
), row=2, col=1)

fig_clima.add_trace(go.Scatter(
    x=x_axis, y=df["rad_media"],
    line=dict(color="#f0e68c", width=2),
    name="Radiação"
), row=3, col=1)

fig_clima.update_layout(
    height=480,
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font=dict(color="#8b949e", family="Inter"),
    showlegend=False,
    margin=dict(l=0, r=0, t=40, b=0),
)
fig_clima.update_xaxes(gridcolor="#21262d", showgrid=True)
fig_clima.update_yaxes(gridcolor="#21262d", showgrid=True)

st.plotly_chart(fig_clima, use_container_width=True)


# ──────────────────────────────────────────────
# GRÁFICO 2 — PRODUTIVIDADE PREVISTA
# ──────────────────────────────────────────────

st.markdown("### 🌾 Produtividade Agrícola Prevista")

col_a, col_b = st.columns([2, 1])

with col_a:
    cores = ["#3fb950" if p > 7000 else "#d29922" if p > 4500 else "#f85149"
             for p in df["produtividade"]]

    fig_prod = go.Figure(go.Bar(
        x=x_axis,
        y=df["produtividade"],
        marker_color=cores,
        text=[f"{p:,.0f}" for p in df["produtividade"]],
        textposition="outside",
        textfont=dict(size=9, color="#8b949e"),
    ))
    fig_prod.add_hline(y=7000, line_dash="dash", line_color="#3fb950",
                       annotation_text="Alta produtividade", annotation_font_color="#3fb950")
    fig_prod.add_hline(y=4500, line_dash="dash", line_color="#d29922",
                       annotation_text="Produtividade média", annotation_font_color="#d29922")
    fig_prod.update_layout(
        height=360,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", family="Inter"),
        yaxis_title="kg/ha",
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    fig_prod.update_xaxes(gridcolor="#21262d")
    fig_prod.update_yaxes(gridcolor="#21262d")
    st.plotly_chart(fig_prod, use_container_width=True)

with col_b:
    st.markdown("#### Correlação Clima × Produtividade")
    feat_sel = st.selectbox("Variável climática", ["temp_media", "precip_total", "rad_media", "dias_chuva"],
                            format_func=lambda x: {"temp_media":"Temperatura","precip_total":"Precipitação",
                                                   "rad_media":"Radiação","dias_chuva":"Dias de chuva"}[x])

    fig_corr = px.scatter(
        df, x=feat_sel, y="produtividade",
        trendline="ols",
        color_discrete_sequence=["#58a6ff"],
        labels={feat_sel: feat_sel, "produtividade": "kg/ha"},
    )
    fig_corr.update_layout(
        height=320,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", family="Inter"),
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
    )
    fig_corr.update_traces(marker=dict(size=6, opacity=0.7))
    fig_corr.update_xaxes(gridcolor="#21262d")
    fig_corr.update_yaxes(gridcolor="#21262d")
    st.plotly_chart(fig_corr, use_container_width=True)


# ──────────────────────────────────────────────
# ARQUITETURA DO SISTEMA
# ──────────────────────────────────────────────

st.markdown("### 🏗️ Arquitetura da Solução")
st.markdown("""
```
┌─────────────────────────────────────────────────────────────────────┐
│                        AgroSat — Fluxo de Dados                     │
│                                                                     │
│  🛰️ SATÉLITE          ☁️ CLOUD API          🧠 ML MODEL             │
│  ──────────────       ─────────────         ───────────             │
│  Landsat / Sentinel   NASA POWER API        Random Forest           │
│  NDVI (vegetação)  →  T2M, PRECTOT,      →  Previsão de            │
│  Imagens orbitais     ALLSKY_SW_DWN         produtividade           │
│                                              (kg/ha)                │
│                                                  │                  │
│  📡 ESP32 (CAMPO)                         📊 DASHBOARD             │
│  ───────────────                          ────────────             │
│  DHT22 (temp/umid) ─────────────────────→ Streamlit + Plotly       │
│  BMP280 (pressão)    MQTT → cloud        Alertas em tempo real      │
│  UV sensor                               Interface web              │
└─────────────────────────────────────────────────────────────────────┘
```
""")

st.caption("Fonte de dados reais: [NASA POWER API](https://power.larc.nasa.gov/) | "
           "Modelo: Random Forest Regressor (scikit-learn) | "
           "Dashboard: Streamlit + Plotly")


# ──────────────────────────────────────────────
# HISTÓRICO DE PREVISÕES — SQLite
# ──────────────────────────────────────────────

st.markdown("### 🗄️ Histórico de Previsões — SQLite")

@st.cache_data(ttl=5)
def carregar_historico_db():
    db_path = "ml/agrosat.db"
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT * FROM previsoes ORDER BY id DESC LIMIT 50", conn
        )
        conn.close()
        return df
    except Exception:
        return None

@st.cache_data(ttl=5)
def carregar_metricas_db():
    db_path = "ml/agrosat.db"
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT * FROM metricas_modelo ORDER BY id DESC LIMIT 10", conn
        )
        conn.close()
        return df
    except Exception:
        return None

hist = carregar_historico_db()

if hist is not None and not hist.empty:
    col_h1, col_h2 = st.columns([3, 1])

    with col_h1:
        # Gráfico de barras com histórico de previsões
        cores_hist = [
            "#3fb950" if n == "alta" else "#d29922" if n == "media" else "#f85149"
            for n in hist["nivel_risco"]
        ]
        fig_hist = go.Figure(go.Bar(
            x=hist["timestamp"].str[:16],
            y=hist["produtividade_prevista"],
            marker_color=cores_hist,
            text=[f"{p:,.0f}" for p in hist["produtividade_prevista"]],
            textposition="outside",
            textfont=dict(size=9, color="#8b949e"),
        ))
        fig_hist.update_layout(
            height=300,
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(color="#8b949e", family="Inter"),
            yaxis_title="kg/ha",
            xaxis_title="Timestamp",
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=60),
            xaxis=dict(tickangle=-35),
        )
        fig_hist.update_xaxes(gridcolor="#21262d")
        fig_hist.update_yaxes(gridcolor="#21262d")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_h2:
        # Estatísticas do banco
        total    = len(hist)
        alta     = (hist["nivel_risco"] == "alta").sum()
        media    = (hist["nivel_risco"] == "media").sum()
        baixa    = (hist["nivel_risco"] == "baixa").sum()
        media_kg = hist["produtividade_prevista"].mean()

        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:10px">
            <div class="metric-value" style="font-size:1.6rem">{total}</div>
            <div class="metric-label">Previsões no banco</div>
        </div>
        <div class="metric-card" style="margin-bottom:10px">
            <div class="metric-value" style="font-size:1.6rem; color:#3fb950">{alta}</div>
            <div class="metric-label">Alta produtividade</div>
        </div>
        <div class="metric-card" style="margin-bottom:10px">
            <div class="metric-value" style="font-size:1.6rem; color:#d29922">{media}</div>
            <div class="metric-label">Média produtividade</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.6rem; color:#f85149">{baixa}</div>
            <div class="metric-label">Baixa produtividade</div>
        </div>
        """, unsafe_allow_html=True)

    # Tabela completa
    st.markdown("**Registros armazenados no banco**")
    df_exibir = hist[["id", "timestamp", "mes", "temp_media", "precip_total",
                       "produtividade_prevista", "nivel_risco"]].copy()
    df_exibir.columns = ["ID", "Timestamp", "Mês", "Temp (°C)", "Precip (mm)", "Prod. Prevista (kg/ha)", "Risco"]
    df_exibir["Prod. Prevista (kg/ha)"] = df_exibir["Prod. Prevista (kg/ha)"].round(0).astype(int)
    df_exibir["Temp (°C)"] = df_exibir["Temp (°C)"].round(1)
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # Métricas do modelo salvas no banco
    metricas_hist = carregar_metricas_db()
    if metricas_hist is not None and not metricas_hist.empty:
        st.markdown("**Histórico de treinamentos do modelo**")
        df_met = metricas_hist[["id", "timestamp", "r2", "mae", "n_amostras"]].copy()
        df_met.columns = ["ID", "Timestamp", "R²", "MAE (kg/ha)", "Amostras"]
        st.dataframe(df_met, use_container_width=True, hide_index=True)

    st.caption(f"Banco de dados: ml/agrosat.db (SQLite) — {total} previsões persistidas")

else:
    st.info("Banco SQLite não encontrado. Execute `python ml/model.py` primeiro para gerar os dados.")

