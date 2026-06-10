"""
AgroSat — Download de Imagem Real de Satélite + YOLO
Baixa imagem real do Cerrado Brasileiro via NASA WorldView/EarthData
e aplica detecção YOLO + classificação espectral NDVI.

Execute com: python vision/download_e_detectar.py
"""

import os
import sys
import json
import urllib.request
from datetime import datetime


def baixar_imagem_nasa_worldview():
    """
    Baixa imagem real MODIS/Terra do Cerrado Brasileiro
    via NASA WorldView EPSG endpoint (público, sem login).
    Região: Sorriso/MT — lat -12.55, lon -55.72
    """
    print("[DOWNLOAD] Buscando imagem real de satélite — NASA MODIS Terra...")

    # NASA WorldView Snapshots API — endpoint público
    # Documentação: https://worldview.earthdata.nasa.gov/
    url = (
        "https://wvs.earthdata.nasa.gov/api/v1/snapshot"
        "?REQUEST=GetSnapshot"
        "&TIME=2024-01-20"
        "&BBOX=-57.5,-14.0,-54.0,-11.0"
        "&CRS=EPSG:4326"
        "&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor,Coastlines_15m"
        "&FORMAT=image/jpeg"
        "&WIDTH=1024"
        "&HEIGHT=1024"
        "&AUTOSCALE=TRUE"
    )

    output = "vision/satelite_real_cerrado.jpg"
    os.makedirs("vision", exist_ok=True)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AgroSat/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            with open(output, "wb") as f:
                f.write(data)
        print(f"[DOWNLOAD] Imagem real baixada: {output} ({len(data)/1024:.0f} KB)")
        return output
    except Exception as e:
        print(f"[DOWNLOAD] Falha no download automático: {e}")
        return None


def baixar_imagem_alternativa():
    """
    Alternativa: baixa tile público do OpenStreetMap/Sentinel
    via Sinergise (sem autenticação).
    """
    print("[DOWNLOAD] Tentando fonte alternativa...")

    # Tile público Sentinel-2 cloudless via S2Maps
    urls_alternativas = [
        # EOX Sentinel-2 cloudless 2021 — público
        "https://tiles.maps.eox.at/wms?service=WMS&request=GetMap&version=1.1.1"
        "&layers=s2cloudless-2021&srs=EPSG:4326"
        "&bbox=-57,-14,-54,-11&width=1024&height=1024&format=image/jpeg",

        # USGS EarthExplorer thumbnail público
        "https://earthexplorer.usgs.gov/browse/eo-1/ali/186/068/2023/EO1A1860682023010110KF_B.JPG",
    ]

    output = "vision/satelite_real_cerrado.jpg"
    for url in urls_alternativas:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                ct = r.headers.get("Content-Type", "")
                if "image" in ct:
                    data = r.read()
                    with open(output, "wb") as f:
                        f.write(data)
                    print(f"[DOWNLOAD] OK — {len(data)/1024:.0f} KB — {url[:60]}...")
                    return output
        except Exception as e:
            print(f"[DOWNLOAD] Falhou: {e}")

    return None


def processar_imagem_real(image_path: str):
    """Aplica YOLO + classificação espectral na imagem real."""
    print(f"\n[YOLO] Processando imagem real: {image_path}")

    # Importa o módulo de visão já existente
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from vision.yolo_detector import (
        classificar_regioes_espectrais,
        detectar_com_yolo,
        gerar_mapa_classificacao,
    )

    # Classificação espectral NDVI
    print("\n[NDVI] Calculando índices espectrais...")
    classificacao = classificar_regioes_espectrais(image_path)

    print("\n[NDVI] Resultados:")
    print(f"  {'Classe':<25} {'Cobertura':>10}  {'NDVI':>8}")
    print("  " + "-" * 50)
    for classe, dados in classificacao.items():
        print(f"  {classe:<25} {dados['percentual']:>9.1f}%  {dados['ndvi_estimado']:>8.2f}")

    # YOLO
    n = detectar_com_yolo(image_path, "vision/yolo_real_resultado.jpg")

    # Mapa de classificação
    mapa = gerar_mapa_classificacao(
        image_path, classificacao, "vision/mapa_real_classificacao.png"
    )

    # Salva resultado
    resultado = {
        "timestamp":     datetime.now().isoformat(),
        "imagem_fonte":  "Satélite real (NASA MODIS Terra / Sentinel-2)",
        "regiao":        "Cerrado Brasileiro — Sorriso/MT",
        "bbox":          {"lat_min": -14.0, "lat_max": -11.0, "lon_min": -57.5, "lon_max": -54.0},
        "classificacao": classificacao,
        "yolo_deteccoes": n,
    }
    with open("vision/resultado_real.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Processamento concluído!")
    print(f"     → vision/yolo_real_resultado.jpg")
    print(f"     → vision/mapa_real_classificacao.png")
    print(f"     → vision/resultado_real.json")
    return resultado


if __name__ == "__main__":
    print("=" * 55)
    print("  AgroSat — Imagem Real de Satélite + YOLO")
    print("=" * 55)

    # Verifica se já existe imagem local salva pelo usuário
    imagem_local = "vision/satelite_real_cerrado.jpg"
    if os.path.exists(imagem_local) and os.path.getsize(imagem_local) > 100_000:
        print(f"[OK] Imagem local encontrada: {imagem_local} ({os.path.getsize(imagem_local)//1024} KB)")
        img = imagem_local
    else:
        # Tenta baixar automaticamente
        img = baixar_imagem_nasa_worldview()
        if not img:
            img = baixar_imagem_alternativa()

    if img and os.path.exists(img):
        processar_imagem_real(img)
    else:
        print("\n[INSTRUÇÃO] Download automático não disponível.")
        print("Faça o download manual em uma dessas fontes gratuitas:")
        print()
        print("  OPÇÃO 1 — NASA WorldView (recomendado, mais fácil):")
        print("  1. Acesse: https://worldview.earthdata.nasa.gov/")
        print("  2. Na busca, digite: Sorriso Mato Grosso")
        print("  3. Selecione a camada: MODIS Terra True Color")
        print("  4. Escolha data: Janeiro 2024")
        print("  5. Clique em 'Download' → Snapshot → JPEG")
        print("  6. Salve como: vision/satelite_real_cerrado.jpg")
        print()
        print("  OPÇÃO 2 — EO Browser (Sentinel-2, mais detalhado):")
        print("  1. Acesse: https://apps.sentinel-hub.com/eo-browser/")
        print("  2. Pesquise: -12.55, -55.72 (Sorriso/MT)")
        print("  3. Selecione Sentinel-2 L2A, data: Jan/2024, nuvens < 20%")
        print("  4. Download → High-res image → JPG")
        print("  5. Salve como: vision/satelite_real_cerrado.jpg")
        print()
        print("  Depois rode: python vision/download_e_detectar.py")