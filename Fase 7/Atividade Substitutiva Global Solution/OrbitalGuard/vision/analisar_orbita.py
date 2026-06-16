"""
OrbitalGuard — Análise de Imagem Orbital
Monta cena como grid de objetos 64x64 (sem redimensionamento),
garantindo consistência visual com o treino da CNN.
"""

import os, sys, json
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image, ImageDraw, ImageFilter
import torch
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))
from model import OrbitalCNN, CLASSES, IMG_SIZE
from gerar_dataset import (
    gerar_satelite_ativo, gerar_detrito_metalico,
    gerar_fragmento_rochoso, gerar_satelite_inativo,
)

BASE_DIR       = os.path.dirname(__file__)
MODEL_PATH     = os.path.join(BASE_DIR, "..", "ml", "modelo_cnn.pth")
RESULTADO_PATH = os.path.join(BASE_DIR, "resultado_visao.json")
MAPA_PATH      = os.path.join(BASE_DIR, "mapa_orbital.png")
IMAGEM_PATH    = os.path.join(BASE_DIR, "cena_orbital.png")

CORES_BGR = {
    "satelite_ativo":    (255, 220,  50),
    "detrito_metalico":  ( 50,  50, 255),
    "fragmento_rochoso": ( 50, 165, 255),
    "satelite_inativo":  (200, 200, 200),
}
RISCO = {
    "satelite_ativo":   "BAIXO",
    "detrito_metalico": "ALTO",
    "fragmento_rochoso":"ALTO",
    "satelite_inativo": "MEDIO",
}

# 6 objetos: 2 de cada classe de risco alto + 1 de cada baixo/médio
OBJETOS_CENA = [
    {"gerador": gerar_satelite_ativo,    "classe_id": 0, "seed": 101},
    {"gerador": gerar_detrito_metalico,  "classe_id": 1, "seed": 202},
    {"gerador": gerar_fragmento_rochoso, "classe_id": 2, "seed": 303},
    {"gerador": gerar_satelite_inativo,  "classe_id": 3, "seed": 404},
    {"gerador": gerar_detrito_metalico,  "classe_id": 1, "seed": 505},
    {"gerador": gerar_fragmento_rochoso, "classe_id": 2, "seed": 606},
]

# Grid 3x2, cada célula 64x64, separadas por borda escura de 20px
COLS, ROWS = 3, 2
PAD = 20
CELL = IMG_SIZE  # 64


def gerar_cena_orbital():
    """Monta cena como grid 3x2 de objetos 64x64 nativos — sem redimensionamento."""
    W = COLS * CELL + (COLS + 1) * PAD
    H = ROWS * CELL + (ROWS + 1) * PAD

    # Fundo escuro estelar
    fundo = np.zeros((H, W, 3), dtype=np.uint8)
    rng_f = np.random.default_rng(77)
    for _ in range(400):
        x, y = rng_f.integers(0, W), rng_f.integers(0, H)
        b    = rng_f.integers(80, 220)
        fundo[y, x] = [b, b, b]

    posicoes = []  # (x0, y0) de cada objeto na cena
    for idx, cfg in enumerate(OBJETOS_CENA):
        col = idx % COLS
        row = idx // COLS
        x0  = PAD + col * (CELL + PAD)
        y0  = PAD + row * (CELL + PAD)

        # Gera objeto 64x64 com seed fixa — mesmo estilo do dataset
        rng_obj = np.random.default_rng(cfg["seed"])
        obj_img = cfg["gerador"](rng_obj)  # PIL 64x64
        obj_arr = np.array(obj_img)

        fundo[y0:y0+CELL, x0:x0+CELL] = obj_arr
        posicoes.append((x0, y0, CELL, CELL, cfg["classe_id"]))

    cena = Image.fromarray(fundo)
    cena.save(IMAGEM_PATH)
    print(f"[CENA] Grid {COLS}x{ROWS} gerado: {IMAGEM_PATH} ({W}x{H}px)")
    return np.array(cena), posicoes


def classificar_cena(img_array, posicoes, modelo, device):
    """Classifica cada célula do grid diretamente — sem detecção por contorno."""
    resultados = []
    modelo.eval()
    with torch.no_grad():
        for (x0, y0, w, h, classe_real) in posicoes:
            recorte  = img_array[y0:y0+h, x0:x0+w]
            rec_norm = np.array(
                Image.fromarray(recorte).resize((IMG_SIZE, IMG_SIZE)),
                dtype=np.float32
            ) / 255.0
            tensor  = torch.tensor(rec_norm).permute(2, 0, 1).unsqueeze(0).to(device)
            prob    = torch.softmax(modelo(tensor), dim=1).cpu().numpy()[0]
            pred_id = int(np.argmax(prob))
            acerto  = "OK" if pred_id == classe_real else "ERRO"
            resultados.append({
                "bbox":        [x0, y0, w, h],
                "classe_real": CLASSES[classe_real],
                "classe":      CLASSES[pred_id],
                "confianca":   round(float(prob[pred_id]), 4),
                "nivel_risco": RISCO[CLASSES[pred_id]],
                "acerto":      acerto,
            })
    return resultados


def gerar_mapa(img_array, resultados):
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    for r in resultados:
        x, y, w, h = r["bbox"]
        cor   = CORES_BGR[r["classe"]]
        cv2.rectangle(img_bgr, (x, y), (x+w, y+h), cor, 2)
        label = f"{r['acerto']} {r['classe']}"
        conf  = f"{r['confianca']:.0%}"
        ty    = min(y + h - 6, img_bgr.shape[0] - 6)
        cv2.putText(img_bgr, label, (x+2, ty - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, cor, 1, cv2.LINE_AA)
        cv2.putText(img_bgr, conf, (x+2, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, cor, 1, cv2.LINE_AA)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#0a0a1a")
    ax.imshow(img_rgb)
    ax.set_title("OrbitalGuard — Mapa de Risco Orbital", color="white", fontsize=13)
    ax.axis("off")
    patches = [
        mpatches.Patch(color=(1,.86,.2),    label="Satélite Ativo — Risco BAIXO"),
        mpatches.Patch(color=(1,.2,.2),     label="Detrito Metálico — Risco ALTO"),
        mpatches.Patch(color=(1,.65,.2),    label="Fragmento Rochoso — Risco ALTO"),
        mpatches.Patch(color=(.78,.78,.78), label="Satélite Inativo — Risco MÉDIO"),
    ]
    ax.legend(handles=patches, loc="lower left", fontsize=8,
              facecolor="#0d0d2b", labelcolor="white", edgecolor="#334")
    plt.tight_layout()
    plt.savefig(MAPA_PATH, dpi=120, bbox_inches="tight", facecolor="#0a0a1a")
    plt.close()
    print(f"[MAPA] Salvo em {MAPA_PATH}")


def analisar():
    print("=" * 52)
    print("  OrbitalGuard — Análise de Imagem Orbital")
    print("=" * 52)

    if not os.path.exists(MODEL_PATH):
        print("[ERRO] Modelo não encontrado. Execute treinar_cnn.py primeiro.")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    modelo = OrbitalCNN()
    modelo.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    modelo.to(device)
    print(f"[CNN] Modelo carregado ({device})")

    img_array, posicoes = gerar_cena_orbital()
    resultados = classificar_cena(img_array, posicoes, modelo, device)
    gerar_mapa(img_array, resultados)

    cobertura     = {}
    acertos       = sum(1 for r in resultados if r["acerto"] == "OK")
    for r in resultados:
        cobertura[r["classe"]] = cobertura.get(r["classe"], 0) + 1
    cobertura_pct = {k: round(v/len(resultados)*100, 1) for k, v in cobertura.items()}

    print(f"\n[RESULTADOS] {len(resultados)} objetos classificados ({acertos}/{len(resultados)} corretos):")
    print(f"  {'Acerto'} {'Classe Real':<22} {'Previsto':<22} {'Conf':>7} {'Risco':>6}")
    print(f"  {'-'*65}")
    for r in resultados:
        print(f"  {r['acerto']}  {r['classe_real']:<22} {r['classe']:<22} {r['confianca']:>6.1%} {r['nivel_risco']:>6}")

    print(f"\n[COBERTURA] {cobertura_pct}")

    with open(RESULTADO_PATH, "w") as f:
        json.dump({
            "timestamp":          datetime.now().isoformat(),
            "objetos_detectados": len(resultados),
            "acertos":            acertos,
            "resultados":         resultados,
            "cobertura_pct":      cobertura_pct
        }, f, indent=2, ensure_ascii=True)

    print(f"\n[OK] → vision/mapa_orbital.png | vision/resultado_visao.json")


if __name__ == "__main__":
    analisar()