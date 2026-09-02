"""
AquaWatch — Módulo 2: Visão Computacional — Análise Espectral de Imagens de Satélite
Simula análise de bandas espectrais de imagens de satélite (Sentinel-2 / Landsat)
para detecção visual de qualidade da água via NDWI e índices espectrais.

Técnicas aplicadas (completamente diferentes do OrbitalGuard e AgroSat):
  - NDWI  : Normalized Difference Water Index (detecta água limpa via B-G/B+G)
  - Análise de bandas RGB sintéticas (proxy multiespectral)
  - Segmentação de 4 zonas: normal, alerta, crítico, tóxico
  - Mapa de turbidez por dominância espectral da banda vermelha
  - Classificação por limiares de bandas RGB

Inspiração real: satélites Sentinel-2 usam banda B3 (verde) e B8 (NIR)
para NDWI = (B3 - B8) / (B3 + B8). Adaptação RGB: B≈profundidade, R≈turbidez.
"""

import numpy as np
import json
import os
from skimage.filters import gaussian
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

SEED = 42
np.random.seed(SEED)
IMG_SIZE = 256

def gerar_imagem_satelite():
    """
    Gera imagem sintética que simula dados multiespectrais de satélite.
      R alto → turbidez/sedimento/efluente
      G alto → reflexão vegetal superficial
      B alto → água limpa e profunda
    """
    img = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.float32)
    img[:,:,0] = np.random.uniform(0.15, 0.30, (IMG_SIZE, IMG_SIZE))
    img[:,:,1] = np.random.uniform(0.30, 0.50, (IMG_SIZE, IMG_SIZE))
    img[:,:,2] = np.random.uniform(0.10, 0.20, (IMG_SIZE, IMG_SIZE))

    # Zona NORMAL: B alto, R baixo (água limpa e profunda)
    img[40:120, 30:100, 0] = np.random.uniform(0.05, 0.10, (80, 70))
    img[40:120, 30:100, 1] = np.random.uniform(0.15, 0.25, (80, 70))
    img[40:120, 30:100, 2] = np.random.uniform(0.55, 0.75, (80, 70))

    # Zona ALERTA: G alto, B médio (sedimento leve / vegetação aquática)
    img[50:120, 120:200, 0] = np.random.uniform(0.20, 0.35, (70, 80))
    img[50:120, 120:200, 1] = np.random.uniform(0.35, 0.50, (70, 80))
    img[50:120, 120:200, 2] = np.random.uniform(0.25, 0.40, (70, 80))

    # Zona CRÍTICO: R alto, B baixo (alta turbidez / sedimento)
    img[100:190, 160:230, 0] = np.random.uniform(0.50, 0.70, (90, 70))
    img[100:190, 160:230, 1] = np.random.uniform(0.30, 0.45, (90, 70))
    img[100:190, 160:230, 2] = np.random.uniform(0.05, 0.15, (90, 70))

    # Zona TÓXICO: R médio, G muito baixo, B muito baixo (efluente industrial)
    img[160:230, 60:160, 0] = np.random.uniform(0.30, 0.45, (70, 100))
    img[160:230, 60:160, 1] = np.random.uniform(0.10, 0.20, (70, 100))
    img[160:230, 60:160, 2] = np.random.uniform(0.05, 0.10, (70, 100))

    # Suavização
    for c in range(3):
        img[:,:,c] = gaussian(img[:,:,c], sigma=3)
    return np.clip(img, 0, 1)

def calcular_ndwi(img):
    """
    NDWI adaptado para RGB sintético:
    NDWI = (B - G) / (B + G)
    B alto (água limpa) → NDWI positivo
    G alto (vegetação/superfície) → NDWI negativo
    Limiar > 0.1 = zona de água limpa detectada
    """
    B = img[:,:,2]
    G = img[:,:,1]
    return np.where((B + G) > 0, (B - G) / (B + G), 0)

def calcular_turbidez(img):
    """Turbidez espectral: dominância da banda R sobre B."""
    R = img[:,:,0]
    B = img[:,:,2]
    return np.clip(R - B, 0, 1)

def classificar_zona_espectral(img, y, x, h, w):
    """Classifica zona por análise de bandas RGB médias."""
    roi = img[y:y+h, x:x+w]
    R = roi[:,:,0].mean()
    G = roi[:,:,1].mean()
    B = roi[:,:,2].mean()

    if B > 0.40 and R < 0.15:
        return "normal",  (R, G, B), "#3399ff"
    elif G > 0.30 and B > 0.20 and R < 0.40:
        return "alerta",  (R, G, B), "#33cc66"
    elif R > 0.45 and B < 0.20:
        return "critico", (R, G, B), "#ff8833"
    elif R > 0.25 and G < 0.25 and B < 0.15:
        return "toxico",  (R, G, B), "#cc33cc"
    else:
        return "alerta",  (R, G, B), "#33cc66"

def main():
    print("[AQUAWATCH] Módulo de Visão Computacional — Análise Espectral de Satélite")
    print(f"[CONFIG] Resolução: {IMG_SIZE}x{IMG_SIZE} | Técnica: NDWI + análise de bandas RGB\n")

    os.makedirs("dados", exist_ok=True)
    os.makedirs("vision", exist_ok=True)

    print("[1/5] Gerando imagem sintética de satélite...")
    img = gerar_imagem_satelite()
    print(f"  Shape: {img.shape} | Dtype: {img.dtype} | Faixa: [{img.min():.3f}, {img.max():.3f}]")

    print("[2/5] Calculando NDWI (B-G)/(B+G)...")
    ndwi = calcular_ndwi(img)
    mascara_agua_limpa = ndwi > 0.10
    pct_agua = mascara_agua_limpa.mean() * 100
    print(f"  NDWI médio: {ndwi.mean():.4f} | Pixels de água limpa: {pct_agua:.1f}%")

    print("[3/5] Calculando mapa de turbidez espectral (R - B)...")
    turbidez_map = calcular_turbidez(img)
    turb_media = turbidez_map.mean()
    print(f"  Turbidez média: {turb_media:.4f} | Máxima: {turbidez_map.max():.4f}")

    print("[4/5] Segmentando e classificando zonas de qualidade...")
    zonas_def = [
        ("Zona A — Normal",   40,  30, 80,  70),
        ("Zona B — Alerta",   50, 120, 70,  80),
        ("Zona C — Crítico", 100, 160, 90,  70),
        ("Zona D — Tóxico",  160,  60, 70, 100),
    ]
    esperado = ["normal", "alerta", "critico", "toxico"]

    resultados_zonas = []
    print(f"\n  {'Zona':<22} {'Classe':<12} {'R médio':>8} {'G médio':>8} {'B médio':>8} {'NDWI':>7}")
    print(f"  {'-'*70}")

    for (nome, y, x, h, w), cls_esp in zip(zonas_def, esperado):
        cls, (R, G, B), cor = classificar_zona_espectral(img, y, x, h, w)
        roi_ndwi = ndwi[y:y+h, x:x+w].mean()
        ok = "✓" if cls == cls_esp else "~"
        print(f"  {ok} {nome:<20} {cls:<12} {R:>8.3f} {G:>8.3f} {B:>8.3f} {roi_ndwi:>7.3f}")
        resultados_zonas.append({
            "zona": nome, "classe_detectada": cls,
            "esperado": cls_esp, "correto": cls == cls_esp,
            "R": round(float(R),4), "G": round(float(G),4), "B": round(float(B),4),
            "ndwi_medio": round(float(roi_ndwi),4)
        })

    corretos = sum(1 for z in resultados_zonas if z["correto"])
    print(f"\n  [RESULTADO] {corretos}/{len(zonas_def)} zonas classificadas corretamente")

    print("\n[5/5] Gerando visualização multiespectral...")
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.patch.set_facecolor("#0d1117")
    fig.suptitle("AquaWatch — Análise Espectral de Imagem de Satélite",
                 color="white", fontsize=16, fontweight="bold")

    for ax in axes.flat:
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="white")
        for sp in ax.spines.values(): sp.set_color("#444")

    # 1. Imagem RGB
    axes[0,0].imshow(img)
    axes[0,0].set_title("Imagem Sintética (RGB Multiespectral)", color="white", fontsize=10)

    # 2. NDWI
    im2 = axes[0,1].imshow(ndwi, cmap="RdYlGn", vmin=-1, vmax=1)
    axes[0,1].set_title("NDWI — Índice de Água (B-G)/(B+G)", color="white", fontsize=10)
    plt.colorbar(im2, ax=axes[0,1])

    # 3. Turbidez
    im3 = axes[0,2].imshow(turbidez_map, cmap="YlOrRd", vmin=0, vmax=0.6)
    axes[0,2].set_title("Turbidez Espectral (R - B)", color="white", fontsize=10)
    plt.colorbar(im3, ax=axes[0,2])

    # 4. Máscara de água limpa
    axes[1,0].imshow(mascara_agua_limpa, cmap="Blues")
    axes[1,0].set_title("Máscara Água Limpa (NDWI > 0.10)", color="white", fontsize=10)

    # 5. Barras de bandas por zona
    nomes_curtos = ["A-Normal", "B-Alerta", "C-Crítico", "D-Tóxico"]
    R_vals = [z["R"] for z in resultados_zonas]
    G_vals = [z["G"] for z in resultados_zonas]
    B_vals = [z["B"] for z in resultados_zonas]
    x_pos  = np.arange(4)
    axes[1,1].bar(x_pos-0.25, R_vals, 0.25, label="R (turbidez)", color="#e05252")
    axes[1,1].bar(x_pos,      G_vals, 0.25, label="G (superfície)", color="#52e052")
    axes[1,1].bar(x_pos+0.25, B_vals, 0.25, label="B (profundidade)", color="#5252e0")
    axes[1,1].set_xticks(x_pos); axes[1,1].set_xticklabels(nomes_curtos, color="white", fontsize=8)
    axes[1,1].set_title("Bandas Espectrais por Zona", color="white", fontsize=10)
    axes[1,1].legend(fontsize=8, facecolor="#1e2530", labelcolor="white")
    axes[1,1].set_facecolor("#1e2530")

    # 6. Classificação com bounding boxes
    axes[1,2].imshow(img)
    cores = {"normal":"#3399ff","alerta":"#33cc66","critico":"#ff8833","toxico":"#cc33cc"}
    for rz, (nome, y, x, h, w) in zip(resultados_zonas, zonas_def):
        cor = cores[rz["classe_detectada"]]
        rect = mpatches.Rectangle((x,y), w, h, linewidth=2, edgecolor=cor, facecolor="none")
        axes[1,2].add_patch(rect)
        axes[1,2].text(x+3, y+14, rz["classe_detectada"].upper(),
                       color=cor, fontsize=7, fontweight="bold",
                       bbox=dict(facecolor="black", alpha=0.5, pad=1))
    axes[1,2].set_title(f"Classificação de Qualidade ({corretos}/{len(zonas_def)} corretas)",
                         color="white", fontsize=10)

    plt.tight_layout()
    plt.savefig("vision/analise_espectral.png", dpi=120, bbox_inches="tight",
                facecolor="#0d1117")
    plt.close()

    resultado_final = {
        "imagem_tamanho": f"{IMG_SIZE}x{IMG_SIZE}",
        "ndwi_medio": round(float(ndwi.mean()), 4),
        "percentual_agua_limpa": round(pct_agua, 2),
        "turbidez_espectral_media": round(float(turb_media), 4),
        "zonas_classificadas": resultados_zonas,
        "total_zonas": len(zonas_def),
        "zonas_corretas": corretos
    }
    with open("dados/resultado_visao.json", "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=2, ensure_ascii=True)

    print("  → vision/analise_espectral.png")
    print("  → dados/resultado_visao.json")
    print(f"\n[RESUMO] {pct_agua:.1f}% da cena é água limpa | Turbidez média: {turb_media:.4f}")
    print("[AQUAWATCH] Análise espectral concluída com sucesso!")

if __name__ == "__main__":
    main()
