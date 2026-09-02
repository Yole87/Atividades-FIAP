"""
AquaWatch — Módulo 2B: CNN para Classificação de Imagem de Satélite
Rede Neural Convolucional (PyTorch) treinada em patches de imagens
multiespectrais sintéticas para classificar qualidade da água em 4 classes.

Diferença em relação ao analisar_imagem.py:
  - analisar_imagem.py: análise espectral por limiares (NDWI, bandas RGB)
  - cnn_satelite.py:    aprendizado profundo — a CNN aprende os padrões
                        espectrais automaticamente a partir dos dados, sem
                        regras manuais de limiar.

Inspiração real:
  Satélites Sentinel-2 e Landsat produzem imagens multiespectrais que são
  classificadas por CNNs para detecção de qualidade de água, florescimento
  de algas e turbidez. Este módulo simula esse pipeline com dados sintéticos
  seguindo os mesmos índices espectrais (NDWI, dominância de banda R).

Fluxo:
  gerar_patches() → CNN (Conv→ReLU→Pool × 2 → FC) → treinar → avaliar
                 → modelos/cnn_satelite.pth
                 → dados/metricas_cnn.json
                 → vision/cnn_mapa_ativacao.png

Para rodar: python vision/cnn_satelite.py  (da raiz do projeto)
"""

import numpy as np
import json
import os
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ─── Configuração ─────────────────────────────────────────────────────────────
SEED          = 42
PATCH_SIZE    = 16      # patches 16×16 pixels extraídos da imagem de satélite
N_PATCHES_CLS = 300     # patches por classe gerados sinteticamente
EPOCHS        = 30
BATCH_SIZE    = 32
LR            = 1e-3

CLASSES = {0: "normal", 1: "alerta", 2: "critico", 3: "toxico"}
CORES   = {"normal": "#33ff99", "alerta": "#ffdd33", "critico": "#ff8833", "toxico": "#cc33cc"}

torch.manual_seed(SEED)
np.random.seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[DEVICE] Usando: {device}")

# ─── Geração de patches sintéticos ───────────────────────────────────────────
def gerar_patch_classe(classe_id, patch_size=PATCH_SIZE):
    """
    Gera um patch RGB (patch_size × patch_size × 3) simulando a assinatura
    espectral de cada classe de qualidade de água em imagem de satélite.

    Mapeamento espectral (inspirado em Sentinel-2):
      B (azul)  → profundidade / água limpa
      G (verde) → reflexão superficial / vegetação aquática
      R (vermelho) → turbidez / sedimento / efluente

    Parâmetros baseados em CONAMA 357/2005 e literatura de sensoriamento remoto.
    """
    patch = np.zeros((patch_size, patch_size, 3), dtype=np.float32)

    if classe_id == 0:  # NORMAL — água limpa e profunda
        patch[:, :, 0] = np.random.uniform(0.04, 0.12, (patch_size, patch_size))  # R baixo
        patch[:, :, 1] = np.random.uniform(0.15, 0.28, (patch_size, patch_size))  # G médio-baixo
        patch[:, :, 2] = np.random.uniform(0.50, 0.75, (patch_size, patch_size))  # B alto
    elif classe_id == 1:  # ALERTA — sedimento leve / vegetação aquática
        patch[:, :, 0] = np.random.uniform(0.20, 0.38, (patch_size, patch_size))  # R médio
        patch[:, :, 1] = np.random.uniform(0.35, 0.52, (patch_size, patch_size))  # G alto
        patch[:, :, 2] = np.random.uniform(0.22, 0.40, (patch_size, patch_size))  # B médio
    elif classe_id == 2:  # CRÍTICO — alta turbidez / efluente industrial
        patch[:, :, 0] = np.random.uniform(0.48, 0.72, (patch_size, patch_size))  # R alto
        patch[:, :, 1] = np.random.uniform(0.28, 0.44, (patch_size, patch_size))  # G médio
        patch[:, :, 2] = np.random.uniform(0.04, 0.14, (patch_size, patch_size))  # B baixo
    else:               # TÓXICO — descarte ilegal, efluente escuro
        patch[:, :, 0] = np.random.uniform(0.28, 0.46, (patch_size, patch_size))  # R médio
        patch[:, :, 1] = np.random.uniform(0.08, 0.20, (patch_size, patch_size))  # G muito baixo
        patch[:, :, 2] = np.random.uniform(0.03, 0.10, (patch_size, patch_size))  # B muito baixo

    # Zona de transição (30% das amostras com sobreposição entre classes adjacentes)
    if np.random.random() < 0.30 and classe_id < 3:
        alpha = np.random.uniform(0.35, 0.65)
        patch_next = gerar_patch_classe_puro(classe_id + 1, patch_size)
        patch = alpha * patch + (1 - alpha) * patch_next

    # Ruído de sensor (simulando variação atmosférica e radiométrica)
    patch += np.random.normal(0, 0.025, patch.shape)
    return np.clip(patch, 0, 1)


def gerar_patch_classe_puro(classe_id, patch_size=PATCH_SIZE):
    """Gera patch sem zona de transição (usado internamente para interpolação)."""
    patch = np.zeros((patch_size, patch_size, 3), dtype=np.float32)
    if classe_id == 0:
        patch[:,:,0] = np.random.uniform(0.04, 0.12, (patch_size, patch_size))
        patch[:,:,1] = np.random.uniform(0.15, 0.28, (patch_size, patch_size))
        patch[:,:,2] = np.random.uniform(0.50, 0.75, (patch_size, patch_size))
    elif classe_id == 1:
        patch[:,:,0] = np.random.uniform(0.20, 0.38, (patch_size, patch_size))
        patch[:,:,1] = np.random.uniform(0.35, 0.52, (patch_size, patch_size))
        patch[:,:,2] = np.random.uniform(0.22, 0.40, (patch_size, patch_size))
    elif classe_id == 2:
        patch[:,:,0] = np.random.uniform(0.48, 0.72, (patch_size, patch_size))
        patch[:,:,1] = np.random.uniform(0.28, 0.44, (patch_size, patch_size))
        patch[:,:,2] = np.random.uniform(0.04, 0.14, (patch_size, patch_size))
    else:
        patch[:,:,0] = np.random.uniform(0.28, 0.46, (patch_size, patch_size))
        patch[:,:,1] = np.random.uniform(0.08, 0.20, (patch_size, patch_size))
        patch[:,:,2] = np.random.uniform(0.03, 0.10, (patch_size, patch_size))
    patch += np.random.normal(0, 0.025, patch.shape)
    return np.clip(patch, 0, 1)


# ─── Arquitetura CNN ──────────────────────────────────────────────────────────
class CNNSatelite(nn.Module):
    """
    CNN para classificação de patches de imagem multiespectral de satélite.

    Entrada: (batch, 3, 16, 16) — patch RGB normalizado
    Saída:   (batch, 4)         — logits para 4 classes de qualidade

    Arquitetura:
      Conv1(3→16, 3×3) → BN → ReLU → MaxPool(2×2)   [16×16 → 8×8]
      Conv2(16→32, 3×3) → BN → ReLU → MaxPool(2×2)  [8×8  → 4×4]
      Flatten → FC(512→128) → ReLU → Dropout(0.4) → FC(128→4)

    Por que simples?
      Patches 16×16 têm baixa resolução espacial. CNNs profundas como ResNet
      seriam over-engineering — esta arquitetura é adequada ao tamanho do dado
      e converge rápido sem GPU.
    """
    def __init__(self, n_classes=4, dropout=0.4):
        super().__init__()
        self.features = nn.Sequential(
            # Bloco 1
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),          # 16×16 → 8×8

            # Bloco 2
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),          # 8×8 → 4×4
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 128),  # 32 filtros × 4×4 = 512
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(128, n_classes),
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)

    def feature_maps(self, x):
        """Retorna mapas de ativação do bloco 1 para visualização."""
        return self.features[:4](x)


# ─── Geração do dataset de patches ───────────────────────────────────────────
print("\n[PATCHES] Gerando dataset de patches de imagem de satélite...")
print(f"[CONFIG] {N_PATCHES_CLS} patches/classe × 4 classes | Patch: {PATCH_SIZE}×{PATCH_SIZE}×3\n")

X_patches, y_patches = [], []
for cls_id, cls_nome in CLASSES.items():
    for _ in range(N_PATCHES_CLS):
        patch = gerar_patch_classe(cls_id)
        X_patches.append(patch)
        y_patches.append(cls_id)
    print(f"  [CLASSE {cls_id}] '{cls_nome}' — {N_PATCHES_CLS} patches gerados")

X_patches = np.array(X_patches, dtype=np.float32)  # (1200, 16, 16, 3)
y_patches = np.array(y_patches)

# CNN espera (batch, C, H, W) — transpõe de (N, H, W, C) para (N, C, H, W)
X_patches = X_patches.transpose(0, 3, 1, 2)   # (1200, 3, 16, 16)

print(f"\n[DATASET] Shape X: {X_patches.shape} | Shape y: {y_patches.shape}")
print(f"[NOTA] 30% dos patches em zona de transição — acurácia não-trivial esperada\n")

# Split 70/15/15
X_tr, X_tmp, y_tr, y_tmp = train_test_split(X_patches, y_patches, test_size=0.30,
                                              random_state=SEED, stratify=y_patches)
X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.50,
                                              random_state=SEED, stratify=y_tmp)

print(f"[SPLIT] Treino: {len(y_tr)} | Validação: {len(y_val)} | Teste: {len(y_te)}")

def to_loader(X, y, shuffle=False):
    ds = TensorDataset(torch.FloatTensor(X).to(device),
                       torch.LongTensor(y).to(device))
    return DataLoader(ds, batch_size=BATCH_SIZE, shuffle=shuffle)

train_loader = to_loader(X_tr,  y_tr,  shuffle=True)
val_loader   = to_loader(X_val, y_val)
test_loader  = to_loader(X_te,  y_te)

# ─── Treino ───────────────────────────────────────────────────────────────────
model     = CNNSatelite(n_classes=len(CLASSES)).to(device)
criterion = nn.CrossEntropyLoss(label_smoothing=0.10)
optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

print(f"\n[CNN] Iniciando treinamento — {EPOCHS} épocas\n")

melhor_val_acc   = 0.0
historico_treino = []

for epoch in range(1, EPOCHS + 1):
    # Treino
    model.train()
    tr_loss, tr_corr, tr_tot = 0.0, 0, 0
    for xb, yb in train_loader:
        optimizer.zero_grad()
        logits = model(xb)
        loss   = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        tr_loss += loss.item() * len(yb)
        tr_corr += (logits.argmax(1) == yb).sum().item()
        tr_tot  += len(yb)

    # Validação
    model.eval()
    vl_loss, vl_corr, vl_tot = 0.0, 0, 0
    with torch.no_grad():
        for xb, yb in val_loader:
            logits  = model(xb)
            loss    = criterion(logits, yb)
            vl_loss += loss.item() * len(yb)
            vl_corr += (logits.argmax(1) == yb).sum().item()
            vl_tot  += len(yb)

    tr_acc = tr_corr / tr_tot
    vl_acc = vl_corr / vl_tot
    tr_loss /= tr_tot
    vl_loss /= vl_tot
    scheduler.step(vl_loss)

    historico_treino.append({
        "epoch": epoch,
        "train_loss": round(tr_loss, 4),
        "train_acc":  round(tr_acc,  4),
        "val_loss":   round(vl_loss, 4),
        "val_acc":    round(vl_acc,  4),
    })

    if vl_acc > melhor_val_acc:
        melhor_val_acc = vl_acc
        os.makedirs("modelos", exist_ok=True)
        torch.save(model.state_dict(), "modelos/cnn_satelite.pth")

    print(f"  Época {epoch:02d}/{EPOCHS} | "
          f"Loss: {tr_loss:.4f} | Acc: {tr_acc:.4f} | "
          f"Val Loss: {vl_loss:.4f} | Val Acc: {vl_acc:.4f}")

print(f"\n[CNN] Melhor checkpoint salvo (Val Acc: {melhor_val_acc:.4f})")

# ─── Avaliação no teste ────────────────────────────────────────────────────────
model.load_state_dict(torch.load("modelos/cnn_satelite.pth",
                                  map_location=device, weights_only=True))
model.eval()

all_preds, all_labels = [], []
with torch.no_grad():
    for xb, yb in test_loader:
        preds = model(xb).argmax(1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(yb.cpu().numpy())

acc_teste = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)

print(f"\n[RESULTADO] Acurácia no teste: {acc_teste:.4f} ({acc_teste*100:.2f}%)")
report = classification_report(all_labels, all_preds,
                                target_names=list(CLASSES.values()),
                                output_dict=True)
print("\n[RELATÓRIO] Por classe:")
print(classification_report(all_labels, all_preds, target_names=list(CLASSES.values())))
cm = confusion_matrix(all_labels, all_preds)
print("[MATRIZ DE CONFUSÃO]")
print(cm)

# ─── Visualização: mapas de ativação + exemplos ───────────────────────────────
print("\n[VIZ] Gerando visualização de ativações CNN...")
os.makedirs("vision", exist_ok=True)

fig, axes = plt.subplots(3, 4, figsize=(14, 10))
fig.patch.set_facecolor("#0d1117")
fig.suptitle("AquaWatch — CNN para Classificação de Imagem de Satélite",
             color="white", fontsize=14, fontweight="bold")

cores_plt = {"normal": "#33ff99", "alerta": "#ffdd33",
             "critico": "#ff8833", "toxico": "#cc33cc"}

for ax in axes.flat:
    ax.set_facecolor("#161b22")
    ax.tick_params(colors="white", labelsize=8)
    for sp in ax.spines.values():
        sp.set_color("#444")

# Linha 1: exemplo de patch por classe
for cls_id, cls_nome in CLASSES.items():
    patch_ex = gerar_patch_classe_puro(cls_id)
    axes[0, cls_id].imshow(patch_ex)
    axes[0, cls_id].set_title(f"Patch {cls_nome.upper()}",
                               color=cores_plt[cls_nome], fontsize=10)
    axes[0, cls_id].set_xticks([])
    axes[0, cls_id].set_yticks([])

# Linha 2: mapa de ativação (média dos filtros do bloco 1) por classe
model.eval()
for cls_id, cls_nome in CLASSES.items():
    patch_ex = gerar_patch_classe_puro(cls_id)
    t = torch.FloatTensor(patch_ex.transpose(2, 0, 1)).unsqueeze(0).to(device)
    with torch.no_grad():
        fmaps = model.feature_maps(t)       # (1, 16, 8, 8)
    act = fmaps[0].cpu().numpy().mean(axis=0)  # média dos 16 filtros → (8,8)
    im = axes[1, cls_id].imshow(act, cmap="hot", interpolation="nearest")
    axes[1, cls_id].set_title(f"Ativação — {cls_nome.upper()}",
                               color=cores_plt[cls_nome], fontsize=9)
    axes[1, cls_id].set_xticks([])
    axes[1, cls_id].set_yticks([])
    plt.colorbar(im, ax=axes[1, cls_id], fraction=0.046)

# Linha 3: curvas de treino (span 2 colunas) + matriz de confusão (span 2 colunas)
eps  = [h["epoch"]      for h in historico_treino]
tacc = [h["train_acc"]  for h in historico_treino]
vacc = [h["val_acc"]    for h in historico_treino]
tlos = [h["train_loss"] for h in historico_treino]
vlos = [h["val_loss"]   for h in historico_treino]

ax_curve = axes[2, 0]
ax_curve2 = axes[2, 1]

ax_curve.plot(eps, tacc, color="#33ff99", label="Train Acc", linewidth=1.5)
ax_curve.plot(eps, vacc, color="#58a6ff", label="Val Acc",   linewidth=1.5, linestyle="--")
ax_curve.set_title("Acurácia por Época", color="white", fontsize=9)
ax_curve.legend(fontsize=8, facecolor="#1e2530", labelcolor="white")
ax_curve.set_facecolor("#1e2530")
ax_curve.tick_params(colors="white")

ax_curve2.plot(eps, tlos, color="#ff8833", label="Train Loss", linewidth=1.5)
ax_curve2.plot(eps, vlos, color="#cc33cc", label="Val Loss",   linewidth=1.5, linestyle="--")
ax_curve2.set_title("Loss por Época", color="white", fontsize=9)
ax_curve2.legend(fontsize=8, facecolor="#1e2530", labelcolor="white")
ax_curve2.set_facecolor("#1e2530")
ax_curve2.tick_params(colors="white")

ax_cm = axes[2, 2]
im_cm = ax_cm.imshow(cm, cmap="Blues")
ax_cm.set_xticks(range(4))
ax_cm.set_yticks(range(4))
ax_cm.set_xticklabels([CLASSES[i].upper() for i in range(4)],
                       rotation=30, ha="right", color="white", fontsize=7)
ax_cm.set_yticklabels([CLASSES[i].upper() for i in range(4)],
                       color="white", fontsize=7)
ax_cm.set_title("Matriz de Confusão", color="white", fontsize=9)
for i in range(4):
    for j in range(4):
        ax_cm.text(j, i, str(cm[i, j]),
                   ha="center", va="center",
                   color="white" if cm[i, j] < cm.max() * 0.5 else "#0d1117",
                   fontsize=9)

ax_info = axes[2, 3]
ax_info.axis("off")
linhas = [
    f"CNN AquaWatch",
    f"Acc teste: {acc_teste*100:.1f}%",
    f"Val Acc:   {melhor_val_acc*100:.1f}%",
    f"Patches:   {len(y_patches)}",
    f"Épocas:    {EPOCHS}",
    f"Patch:     {PATCH_SIZE}×{PATCH_SIZE}×3",
    f"Arch:      Conv×2 → FC×2",
]
for i, linha in enumerate(linhas):
    cor = "#58a6ff" if i == 0 else ("#33ff99" if i in (1, 2) else "white")
    ax_info.text(0.05, 0.92 - i * 0.13, linha,
                 transform=ax_info.transAxes,
                 color=cor, fontsize=9,
                 fontfamily="monospace")

plt.tight_layout()
plt.savefig("vision/cnn_mapa_ativacao.png", dpi=110,
            bbox_inches="tight", facecolor="#0d1117")
plt.close()
print("  → vision/cnn_mapa_ativacao.png")

# ─── Salva métricas ───────────────────────────────────────────────────────────
metricas_cnn = {
    "modelo":           "CNN (Conv2d×2 + BN + MaxPool + FC×2)",
    "arquitetura":      "3→16→32 filtros | FC 512→128→4",
    "patch_size":       PATCH_SIZE,
    "n_patches_total":  int(len(y_patches)),
    "n_treino":         int(len(y_tr)),
    "n_val":            int(len(y_val)),
    "n_teste":          int(len(y_te)),
    "epochs":           EPOCHS,
    "acuracia_teste":   round(acc_teste, 4),
    "melhor_val_acc":   round(melhor_val_acc, 4),
    "relatorio_classes": report,
    "matriz_confusao":  cm.tolist(),
    "historico_treino": historico_treino,
    "nota": (
        "Dataset sintético com 30% de patches em zona de transição espectral. "
        "Parâmetros RGB baseados em assinaturas espectrais de satélites Sentinel-2/Landsat "
        "e normas de qualidade de água CONAMA 357/2005."
    )
}

os.makedirs("dados", exist_ok=True)
with open("dados/metricas_cnn.json", "w", encoding="utf-8") as f:
    json.dump(metricas_cnn, f, indent=2, ensure_ascii=True)

print("  → dados/metricas_cnn.json")
print("  → modelos/cnn_satelite.pth")
print(f"\n[AQUAWATCH] CNN treinada com sucesso! Acurácia: {acc_teste*100:.2f}%")
