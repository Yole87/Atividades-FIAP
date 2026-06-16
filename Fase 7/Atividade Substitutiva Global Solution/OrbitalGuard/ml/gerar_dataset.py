"""
OrbitalGuard — Gerador de Dataset Sintético de Detritos Espaciais
Variação real: posição, rotação, escala, ruído E paletas de cor sobrepostas entre classes.
As classes são distinguidas primariamente por FORMA, não por cor.
"""

import numpy as np
import os
from PIL import Image, ImageDraw, ImageFilter
import json

CLASSES     = ["satelite_ativo", "detrito_metalico", "fragmento_rochoso", "satelite_inativo"]
IMG_SIZE    = 64
N_AMOSTRAS  = 800  # 200 por classe
DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "labels.json")


def fundo_espacial(rng):
    """Fundo escuro com estrelas variáveis e ruído gaussiano."""
    img = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    for _ in range(rng.integers(5, 55)):
        x, y = rng.integers(0, IMG_SIZE, size=2)
        b    = rng.integers(100, 255)
        img[y, x] = [b, b, b]
    ruido = rng.integers(-12, 12, size=img.shape, dtype=np.int16)
    return Image.fromarray(np.clip(img.astype(np.int16) + ruido, 0, 255).astype(np.uint8))


def cor_objeto(rng, base_r, base_g, base_b, variacao=60):
    """
    Gera cor com variação ampla em torno da base.
    variacao=60 significa que as cores das classes podem se sobrepor bastante,
    forçando o modelo a aprender forma, não cor.
    """
    r = int(np.clip(base_r + rng.integers(-variacao, variacao), 20, 240))
    g = int(np.clip(base_g + rng.integers(-variacao, variacao), 20, 240))
    b = int(np.clip(base_b + rng.integers(-variacao, variacao), 20, 240))
    return (r, g, b)


def posicao_aleatoria(rng, margem=18):
    return int(rng.integers(margem, IMG_SIZE - margem)), int(rng.integers(margem, IMG_SIZE - margem))


def escala_aleatoria(rng):
    return rng.uniform(0.65, 1.35)


def girar_pontos(pts, cx, cy, ang):
    cos_a, sin_a = np.cos(ang), np.sin(ang)
    return [(int(cx + (px-cx)*cos_a - (py-cy)*sin_a),
             int(cy + (px-cx)*sin_a + (py-cy)*cos_a)) for px, py in pts]


def gerar_satelite_ativo(rng):
    """
    FORMA DISTINTIVA: corpo retangular simétrico + DOIS painéis solares opostos + antena.
    Cor: variação ampla em torno de azul-claro/branco.
    """
    img  = fundo_espacial(rng)
    draw = ImageDraw.Draw(img)
    cx, cy = posicao_aleatoria(rng)
    s   = escala_aleatoria(rng)
    ang = rng.uniform(0, 2 * np.pi)

    cor_corpo  = cor_objeto(rng, 190, 210, 240, variacao=55)
    cor_painel = cor_objeto(rng, 50, 90, 190, variacao=50)

    # Corpo central — retângulo simétrico (característica principal)
    bw, bh = int(9 * s), int(5 * s)
    corpo = [(cx-bw, cy-bh), (cx+bw, cy-bh), (cx+bw, cy+bh), (cx-bw, cy+bh)]
    draw.polygon(girar_pontos(corpo, cx, cy, ang), fill=cor_corpo)

    # DOIS painéis simétricos (diferencial estrutural vs inativo)
    pw, ph = int(13 * s), int(2 * s)
    for sinal in [-1, 1]:
        ox = sinal * (bw + pw + 2)
        p  = [(cx+ox-pw, cy-ph), (cx+ox+pw, cy-ph), (cx+ox+pw, cy+ph), (cx+ox-pw, cy+ph)]
        draw.polygon(girar_pontos(p, cx, cy, ang), fill=cor_painel)

    # Antena (pequeno detalhe distintivo)
    tip = girar_pontos([(cx, cy - bh - int(8*s))], cx, cy, ang)[0]
    base_ant = girar_pontos([(cx, cy - bh)], cx, cy, ang)[0]
    draw.line([base_ant, tip], fill=cor_objeto(rng, 200, 200, 200, 30), width=1)

    return img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 0.7)))


def gerar_detrito_metalico(rng):
    """
    FORMA DISTINTIVA: polígono irregular convexo/côncavo com BORDAS AFIADAS e reflexo pontual.
    Cor: variação ampla em torno de cinza metálico.
    """
    img  = fundo_espacial(rng)
    draw = ImageDraw.Draw(img)
    cx, cy = posicao_aleatoria(rng)
    s   = escala_aleatoria(rng)
    ang = rng.uniform(0, 2 * np.pi)

    # Base cinza com variação ampla (pode sobrepor com inativo)
    base = rng.integers(100, 180)
    cor  = cor_objeto(rng, base, base, base + rng.integers(-20, 30), variacao=50)

    n_pts   = rng.integers(5, 9)
    angulos = np.sort(rng.uniform(0, 2 * np.pi, n_pts))
    # Raios irregulares com alta variação (bordas afiadas)
    raios   = rng.uniform(4 * s, 15 * s, n_pts)
    pts     = [(int(cx + r*np.cos(a)), int(cy + r*np.sin(a))) for r, a in zip(raios, angulos)]
    draw.polygon(girar_pontos(pts, cx, cy, ang), fill=cor, outline=(min(cor[0]+50,255), min(cor[1]+50,255), 255))

    # Reflexo pontual (característica metálica)
    idx_ref = int(rng.integers(0, len(pts)))
    rx, ry  = girar_pontos([pts[idx_ref]], cx, cy, ang)[0]
    rs      = max(1, int(2.5 * s))
    draw.ellipse([rx-rs, ry-rs, rx+rs, ry+rs], fill=(245, 245, 255))

    # Segundo fragmento pequeno solto (mais realismo de detrito)
    if rng.random() > 0.4:
        fx = int(cx + rng.uniform(-18*s, 18*s))
        fy = int(cy + rng.uniform(-18*s, 18*s))
        fs = max(1, int(rng.uniform(1, 3) * s))
        draw.ellipse([fx-fs, fy-fs, fx+fs, fy+fs], fill=cor)

    return img.filter(ImageFilter.GaussianBlur(rng.uniform(0.2, 0.5)))


def gerar_fragmento_rochoso(rng):
    """
    FORMA DISTINTIVA: contorno orgânico irregular com TEXTURA INTERNA densa (pontos/manchas).
    Cor: variação ampla em torno de marrom/cinza-terroso.
    """
    img  = fundo_espacial(rng)
    draw = ImageDraw.Draw(img)
    cx, cy = posicao_aleatoria(rng)
    s   = escala_aleatoria(rng)
    ang = rng.uniform(0, 2 * np.pi)

    # Cor terrosa com variação — pode sobrepor com metálico
    cor  = cor_objeto(rng, 110, 88, 65, variacao=55)
    cor_outline = (max(cor[0]-40,0), max(cor[1]-40,0), max(cor[2]-40,0))

    # Contorno muito irregular (muitos pontos com raios variáveis — aspecto orgânico)
    n_pts   = rng.integers(9, 15)
    angulos = np.sort(rng.uniform(0, 2 * np.pi, n_pts))
    raios   = rng.uniform(6 * s, 16 * s, n_pts)
    pts     = [(int(cx + r*np.cos(a)), int(cy + r*np.sin(a))) for r, a in zip(raios, angulos)]
    draw.polygon(girar_pontos(pts, cx, cy, ang), fill=cor, outline=cor_outline)

    # Textura interna densa — característica principal que diferencia de metálico
    n_manchas = rng.integers(8, 22)
    for _ in range(n_manchas):
        px  = int(cx + rng.uniform(-10*s, 10*s))
        py  = int(cy + rng.uniform(-10*s, 10*s))
        ts  = max(1, int(rng.uniform(0.5, 2.0) * s))
        cor_mancha = (max(cor[0]-rng.integers(20,60),0),
                      max(cor[1]-rng.integers(20,60),0),
                      max(cor[2]-rng.integers(20,50),0))
        draw.ellipse([px-ts, py-ts, px+ts, py+ts], fill=cor_mancha)

    return img.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 0.9)))


def gerar_satelite_inativo(rng):
    """
    FORMA DISTINTIVA: corpo retangular ASSIMÉTRICO — apenas UM painel + fragmento SEPARADO do corpo.
    Cor: variação ampla em torno de cinza escuro/grafite.
    """
    img  = fundo_espacial(rng)
    draw = ImageDraw.Draw(img)
    cx, cy = posicao_aleatoria(rng)
    s   = escala_aleatoria(rng)
    ang = rng.uniform(0, 2 * np.pi)

    # Corpo escuro degradado (pode sobrepor com detrito metálico escuro)
    base_c    = rng.integers(55, 105)
    cor_corpo = cor_objeto(rng, base_c, base_c+5, base_c+10, variacao=40)
    cor_painel = cor_objeto(rng, 28, 48, 85, variacao=45)

    bw, bh = int(7 * s), int(4 * s)
    corpo = [(cx-bw, cy-bh), (cx+bw, cy-bh), (cx+bw, cy+bh), (cx-bw, cy+bh)]
    draw.polygon(girar_pontos(corpo, cx, cy, ang), fill=cor_corpo)

    # APENAS UM painel (assimetria é o diferencial vs satélite ativo)
    pw, ph = int(rng.integers(8, 13) * s), int(2 * s)
    lado   = rng.choice([-1, 1])
    ox     = lado * (bw + pw + 1)
    painel = [(cx+ox-pw, cy-ph), (cx+ox+pw, cy-ph), (cx+ox+pw, cy+ph), (cx+ox-pw, cy+ph)]
    draw.polygon(girar_pontos(painel, cx, cy, ang), fill=cor_painel)

    # Fragmento solto SEPARADO do corpo (mais distante que o ativo)
    dist_frag = rng.uniform(bw + 5, bw + 16) * s
    ang_frag  = rng.uniform(0, 2 * np.pi)
    fx = int(cx + dist_frag * np.cos(ang_frag))
    fy = int(cy + dist_frag * np.sin(ang_frag))
    fs = max(1, int(rng.uniform(1.5, 3.5) * s))
    frag = [(fx, fy-fs), (fx+fs*2, fy), (fx+fs, fy+fs), (fx-fs, fy+fs//2)]
    draw.polygon(girar_pontos(frag, cx, cy, ang), fill=cor_objeto(rng, 38, 38, 48, 30))

    # Antena quebrada (ângulo torto — diferente da reta do ativo)
    tip_quebrada = girar_pontos([(cx + int(6*s), cy - bh - int(7*s))], cx, cy, ang)[0]
    base_ant     = girar_pontos([(cx, cy - bh)], cx, cy, ang)[0]
    draw.line([base_ant, tip_quebrada], fill=cor_objeto(rng, 90, 90, 90, 25), width=1)

    return img.filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 1.0)))


GERADORES = [gerar_satelite_ativo, gerar_detrito_metalico, gerar_fragmento_rochoso, gerar_satelite_inativo]


def gerar_dataset():
    seed = int(np.random.default_rng().integers(0, 99999))
    rng  = np.random.default_rng(seed)
    print(f"[DATASET] Seed: {seed}")
    print(f"[DATASET] Estratégia: variação de cor ampla → CNN aprende FORMA, não cor")

    labels = []
    n_por_classe = N_AMOSTRAS // len(CLASSES)

    for class_id, (classe, gerador) in enumerate(zip(CLASSES, GERADORES)):
        pasta = os.path.join(DATASET_DIR, classe)
        os.makedirs(pasta, exist_ok=True)
        for i in range(n_por_classe):
            img  = gerador(rng)
            nome = f"{classe}_{i:03d}.png"
            img.save(os.path.join(pasta, nome))
            labels.append({"arquivo": os.path.join(classe, nome), "classe": classe, "class_id": class_id})

    with open(LABELS_PATH, "w") as f:
        json.dump(labels, f, indent=2)

    total = len(labels)
    print(f"[DATASET] {total} imagens geradas em {DATASET_DIR}/")
    for c in CLASSES:
        print(f"  {c}: {sum(1 for l in labels if l['classe']==c)} amostras")
    print(f"[LABELS] Salvo em {LABELS_PATH}")


if __name__ == "__main__":
    gerar_dataset()
