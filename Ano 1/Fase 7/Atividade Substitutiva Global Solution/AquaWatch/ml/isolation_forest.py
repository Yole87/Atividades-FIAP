"""
AquaWatch — Módulo 1C: Isolation Forest para Detecção de Anomalias
Algoritmo não-supervisionado que identifica leituras anômalas de sensores
de qualidade da água em tempo real, complementando o LSTM.

Diferença arquitetural:
  - LSTM: classifica o TIPO da contaminação (série temporal supervisionada)
  - Isolation Forest: detecta se a leitura É anômala (snapshot não-supervisionado)

Casos de uso:
  - Sensor IoT manda 1 leitura instantânea → IF decide se é anômalo
  - LSTM precisa de 24 horas de histórico → avaliação de tendência
"""

import numpy as np
import json
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import pickle

SEED    = 42
CLASSES = {0: "normal", 1: "alerta", 2: "critico", 3: "toxico"}
FEATURES = ["pH", "turbidez_NTU", "TDS_mgL", "temperatura_C", "OD_mgL", "condutividade_uScm"]

np.random.seed(SEED)

# ─── Carrega dataset ──────────────────────────────────────────────────────────
print("[AQUAWATCH] Isolation Forest — Detecção de Anomalias em Tempo Real")
print("[DADOS] Carregando dataset...")

X_series = np.load("dados/X_agua.npy")  # (800, 24, 6)
y_series = np.load("dados/y_agua.npy")  # (800,)

# Para IF: usa média dos timesteps como snapshot (1 vetor por amostra)
X_snapshot = X_series.mean(axis=1)   # (800, 6) — média temporal de cada parâmetro
print(f"[DADOS] X snapshot: {X_snapshot.shape} | y: {y_series.shape}")

# ─── Normaliza ────────────────────────────────────────────────────────────────
scaler = StandardScaler()
X_norm = scaler.fit_transform(X_snapshot)

# ─── Treina APENAS com amostras normais (unsupervised) ────────────────────────
# Isolamento Forest aprende o que é "normal" e detecta o que desvia
X_normal = X_norm[y_series == 0]   # apenas classe 0 = normal
print(f"[TREINO] IF treinado em {len(X_normal)} amostras normais (unsupervised)")

iso_forest = IsolationForest(
    n_estimators=200,
    contamination=0.05,    # espera até 5% de contaminação no stream real
    random_state=SEED,
    max_samples="auto"
)
iso_forest.fit(X_normal)

# ─── Avaliação em todo o dataset ──────────────────────────────────────────────
# IF retorna: +1 = normal (inlier), -1 = anômalo (outlier)
preds_raw = iso_forest.predict(X_norm)
scores    = iso_forest.score_samples(X_norm)  # anomaly score (mais negativo = mais anômalo)

# Converte para binário: 0 = normal, 1 = anomalia
preds_bin = np.where(preds_raw == 1, 0, 1)
labels_bin = np.where(y_series == 0, 0, 1)   # 0=normal, 1=qualquer contaminação

print(f"\n[ISOLATION FOREST] Resultados:")
print(f"  Amostras normais detectadas: {(preds_bin == 0).sum()}")
print(f"  Anomalias detectadas:        {(preds_bin == 1).sum()}")
print(f"  Total amostras:              {len(preds_bin)}")

# Métricas binárias
tp = ((preds_bin == 1) & (labels_bin == 1)).sum()
tn = ((preds_bin == 0) & (labels_bin == 0)).sum()
fp = ((preds_bin == 1) & (labels_bin == 0)).sum()
fn = ((preds_bin == 0) & (labels_bin == 1)).sum()

precisao  = tp / (tp + fp) if (tp + fp) > 0 else 0
recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
f1        = 2 * precisao * recall / (precisao + recall) if (precisao + recall) > 0 else 0
acuracia  = (tp + tn) / len(preds_bin)

print(f"\n[MÉTRICAS BINÁRIAS] Normal vs Anomalia:")
print(f"  Precision : {precisao:.4f}")
print(f"  Recall    : {recall:.4f}")
print(f"  F1-Score  : {f1:.4f}")
print(f"  Acurácia  : {acuracia:.4f}")

# Detalhamento por classe real
print(f"\n[DETECÇÃO POR CLASSE]")
print(f"  {'Classe':<15} {'Total':<8} {'Detectadas como anomalia':<25} {'Taxa detecção'}")
print(f"  {'-'*60}")
for cls_id, cls_nome in CLASSES.items():
    mask = y_series == cls_id
    n_total = mask.sum()
    n_detectado = ((preds_bin == 1) & mask).sum()
    taxa = n_detectado / n_total if n_total > 0 else 0
    flag = "✓" if (cls_id == 0 and taxa < 0.3) or (cls_id > 0 and taxa > 0.5) else "~"
    print(f"  {flag} {cls_nome:<13} {n_total:<8} {n_detectado:<25} {taxa:.1%}")

# ─── Simulação de leitura em tempo real (IoT) ─────────────────────────────────
print(f"\n[TEMPO REAL] Simulando leituras de sensor IoT em tempo real...")
print(f"{'Leitura':<8} {'pH':>6} {'Turb':>8} {'TDS':>8} {'Temp':>7} {'OD':>6} {'Cond':>8} | {'Status':<15} {'Score'}")
print("-" * 85)

cenarios_tempo_real = [
    # (nome, pH, turbidez, TDS, temperatura, OD, condutividade)
    ("Rio-001", 7.1,  1.2,  230,  19.5,  8.2, 380),
    ("Rio-002", 6.8,  2.1,  310,  21.0,  7.5, 450),
    ("Rio-003", 5.5,  12.0, 620,  28.0,  4.1, 1200),
    ("Rio-004", 4.2,  45.0, 980,  31.5,  2.3, 2500),
    ("Rio-005", 3.1,  95.0, 1950, 36.0,  0.5, 4200),
    ("Rio-006", 6.9,  3.5,  290,  20.0,  7.8, 420),
    ("Rio-007", 5.8,  8.0,  510,  27.0,  4.8, 980),
    ("Rio-008", 7.3,  0.9,  205,  18.0,  8.5, 350),
]

resultados_rt = []
for nome, pH, turb, TDS, temp, OD, cond in cenarios_tempo_real:
    leitura = np.array([[pH, turb, TDS, temp, OD, cond]])
    leitura_norm = scaler.transform(leitura)
    pred = iso_forest.predict(leitura_norm)[0]
    score = iso_forest.score_samples(leitura_norm)[0]
    status = "NORMAL" if pred == 1 else "⚠ ANOMALIA"

    print(f"  {nome:<8} {pH:>6.1f} {turb:>8.1f} {TDS:>8.0f} {temp:>7.1f} {OD:>6.1f} {cond:>8.0f} "
          f"| {status:<15} {score:.4f}")

    resultados_rt.append({
        "ponto": nome,
        "pH": pH, "turbidez": turb, "TDS": TDS,
        "temperatura": temp, "OD": OD, "condutividade": cond,
        "status": status.replace("⚠ ", ""),
        "anomaly_score": round(score, 4)
    })

# ─── Salva modelo e resultados ────────────────────────────────────────────────
os.makedirs("modelos", exist_ok=True)
os.makedirs("dados", exist_ok=True)

with open("modelos/isolation_forest.pkl", "wb") as f:
    pickle.dump({"modelo": iso_forest, "scaler": scaler}, f)

metricas_if = {
    "modelo": "Isolation Forest",
    "n_estimators": 200,
    "contamination": 0.05,
    "acuracia_binaria": round(acuracia, 4),
    "precision": round(precisao, 4),
    "recall": round(recall, 4),
    "f1_score": round(f1, 4),
    "anomalias_detectadas": int((preds_bin == 1).sum()),
    "total_amostras": int(len(preds_bin)),
    "leituras_tempo_real": resultados_rt
}

with open("dados/metricas_if.json", "w", encoding="utf-8") as f:
    json.dump(metricas_if, f, indent=2, ensure_ascii=True)

print(f"\n[OK] Arquivos salvos:")
print(f"  → modelos/isolation_forest.pkl")
print(f"  → dados/metricas_if.json")
print(f"\n[AQUAWATCH] Isolation Forest treinado com sucesso!")
