"""
OrbitalGuard — Dashboard de Monitoramento Orbital
Interface interativa para visualização de detritos espaciais,
métricas da CNN e simulação de risco de colisão.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import json
import os
import sys
import math
from datetime import datetime
from tinydb import TinyDB
from PIL import Image
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ml"))
from model import OrbitalCNN, CLASSES, IMG_SIZE

BASE_DIR    = os.path.dirname(__file__)
DB_PATH     = os.path.join(BASE_DIR, "db", "orbitalguard.json")
METRICAS    = os.path.join(BASE_DIR, "ml", "metricas.json")
MAPA_PATH   = os.path.join(BASE_DIR, "vision", "mapa_orbital.png")
GRAFICO_CNN = os.path.join(BASE_DIR, "ml", "historico_treino.png")
LAMBDA_RES  = os.path.join(BASE_DIR, "aws", "lambda_resultados.json")
MODEL_PATH  = os.path.join(BASE_DIR, "ml", "modelo_cnn.pth")

st.set_page_config(
    page_title="OrbitalGuard",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #080818; color: #e0e0ff; }
    .metric-card {
        background: linear-gradient(135deg, #0d0d2b, #1a1a40);
        border: 1px solid #2a2a6a;
        border-radius: 10px;
        padding: 18px 22px;
        text-align: center;
    }
    .metric-value { font-size: 2.2em; font-weight: bold; color: #00ccff; }
    .metric-label { font-size: 0.85em; color: #8888bb; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar_metricas():
    if os.path.exists(METRICAS):
        with open(METRICAS) as f:
            return json.load(f)
    return None


@st.cache_data
def carregar_lambda():
    if os.path.exists(LAMBDA_RES):
        with open(LAMBDA_RES) as f:
            return json.load(f)
    return []


def carregar_db():
    if not os.path.exists(DB_PATH):
        return [], []
    db = TinyDB(DB_PATH)
    return db.table("treinos").all(), db.table("predicoes").all()


def calcular_risco(altitude, inclinacao):
    detritos = [
        {"nome": "Fengyun-1C",   "alt": 820, "inc": 98.6},
        {"nome": "Iridium 33",   "alt": 780, "inc": 86.4},
        {"nome": "Bloco Foguete","alt": 560, "inc": 51.6},
        {"nome": "Kosmos-1408",  "alt": 430, "inc": 82.9},
        {"nome": "ASAT Inativo", "alt": 670, "inc": 65.1},
    ]
    riscos = []
    for d in detritos:
        dist = math.sqrt(((d["alt"] - altitude) / 100) ** 2 + ((d["inc"] - inclinacao) / 10) ** 2)
        riscos.append({**d, "prob": round(max(0, 1 - dist / 5), 4)})
    return sorted(riscos, key=lambda x: x["prob"], reverse=True)


@st.cache_resource
def carregar_modelo():
    if not os.path.exists(MODEL_PATH):
        return None
    device = torch.device("cpu")
    modelo = OrbitalCNN()
    modelo.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    modelo.eval()
    return modelo


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛸 OrbitalGuard")
    st.markdown("**Monitoramento de Detritos Espaciais**")
    st.markdown("---")
    st.markdown("**Fonte de dados**")
    st.markdown("🛰️ CNN Própria (PyTorch)")
    st.markdown("🌐 Open Notify ISS API")
    st.markdown("📡 ESP32 + MPU6050")
    st.markdown("---")
    st.markdown("**Região simulada**")
    st.markdown("Órbita LEO — 200–2000 km")
    st.markdown("Inclinação: 0–130°")
    st.markdown("---")
    st.markdown("**Simular Risco Orbital**")
    altitude_sim   = st.slider("Altitude (km)",  200, 2000, 408, 10)
    inclinacao_sim = st.slider("Inclinação (°)",   0,  130,  52,  1)
    tipo_sim = st.selectbox("Objeto para classificar (CNN)", CLASSES, index=1)
    st.markdown("---")
    st.caption("Alan Robin Santos — RM 567437")
    st.caption("FIAP IA | Fase 7 — Global Solution 2026.1")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🛸 OrbitalGuard")
st.markdown("### Classificação de Detritos Espaciais com CNN + Monitoramento Orbital")
st.markdown("---")

# ── Métricas ──────────────────────────────────────────────────────────────────
metricas       = carregar_metricas()
treinos, predicoes = carregar_db()

if metricas:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{metricas['acuracia']:.4f}</div>
            <div class="metric-label">Acurácia CNN</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{metricas['loss']:.4f}</div>
            <div class="metric-label">Loss (Cross-Entropy)</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{metricas['amostras_treino']}</div>
            <div class="metric-label">Amostras Treino</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{metricas['epocas']}</div>
            <div class="metric-label">Épocas Treinadas</div></div>""", unsafe_allow_html=True)
else:
    st.warning("⚠️ Modelo não encontrado. Execute `python ml/gerar_dataset.py` e depois `python ml/treinar_cnn.py`")

st.markdown("---")

# ── Simulador de Risco + CNN ao vivo ─────────────────────────────────────────
st.markdown("## 🎯 Simulador de Risco Orbital")
riscos   = calcular_risco(altitude_sim, inclinacao_sim)
prob_max = riscos[0]["prob"] if riscos else 0

def nivel_alerta(p):
    if p >= 0.7: return "CRÍTICO", "#ff00ff"
    if p >= 0.4: return "ALTO",    "#ff4444"
    if p >= 0.2: return "MÉDIO",   "#ff9900"
    return "BAIXO", "#44ff88"

alerta_txt, alerta_cor = nivel_alerta(prob_max)

col_sim1, col_sim2, col_sim3 = st.columns([1, 2, 1])
with col_sim1:
    st.markdown(f"""<div class="metric-card" style="border-color:{alerta_cor}">
        <div class="metric-value" style="color:{alerta_cor}">{alerta_txt}</div>
        <div class="metric-label">Nível de Alerta</div>
        <br>
        <div class="metric-value" style="font-size:1.4em;color:{alerta_cor}">{prob_max:.1%}</div>
        <div class="metric-label">Prob. máx. colisão</div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f"**Altitude:** {altitude_sim} km | **Inclinação:** {inclinacao_sim}°")

with col_sim2:
    fig_risco = go.Figure(go.Bar(
        x=[r["nome"] for r in riscos],
        y=[r["prob"] for r in riscos],
        marker_color=[alerta_cor if r["prob"] >= 0.4 else "#00ccff" for r in riscos],
        text=[f"{r['prob']:.0%}" for r in riscos],
        textposition="outside",
    ))
    fig_risco.update_layout(
        title="Probabilidade de Colisão por Detrito",
        paper_bgcolor="#0a0a1a", plot_bgcolor="#0d0d2b",
        font_color="#e0e0ff", height=280,
        yaxis=dict(range=[0, 1.1], tickformat=".0%", gridcolor="#1a1a3a"),
        xaxis=dict(gridcolor="#1a1a3a"),
        margin=dict(t=40, b=10)
    )
    st.plotly_chart(fig_risco, width="stretch")

with col_sim3:
    modelo = carregar_modelo()
    if modelo:
        tipo_idx = CLASSES.index(tipo_sim)
        # Gera imagem sintética e classifica ao vivo
        from aws.lambda_function import gerar_objeto_sintetico
        tensor = gerar_objeto_sintetico(tipo_idx)
        with torch.no_grad():
            prob_vec = torch.softmax(modelo(tensor), dim=1).cpu().numpy()[0]
        pred_id   = int(np.argmax(prob_vec))
        confianca = float(prob_vec[pred_id])
        risco_cnn = "ALTO" if pred_id in [1, 2] else "BAIXO"
        cor_cnn   = "#ff4444" if risco_cnn == "ALTO" else "#44ff88"
        st.markdown(f"""<div class="metric-card" style="border-color:{cor_cnn}">
            <div class="metric-label">CNN classifica como</div>
            <div class="metric-value" style="font-size:1em;color:{cor_cnn}">{CLASSES[pred_id]}</div>
            <div class="metric-label">Confiança: {confianca:.1%}</div>
            <br>
            <div class="metric-value" style="font-size:1.3em;color:{cor_cnn}">{risco_cnn}</div>
            <div class="metric-label">Risco CNN</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Execute treinar_cnn.py para ativar a classificação CNN ao vivo.")

st.markdown("---")

# ── Mapa Orbital + Histórico CNN ──────────────────────────────────────────────
col_vis, col_cnn = st.columns(2)
with col_vis:
    st.markdown("## 🗺️ Mapa de Risco Orbital")
    if os.path.exists(MAPA_PATH):
        st.image(Image.open(MAPA_PATH), caption="Detecção e classificação via CNN + OpenCV", width="stretch")
    else:
        st.info("Execute `python vision/analisar_orbita.py` para gerar o mapa orbital.")

with col_cnn:
    st.markdown("## 📈 Histórico de Treinamento CNN")
    if os.path.exists(GRAFICO_CNN):
        st.image(Image.open(GRAFICO_CNN), caption="Acurácia e Loss por época", width="stretch")
    else:
        st.info("Execute `python ml/treinar_cnn.py` para gerar o gráfico de treinamento.")

st.markdown("---")

# ── TinyDB ────────────────────────────────────────────────────────────────────
st.markdown("## 🗄️ Histórico de Predições — TinyDB (NoSQL)")
if predicoes:
    p1, p2, p3, p4 = st.columns(4)
    classes_count = {c: sum(1 for p in predicoes if p.get("objeto_previsto") == c) for c in CLASSES}
    alto_count    = sum(1 for p in predicoes if p.get("nivel_risco") == "ALTO")
    for col, (label, val) in zip([p1, p2, p3, p4], [
        ("Predições no banco", len(predicoes)),
        ("Risco ALTO",         alto_count),
        ("Detritos Metálicos", classes_count.get("detrito_metalico", 0)),
        ("Satélites Ativos",   classes_count.get("satelite_ativo", 0)),
    ]):
        col.metric(label, val)

    fig_pie = px.pie(
        names=list(classes_count.keys()),
        values=list(classes_count.values()),
        title="Distribuição de Classes Previstas",
        color_discrete_sequence=["#00ccff", "#ff4444", "#ff9900", "#aaaaaa"]
    )
    fig_pie.update_layout(paper_bgcolor="#0a0a1a", font_color="#e0e0ff", height=320,
                          legend=dict(bgcolor="#0d0d2b"))
    st.plotly_chart(fig_pie, width="stretch")
    st.dataframe([{
        "Objeto Real":     p.get("objeto_real", "—"),
        "Objeto Previsto": p.get("objeto_previsto", "—"),
        "Confiança":       f"{p.get('confianca', 0):.1%}",
        "Risco":           p.get("nivel_risco", "—"),
        "Timestamp":       p.get("timestamp", "—")
    } for p in predicoes], width="stretch")
else:
    st.info("Nenhuma predição no banco. Execute `python ml/treinar_cnn.py`")

st.markdown("---")

# ── Lambda ────────────────────────────────────────────────────────────────────
st.markdown("## ☁️ AWS Lambda — Simulação Serverless + CNN")
lambda_res = carregar_lambda()
if lambda_res:
    for r in lambda_res:
        alerta = r.get("nivel_alerta", "—")
        cor = "#ff4444" if alerta in ["CRITICO", "ALTO"] else "#44ff88"
        cnn = r.get("classificacao_cnn", {})
        with st.expander(f"📡 {r.get('cenario','Cenário')} — Alerta: **{alerta}**"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Altitude",      f"{r['entrada']['altitude_km']} km")
            c2.metric("Inclinação",    f"{r['entrada']['inclinacao_graus']}°")
            c3.metric("Prob. Colisão", f"{r['prob_colisao_maxima']:.1%}")
            st.markdown(f"**CNN classificou:** `{cnn.get('classe','—')}` com **{cnn.get('confianca', 0):.1%}** de confiança")
            st.markdown(f"**ISS:** lat={r['iss_posicao']['latitude']:.2f} | lon={r['iss_posicao']['longitude']:.2f} | {r['iss_posicao']['fonte']}")
            top = r["detritos_proximos"][0]
            st.markdown(f"**Detrito mais próximo:** {top['detrito_nome']} — {top['prob_colisao']:.1%}")
else:
    st.info("Execute `python aws/lambda_function.py` para gerar os resultados Lambda.")

st.markdown("---")

# ── Arquitetura ───────────────────────────────────────────────────────────────
st.markdown("## 🏗️ Arquitetura da Solução")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("**Fontes**")
    st.markdown("- Imagens Sintéticas")
    st.markdown("- Open Notify ISS API")
    st.markdown("- ESP32 + MPU6050")
with col_b:
    st.markdown("**Pipeline**")
    st.markdown("- Feature Engineering")
    st.markdown("- CNN (PyTorch)")
    st.markdown("- Previsão de Risco")
with col_c:
    st.markdown("**Entregáveis**")
    st.markdown("- Dashboard Streamlit")
    st.markdown("- Mapa Orbital")
    st.markdown("- Alerta de Colisão")

st.code(
    "🛸 Imagens Sintéticas → CNN (PyTorch) → Classificação de Detritos\n"
    "🌐 Open Notify API   → Lambda → CNN → Risco de Colisão Orbital\n"
    "📡 ESP32 + MPU6050   → MQTT → Dashboard (enriquecimento local)",
    language=None
)
st.caption("Modelo: CNN PyTorch (model.py compartilhado) | Dashboard: Streamlit + Plotly | Banco: TinyDB NoSQL")
