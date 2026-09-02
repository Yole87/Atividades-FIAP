const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageBreak, LevelFormat, HorizontalPositionRelativeFrom,
  VerticalPositionRelativeFrom, TableLayoutType,
} = require("docx");
const fs = require("fs");
const path = require("path");

// ── Cores ─────────────────────────────────────────────────────────────────────
const AZUL     = "0D2D5E";
const AZUL_CL  = "1A6EA8";
const CINZA_BG = "F5F7FA";
const VERDE_BG = "E6F4EA";
const VERDE_TX = "0D5C2E";
const BORDA    = "CCCCCC";

// ── Helpers ───────────────────────────────────────────────────────────────────
const sp = (before = 0, after = 100) =>
  ({ spacing: { before, after } });

const run = (text, opts = {}) =>
  new TextRun({ text, font: "Arial", size: 20, ...opts });

const heading1 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: AZUL })],
    ...sp(300, 120),
  });

const heading2 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: "Arial", size: 24, bold: true, color: AZUL_CL })],
    ...sp(200, 80),
  });

const heading3 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [new TextRun({ text, font: "Arial", size: 22, bold: true, color: AZUL_CL })],
    ...sp(160, 60),
  });

const body = (text, extra = {}) =>
  new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 20 })],
    ...sp(0, 100),
    ...extra,
  });

const bullet = (text, bold_prefix = "") =>
  new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [
      ...(bold_prefix ? [new TextRun({ text: bold_prefix + ": ", font: "Arial", size: 20, bold: true })] : []),
      new TextRun({ text, font: "Arial", size: 20 }),
    ],
    ...sp(0, 80),
  });

const code = (lines) => {
  const allLines = typeof lines === "string" ? lines.split("\n") : lines;
  return allLines.map((line) =>
    new Paragraph({
      children: [new TextRun({ text: line, font: "Courier New", size: 16, color: "24292e" })],
      shading: { type: ShadingType.CLEAR, fill: "F6F8FA" },
      indent: { left: 360 },
      ...sp(0, 0),
    })
  );
};

const pageBreak = () =>
  new Paragraph({ children: [new PageBreak()] });

const hr = () =>
  new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDA } },
    ...sp(100, 100),
    children: [],
  });

// ── Tabela genérica ───────────────────────────────────────────────────────────
function makeTable(rows, widths, headerColor = AZUL_CL) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows: rows.map((row, ri) =>
      new TableRow({
        children: row.map((cell, ci) => {
          const isHeader = ri === 0;
          const isLastCol = ci === row.length - 1;
          return new TableCell({
            width: { size: widths[ci], type: WidthType.PERCENTAGE },
            shading: isHeader
              ? { type: ShadingType.CLEAR, fill: headerColor }
              : ri % 2 === 0
              ? { type: ShadingType.CLEAR, fill: "FFFFFF" }
              : { type: ShadingType.CLEAR, fill: CINZA_BG },
            borders: {
              top:    { style: BorderStyle.SINGLE, size: 2, color: BORDA },
              bottom: { style: BorderStyle.SINGLE, size: 2, color: BORDA },
              left:   { style: BorderStyle.SINGLE, size: 2, color: BORDA },
              right:  { style: BorderStyle.SINGLE, size: 2, color: BORDA },
            },
            verticalAlign: VerticalAlign.CENTER,
            children: [
              new Paragraph({
                alignment: ri === 0 ? AlignmentType.CENTER : AlignmentType.LEFT,
                children: [
                  new TextRun({
                    text: cell,
                    font: "Arial",
                    size: 16,
                    bold: isHeader || ci === 0,
                    color: isHeader ? "FFFFFF" : "111111",
                  }),
                ],
                ...sp(40, 40),
              }),
            ],
          });
        }),
      })
    ),
  });
}

// ═════════════════════════════════════════════════════════════════════════════
// CONTEÚDO DO DOCUMENTO
// ═════════════════════════════════════════════════════════════════════════════
const children = [];

// ─── CAPA ─────────────────────────────────────────────────────────────────────
children.push(
  new Paragraph({ ...sp(2000, 0), children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "AquaWatch", font: "Arial", size: 56, bold: true, color: AZUL })],
    ...sp(0, 120),
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "Monitoramento de Qualidade da Água com Dados de Satélite e Machine Learning",
      font: "Arial", size: 24, color: "444444",
    })],
    ...sp(0, 400),
  }),
  hr(),
  ...([
    ["Aluno",       "Lucas Alberto da Silva Amorim"],
    ["RM",          "567505"],
    ["Atividade",   "Substitutiva Global Solution — Sub GS 2026.1"],
    ["Fase",        "7 — IA Como Fertilizante Digital"],
    ["Instituição", "FIAP — Faculdade de Informática e Administração Paulista"],
    ["Data",        "16 de junho de 2026"],
    ["GitHub",      "[INSERIR LINK DO REPOSITÓRIO AQUI]"],
    ["Vídeo",       "[INSERIR LINK DO YOUTUBE NÃO LISTADO AQUI]"],
  ].map(([label, val]) =>
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ text: `${label}: `, font: "Arial", size: 20, bold: true }),
        new TextRun({ text: val, font: "Arial", size: 20 }),
      ],
      ...sp(0, 60),
    })
  )),
  hr(),
  pageBreak(),
);

// ─── 1. INTRODUÇÃO ────────────────────────────────────────────────────────────
children.push(heading1("1. Introdução"), hr());

children.push(heading2("1.1 Contextualização — Economia Espacial e Recursos Hídricos"));
children.push(body(
  "A nova economia espacial vai muito além da exploração de planetas: satélites de observação " +
  "terrestre monitoram continuamente oceanos, rios, represas e lençóis freáticos, fornecendo " +
  "dados multiespectrais que permitem avaliar a qualidade da água em escala global. O satélite " +
  "Sentinel-2 da ESA revisita qualquer ponto da Terra a cada 5 dias, capturando bandas espectrais " +
  "que revelam turbidez, clorofila, sedimentação e presença de contaminantes."
));
children.push(body(
  "Ao mesmo tempo, a proliferação de dispositivos IoT de baixo custo como o ESP32 permite " +
  "implantar redes densas de sensores em campo. A convergência dessas tecnologias cria uma " +
  "oportunidade única: combinar dados de satélite com leituras locais de sensores, processados " +
  "por modelos de Machine Learning, para gerar alertas em tempo real sobre a qualidade da água."
));

children.push(heading2("1.2 A Pergunta da Global Solution"));
children.push(new Paragraph({
  children: [new TextRun({
    text: "Como a Inteligência Artificial e as tecnologias digitais podem transformar a nova economia espacial e gerar impacto positivo na Terra?",
    font: "Arial", size: 20, bold: true, italics: true,
  })],
  ...sp(0, 100),
}));
children.push(body(
  "O AquaWatch responde combinando análise espectral NDWI de imagens de satélite, um LSTM Bidirecional " +
  "com Atenção treinado em séries temporais de sensores IoT, um Isolation Forest para detecção de anomalias, " +
  "dados reais da USGS Water Quality API, uma Cloud Function Firebase, um dashboard Dash interativo e " +
  "um firmware ESP32 com sensores de TDS e turbidez."
));

children.push(heading2("1.3 Diferenciação da Solução"));
children.push(
  makeTable(
    [
      ["Componente", "AgroSat (Ref. Turma)", "OrbitalGuard (Alan)", "AquaWatch ✓ (Lucas)"],
      ["ML principal",    "Random Forest",         "CNN PyTorch",              "LSTM Bidirecional + Atenção"],
      ["ML secundário",   "—",                     "—",                        "Isolation Forest"],
      ["API externa",     "NASA POWER",             "Open Notify (ISS)",        "USGS Water Quality"],
      ["Dashboard",       "Streamlit",              "Streamlit",                "Dash + Plotly"],
      ["Banco de dados",  "SQLite",                 "TinyDB",                   "MongoDB (JSON simulado)"],
      ["Visão Comp.",     "YOLOv8 (detecção)",      "OpenCV grid sintético",    "NDWI + análise espectral"],
      ["ESP32 sensor",    "Sensor campo",            "MPU6050 (acelerômetro)",   "TDS + Turbidez + DS18B20"],
      ["Cloud",           "AWS Lambda",              "AWS Lambda",               "Firebase Cloud Function"],
      ["Tema",            "Agronegócio/soja",        "Detritos orbitais",        "Qualidade da água"],
    ],
    [16, 22, 22, 24]
  ),
  new Paragraph({ ...sp(200, 0), children: [] }),
  pageBreak(),
);

// ─── 2. DESENVOLVIMENTO ───────────────────────────────────────────────────────
children.push(heading1("2. Desenvolvimento"), hr());

children.push(heading2("2.1 Arquitetura da Solução"));
children.push(body("O AquaWatch é composto por cinco módulos integrados:"));
children.push(
  makeTable(
    [
      ["Módulo", "Tecnologia", "Função"],
      ["Pipeline ML",     "PyTorch (LSTM) + scikit-learn (IF)", "Classifica 4 níveis de qualidade em séries 24h × 6 parâmetros"],
      ["Dashboard",       "Dash + Plotly",                      "Interface reativa com mapa, classificador ao vivo e histórico MongoDB"],
      ["Sensor IoT",      "ESP32 + TDS + Turbidez + DS18B20",   "Mede qualidade em campo e publica via MQTT no HiveMQ"],
      ["Visão Comp.",     "scikit-image + NDWI",                "Análise espectral de imagem de satélite — 4 zonas classificadas"],
      ["Cloud",           "Firebase + USGS API + MongoDB",      "Serverless que consulta USGS, classifica com LSTM+IF e persiste"],
    ],
    [18, 30, 52]
  ),
  new Paragraph({ ...sp(120, 0), children: [] }),
);
children.push(heading3("Fluxo de dados:"));
children.push(...code([
  "Satélite (256x256 px)  →  NDWI + Bandas RGB  →  4 Zonas Classificadas",
  "ESP32 (TDS+Turb+Temp)  →  MQTT/HiveMQ  →  Firebase Function  →  LSTM + IF  →  MongoDB",
  "USGS Water Quality API →  Firebase Function  →  enriquecimento real",
  "Dashboard Dash         →  LSTM ao vivo (sliders) + mapa + histórico MongoDB",
]));
children.push(new Paragraph({ ...sp(200, 0), children: [] }));

// 2.2 LSTM
children.push(heading2("2.2 Módulo 1 — Pipeline de Machine Learning (LSTM + Isolation Forest)"));

children.push(heading3("2.2.1 Dataset Sintético de Séries Temporais"));
children.push(body(
  "O dataset foi gerado com 800 amostras (200 por classe), cada uma sendo uma série temporal de " +
  "24 timesteps × 6 parâmetros: pH, turbidez (NTU), TDS (mg/L), temperatura (°C), oxigênio " +
  "dissolvido OD (mg/L) e condutividade (μS/cm). Cada classe possui médias e desvios-padrão " +
  "distintos, drift temporal suave e spikes de contaminação para as classes crítico e tóxico:"
));
children.push(...code([
  "# ml/gerar_dataset.py",
  "PARAMETROS = {",
  "    0: dict(means=[7.2, 1.5, 250., 20., 8.0, 400.],  stds=[0.3, 0.5, 30., 1.5, 0.5, 50.]),   # normal",
  "    1: dict(means=[6.2, 6.0, 450., 26., 5.5, 900.],  stds=[0.5, 1.5, 60., 2.0, 0.8, 150.]),  # alerta",
  "    2: dict(means=[5.0, 18., 750., 30., 3.0, 1600.], stds=[0.8, 4.0, 100., 3., 1.0, 250.]),  # critico",
  "    3: dict(means=[3.5, 80., 1800., 35., 0.8, 4000.],stds=[1.0, 15., 200., 4., 0.5, 500.]),  # toxico",
  "}",
  "X = (800, 24, 6)  # 800 amostras × 24 timesteps × 6 features",
]));

children.push(heading3("2.2.2 Arquitetura LSTM Bidirecional com Atenção"));
children.push(body(
  "O modelo usa LSTM bidirecional com mecanismo de atenção — aprende quais timesteps são mais " +
  "relevantes para a classificação, em vez de usar apenas o último hidden state:"
));
children.push(...code([
  "# ml/treinar_lstm.py",
  "class LSTMClassifier(nn.Module):",
  "    def __init__(self, input_dim=6, hidden_dim=64, n_layers=2, n_classes=4, dropout=0.3):",
  "        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers,",
  "            batch_first=True, bidirectional=True,       # bidirecional: 2 direções",
  "            dropout=dropout if n_layers > 1 else 0.0)",
  "        self.attention = nn.Linear(hidden_dim * 2, 1)  # peso por timestep",
  "        self.classifier = nn.Sequential(",
  "            nn.Linear(hidden_dim * 2, 64), nn.ReLU(),",
  "            nn.Dropout(dropout), nn.Linear(64, n_classes)",
  "        )",
  "    def forward(self, x):",
  "        lstm_out, _ = self.lstm(x)                     # (batch, 24, 128)",
  "        attn = torch.softmax(self.attention(lstm_out), dim=1)",
  "        ctx  = (lstm_out * attn).sum(dim=1)            # context vector ponderado",
  "        return self.classifier(ctx)",
  "",
  "# Treino: Adam(lr=1e-3) | ReduceLROnPlateau | GradClip(max=1.0) | Split 70/15/15",
]));

children.push(heading3("2.2.3 Isolation Forest (Detecção de Anomalias Não-Supervisionada)"));
children.push(body(
  "Complementar ao LSTM (supervisionado), o Isolation Forest é treinado apenas com amostras " +
  "normais e detecta leituras anômalas sem necessitar de rótulo — útil para eventos não vistos:"
));
children.push(...code([
  "# ml/isolation_forest.py",
  "iso_forest = IsolationForest(",
  "    n_estimators=200,",
  "    contamination=0.05,   # espera até 5% de contaminação no stream real",
  "    random_state=42",
  ")",
  "iso_forest.fit(X_normal)  # treina APENAS com amostras normais (unsupervised)",
  "# +1 = inlier (normal)  |  -1 = outlier (anomalia detectada)",
]));

// 2.3 Visão
children.push(heading2("2.3 Módulo 2 — Visão Computacional: Análise Espectral NDWI"));
children.push(body(
  "O módulo gera uma imagem sintética de 256×256 pixels simulando bandas multiespectrais de " +
  "satélite e calcula o NDWI adaptado para RGB sintético. A relação espectral B > G indica " +
  "água limpa e profunda; R dominante indica turbidez ou contaminação:"
));
children.push(...code([
  "# vision/analisar_imagem.py",
  "def calcular_ndwi(img):",
  "    B = img[:,:,2]   # canal azul: proxy de profundidade/pureza da água",
  "    G = img[:,:,1]   # canal verde: reflexão superficial/vegetação",
  "    return np.where((B + G) > 0, (B - G) / (B + G), 0)",
  "    # NDWI > 0.10 → água limpa  |  NDWI < 0 → terra/vegetação",
  "",
  "# Classificação espectral por zona (R, G, B médios da ROI):",
  "if B > 0.40 and R < 0.15:   → 'normal'   (B=0.618, R=0.084)",
  "if G > 0.30 and B > 0.20:   → 'alerta'   (G=0.417, B=0.285)",
  "if R > 0.45 and B < 0.20:   → 'critico'  (R=0.579, B=0.105)",
  "if R > 0.25 and G < 0.25:   → 'toxico'   (R=0.368, G=0.165)",
]));

// 2.4 Dashboard
children.push(heading2("2.4 Módulo 3 — Dashboard Interativo (Dash + Plotly)"));
children.push(body(
  "O dashboard Dash oferece callbacks reativos sem recarregar a página — diferença arquitetural " +
  "em relação ao Streamlit. Inclui mapa Scattergeo dos pontos de monitoramento no Brasil, " +
  "classificador LSTM ao vivo com 6 sliders, curvas de treinamento e histórico MongoDB:"
));
children.push(...code([
  "# dashboard/app.py — Callback do classificador ao vivo",
  "@app.callback(",
  "    [Output('resultado-classificacao','children'),",
  "     Output('resultado-if','children')],",
  "    Input('btn-classificar','n_clicks'),",
  "    [State('sl-ph','value'), State('sl-turb','value'),",
  "     State('sl-tds','value'), State('sl-temp','value'),",
  "     State('sl-od','value'),  State('sl-cond','value')],",
  "    prevent_initial_call=True",
  ")",
  "def classificar_live(n, pH, turb, TDS, temp, OD, cond):",
  "    classe, conf, probs, anomalia, score = classificar_ao_vivo(",
  "        pH, turb, TDS, temp, OD, cond  # expande para série 24h com drift",
  "    )",
  "    # retorna componentes HTML com resultado LSTM + IF em tempo real",
  "",
  "# Para executar: python dashboard/app.py",
  "# Acesso:        http://localhost:8050",
]));

// 2.5 Firebase
children.push(heading2("2.5 Módulo 4 — Firebase Cloud Function + USGS API"));
children.push(body(
  "A Cloud Function simula uma função serverless Firebase que recebe JSON do ESP32, consulta " +
  "a USGS Water Quality API com dados reais de rios, executa LSTM + IF e persiste no MongoDB:"
));
children.push(...code([
  "# cloud/firebase_sim.py",
  "def consultar_usgs_api(site_code='01646500'):",
  "    # Potomac River at Little Falls Pump Station, MD (dado público real)",
  "    url = ('https://waterservices.usgs.gov/nwis/iv/'",
  "           f'?sites={site_code}'",
  "           '&parameterCd=00010,00095'   # temperatura + condutividade",
  "           '&period=PT1H&format=json')",
  "    # Retorna dado real ou fallback simulado se offline",
  "",
  "def firebase_cloud_function(request_body):",
  "    # 1. Expande snapshot IoT para série 24h (drift gaussiano suave)",
  "    # 2. LSTM classifica: normal / alerta / critico / toxico",
  "    # 3. Isolation Forest verifica se é anomalia",
  "    # 4. USGS API enriquece com temperatura/condutividade reais",
  "    # 5. Retorna JSON: nivel_alerta + acao_recomendada + timestamp",
  "    # 6. salvar_mongodb() → db/historico.json (simulação NoSQL)",
]));

// 2.6 ESP32
children.push(heading2("2.6 Módulo 5 — Sensor IoT de Campo (ESP32 + TDS + Turbidez)"));
children.push(
  makeTable(
    [
      ["Componente",      "Pino",    "Protocolo",  "Função"],
      ["TDS Sensor SEN0189", "GPIO 34", "ADC 12-bit", "Mede Total Dissolved Solids (mg/L)"],
      ["Sensor Turbidez",    "GPIO 35", "ADC 12-bit", "Mede transparência da água (NTU)"],
      ["DS18B20",            "GPIO 4",  "OneWire",    "Temperatura da água (°C)"],
      ["LED Alerta",         "GPIO 2",  "Digital",    "Pisca por severidade: 1Hz=alerta, 5Hz=crítico"],
      ["WiFi ESP32",         "Embutido","TCP/IP",     "Publica MQTT no HiveMQ porta 1883"],
    ],
    [24, 12, 14, 50],
    "0D5C2E"
  ),
  new Paragraph({ ...sp(120, 0), children: [] }),
);
children.push(heading3("Payload MQTT — tópico: aquawatch/sensor/ESP32-001"));
children.push(...code([
  '{',
  '  "sensor_id": "AquaWatch-ESP32-001",',
  '  "TDS_mgL": 245.3,  "turbidez_NTU": 1.8,  "temperatura_C": 19.5,',
  '  "OD_mgL": 7.88,    "condutividade_uScm": 383.0,  "pH_estimado": 8.3,',
  '  "classificacao_local": "normal",  "nivel_alerta": "BAIXO",',
  '  "alertas_sessao": 0,  "projeto": "AquaWatch_FIAP_RM567505"',
  '}',
]));
children.push(new Paragraph({ ...sp(200, 0), children: [] }));
children.push(body(
  "Classificação local no ESP32 baseada na CONAMA 357/2005 Classe II: TDS > 500 mg/L → alerta; " +
  "TDS > 1000 mg/L → crítico; turbidez > 40 NTU → alerta; turbidez > 100 NTU → crítico. " +
  "LED apagado = normal, pisca 1Hz = alerta, pisca 5Hz = crítico, aceso contínuo = tóxico."
));
children.push(pageBreak());

// ─── 3. RESULTADOS ────────────────────────────────────────────────────────────
children.push(heading1("3. Resultados Obtidos"), hr());

children.push(heading2("3.1 Desempenho do LSTM Bidirecional"));
children.push(
  makeTable(
    [
      ["Métrica", "Valor", "Interpretação"],
      ["Acurácia (teste)",   "86.67%",   "104/120 amostras corretas — erros so entre classes adjacentes"],
      ["Loss (Cross-Entropy)", "0.5228", "Convergência estável após 40 épocas"],
      ["Amostras de treino", "560",       "70% de 800 (split 70/15/15 estratificado)"],
      ["Amostras de teste",  "120",       "Dados nunca vistos pelo modelo"],
      ["Épocas treinadas",   "40",        "Com ReduceLROnPlateau + gradient clipping"],
      ["Melhor val_acc",     "0.9333",    "Checkpoint salvo — ReduceLROnPlateau ativo"],
    ],
    [28, 16, 56]
  ),
);
children.push(new Paragraph({ ...sp(160, 0), children: [] }));

children.push(heading2("3.2 Relatório por Classe (LSTM)"));
children.push(
  makeTable(
    [
      ["Classe", "Precision", "Recall", "F1-Score", "Suporte"],
      ["normal",    "0.87", "0.87", "0.87", "30"],
      ["alerta",    "0.85", "0.77", "0.81", "30"],
      ["critico",   "0.89", "0.83", "0.86", "30"],
      ["toxico",    "0.86", "1.00", "0.92", "30"],
      ["macro avg", "0.87", "0.87", "0.86", "120"],
    ],
    [30, 14, 14, 14, 14]
  ),
);
children.push(body(
  "Matriz de Confusão: [[26,4,0,0],[4,23,3,0],[0,0,25,5],[0,0,0,30]] — erros tecnicamente defensáveis: ocorrem apenas entre classes adjacentes (normal/alerta, crítico/tóxico), evidenciando que o modelo aprendeu a escala de qualidade.",
  { ...sp(80, 120) }
));

children.push(heading2("3.3 Isolation Forest"));
children.push(
  makeTable(
    [
      ["Métrica",      "Valor",   "Detalhe"],
      ["Acurácia binária", "98.75%", "Normal vs Anomalia (800 amostras)"],
      ["Precision",    "0.9836",  "5% falsos positivos em amostras normais (contamination=0.05 intencional)"],
      ["Recall",       "1.0000",  "100% das amostras alerta/critico/toxico detectadas como anômalas"],
      ["F1-Score",     "0.9917",  "Excelente equilíbrio precisão-revocação"],
    ],
    [24, 14, 62]
  ),
);
children.push(new Paragraph({ ...sp(160, 0), children: [] }));

children.push(heading2("3.4 Visão Computacional — NDWI"));
children.push(
  makeTable(
    [
      ["Zona", "Classe Detectada", "R médio", "G médio", "B médio", "NDWI", "Correto"],
      ["Zona A — Normal",  "normal",  "0.084", "0.212", "0.618", "+0.485", "✓"],
      ["Zona B — Alerta",  "alerta",  "0.320", "0.417", "0.285", "-0.206", "✓"],
      ["Zona C — Crítico", "critico", "0.579", "0.375", "0.105", "-0.565", "✓"],
      ["Zona D — Tóxico",  "toxico",  "0.368", "0.165", "0.079", "-0.346", "✓"],
    ],
    [22, 18, 10, 10, 10, 10, 10]
  ),
);
children.push(body("4/4 zonas classificadas corretamente. NDWI médio: -0.34 | Água limpa: 8.5% | Turbidez máx: 0.5146."));

children.push(heading2("3.5 Firebase Cloud Function — 4 Cenários"));
children.push(
  makeTable(
    [
      ["Cenário", "Ponto", "LSTM", "Conf.", "IF Anomalia", "Alerta"],
      ["Rio Limpo — Parque Nacional",  "PONTO-PN-001",  "NORMAL",  "92.7%", "SIM", "MEDIO"],
      ["Sedimentacao Agricola",         "PONTO-AGR-007", "ALERTA",  "48.3%", "SIM", "MEDIO"],
      ["Contaminação Industrial",       "PONTO-IND-023", "CRITICO", "89.0%", "SIM", "ALTO"],
      ["Descarte Ilegal de Efluentes",  "PONTO-ALE-099", "TOXICO",  "92.0%", "SIM", "CRITICO"],
    ],
    [32, 20, 12, 10, 14, 12]
  ),
);
children.push(new Paragraph({ ...sp(200, 0), children: [] }));
children.push(pageBreak());

// ─── 4. CONCLUSÃO ─────────────────────────────────────────────────────────────
children.push(heading1("4. Conclusão"), hr());
children.push(body(
  "O AquaWatch demonstrou com sucesso como a Inteligência Artificial e dados de satélite podem " +
  "transformar o monitoramento de recursos hídricos, respondendo diretamente ao tema da Sub GS " +
  "2026.1: tecnologias da economia espacial gerando impacto positivo na Terra."
));
children.push(body("Principais contribuições técnicas:"));

const contribuicoes = [
  ["LSTM Bidirecional com Atenção", "aprende padrões temporais de 24h de dados de sensor, atingindo 86.67% de acurácia — erros ocorrem apenas entre classes adjacentes, comportamento esperado e tecnicamente defensável."],
  ["Isolation Forest não-supervisionado", "detecta anomalias sem rótulo (F1=0.9917), complementando o LSTM para eventos inéditos."],
  ["NDWI adaptado para RGB sintético", "classifica 4 zonas de qualidade da água com análise espectral baseada na proporção B/G."],
  ["Firebase Cloud Function + USGS API", "arquitetura serverless diferente de AWS Lambda, integrando dado real de qualidade de água."],
  ["ESP32 com TDS + Turbidez + DS18B20", "sensores de qualidade da água reais, com classificação local baseada na CONAMA 357/2005."],
  ["Dashboard Dash", "callbacks reativos, classificador LSTM ao vivo com sliders, mapa geográfico e histórico MongoDB."],
];
contribuicoes.forEach(([bold, text]) => children.push(bullet(text, bold)));

children.push(body(
  "\nComo próximos passos: integração com imagens reais do Sentinel-2 via API Copernicus, " +
  "deploy da Firebase Function em produção com endpoint público, e expansão da rede de " +
  "sensores ESP32 para bacias hidrográficas brasileiras.",
  { ...sp(100, 0) }
));
children.push(pageBreak());

// ─── 5. LINKS ─────────────────────────────────────────────────────────────────
children.push(heading1("5. Links e Referências"), hr());

children.push(heading2("Repositório GitHub"));
children.push(body("[INSERIR LINK DO REPOSITÓRIO AQUI]"));

children.push(heading2("Vídeo Demonstrativo"));
children.push(body("[INSERIR LINK DO YOUTUBE NÃO LISTADO AQUI]"));

children.push(heading2("Referências Técnicas"));
const refs = [
  "USGS Water Quality Web Service: https://waterservices.usgs.gov/rest/IV-Service.html",
  "PyTorch LSTM Documentation: https://pytorch.org/docs/stable/generated/torch.nn.LSTM.html",
  "scikit-learn Isolation Forest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html",
  "Dash by Plotly Documentation: https://dash.plotly.com/",
  "DFRobot TDS Sensor SEN0189: https://wiki.dfrobot.com/Gravity__Analog_TDS_Sensor",
  "CONAMA Resolução 357/2005 — Padrões de qualidade da água",
  "McFeeters, S.K. (1996). Use of NDWI in delineation of open water features. Int. J. Remote Sensing, 17(7)",
  "ESA Sentinel-2 Multispectral: https://sentinel.esa.int/web/sentinel/missions/sentinel-2",
  "Firebase Cloud Functions: https://firebase.google.com/docs/functions",
  "HiveMQ MQTT Broker: https://www.hivemq.com/",
  "Arduino ESP32 Core: https://github.com/espressif/arduino-esp32",
];
refs.forEach((r) => children.push(bullet(r)));

// ═════════════════════════════════════════════════════════════════════════════
// MONTA O DOCUMENTO
// ═════════════════════════════════════════════════════════════════════════════
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 20 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: AZUL },
        paragraph: { spacing: { before: 300, after: 120 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: AZUL_CL },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: AZUL_CL },
        paragraph: { spacing: { before: 160, after: 60 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  const out = path.join(__dirname, "../outputs/AquaWatch_LucasAmorim_RM567505.docx");
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, buffer);
  console.log("[DOCX] Gerado:", out);
});
