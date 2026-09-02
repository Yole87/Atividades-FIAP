"""
AquaWatch — Módulo 1B: LSTM para Classificação de Qualidade da Água
Arquitetura LSTM (Long Short-Term Memory) treinada em séries temporais de
sensores de água — completamente diferente da CNN usada no OrbitalGuard.

Fluxo:
  dados/X_agua.npy  →  LSTMClassifier  →  modelos/lstm_agua.pth
                                        →  dados/metricas_lstm.json
"""

import numpy as np
import json
import os
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

# ─── Configuração ─────────────────────────────────────────────────────────────
SEED       = 42
EPOCHS     = 40
BATCH_SIZE = 32
LR         = 1e-3
HIDDEN_DIM = 64
N_LAYERS   = 2
DROPOUT    = 0.3

CLASSES = {0: "normal", 1: "alerta", 2: "critico", 3: "toxico"}
FEATURES = ["pH", "turbidez_NTU", "TDS_mgL", "temperatura_C", "OD_mgL", "condutividade_uScm"]

torch.manual_seed(SEED)
np.random.seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[DEVICE] Usando: {device}")

# ─── Modelo LSTM ──────────────────────────────────────────────────────────────
class LSTMClassifier(nn.Module):
    """
    LSTM bidirecional para classificação de séries temporais de qualidade da água.
    Entrada: (batch, timesteps=24, features=6)
    Saída:   (batch, 4 classes)
    """
    def __init__(self, input_dim, hidden_dim, n_layers, n_classes, dropout):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=n_layers,
            batch_first=True,
            bidirectional=True,   # bidirecional: captura padrão temporal nos dois sentidos
            dropout=dropout if n_layers > 1 else 0.0
        )
        self.attention = nn.Linear(hidden_dim * 2, 1)   # mecanismo de atenção simples
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, n_classes)
        )

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)           # (batch, seq_len, hidden*2)

        # Atenção: peso de cada timestep
        attn_scores = self.attention(lstm_out)       # (batch, seq_len, 1)
        attn_weights = torch.softmax(attn_scores, dim=1)
        context = (lstm_out * attn_weights).sum(dim=1)  # (batch, hidden*2)

        return self.classifier(context)

# ─── Carrega e prepara dados ──────────────────────────────────────────────────
print("\n[DADOS] Carregando dataset...")
X = np.load("dados/X_agua.npy")   # (800, 24, 6)
y = np.load("dados/y_agua.npy")   # (800,)
print(f"[DADOS] X: {X.shape} | y: {y.shape}")

# Normalização feature-wise (por feature, não por timestep)
n_samples, n_steps, n_feat = X.shape
X_flat = X.reshape(-1, n_feat)
scaler = StandardScaler()
X_norm = scaler.fit_transform(X_flat).reshape(n_samples, n_steps, n_feat)

# Split: 70% treino / 15% validação / 15% teste
X_train, X_temp, y_train, y_temp = train_test_split(
    X_norm, y, test_size=0.30, random_state=SEED, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=SEED, stratify=y_temp
)

print(f"[SPLIT] Treino: {len(y_train)} | Validação: {len(y_val)} | Teste: {len(y_test)}")

# Converte para tensores
def to_tensor(X, y):
    return TensorDataset(
        torch.FloatTensor(X).to(device),
        torch.LongTensor(y).to(device)
    )

train_ds = to_tensor(X_train, y_train)
val_ds   = to_tensor(X_val,   y_val)
test_ds  = to_tensor(X_test,  y_test)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE)
test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE)

# ─── Treino ───────────────────────────────────────────────────────────────────
model = LSTMClassifier(
    input_dim=n_feat,
    hidden_dim=HIDDEN_DIM,
    n_layers=N_LAYERS,
    n_classes=len(CLASSES),
    dropout=DROPOUT
).to(device)

criterion = nn.CrossEntropyLoss(label_smoothing=0.12)
optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

print(f"\n[LSTM] Iniciando treinamento — {EPOCHS} épocas com LSTM Bidirecional + Atenção...")
print(f"[AUGMENTAÇÃO] Dropout({DROPOUT}) | Weight Decay(1e-4) | LR scheduler adaptativo\n")

melhor_val_acc = 0.0
historico_treino = []

for epoch in range(1, EPOCHS + 1):
    # ── Treino ──
    model.train()
    train_loss, train_correct, train_total = 0.0, 0, 0

    for xb, yb in train_loader:
        optimizer.zero_grad()
        logits = model(xb)
        loss   = criterion(logits, yb)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)   # gradient clipping
        optimizer.step()

        train_loss    += loss.item() * len(yb)
        train_correct += (logits.argmax(1) == yb).sum().item()
        train_total   += len(yb)

    train_acc  = train_correct / train_total
    train_loss = train_loss / train_total

    # ── Validação ──
    model.eval()
    val_loss, val_correct, val_total = 0.0, 0, 0
    with torch.no_grad():
        for xb, yb in val_loader:
            logits = model(xb)
            loss   = criterion(logits, yb)
            val_loss    += loss.item() * len(yb)
            val_correct += (logits.argmax(1) == yb).sum().item()
            val_total   += len(yb)

    val_acc  = val_correct / val_total
    val_loss = val_loss / val_total
    scheduler.step(val_loss)

    historico_treino.append({
        "epoch": epoch,
        "train_loss": round(train_loss, 4),
        "train_acc":  round(train_acc,  4),
        "val_loss":   round(val_loss,   4),
        "val_acc":    round(val_acc,    4),
    })

    # Salva melhor modelo
    if val_acc > melhor_val_acc:
        melhor_val_acc = val_acc
        os.makedirs("modelos", exist_ok=True)
        torch.save(model.state_dict(), "modelos/lstm_agua.pth")

    print(f"  Época {epoch:02d}/{EPOCHS} | "
          f"Loss: {train_loss:.4f} | Acc: {train_acc:.4f} | "
          f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")

print(f"\n[MODELO] Melhor checkpoint salvo (Val Acc: {melhor_val_acc:.4f})")

# ─── Avaliação Final no Teste ─────────────────────────────────────────────────
model.load_state_dict(torch.load("modelos/lstm_agua.pth", map_location=device, weights_only=True))
model.eval()

all_preds, all_labels = [], []
with torch.no_grad():
    for xb, yb in test_loader:
        preds = model(xb).argmax(1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(yb.cpu().numpy())

acc_teste = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)

print(f"\n[RESULTADO] Acurácia no teste: {acc_teste:.4f} ({acc_teste*100:.2f}%)")
print("\n[RELATÓRIO] Por classe:")
report = classification_report(
    all_labels, all_preds,
    target_names=list(CLASSES.values()),
    output_dict=True
)
print(classification_report(all_labels, all_preds, target_names=list(CLASSES.values())))

cm = confusion_matrix(all_labels, all_preds)
print("[MATRIZ DE CONFUSÃO]")
print(cm)

# ─── Exemplos de Predição ─────────────────────────────────────────────────────
print("\n[PREVISÕES] Exemplos do conjunto de teste:")
print(f"{'Real':<15} {'Previsto':<15} {'Correto'}")
print("-" * 45)

indices_amostra = np.random.choice(len(all_labels), min(15, len(all_labels)), replace=False)
for idx in sorted(indices_amostra):
    real     = CLASSES[all_labels[idx]]
    previsto = CLASSES[all_preds[idx]]
    correto  = "✓" if real == previsto else "✗"
    print(f"  {real:<15} {previsto:<15} {correto}")

# ─── Salva métricas ───────────────────────────────────────────────────────────
metricas = {
    "modelo": "LSTM Bidirecional + Atenção",
    "epochs": EPOCHS,
    "hidden_dim": HIDDEN_DIM,
    "n_layers": N_LAYERS,
    "acuracia_teste": round(acc_teste, 4),
    "melhor_val_acc": round(melhor_val_acc, 4),
    "n_treino": len(y_train),
    "n_val": len(y_val),
    "n_teste": len(y_test),
    "relatorio_por_classe": report,
    "historico_treino": historico_treino,
    "matriz_confusao": cm.tolist()
}

with open("dados/metricas_lstm.json", "w", encoding="utf-8") as f:
    json.dump(metricas, f, indent=2, ensure_ascii=True)

# Salva parâmetros do scaler para uso no dashboard
scaler_params = {
    "mean": scaler.mean_.tolist(),
    "scale": scaler.scale_.tolist(),
    "features": FEATURES
}
with open("dados/scaler_params.json", "w", encoding="utf-8") as f:
    json.dump(scaler_params, f, indent=2)

print("\n[OK] Arquivos salvos:")
print("  → modelos/lstm_agua.pth")
print("  → dados/metricas_lstm.json")
print("  → dados/scaler_params.json")
print("\n[AQUAWATCH] LSTM treinado com sucesso!")
