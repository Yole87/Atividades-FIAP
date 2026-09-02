"""
AquaWatch — Módulo 4: Dashboard Interativo (Dash + Plotly)
Interface web completa para monitoramento de qualidade da água.

Por que Dash e não Streamlit?
  - AgroSat usou Streamlit → AquaWatch usa Dash (framework diferente)
  - Dash é mais adequado para dashboards com múltiplos callbacks reativos
  - Plotly nativo no Dash permite gráficos mais sofisticados

Funcionalidades:
  - Mapa de pontos de monitoramento (scatter geo)
  - Classificador LSTM ao vivo (sidebar com sliders)
  - Gráfico de séries temporais por parâmetro
  - Histórico de predições (MongoDB JSON)
  - Métricas do modelo em cards
  - Indicador de anomalia (Isolation Forest)

Para rodar: python dashboard/app.py
Acesso:     http://localhost:8050
"""

import json
import os
import sys
import pickle
import numpy as np

import torch
import torch.nn as nn

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px

# ─── Modelo LSTM (shared) ─────────────────────────────────────────────────────
class LSTMClassifier(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=64, n_layers=2, n_classes=4, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers,
                            batch_first=True, bidirectional=True,
                            dropout=dropout if n_layers > 1 else 0.0)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(64, n_classes)
        )
    def forward(self, x):
        out, _ = self.lstm(x)
        attn = torch.softmax(self.attention(out), dim=1)
        ctx  = (out * attn).sum(dim=1)
        return self.classifier(ctx)

CLASSES = {0: "normal", 1: "alerta", 2: "critico", 3: "toxico"}
CORES   = {"normal": "#33ff99", "alerta": "#ffdd33", "critico": "#ff8833", "toxico": "#cc33cc"}

# ─── Carrega modelos e dados ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def carregar_modelos():
    device = torch.device("cpu")
    lstm = LSTMClassifier().to(device)
    lstm.load_state_dict(torch.load(
        os.path.join(BASE_DIR, "modelos/lstm_agua.pth"),
        map_location=device, weights_only=True
    ))
    lstm.eval()
    with open(os.path.join(BASE_DIR, "modelos/isolation_forest.pkl"), "rb") as f:
        if_bundle = pickle.load(f)
    scaler_params = json.load(open(os.path.join(BASE_DIR, "dados/scaler_params.json")))
    return lstm, if_bundle["modelo"], if_bundle["scaler"], scaler_params, device

lstm_model, if_model, if_scaler, scaler_params, device = carregar_modelos()
scaler_mean  = np.array(scaler_params["mean"],  dtype=np.float32)
scaler_scale = np.array(scaler_params["scale"], dtype=np.float32)

def carregar_historico():
    path = os.path.join(BASE_DIR, "db/historico.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"documentos": []}

def carregar_metricas():
    path = os.path.join(BASE_DIR, "dados/metricas_lstm.json")
    if os.path.exists(path):
        return json.load(open(path))
    return {}

def carregar_resultado_visao():
    path = os.path.join(BASE_DIR, "dados/resultado_visao.json")
    if os.path.exists(path):
        return json.load(open(path))
    return {}

# ─── Predição ao vivo ────────────────────────────────────────────────────────
def classificar_ao_vivo(pH, turbidez, TDS, temperatura, OD, condutividade):
    snapshot = np.array([pH, turbidez, TDS, temperatura, OD, condutividade], dtype=np.float32)
    N = 24
    serie = np.tile(snapshot, (N, 1)).astype(np.float32)
    serie += np.random.normal(0, 0.02, serie.shape) * np.abs(snapshot)
    serie_norm = (serie - scaler_mean) / scaler_scale
    tensor = torch.FloatTensor(serie_norm).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = lstm_model(tensor)
        probs  = torch.softmax(logits, dim=1)[0].cpu().numpy()
    cls_id = int(probs.argmax())

    snap_norm = if_scaler.transform(snapshot.reshape(1, -1))
    anomalia  = if_model.predict(snap_norm)[0] == -1
    if_score  = float(if_model.score_samples(snap_norm)[0])

    return CLASSES[cls_id], float(probs[cls_id])*100, probs.tolist(), bool(anomalia), if_score

# ─── Pontos de monitoramento simulados ───────────────────────────────────────
PONTOS_MAPA = [
    {"id":"PONTO-PN-001",  "lat":-22.9,  "lon":-43.1, "classe":"normal",  "nome":"Rio Guandu — Parque Nacional"},
    {"id":"PONTO-AGR-007", "lat":-15.8,  "lon":-47.9, "classe":"alerta",  "nome":"Rio São Marcos — Agricultura"},
    {"id":"PONTO-IND-023", "lat":-23.5,  "lon":-46.6, "classe":"critico", "nome":"Rio Tietê — Zona Industrial"},
    {"id":"PONTO-ALE-099", "lat": -3.7,  "lon":-38.5, "classe":"toxico",  "nome":"Rio Cocó — Alerta Emergência"},
    {"id":"PONTO-NOR-011", "lat":-12.9,  "lon":-38.4, "classe":"normal",  "nome":"Rio Paraguaçu — Normal"},
    {"id":"PONTO-ALE-033", "lat":-20.3,  "lon":-43.5, "classe":"alerta",  "nome":"Rio Piranga — Alerta"},
]

# ─── Layout ───────────────────────────────────────────────────────────────────
DARK_BG   = "#0d1117"
CARD_BG   = "#161b22"
TEXT_MAIN = "#e6edf3"
TEXT_SEC  = "#8b949e"
BORDER    = "#30363d"

app = dash.Dash(__name__, title="AquaWatch — Monitoramento de Qualidade da Água")
app.layout = html.Div(style={"backgroundColor": DARK_BG, "minHeight": "100vh",
                              "fontFamily": "Inter, system-ui, sans-serif", "color": TEXT_MAIN},
children=[
    # ── Header ───────────────────────────────────────────────────────────────
    html.Div(style={"background":"linear-gradient(135deg,#0d2137,#0d3d5c)",
                    "padding":"20px 32px", "borderBottom":f"1px solid {BORDER}",
                    "display":"flex", "alignItems":"center", "gap":"16px"},
    children=[
        html.Div("💧", style={"fontSize":"32px"}),
        html.Div([
            html.H1("AquaWatch", style={"margin":0,"fontSize":"24px","fontWeight":700,"color":"#58a6ff"}),
            html.P("Monitoramento de Qualidade da Água via Satélite + ML",
                   style={"margin":0,"fontSize":"13px","color":TEXT_SEC})
        ]),
        html.Div([
            html.Span("● LSTM Bidirecional", style={"color":"#33ff99","fontSize":"12px","marginRight":"16px"}),
            html.Span("● Isolation Forest",  style={"color":"#ffdd33","fontSize":"12px","marginRight":"16px"}),
            html.Span("● USGS API",          style={"color":"#58a6ff","fontSize":"12px"}),
        ], style={"marginLeft":"auto"}),
    ]),

    # ── Métricas rápidas ──────────────────────────────────────────────────────
    html.Div(id="cards-metricas", style={"display":"flex","gap":"16px","padding":"20px 32px"}),

    # ── Conteúdo principal ────────────────────────────────────────────────────
    html.Div(style={"display":"flex","gap":"20px","padding":"0 32px 20px"},
    children=[
        # ── Sidebar com classificador ao vivo ─────────────────────────────────
        html.Div(style={"width":"300px","flexShrink":0}, children=[
            html.Div(style={"background":CARD_BG,"border":f"1px solid {BORDER}",
                            "borderRadius":"8px","padding":"20px","marginBottom":"16px"},
            children=[
                html.H3("🔬 Classificador LSTM ao Vivo", style={"margin":"0 0 16px","fontSize":"14px",
                                                                   "color":"#58a6ff"}),
                html.P("RM 567505 — Lucas Alberto da Silva Amorim",
                       style={"fontSize":"11px","color":TEXT_SEC,"margin":"0 0 16px"}),

                *[html.Div([
                    html.Label(label, style={"fontSize":"12px","color":TEXT_SEC,"display":"block","marginBottom":"4px"}),
                    dcc.Slider(id=sid, min=mn, max=mx, step=st, value=vl,
                               marks={mn:str(mn), mx:str(mx)},
                               tooltip={"placement":"bottom","always_visible":True})
                ], style={"marginBottom":"16px"})
                for label, sid, mn, mx, st, vl in [
                    ("pH", "sl-ph", 0, 14, 0.1, 7.2),
                    ("Turbidez (NTU)", "sl-turb", 0, 120, 0.5, 1.5),
                    ("TDS (mg/L)", "sl-tds", 0, 3000, 10, 250),
                    ("Temperatura (°C)", "sl-temp", 5, 45, 0.5, 20),
                    ("OD (mg/L)", "sl-od", 0, 15, 0.1, 8.0),
                    ("Condutividade (μS/cm)", "sl-cond", 0, 6000, 10, 400),
                ]],

                html.Button("▶ Classificar", id="btn-classificar",
                            style={"width":"100%","padding":"10px","background":"#238636",
                                   "color":"white","border":"none","borderRadius":"6px",
                                   "cursor":"pointer","fontSize":"14px","fontWeight":600}),
                html.Div(id="resultado-classificacao", style={"marginTop":"16px"})
            ]),

            # Isolation Forest
            html.Div(id="resultado-if",
                     style={"background":CARD_BG,"border":f"1px solid {BORDER}",
                            "borderRadius":"8px","padding":"16px"}),
        ]),

        # ── Área principal ────────────────────────────────────────────────────
        html.Div(style={"flex":1}, children=[
            # Mapa
            html.Div(style={"background":CARD_BG,"border":f"1px solid {BORDER}",
                            "borderRadius":"8px","padding":"16px","marginBottom":"16px"},
            children=[
                html.H3("🗺️ Mapa de Pontos de Monitoramento", style={"margin":"0 0 12px","fontSize":"14px","color":"#58a6ff"}),
                dcc.Graph(id="mapa-pontos", style={"height":"300px"})
            ]),

            # Série temporal + histórico
            html.Div(style={"display":"flex","gap":"16px"}, children=[
                html.Div(style={"flex":2,"background":CARD_BG,"border":f"1px solid {BORDER}",
                                "borderRadius":"8px","padding":"16px"},
                children=[
                    html.H3("📈 Histórico de Treinamento LSTM", style={"margin":"0 0 12px","fontSize":"14px","color":"#58a6ff"}),
                    dcc.Graph(id="grafico-treino", style={"height":"280px"})
                ]),
                html.Div(style={"flex":1,"background":CARD_BG,"border":f"1px solid {BORDER}",
                                "borderRadius":"8px","padding":"16px"},
                children=[
                    html.H3("📊 Predições — MongoDB", style={"margin":"0 0 12px","fontSize":"14px","color":"#58a6ff"}),
                    dcc.Graph(id="grafico-historico", style={"height":"280px"})
                ]),
            ]),

            # Tabela de histórico
            html.Div(style={"background":CARD_BG,"border":f"1px solid {BORDER}",
                            "borderRadius":"8px","padding":"16px","marginTop":"16px"},
            children=[
                html.H3("🗄️ Histórico de Predições — MongoDB NoSQL", style={"margin":"0 0 12px","fontSize":"14px","color":"#58a6ff"}),
                html.Div(id="tabela-historico")
            ]),
        ]),
    ]),

    # Rodapé
    html.Div(style={"textAlign":"center","padding":"16px","borderTop":f"1px solid {BORDER}",
                    "color":TEXT_SEC,"fontSize":"12px"},
    children=[
        html.Span("AquaWatch • FIAP IA • Fase 7 • Sub GS 2026.1 • Lucas Alberto da Silva Amorim — RM 567505")
    ])
])

# ─── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(Output("cards-metricas", "children"), Input("btn-classificar", "n_clicks"))
def atualizar_cards(_):
    metricas = carregar_metricas()
    hist = carregar_historico()
    n_docs = len(hist.get("documentos", []))
    acc = metricas.get("acuracia_teste", 0)

    cards_data = [
        ("Acurácia LSTM",     f"{acc*100:.2f}%",        "#33ff99"),
        ("Amostras Treino",   str(metricas.get("n_treino", 560)),    "#58a6ff"),
        ("Épocas Treinadas",  str(metricas.get("epochs", 40)),       "#ffdd33"),
        ("Registros MongoDB", str(n_docs),                           "#cc33cc"),
    ]
    return [
        html.Div([
            html.P(label, style={"margin":0,"fontSize":"11px","color":TEXT_SEC}),
            html.H2(valor, style={"margin":0,"fontSize":"28px","fontWeight":700,"color":cor})
        ], style={"background":CARD_BG,"border":f"1px solid {BORDER}","borderRadius":"8px",
                  "padding":"16px 20px","flex":1,"textAlign":"center"})
        for label, valor, cor in cards_data
    ]

@app.callback(Output("mapa-pontos", "figure"), Input("btn-classificar", "n_clicks"))
def atualizar_mapa(_):
    fig = go.Figure()
    for p in PONTOS_MAPA:
        cor = CORES[p["classe"]]
        fig.add_trace(go.Scattergeo(
            lat=[p["lat"]], lon=[p["lon"]],
            mode="markers+text",
            marker=dict(size=14, color=cor, symbol="circle",
                        line=dict(width=2, color="white")),
            text=[p["id"]],
            textposition="top center",
            textfont=dict(size=9, color="white"),
            name=p["classe"].upper(),
            hovertemplate=f"<b>{p['nome']}</b><br>Classe: {p['classe'].upper()}<br>Lat: {p['lat']} | Lon: {p['lon']}<extra></extra>"
        ))
    fig.update_layout(
        geo=dict(scope="south america", bgcolor=DARK_BG,
                 showland=True, landcolor="#1e2530",
                 showocean=True, oceancolor="#0d1f3c",
                 showcoastlines=True, coastlinecolor="#444"),
        paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
        margin=dict(l=0,r=0,t=0,b=0), showlegend=False
    )
    return fig

@app.callback(Output("grafico-treino", "figure"), Input("btn-classificar", "n_clicks"))
def atualizar_grafico_treino(_):
    metricas = carregar_metricas()
    hist = metricas.get("historico_treino", [])
    if not hist: return go.Figure()

    eps  = [h["epoch"] for h in hist]
    tacc = [h["train_acc"] for h in hist]
    vacc = [h["val_acc"]   for h in hist]
    tlos = [h["train_loss"] for h in hist]
    vlos = [h["val_loss"]   for h in hist]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eps, y=tacc, name="Train Acc",  line=dict(color="#33ff99", width=2)))
    fig.add_trace(go.Scatter(x=eps, y=vacc, name="Val Acc",    line=dict(color="#58a6ff", width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=eps, y=tlos, name="Train Loss", line=dict(color="#ff8833", width=2), yaxis="y2"))
    fig.add_trace(go.Scatter(x=eps, y=vlos, name="Val Loss",   line=dict(color="#cc33cc", width=2, dash="dot"), yaxis="y2"))

    fig.update_layout(
        paper_bgcolor=CARD_BG, plot_bgcolor="#1e2530",
        font=dict(color=TEXT_MAIN, size=11),
        legend=dict(bgcolor=DARK_BG, bordercolor=BORDER, borderwidth=1, font=dict(size=10)),
        xaxis=dict(title="Época", gridcolor=BORDER, color=TEXT_SEC),
        yaxis=dict(title="Acurácia", gridcolor=BORDER, color=TEXT_SEC, side="left"),
        yaxis2=dict(title="Loss", overlaying="y", side="right", color=TEXT_SEC),
        margin=dict(l=40,r=40,t=10,b=40)
    )
    return fig

@app.callback(Output("grafico-historico", "figure"), Input("btn-classificar", "n_clicks"))
def atualizar_historico(_):
    hist = carregar_historico()
    docs = hist.get("documentos", [])
    if not docs:
        return go.Figure()

    contagem = {c: 0 for c in CLASSES.values()}
    for d in docs:
        cls = d.get("classe_lstm", "normal")
        contagem[cls] = contagem.get(cls, 0) + 1

    fig = go.Figure(go.Pie(
        labels=[c.upper() for c in contagem.keys()],
        values=list(contagem.values()),
        marker=dict(colors=[CORES[c] for c in contagem.keys()]),
        textfont=dict(color="white", size=12),
        hole=0.4
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG, font=dict(color=TEXT_MAIN, size=11),
        legend=dict(bgcolor=DARK_BG, bordercolor=BORDER, font=dict(size=10)),
        margin=dict(l=10,r=10,t=10,b=10)
    )
    return fig

@app.callback(
    [Output("resultado-classificacao", "children"),
     Output("resultado-if", "children")],
    Input("btn-classificar", "n_clicks"),
    [State("sl-ph", "value"), State("sl-turb", "value"), State("sl-tds", "value"),
     State("sl-temp", "value"), State("sl-od", "value"), State("sl-cond", "value")],
    prevent_initial_call=True
)
def classificar_live(n, pH, turb, TDS, temp, OD, cond):
    if not n:
        return html.Div(), html.Div()

    classe, conf, probs, anomalia, if_score = classificar_ao_vivo(pH, turb, TDS, temp, OD, cond)
    cor = CORES[classe]

    # Barras de probabilidade
    barras = []
    for i, (cls_name, p) in enumerate(zip(CLASSES.values(), probs)):
        barras.append(html.Div([
            html.Span(cls_name.upper(), style={"fontSize":"10px","color":TEXT_SEC,"width":"60px","display":"inline-block"}),
            html.Div(style={"display":"inline-block","verticalAlign":"middle","width":f"{p*100:.0f}%",
                            "minWidth":"4px","height":"8px","background":CORES[cls_name],
                            "borderRadius":"4px","marginLeft":"4px"}),
            html.Span(f"{p*100:.1f}%", style={"fontSize":"10px","color":TEXT_SEC,"marginLeft":"4px"})
        ], style={"marginBottom":"4px"}))

    resultado_lstm = html.Div([
        html.Div([
            html.Span("LSTM classificou como", style={"fontSize":"11px","color":TEXT_SEC}),
            html.H3(classe.upper(), style={"margin":"4px 0","color":cor,"fontSize":"20px"}),
            html.Span(f"Confiança: {conf:.1f}%", style={"fontSize":"11px","color":TEXT_SEC}),
        ], style={"textAlign":"center","padding":"12px","background":f"{cor}22",
                  "borderRadius":"6px","border":f"1px solid {cor}","marginBottom":"12px"}),
        html.Div(barras)
    ])

    # IF resultado
    cor_if = "#ff8833" if anomalia else "#33ff99"
    texto_if = "⚠ ANOMALIA DETECTADA" if anomalia else "✓ Leitura Normal"
    resultado_if = html.Div([
        html.H3("🔍 Isolation Forest", style={"margin":"0 0 12px","fontSize":"14px","color":"#58a6ff"}),
        html.Div([
            html.Span(texto_if, style={"color":cor_if,"fontWeight":700,"fontSize":"14px"}),
            html.Br(),
            html.Span(f"Anomaly Score: {if_score:.4f}", style={"fontSize":"11px","color":TEXT_SEC}),
            html.Br(),
            html.Span("(mais negativo = mais anômalo)", style={"fontSize":"10px","color":TEXT_SEC}),
        ], style={"padding":"12px","background":f"{cor_if}22","borderRadius":"6px",
                  "border":f"1px solid {cor_if}","marginBottom":"12px"}),
        html.P("O IF detecta anomalias sem supervisão, complementando o LSTM.",
               style={"fontSize":"11px","color":TEXT_SEC,"margin":0})
    ])

    return resultado_lstm, resultado_if

@app.callback(Output("tabela-historico", "children"), Input("btn-classificar", "n_clicks"))
def atualizar_tabela(_):
    hist = carregar_historico()
    docs = hist.get("documentos", [])
    if not docs:
        return html.P("Nenhum registro no banco.", style={"color": TEXT_SEC})

    header = html.Tr([
        html.Th(col, style={"padding":"8px 12px","fontSize":"11px","color":TEXT_SEC,
                            "borderBottom":f"1px solid {BORDER}","fontWeight":600})
        for col in ["Documento", "Timestamp", "Ponto", "Classe LSTM", "Confiança", "Anomalia IF", "Alerta"]
    ])

    rows = []
    for doc in docs[-8:]:  # últimos 8
        cls = doc.get("classe_lstm", "normal")
        cor = CORES.get(cls, "white")
        rows.append(html.Tr([
            html.Td(doc.get("_id",""), style={"padding":"6px 12px","fontSize":"11px","color":TEXT_SEC}),
            html.Td(doc.get("timestamp","")[:19].replace("T"," "), style={"padding":"6px 12px","fontSize":"11px","color":TEXT_SEC}),
            html.Td(doc.get("ponto_id",""), style={"padding":"6px 12px","fontSize":"11px","color":TEXT_MAIN}),
            html.Td(html.Span(cls.upper(), style={"color":cor,"fontWeight":600}),
                    style={"padding":"6px 12px","fontSize":"11px"}),
            html.Td(f"{doc.get('confianca_lstm',0):.1f}%", style={"padding":"6px 12px","fontSize":"11px","color":TEXT_SEC}),
            html.Td("⚠ SIM" if doc.get("anomalia_if") else "✓ NÃO",
                    style={"padding":"6px 12px","fontSize":"11px",
                           "color":"#ff8833" if doc.get("anomalia_if") else "#33ff99"}),
            html.Td(html.Span(doc.get("nivel_alerta",""),
                              style={"background":{"BAIXO":"#1e4020","MEDIO":"#3d3000","ALTO":"#3d1500","CRITICO":"#2d0030"}.get(doc.get("nivel_alerta",""),""),
                                     "color":{"BAIXO":"#33ff99","MEDIO":"#ffdd33","ALTO":"#ff8833","CRITICO":"#cc33cc"}.get(doc.get("nivel_alerta",""),"white"),
                                     "padding":"2px 8px","borderRadius":"4px","fontSize":"11px"}),
                    style={"padding":"6px 12px"}),
        ], style={"borderBottom":f"1px solid {BORDER}"}))

    return html.Table([html.Thead(header), html.Tbody(rows)],
                      style={"width":"100%","borderCollapse":"collapse"})

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[AQUAWATCH] Iniciando Dashboard Dash...")
    print("[INFO] Acesse: http://localhost:8050")
    print("[INFO] Para encerrar: Ctrl+C\n")
    app.run(debug=False, host="0.0.0.0", port=8050)
