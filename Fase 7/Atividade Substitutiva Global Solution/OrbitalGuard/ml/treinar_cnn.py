"""
OrbitalGuard — Treinamento da CNN de Classificação de Detritos Espaciais
Modelo: Convolutional Neural Network (PyTorch)
Data augmentation: flip, rotação, jitter de cor — força aprendizado por FORMA.
"""

import os
import sys
import json
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tinydb import TinyDB
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from model import OrbitalCNN, CLASSES, IMG_SIZE

BASE_DIR      = os.path.dirname(__file__)
DATASET_DIR   = os.path.join(BASE_DIR, "dataset")
LABELS_PATH   = os.path.join(BASE_DIR, "labels.json")
MODEL_PATH    = os.path.join(BASE_DIR, "modelo_cnn.pth")
METRICAS_PATH = os.path.join(BASE_DIR, "metricas.json")
DB_PATH       = os.path.join(BASE_DIR, "..", "db", "orbitalguard.json")
GRAFICO_PATH  = os.path.join(BASE_DIR, "historico_treino.png")

EPOCHS = 40
BATCH  = 32

# ── Augmentation: aplicado APENAS no treino ───────────────────────────────────
# RandomHorizontalFlip + RandomVerticalFlip: objeto pode aparecer em qualquer orientação
# RandomRotation: rotação até 45° — CNN não pode depender de orientação fixa
# ColorJitter: varia brilho/contraste/saturação — CNN não pode depender de cor exata
# RandomAffine: pequena translação e escala — generalização espacial
AUGMENTATION_TREINO = T.Compose([
    T.ToPILImage(),
    T.RandomHorizontalFlip(p=0.5),
    T.RandomVerticalFlip(p=0.5),
    T.RandomRotation(degrees=45),
    T.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.15),
    T.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.85, 1.15)),
    T.ToTensor(),
])

TRANSFORM_VAL = T.Compose([
    T.ToPILImage(),
    T.ToTensor(),
])


class DebritosDataset(Dataset):
    def __init__(self, imagens, labels, transform=None):
        # imagens: numpy (N, H, W, C) float32 0-1 → converter para uint8 para o transform
        self.X         = (imagens * 255).astype(np.uint8)
        self.y         = torch.tensor(labels, dtype=torch.long)
        self.transform = transform

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        img = self.X[idx]  # (H, W, C) uint8
        if self.transform:
            x = self.transform(img)   # → tensor (C, H, W) float 0-1
        else:
            x = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1) / 255.0
        return x, self.y[idx]


def carregar_dados():
    print("[DADOS] Carregando imagens do dataset...")
    with open(LABELS_PATH) as f:
        labels = json.load(f)
    X, y = [], []
    for item in labels:
        caminho = os.path.join(DATASET_DIR, item["arquivo"])
        img = Image.open(caminho).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
        X.append(np.array(img, dtype=np.float32) / 255.0)
        y.append(item["class_id"])
    print(f"[DADOS] {len(X)} imagens carregadas")
    return np.array(X), np.array(y)


def salvar_grafico(hist_loss, hist_acc, hist_val_loss, hist_val_acc):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#0a0a1a")
    for ax in [ax1, ax2]:
        ax.set_facecolor("#0d0d2b")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#334")

    ax1.plot(hist_acc,     color="#00ccff", label="Treino")
    ax1.plot(hist_val_acc, color="#ff6600", label="Validação")
    ax1.set_title("Acurácia por Época"); ax1.set_xlabel("Época"); ax1.set_ylabel("Acurácia")
    ax1.legend(facecolor="#0d0d2b", labelcolor="white")

    ax2.plot(hist_loss,     color="#00ccff", label="Treino")
    ax2.plot(hist_val_loss, color="#ff6600", label="Validação")
    ax2.set_title("Loss por Época"); ax2.set_xlabel("Época"); ax2.set_ylabel("Loss")
    ax2.legend(facecolor="#0d0d2b", labelcolor="white")

    plt.tight_layout()
    plt.savefig(GRAFICO_PATH, dpi=120, bbox_inches="tight", facecolor="#0a0a1a")
    plt.close()
    print(f"[GRÁFICO] Salvo em {GRAFICO_PATH}")


def treinar():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[DEVICE] Usando: {device}")
    print(f"[AUGMENTATION] Flip H/V + Rotação 45° + ColorJitter + Affine — CNN aprende FORMA")

    X, y = carregar_dados()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42
    )
    print(f"[SPLIT] Treino: {len(X_tr)} | Val: {len(X_val)} | Teste: {len(X_test)}")

    # Treino com augmentation, validação/teste sem
    train_loader = DataLoader(
        DebritosDataset(X_tr,   y_tr,   transform=AUGMENTATION_TREINO),
        batch_size=BATCH, shuffle=True
    )
    val_loader = DataLoader(
        DebritosDataset(X_val,  y_val,  transform=TRANSFORM_VAL),
        batch_size=BATCH
    )
    test_loader = DataLoader(
        DebritosDataset(X_test, y_test, transform=TRANSFORM_VAL),
        batch_size=BATCH
    )

    modelo     = OrbitalCNN().to(device)
    criterio   = nn.CrossEntropyLoss()
    otimizador = optim.Adam(modelo.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler  = optim.lr_scheduler.CosineAnnealingLR(otimizador, T_max=EPOCHS)

    hist_loss, hist_acc, hist_val_loss, hist_val_acc = [], [], [], []
    melhor_acc_val = 0.0

    print(f"\n[CNN] Iniciando treinamento — {EPOCHS} épocas com data augmentation...")
    for epoca in range(1, EPOCHS + 1):
        modelo.train()
        total_loss, total_correct, total = 0, 0, 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            otimizador.zero_grad()
            pred = modelo(xb)
            loss = criterio(pred, yb)
            loss.backward()
            otimizador.step()
            total_loss    += loss.item() * len(yb)
            total_correct += (pred.argmax(1) == yb).sum().item()
            total         += len(yb)
        ep_loss = total_loss / total
        ep_acc  = total_correct / total

        modelo.eval()
        v_loss, v_correct, v_total = 0, 0, 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                pred    = modelo(xb)
                v_loss += criterio(pred, yb).item() * len(yb)
                v_correct += (pred.argmax(1) == yb).sum().item()
                v_total   += len(yb)
        vl = v_loss / v_total
        va = v_correct / v_total

        # Salva o melhor modelo por val_acc
        if va > melhor_acc_val:
            melhor_acc_val = va
            torch.save(modelo.state_dict(), MODEL_PATH)

        scheduler.step()
        hist_loss.append(ep_loss); hist_acc.append(ep_acc)
        hist_val_loss.append(vl);  hist_val_acc.append(va)

        print(f"  Época {epoca:02d}/{EPOCHS} | Loss: {ep_loss:.4f} | Acc: {ep_acc:.4f} | Val Loss: {vl:.4f} | Val Acc: {va:.4f}")

    # Avaliação no teste com o MELHOR modelo salvo
    print(f"\n[MODELO] Carregando melhor checkpoint (Val Acc: {melhor_acc_val:.4f})...")
    modelo.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    modelo.eval()

    all_preds, all_true = [], []
    with torch.no_grad():
        for xb, yb in test_loader:
            xb = xb.to(device)
            all_preds.extend(modelo(xb).argmax(1).cpu().numpy())
            all_true.extend(yb.numpy())

    acc_final = sum(p == t for p, t in zip(all_preds, all_true)) / len(all_true)
    print(f"\n[MODELO] Acurácia no teste: {acc_final:.4f}")
    print(f"[NOTA]   Acurácia < 100% esperada — CNN aprende forma com cores sobrepostas + augmentation")
    print(f"\n[RELATÓRIO] Por classe:")
    print(classification_report(all_true, all_preds, target_names=CLASSES))

    metricas = {
        "acuracia":        round(acc_final, 4),
        "loss":            round(min(hist_val_loss), 4),
        "amostras_treino": int(len(X_tr)),
        "amostras_teste":  int(len(X_test)),
        "epocas":          EPOCHS,
        "melhor_val_acc":  round(melhor_acc_val, 4),
        "classes":         CLASSES,
        "augmentation":    "Flip H/V + Rotation45 + ColorJitter + RandomAffine",
        "timestamp":       datetime.now().isoformat()
    }
    with open(METRICAS_PATH, "w") as f:
        json.dump(metricas, f, indent=2)
    print(f"[MÉTRICAS] Salvas em {METRICAS_PATH}")

    # TinyDB — limpa e insere
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = TinyDB(DB_PATH)
    db.table("treinos").truncate()
    db.table("predicoes").truncate()
    db.table("treinos").insert(metricas)
    print(f"[TINYDB] Banco limpo e métricas inseridas")

    print("\n[PREVISÃO] Exemplos do conjunto de teste:")
    db_preds = db.table("predicoes")
    with torch.no_grad():
        for i in range(min(8, len(X_test))):
            xb = torch.tensor(X_test[i:i+1], dtype=torch.float32).permute(0,3,1,2).to(device)
            prob      = torch.softmax(modelo(xb), dim=1).cpu().numpy()[0]
            pred_id   = int(np.argmax(prob))
            real_id   = int(y_test[i])
            confianca = float(prob[pred_id])
            risco     = "ALTO" if pred_id in [1, 2] else "BAIXO"
            acerto    = "✓" if pred_id == real_id else "✗"
            print(f"  {acerto} Real: {CLASSES[real_id]:<22} | Previsto: {CLASSES[pred_id]:<22} | Confiança: {confianca:.2%} | Risco: {risco}")
            db_preds.insert({
                "objeto_real":     CLASSES[real_id],
                "objeto_previsto": CLASSES[pred_id],
                "confianca":       round(confianca, 4),
                "nivel_risco":     risco,
                "timestamp":       datetime.now().isoformat()
            })

    salvar_grafico(hist_loss, hist_acc, hist_val_loss, hist_val_acc)

    print(f"\n[OK] Arquivos salvos em ml/")
    print(f"  → ml/modelo_cnn.pth  (melhor checkpoint)")
    print(f"  → ml/metricas.json")
    print(f"  → ml/historico_treino.png")
    print(f"  → db/orbitalguard.json (banco limpo e atualizado)")


if __name__ == "__main__":
    treinar()
