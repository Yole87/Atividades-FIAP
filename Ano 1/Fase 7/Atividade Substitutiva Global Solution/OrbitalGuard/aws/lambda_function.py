"""
OrbitalGuard — AWS Lambda Simulada
Recebe coordenadas orbitais, busca posição real da ISS (Open Notify API),
identifica o detrito mais próximo e classifica seu TIPO com a CNN treinada.
A CNN recebe o tipo do detrito mais próximo — conexão real entre os módulos.
Arquitetura: Cliente → API Gateway → Lambda → CNN + Open Notify API → S3 + CloudWatch
"""

import json
import urllib.request
import math
import os
import sys
import numpy as np
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFilter
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))
from model import OrbitalCNN, CLASSES, IMG_SIZE

RESULTADO_PATH = os.path.join(os.path.dirname(__file__), "lambda_resultados.json")
MODEL_PATH     = os.path.join(os.path.dirname(__file__), "..", "ml", "modelo_cnn.pth")

# Mapeamento tipo de detrito → class_id da CNN
TIPO_PARA_CLASS_ID = {
    "detrito_metalico":  1,
    "satelite_inativo":  3,
    "fragmento_rochoso": 2,
    "satelite_ativo":    0,
}

DETRITOS_CONHECIDOS = [
    {"id": "1999-025F", "nome": "Fragmento Fengyun-1C",  "altitude_km": 820, "inclinacao_graus": 98.6, "tipo": "detrito_metalico"},
    {"id": "2009-005A", "nome": "Iridium 33 (inativo)",  "altitude_km": 780, "inclinacao_graus": 86.4, "tipo": "satelite_inativo"},
    {"id": "2007-004B", "nome": "Bloco Superior Foguete", "altitude_km": 560, "inclinacao_graus": 51.6, "tipo": "detrito_metalico"},
    {"id": "2021-059K", "nome": "Fragmento Kosmos-1408", "altitude_km": 430, "inclinacao_graus": 82.9, "tipo": "fragmento_rochoso"},
    {"id": "1985-092C", "nome": "Satélite Inativo ASAT", "altitude_km": 670, "inclinacao_graus": 65.1, "tipo": "satelite_inativo"},
]


def buscar_posicao_iss():
    try:
        with urllib.request.urlopen("http://api.open-notify.org/iss-now.json", timeout=5) as resp:
            data = json.loads(resp.read())
            return float(data["iss_position"]["latitude"]), float(data["iss_position"]["longitude"]), True
    except Exception:
        return -15.5, -47.9, False


def calcular_risco_colisao(altitude_alvo, inclinacao_alvo):
    riscos = []
    for d in DETRITOS_CONHECIDOS:
        delta_alt = abs(d["altitude_km"] - altitude_alvo)
        delta_inc = abs(d["inclinacao_graus"] - inclinacao_alvo)
        dist = math.sqrt((delta_alt / 100) ** 2 + (delta_inc / 10) ** 2)
        prob = round(max(0, 1 - dist / 5), 4)
        riscos.append({
            "detrito_id":             d["id"],
            "detrito_nome":           d["nome"],
            "tipo":                   d["tipo"],
            "prob_colisao":           prob,
            "delta_altitude_km":      round(delta_alt, 1),
            "delta_inclinacao_graus": round(delta_inc, 2),
        })
    return sorted(riscos, key=lambda x: x["prob_colisao"], reverse=True)


def nivel_alerta(prob_max):
    if prob_max >= 0.7: return "CRITICO"
    if prob_max >= 0.4: return "ALTO"
    if prob_max >= 0.2: return "MEDIO"
    return "BAIXO"


def gerar_objeto_sintetico(tipo_idx):
    """Gera imagem sintética do tipo de objeto para classificar com a CNN."""
    rng  = np.random.default_rng(tipo_idx * 17 + 3)
    img  = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    for _ in range(20):
        x, y = rng.integers(0, IMG_SIZE, size=2)
        b    = rng.integers(120, 220)
        img[y, x] = [b, b, b]
    pil  = Image.fromarray(img).filter(ImageFilter.GaussianBlur(0.5))
    draw = ImageDraw.Draw(pil)
    cx, cy = IMG_SIZE // 2, IMG_SIZE // 2

    if tipo_idx == 0:      # satelite_ativo — corpo + 2 painéis simétricos
        draw.rectangle([cx-8, cy-5, cx+8, cy+5], fill=(205, 225, 255))
        draw.rectangle([cx-21, cy-2, cx-9, cy+2], fill=(55, 105, 205))
        draw.rectangle([cx+9,  cy-2, cx+21, cy+2], fill=(55, 105, 205))
    elif tipo_idx == 1:    # detrito_metalico — polígono irregular com reflexo
        pts = [(cx-11,cy-7),(cx+9,cy-13),(cx+15,cy+3),(cx+3,cy+11),(cx-13,cy+5)]
        draw.polygon(pts, fill=(158, 158, 178), outline=(218, 218, 238))
        draw.ellipse([pts[0][0]-2, pts[0][1]-2, pts[0][0]+2, pts[0][1]+2], fill=(255, 255, 255))
    elif tipo_idx == 2:    # fragmento_rochoso — orgânico com textura
        angulos = np.linspace(0, 2*np.pi, 9, endpoint=False)
        raios   = [13, 9, 15, 10, 12, 8, 14, 11, 13]
        pts = [(int(cx + r*np.cos(a)), int(cy + r*np.sin(a))) for r, a in zip(raios, angulos)]
        draw.polygon(pts, fill=(108, 92, 72), outline=(78, 68, 58))
        for _ in range(8):
            px = int(cx + rng.integers(-8, 8))
            py = int(cy + rng.integers(-8, 8))
            draw.ellipse([px-1, py-1, px+1, py+1], fill=(45, 38, 30))
    elif tipo_idx == 3:    # satelite_inativo — corpo + 1 painel + fragmento solto
        draw.rectangle([cx-7, cy-4, cx+7, cy+4], fill=(80, 90, 100))
        draw.rectangle([cx-19, cy-2, cx-8, cy+2], fill=(32, 52, 88))
        draw.rectangle([cx+10, cy+5, cx+16, cy+8], fill=(40, 40, 52))

    arr = np.array(pil, dtype=np.float32) / 255.0
    return torch.tensor(arr).permute(2, 0, 1).unsqueeze(0)


def classificar_com_cnn(tipo_idx):
    """Classifica o objeto do tipo do detrito mais próximo usando a CNN treinada."""
    if not os.path.exists(MODEL_PATH):
        return None, None
    device = torch.device("cpu")
    modelo = OrbitalCNN()
    modelo.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    modelo.eval()
    tensor = gerar_objeto_sintetico(tipo_idx).to(device)
    with torch.no_grad():
        prob    = torch.softmax(modelo(tensor), dim=1).cpu().numpy()[0]
        pred_id = int(np.argmax(prob))
    return CLASSES[pred_id], round(float(prob[pred_id]), 4)


def handler(event, context=None):
    params     = event.get("queryStringParameters", {}) or {}
    altitude   = float(params.get("altitude_km", 408))
    inclinacao = float(params.get("inclinacao", 51.6))

    lat_iss, lon_iss, iss_online = buscar_posicao_iss()
    riscos   = calcular_risco_colisao(altitude, inclinacao)
    prob_max = riscos[0]["prob_colisao"] if riscos else 0
    alerta   = nivel_alerta(prob_max)

    # CNN classifica o TIPO DO DETRITO MAIS PRÓXIMO — conexão real entre módulos
    detrito_mais_proximo = riscos[0] if riscos else None
    tipo_detrito         = detrito_mais_proximo["tipo"] if detrito_mais_proximo else "detrito_metalico"
    tipo_idx             = TIPO_PARA_CLASS_ID.get(tipo_detrito, 1)
    classe_cnn, confianca_cnn = classificar_com_cnn(tipo_idx)

    return {
        "statusCode": 200,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "entrada": {
            "altitude_km":      altitude,
            "inclinacao_graus": inclinacao,
        },
        "iss_posicao": {
            "latitude":  lat_iss,
            "longitude": lon_iss,
            "fonte":     "Open Notify API (real)" if iss_online else "fallback simulado"
        },
        "classificacao_cnn": {
            "detrito_analisado": detrito_mais_proximo["detrito_nome"] if detrito_mais_proximo else "—",
            "tipo_esperado":     tipo_detrito,
            "classe_prevista":   classe_cnn,
            "confianca":         confianca_cnn,
            "modelo":            "OrbitalCNN (PyTorch) — ml/modelo_cnn.pth"
        },
        "nivel_alerta":        alerta,
        "prob_colisao_maxima": prob_max,
        "detritos_proximos":   riscos[:3],
        "arquitetura":         "Cliente → API Gateway → Lambda → CNN + Open Notify API → S3 + CloudWatch",
        "endpoint_producao":   f"GET https://api.orbitalguard.io/risco?altitude_km={altitude}&inclinacao={inclinacao}"
    }


def simular():
    print("=" * 54)
    print("  OrbitalGuard — AWS Lambda (Simulação Local)")
    print("=" * 54)

    cenarios = [
        {"nome": "ISS (altitude padrão)", "altitude_km": 408,  "inclinacao": 51.6},
        {"nome": "Órbita LEO Alta",       "altitude_km": 780,  "inclinacao": 86.4},
        {"nome": "Órbita Sun-Sync",       "altitude_km": 820,  "inclinacao": 98.6},
        {"nome": "Órbita Baixa Crítica",  "altitude_km": 430,  "inclinacao": 82.9},
    ]

    resultados = []
    for c in cenarios:
        event = {"queryStringParameters": {"altitude_km": c["altitude_km"], "inclinacao": c["inclinacao"]}}
        resp  = handler(event)
        cnn   = resp["classificacao_cnn"]
        print(f"\n[Lambda] Cenário: {c['nome']}")
        print(f"  Status HTTP        : {resp['statusCode']}")
        print(f"  Altitude           : {c['altitude_km']} km | Inclinação: {c['inclinacao']}°")
        print(f"  Nível de Alerta    : {resp['nivel_alerta']}")
        print(f"  Prob. Max Colisão  : {resp['prob_colisao_maxima']:.1%}")
        print(f"  ISS Posição        : lat={resp['iss_posicao']['latitude']:.2f} lon={resp['iss_posicao']['longitude']:.2f}")
        print(f"  Fonte ISS          : {resp['iss_posicao']['fonte']}")
        print(f"  Detrito mais próx. : {resp['detritos_proximos'][0]['detrito_nome']} ({resp['detritos_proximos'][0]['tipo']})")
        print(f"  CNN — Analisou     : {cnn['detrito_analisado']}")
        print(f"  CNN — Tipo esperado: {cnn['tipo_esperado']}")
        print(f"  CNN — Classe prev. : {cnn['classe_prevista']} ({cnn['confianca']:.1%} confiança)")
        resultados.append({"cenario": c["nome"], **resp})

    with open(RESULTADO_PATH, "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=True)

    print(f"\n[OK] Resultados salvos em aws/lambda_resultados.json")
    print(f"\n[ENDPOINT] Em produção:")
    print(f"  GET https://api.orbitalguard.io/risco?altitude_km=408&inclinacao=51.6")
    print(f"\n[ARQUITETURA AWS]")
    print(f"  Cliente → API Gateway → Lambda → CNN (PyTorch) + Open Notify API")
    print(f"  Lambda → S3 (resultados) + CloudWatch (logs)")


if __name__ == "__main__":
    simular()
