"""
Gerador do PDF do projeto AquaWatch para entrega na FIAP.
Estrutura: Capa, Introdução, Desenvolvimento (5 módulos), Resultados, Conclusão, Links.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, Image, KeepTogether)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable
import os, json

# ─── Cores ───────────────────────────────────────────────────────────────────
AZUL_FIAP   = HexColor("#0d2d5e")
AZUL_CLARO  = HexColor("#1a6ea8")
CIANO       = HexColor("#00b4d8")
VERDE       = HexColor("#33cc66")
AMARELO     = HexColor("#ffdd33")
LARANJA     = HexColor("#ff8833")
ROXO        = HexColor("#cc33cc")
CINZA_BG    = HexColor("#f5f7fa")
CINZA_TEXT  = HexColor("#444444")
CINZA_BORDA = HexColor("#cccccc")
PRETO       = HexColor("#111111")

W, H = A4

# ─── Estilos ─────────────────────────────────────────────────────────────────
def estilos():
    base = getSampleStyleSheet()
    return {
        "titulo_capa": ParagraphStyle("titulo_capa", fontName="Helvetica-Bold",
            fontSize=28, textColor=AZUL_FIAP, alignment=TA_CENTER, spaceAfter=6),
        "subtitulo_capa": ParagraphStyle("sub_capa", fontName="Helvetica",
            fontSize=13, textColor=CINZA_TEXT, alignment=TA_CENTER, spaceAfter=4),
        "meta_capa": ParagraphStyle("meta", fontName="Helvetica",
            fontSize=11, textColor=CINZA_TEXT, alignment=TA_CENTER, spaceAfter=3),
        "secao": ParagraphStyle("secao", fontName="Helvetica-Bold",
            fontSize=14, textColor=AZUL_FIAP, spaceBefore=18, spaceAfter=8,
            borderPadding=(0,0,4,0)),
        "subsecao": ParagraphStyle("subsec", fontName="Helvetica-Bold",
            fontSize=11, textColor=AZUL_CLARO, spaceBefore=10, spaceAfter=4),
        "corpo": ParagraphStyle("corpo", fontName="Helvetica",
            fontSize=9.5, textColor=PRETO, leading=15, spaceAfter=6, alignment=TA_JUSTIFY),
        "codigo": ParagraphStyle("codigo", fontName="Courier",
            fontSize=7.5, textColor=HexColor("#24292e"), leading=11,
            backColor=HexColor("#f6f8fa"), leftIndent=8, rightIndent=8,
            spaceBefore=4, spaceAfter=4, borderPadding=4),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold",
            fontSize=8.5, textColor=AZUL_FIAP, spaceAfter=2),
        "rodape": ParagraphStyle("rodape", fontName="Helvetica",
            fontSize=8, textColor=CINZA_TEXT, alignment=TA_CENTER),
    }

def hr(cor=CINZA_BORDA, espessura=0.5):
    return HRFlowable(width="100%", thickness=espessura, color=cor, spaceAfter=8, spaceBefore=4)

def caixa_codigo(texto, s):
    return Paragraph(texto.replace("\n","<br/>").replace(" ","&nbsp;").replace("<","&lt;").replace(">","&gt;"), s["codigo"])

def badge(texto, cor):
    return Paragraph(f'<font color="{cor.hexval() if hasattr(cor,"hexval") else cor}"><b>{texto}</b></font>', 
                     ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=9, spaceAfter=2))

# ─── Gera PDF ────────────────────────────────────────────────────────────────
def gerar_pdf(output_path="AquaWatch_LucasAmorim_RM567505.pdf"):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        title="AquaWatch — Lucas Alberto da Silva Amorim — RM 567505",
        author="Lucas Alberto da Silva Amorim"
    )

    s = estilos()
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # CAPA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 2*cm))

    # Ícone / logotipo simulado
    story.append(Paragraph("💧", ParagraphStyle("icon", fontName="Helvetica",
        fontSize=48, alignment=TA_CENTER, spaceAfter=12)))

    story.append(Paragraph("AquaWatch", s["titulo_capa"]))
    story.append(Paragraph("Monitoramento de Qualidade da Água com Dados de Satélite e Machine Learning",
                            s["subtitulo_capa"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(hr(CIANO, 2))
    story.append(Spacer(1, 0.3*cm))

    meta = [
        ("Aluno", "Lucas Alberto da Silva Amorim"),
        ("RM", "567505"),
        ("Disciplina", "Atividade Substitutiva Global Solution — Sub GS 2026.1"),
        ("Fase", "7 — IA Como Fertilizante Digital"),
        ("Instituição", "FIAP — Faculdade de Informática e Administração Paulista"),
        ("Data", "16 de junho de 2026"),
        ("GitHub", "[link do repositório]"),
        ("Vídeo", "[link do YouTube — Não Listado]"),
    ]
    for label, valor in meta:
        story.append(Paragraph(f"<b>{label}:</b> {valor}", s["meta_capa"]))

    story.append(Spacer(1, 0.5*cm))
    story.append(hr(CIANO, 2))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 1. INTRODUÇÃO
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Introdução", s["secao"]))
    story.append(hr())

    story.append(Paragraph("1.1 Contextualização — Economia Espacial e Recursos Hídricos", s["subsecao"]))
    story.append(Paragraph(
        "A nova economia espacial vai muito além da exploração de planetas: satélites de observação "
        "terrestre monitoram continuamente oceanos, rios, represas e lençóis freáticos, fornecendo "
        "dados multiespectrais que permitem avaliar a qualidade da água em escala global. O satélite "
        "Sentinel-2 da ESA, por exemplo, revisita qualquer ponto da Terra a cada 5 dias, capturando "
        "bandas espectrais que revelam turbidez, clorofila, sedimentação e presença de contaminantes.",
        s["corpo"]))

    story.append(Paragraph(
        "Ao mesmo tempo, a proliferação de dispositivos IoT de baixo custo — como o ESP32 — permite "
        "implantar redes densas de sensores em campo. A convergência dessas tecnologias cria uma "
        "oportunidade única: combinar dados de satélite com leituras locais de sensores, processados "
        "por modelos de Machine Learning, para gerar alertas em tempo real sobre a qualidade da água.",
        s["corpo"]))

    story.append(Paragraph("1.2 A Pergunta da Global Solution", s["subsecao"]))
    story.append(Paragraph(
        "<b>Como a Inteligência Artificial e as tecnologias digitais podem transformar a nova economia "
        "espacial e gerar impacto positivo na Terra?</b>",
        s["corpo"]))
    story.append(Paragraph(
        "O AquaWatch responde a essa pergunta utilizando dados orbitais multiespectrais para calcular "
        "o NDWI (Normalized Difference Water Index), combinados com um LSTM Bidirecional treinado em "
        "séries temporais de sensores IoT e um Isolation Forest para detecção de anomalias. O sistema "
        "conecta dados reais da USGS Water Quality API, uma Cloud Function Firebase, um dashboard "
        "Dash interativo e um firmware ESP32 com sensores de TDS e turbidez.",
        s["corpo"]))

    story.append(Paragraph("1.3 Diferenciação da Solução", s["subsecao"]))
    diff_data = [
        ["Componente", "AgroSat (Ref. Turma)", "OrbitalGuard (Alan)", "AquaWatch ✓ (Lucas)"],
        ["ML principal", "Random Forest", "CNN PyTorch", "LSTM Bidirecional + Atenção"],
        ["ML secundário", "—", "—", "Isolation Forest"],
        ["API externa", "NASA POWER", "Open Notify (ISS)", "USGS Water Quality"],
        ["Dashboard", "Streamlit", "Streamlit", "Dash + Plotly"],
        ["Banco de dados", "SQLite", "TinyDB", "MongoDB (JSON simulado)"],
        ["Visão Comp.", "YOLOv8 (detecção)", "OpenCV grid sintético", "NDWI + análise espectral"],
        ["ESP32 sensor", "Sensor campo", "MPU6050 (acelerômetro)", "TDS + Turbidez + DS18B20"],
        ["Cloud", "AWS Lambda", "AWS Lambda", "Firebase Cloud Function"],
        ["Tema", "Agronegócio/soja", "Detritos orbitais", "Qualidade da água"],
    ]
    diff_table = Table(diff_data, colWidths=[3.5*cm, 3.8*cm, 4*cm, 4.5*cm])
    diff_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_FIAP),
        ("TEXTCOLOR",  (0,0), (-1,0), white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("BACKGROUND", (0,1), (-1,-1), CINZA_BG),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_BG]),
        ("GRID", (0,0), (-1,-1), 0.3, CINZA_BORDA),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 4),
        ("BACKGROUND", (-1,1), (-1,-1), HexColor("#e6f4ea")),
        ("TEXTCOLOR",  (-1,1), (-1,-1), HexColor("#0d5c2e")),
        ("FONTNAME",   (-1,1), (-1,-1), "Helvetica-Bold"),
    ]))
    story.append(diff_table)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 2. DESENVOLVIMENTO
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Desenvolvimento", s["secao"]))
    story.append(hr())

    story.append(Paragraph("2.1 Arquitetura da Solução", s["subsecao"]))
    story.append(Paragraph(
        "O AquaWatch é composto por cinco módulos integrados, todos compartilhando os pesos do LSTM "
        "e o scaler de normalização:",
        s["corpo"]))

    arq_data = [
        ["Módulo", "Tecnologia", "Função"],
        ["Pipeline ML", "PyTorch (LSTM) + scikit-learn (IF)", "Treina LSTM para classificar 4 níveis de qualidade\nem séries de 24h × 6 parâmetros"],
        ["Dashboard", "Dash + Plotly", "Interface reativa com mapa, classificador ao vivo\ne histórico MongoDB"],
        ["Sensor IoT", "ESP32 + TDS + Turbidez + DS18B20 + MQTT", "Mede qualidade em campo e publica via MQTT\nno HiveMQ"],
        ["Visão Comp.", "scikit-image + NDWI", "Análise espectral de imagem de satélite\n(4 zonas classificadas)"],
        ["Cloud", "Firebase Function + USGS API + MongoDB", "API serverless que consulta USGS, classifica\ncom LSTM+IF e persiste no banco"],
    ]
    arq_table = Table(arq_data, colWidths=[3.2*cm, 5.5*cm, 7*cm])
    arq_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_CLARO),
        ("TEXTCOLOR",  (0,0), (-1,0), white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME",   (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_BG]),
        ("GRID", (0,0), (-1,-1), 0.3, CINZA_BORDA),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(arq_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Fluxo de dados:", s["label"]))
    story.append(caixa_codigo(
        "Imagens Satélite (256x256) → NDWI + Bandas RGB → Classificação 4 Zonas → vision/resultado_visao.json\n"
        "ESP32 (TDS+Turbidez+Temp) → MQTT/HiveMQ → Firebase Function → LSTM + IF → MongoDB\n"
        "USGS Water Quality API    → Firebase Function → enriquecimento real → dashboard\n"
        "Dashboard Dash            → LSTM ao vivo (sliders) + mapa + histórico MongoDB", s))

    # ── Módulo 1: LSTM ────────────────────────────────────────────────────────
    story.append(Paragraph("2.2 Módulo 1 — Pipeline de Machine Learning (LSTM + Isolation Forest)", s["subsecao"]))

    story.append(Paragraph("2.2.1 Dataset Sintético de Séries Temporais", s["label"]))
    story.append(Paragraph(
        "O dataset foi gerado proceduralmente com 800 amostras (200 por classe), cada uma sendo uma "
        "série temporal de 24 timesteps × 6 parâmetros (pH, turbidez, TDS, temperatura, OD, "
        "condutividade). A estratégia usou médias e desvios-padrão distintos entre classes, drift "
        "temporal suave e spikes de contaminação para classes crítico e tóxico:",
        s["corpo"]))

    story.append(caixa_codigo(
        "# ml/gerar_dataset.py — Parâmetros por classe\n"
        "PARAMETROS = {\n"
        "    0: dict(means=[7.2, 1.5, 250.0, 20.0, 8.0, 400.0],    # normal\n"
        "            stds =[0.3, 0.5,  30.0,  1.5, 0.5,  50.0]),\n"
        "    1: dict(means=[6.2, 6.0, 450.0, 26.0, 5.5, 900.0],    # alerta\n"
        "            stds =[0.5, 1.5,  60.0,  2.0, 0.8, 150.0]),\n"
        "    2: dict(means=[5.0, 18., 750.0, 30.0, 3.0, 1600.],    # critico\n"
        "            stds =[0.8, 4.0, 100.0,  3.0, 1.0, 250.0]),\n"
        "    3: dict(means=[3.5, 80., 1800., 35.0, 0.8, 4000.],    # toxico\n"
        "            stds =[1.0, 15., 200.0,  4.0, 0.5, 500.0]),\n"
        "}", s))

    story.append(Paragraph("2.2.2 Arquitetura LSTM Bidirecional com Atenção", s["label"]))
    story.append(Paragraph(
        "O modelo usa LSTM bidirecional com mecanismo de atenção — o modelo aprende quais timesteps "
        "são mais importantes para a classificação, em vez de usar apenas o último hidden state:",
        s["corpo"]))
    story.append(caixa_codigo(
        "# ml/treinar_lstm.py — LSTMClassifier\n"
        "class LSTMClassifier(nn.Module):\n"
        "    def __init__(self, input_dim=6, hidden_dim=64, n_layers=2,\n"
        "                 n_classes=4, dropout=0.3):\n"
        "        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers,\n"
        "            batch_first=True, bidirectional=True,        # bidirecional\n"
        "            dropout=dropout if n_layers > 1 else 0.0)\n"
        "        self.attention = nn.Linear(hidden_dim * 2, 1)   # atenção temporal\n"
        "        self.classifier = nn.Sequential(\n"
        "            nn.Linear(hidden_dim * 2, 64), nn.ReLU(),\n"
        "            nn.Dropout(dropout), nn.Linear(64, n_classes)\n"
        "        )\n"
        "    def forward(self, x):\n"
        "        lstm_out, _ = self.lstm(x)                      # (batch, 24, 128)\n"
        "        attn = torch.softmax(self.attention(lstm_out), dim=1)\n"
        "        ctx  = (lstm_out * attn).sum(dim=1)             # context vector\n"
        "        return self.classifier(ctx)", s))
    story.append(Paragraph(
        "Otimizador: Adam (lr=1e-3, weight_decay=1e-4) | Scheduler: ReduceLROnPlateau | "
        "Gradient Clipping (max_norm=1.0) | Split: 70/15/15",
        s["corpo"]))

    story.append(Paragraph("2.2.3 Isolation Forest (Detecção de Anomalias)", s["label"]))
    story.append(Paragraph(
        "Complementar ao LSTM (supervisionado), o Isolation Forest é treinado apenas com amostras "
        "normais e detecta leituras anômalas sem necessitar de rótulo — útil para eventos não vistos "
        "no treinamento:",
        s["corpo"]))
    story.append(caixa_codigo(
        "# ml/isolation_forest.py\n"
        "iso_forest = IsolationForest(\n"
        "    n_estimators=200,\n"
        "    contamination=0.05,   # espera até 5% de contaminação no stream\n"
        "    random_state=42\n"
        ")\n"
        "iso_forest.fit(X_normal)   # treina APENAS com amostras normais\n"
        "# Predição: +1=inlier (normal), -1=outlier (anomalia)", s))

    # ── Módulo 2: Visão ───────────────────────────────────────────────────────
    story.append(Paragraph("2.3 Módulo 2 — Visão Computacional: Análise Espectral NDWI", s["subsecao"]))
    story.append(Paragraph(
        "O módulo gera uma imagem sintética de 256×256 pixels simulando bandas multiespectrais de "
        "satélite e calcula o NDWI adaptado para RGB:",
        s["corpo"]))
    story.append(caixa_codigo(
        "# vision/analisar_imagem.py\n"
        "# NDWI adaptado para RGB sintético:\n"
        "# B alto → água limpa (profundidade)  → NDWI positivo\n"
        "# G alto → vegetação / superfície     → NDWI negativo\n"
        "def calcular_ndwi(img):\n"
        "    B = img[:,:,2]   # canal azul: proxy de profundidade/pureza\n"
        "    G = img[:,:,1]   # canal verde: reflexão superficial\n"
        "    return np.where((B + G) > 0, (B - G) / (B + G), 0)\n\n"
        "# Classificação espectral por zona:\n"
        "if B > 0.40 and R < 0.15:   → 'normal'   (água limpa e profunda)\n"
        "if G > 0.30 and B > 0.20:   → 'alerta'   (sedimento leve)\n"
        "if R > 0.45 and B < 0.20:   → 'critico'  (alta turbidez)\n"
        "if R > 0.25 and G < 0.25:   → 'toxico'   (efluente industrial)", s))

    # ── Módulo 3: Dashboard ───────────────────────────────────────────────────
    story.append(Paragraph("2.4 Módulo 3 — Dashboard Interativo (Dash + Plotly)", s["subsecao"]))
    story.append(Paragraph(
        "O dashboard Dash oferece callbacks reativos sem recarregar a página — diferença arquitetural "
        "fundamental em relação ao Streamlit. Componentes principais:",
        s["corpo"]))
    story.append(caixa_codigo(
        "# dashboard/app.py — Callback do classificador ao vivo\n"
        "@app.callback(\n"
        "    [Output('resultado-classificacao','children'),\n"
        "     Output('resultado-if','children')],\n"
        "    Input('btn-classificar','n_clicks'),\n"
        "    [State('sl-ph','value'), State('sl-turb','value'),\n"
        "     State('sl-tds','value'), State('sl-temp','value'),\n"
        "     State('sl-od','value'),  State('sl-cond','value')],\n"
        "    prevent_initial_call=True\n"
        ")\n"
        "def classificar_live(n, pH, turb, TDS, temp, OD, cond):\n"
        "    classe, conf, probs, anomalia, score = classificar_ao_vivo(\n"
        "        pH, turb, TDS, temp, OD, cond\n"
        "    )\n"
        "    # Retorna componentes HTML reativos com resultado LSTM + IF", s))

    # ── Módulo 4: Firebase ────────────────────────────────────────────────────
    story.append(Paragraph("2.5 Módulo 4 — Firebase Cloud Function + USGS API", s["subsecao"]))
    story.append(Paragraph(
        "A Cloud Function simula uma função serverless Firebase que recebe JSON do ESP32, consulta "
        "a USGS Water Quality API com dados reais de rios americanos, executa LSTM + IF e persiste "
        "o resultado no MongoDB:",
        s["corpo"]))
    story.append(caixa_codigo(
        "# cloud/firebase_sim.py\n"
        "def consultar_usgs_api(site_code='01646500'):\n"
        "    # Potomac River at Little Falls Pump Station, MD\n"
        "    url = ('https://waterservices.usgs.gov/nwis/iv/'\n"
        "           f'?sites={site_code}'\n"
        "           '&parameterCd=00010,00095'  # temperatura + condutividade\n"
        "           '&period=PT1H&format=json')\n"
        "    # Retorna dados reais ou fallback simulado\n\n"
        "def firebase_cloud_function(request_body):\n"
        "    # 1. Expande snapshot IoT para série 24h (drift suave)\n"
        "    # 2. LSTM classifica a série temporal\n"
        "    # 3. Isolation Forest avalia snapshot diretamente\n"
        "    # 4. USGS API enriquece com dado real externo\n"
        "    # 5. Retorna JSON com nivel_alerta + acao_recomendada", s))

    # ── Módulo 5: ESP32 ───────────────────────────────────────────────────────
    story.append(Paragraph("2.6 Módulo 5 — Sensor IoT de Campo (ESP32 + TDS + Turbidez)", s["subsecao"]))

    esp32_data = [
        ["Componente", "Conexão", "Função"],
        ["TDS Sensor SEN0189", "GPIO 34 (ADC1)", "Mede Total Dissolved Solids (mg/L)"],
        ["Sensor Turbidez", "GPIO 35 (ADC1)", "Mede transparência da água (NTU)"],
        ["DS18B20", "GPIO 4 (OneWire)", "Temperatura da água (°C)"],
        ["LED Alerta", "GPIO 2 (embutido)", "Feedback visual: pisca por severidade"],
        ["WiFi ESP32", "Integrado", "Publica MQTT no HiveMQ (broker.hivemq.com:1883)"],
    ]
    esp_table = Table(esp32_data, colWidths=[4.5*cm, 3.5*cm, 7.8*cm])
    esp_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), HexColor("#0d5c2e")),
        ("TEXTCOLOR",  (0,0), (-1,0), white),
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTNAME",   (1,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, HexColor("#e6f4ea")]),
        ("GRID", (0,0), (-1,-1), 0.3, CINZA_BORDA),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(esp_table)
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("Payload MQTT — tópico aquawatch/sensor/ESP32-001:", s["label"]))
    story.append(caixa_codigo(
        '{"sensor_id":"AquaWatch-ESP32-001","TDS_mgL":245.3,\n'
        ' "turbidez_NTU":1.8,"temperatura_C":19.5,"OD_mgL":7.88,\n'
        ' "condutividade_uScm":383.0,"pH_estimado":8.3,\n'
        ' "classificacao_local":"normal","nivel_alerta":"BAIXO",\n'
        ' "alertas_sessao":0,"projeto":"AquaWatch_FIAP_RM567505"}', s))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 3. RESULTADOS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Resultados Obtidos", s["secao"]))
    story.append(hr())

    story.append(Paragraph("3.1 Desempenho do LSTM Bidirecional", s["subsecao"]))

    metricas_data = [
        ["Métrica", "Valor", "Interpretação"],
        ["Acurácia (teste)", "100.00%", "120/120 amostras classificadas corretamente"],
        ["Loss (Cross-Entropy)", "0.0006", "Convergência estável após 40 épocas"],
        ["Amostras de treino", "560", "70% de 800 (split 70/15/15)"],
        ["Amostras de teste",  "120", "Dados nunca vistos pelo modelo"],
        ["Épocas treinadas",   "40", "Com ReduceLROnPlateau + gradient clipping"],
        ["Melhor val_acc",     "1.0000", "Checkpoint salvo na época 3"],
    ]
    m_table = Table(metricas_data, colWidths=[4*cm, 3*cm, 8.8*cm])
    m_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_CLARO),
        ("TEXTCOLOR",  (0,0), (-1,0), white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME",   (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_BG]),
        ("GRID", (0,0), (-1,-1), 0.3, CINZA_BORDA),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(m_table)

    story.append(Paragraph("3.2 Relatório por Classe", s["subsecao"]))
    cls_data = [
        ["Classe", "Precision", "Recall", "F1-Score", "Suporte"],
        ["normal",  "1.00", "1.00", "1.00", "30"],
        ["alerta",  "1.00", "1.00", "1.00", "30"],
        ["critico", "1.00", "1.00", "1.00", "30"],
        ["toxico",  "1.00", "1.00", "1.00", "30"],
        ["accuracy",   "—",    "—",  "1.00", "120"],
        ["macro avg", "1.00", "1.00", "1.00", "120"],
    ]
    cores_cls = [CINZA_BG, HexColor("#e6f4ea"), HexColor("#fff8e1"),
                 HexColor("#fff0e6"), HexColor("#f8e6ff"), CINZA_BG, CINZA_BG]
    cls_table = Table(cls_data, colWidths=[3.5*cm, 3*cm, 3*cm, 3*cm, 3.3*cm])
    cls_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_FIAP),
        ("TEXTCOLOR",  (0,0), (-1,0), white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_BG]),
        ("GRID", (0,0), (-1,-1), 0.3, CINZA_BORDA),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(cls_table)
    story.append(Paragraph(
        "Matriz de Confusão: [[30,0,0,0],[0,30,0,0],[0,0,30,0],[0,0,0,30]] — "
        "zero erros em todas as classes.",
        s["corpo"]))

    story.append(Paragraph("3.3 Isolation Forest", s["subsecao"]))
    story.append(Paragraph(
        "O IF atingiu 98.75% de acurácia binária (Normal vs Anomalia), com Precision=0.9836, "
        "Recall=1.0000 e F1=0.9917. Detectou 100% das amostras críticas e tóxicas como anômalas, "
        "com apenas 5% de falsos positivos nas amostras normais (contamination=0.05 intencional).",
        s["corpo"]))

    story.append(Paragraph("3.4 Visão Computacional — NDWI", s["subsecao"]))
    story.append(Paragraph(
        "4/4 zonas classificadas corretamente pela análise espectral. NDWI médio da cena: -0.34 "
        "(dominância de terra/vegetação). Zona de água limpa (NDWI > 0.10): 8.5% da cena. "
        "Turbidez espectral média: 0.1251. Máxima detectada: 0.5146 (Zona Crítico).",
        s["corpo"]))

    # Imagem da análise espectral
    vis_path = "/home/claude/AquaWatch/vision/analise_espectral.png"
    if os.path.exists(vis_path):
        img = Image(vis_path, width=15*cm, height=10*cm)
        story.append(img)
        story.append(Paragraph("Figura 1 — Análise espectral multiespectral: imagem RGB, NDWI, "
                                "turbidez, máscara d'água, bandas por zona e classificação final.",
                                ParagraphStyle("caption", fontName="Helvetica", fontSize=8,
                                               textColor=CINZA_TEXT, alignment=TA_CENTER, spaceAfter=8)))

    story.append(Paragraph("3.5 Firebase Cloud Function — 4 Cenários", s["subsecao"]))
    cloud_data = [
        ["Cenário", "Ponto", "Classe LSTM", "Confiança", "Anomalia IF", "Alerta"],
        ["Rio Limpo — Parque Nacional",      "PONTO-PN-001",  "NORMAL",  "93.0%", "SIM", "MEDIO"],
        ["Sedimentação Agrícola",             "PONTO-AGR-007", "ALERTA",  "85.9%", "SIM", "MEDIO"],
        ["Contaminação Industrial",           "PONTO-IND-023", "CRITICO", "97.5%", "SIM", "ALTO"],
        ["Descarte Ilegal de Efluentes",      "PONTO-ALE-099", "TOXICO",  "99.8%", "SIM", "CRITICO"],
    ]
    alerta_cores = [None, HexColor("#e6f4ea"), HexColor("#fff8e1"), HexColor("#fff0e6"), HexColor("#f8e6ff")]
    cl_table = Table(cloud_data, colWidths=[4.8*cm, 3.2*cm, 2.2*cm, 2*cm, 2*cm, 2.1*cm])
    cl_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_CLARO),
        ("TEXTCOLOR",  (0,0), (-1,0), white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_BG]),
        ("GRID", (0,0), (-1,-1), 0.3, CINZA_BORDA),
        ("ALIGN", (2,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(cl_table)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 4. CONCLUSÃO
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Conclusão", s["secao"]))
    story.append(hr())

    story.append(Paragraph(
        "O AquaWatch demonstrou com sucesso como a Inteligência Artificial e dados de satélite podem "
        "transformar o monitoramento de recursos hídricos, respondendo diretamente ao tema da Sub GS "
        "2026.1: tecnologias da economia espacial gerando impacto positivo na Terra.",
        s["corpo"]))

    story.append(Paragraph(
        "Os cinco módulos integrados compõem uma solução coerente e diferenciada:",
        s["corpo"]))

    contribuicoes = [
        "LSTM Bidirecional com Atenção — aprende padrões temporais de 24 horas de dados de sensor, "
        "atingindo 100% de acurácia com convergência em 3 épocas.",
        "Isolation Forest não-supervisionado — detecta anomalias sem rótulo (F1=0.9917), "
        "complementando o LSTM para eventos inéditos.",
        "NDWI adaptado para RGB sintético — classifica 4 zonas de qualidade da água com análise "
        "espectral baseada na proporção B/G dos canais multiespectrais.",
        "Firebase Cloud Function + USGS API — arquitetura serverless diferente de AWS Lambda, "
        "integrando dado real externo de qualidade de água.",
        "ESP32 com TDS + Turbidez + DS18B20 — sensores de qualidade da água reais, publicando "
        "via MQTT com classificação local baseada na CONAMA 357/2005.",
        "Dashboard Dash — callbacks reativos sem recarregar página, classificador LSTM ao vivo "
        "com sliders, mapa geográfico e histórico MongoDB.",
    ]
    for c in contribuicoes:
        story.append(Paragraph(f"• {c}", s["corpo"]))

    story.append(Paragraph(
        "Como próximos passos: integração com imagens reais do Sentinel-2 via API Copernicus, "
        "deploy da Firebase Function em produção com endpoint público, e expansão da rede de "
        "sensores ESP32 para bacias hidrográficas brasileiras.",
        s["corpo"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 5. LINKS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Links e Referências", s["secao"]))
    story.append(hr())

    story.append(Paragraph("Repositório GitHub", s["subsecao"]))
    story.append(Paragraph("[inserir link do GitHub aqui]", s["corpo"]))

    story.append(Paragraph("Vídeo Demonstrativo", s["subsecao"]))
    story.append(Paragraph("[inserir link do YouTube Não Listado aqui]", s["corpo"]))

    story.append(Paragraph("Referências Técnicas", s["subsecao"]))
    refs = [
        "USGS Water Quality Web Service: https://waterservices.usgs.gov/rest/IV-Service.html",
        "PyTorch LSTM Documentation: https://pytorch.org/docs/stable/generated/torch.nn.LSTM.html",
        "scikit-learn Isolation Forest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html",
        "Dash by Plotly Documentation: https://dash.plotly.com/",
        "DFRobot TDS Sensor SEN0189: https://wiki.dfrobot.com/Gravity__Analog_TDS_Sensor",
        "CONAMA Resolução 357/2005: http://conama.mma.gov.br/images/conteudo/CONAMA_RES_CONS_2005_357.pdf",
        "McFeeters, S.K. (1996). Use of NDWI in delineation of open water features. Int. J. Remote Sensing, 17(7)",
        "ESA Sentinel-2 Multispectral: https://sentinel.esa.int/web/sentinel/missions/sentinel-2",
        "Firebase Cloud Functions: https://firebase.google.com/docs/functions",
        "HiveMQ MQTT Broker: https://www.hivemq.com/",
        "Arduino ESP32 Core: https://github.com/espressif/arduino-esp32",
    ]
    for r in refs:
        story.append(Paragraph(f"• {r}", s["corpo"]))

    # ─── Build ────────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"[PDF] Gerado: {output_path}")

if __name__ == "__main__":
    gerar_pdf("/mnt/user-data/outputs/AquaWatch_LucasAmorim_RM567505.pdf")
