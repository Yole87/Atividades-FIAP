"""
AquaWatch — Módulo 3: Cloud Function (Firebase Simulation) + USGS Water Quality API
Simula uma Firebase Cloud Function que:
  1. Consulta dados reais da USGS Water Quality API (dados públicos de rios dos EUA)
  2. Executa o LSTM localmente para classificar a qualidade
  3. Aciona o Isolation Forest para detecção de anomalias
  4. Armazena o resultado em MongoDB (simulado via JSON local)
  5. Retorna um relatório de risco via HTTP (status 200)

Por que Firebase e não AWS Lambda (como OrbitalGuard)?
  - AWS Lambda + PyTorch = usado por OrbitalGuard
  - Firebase Functions = serverless diferente, custo zero na camada gratuita
  - USGS API = dados reais de qualidade de água (diferente de Open Notify ISS)

USGS Water Quality Web Service:
  https://waterservices.usgs.gov/rest/IV-Service.html
  Parâmetros: 00010=temperatura, 00400=pH, 63680=turbidez, 00095=condutividade
"""

import json
import os
import pickle
import numpy as np
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import torch
import torch.nn as nn

# ─── Modelo LSTM (compartilhado com treinar_lstm.py) ──────────────────────────
class LSTMClassifier(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=64, n_layers=2, n_classes=4, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers,
                            batch_first=True, bidirectional=True,
                            dropout=dropout if n_layers > 1 else 0.0)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(64, n_classes)
        )
    def forward(self, x):
        out, _ = self.lstm(x)
        attn = torch.softmax(self.attention(out), dim=1)
        ctx  = (out * attn).sum(dim=1)
        return self.classifier(ctx)


class NpEncoder(json.JSONEncoder):
    """Serializa tipos NumPy para JSON padrão."""
    def default(self, obj):
        if isinstance(obj, (bool,)): return bool(obj)
        import numpy as np
        if isinstance(obj, np.bool_): return bool(obj)
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

CLASSES = {0: "normal", 1: "alerta", 2: "critico", 3: "toxico"}
FEATURES = ["pH", "turbidez_NTU", "TDS_mgL", "temperatura_C", "OD_mgL", "condutividade_uScm"]

# ─── Consulta USGS API (dados reais) ──────────────────────────────────────────
def consultar_usgs_api(site_code="01646500"):
    """
    Consulta a USGS Instantaneous Values API para um posto hidrológico.
    Retorna leituras reais de temperatura e condutividade.

    Site 01646500 = Potomac River at Little Falls Pump Station, MD (público)
    """
    url = (
        "https://waterservices.usgs.gov/nwis/iv/"
        f"?sites={site_code}"
        "&parameterCd=00010,00095"   # temperatura + condutividade
        "&period=PT1H"               # última hora
        "&format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AquaWatch/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        ts = data.get("value", {}).get("timeSeries", [])
        resultado = {"fonte": "USGS_API_real", "site": site_code, "parametros": {}}

        for serie in ts:
            nome_param = serie["variable"]["variableName"]
            valores = serie.get("values", [{}])[0].get("value", [])
            if valores:
                ultimo = valores[-1]
                resultado["parametros"][nome_param] = {
                    "valor": float(ultimo["value"]) if ultimo["value"] != "-999999" else None,
                    "timestamp": ultimo["dateTime"],
                    "unidade": serie["variable"]["unit"]["unitCode"]
                }

        resultado["status_http"] = 200
        return resultado

    except Exception as e:
        # Fallback: dados simulados se API offline
        return {
            "fonte": "USGS_simulado_fallback",
            "site": site_code,
            "status_http": 200,
            "erro": str(e),
            "parametros": {
                "Temperature, water": {"valor": 18.5, "unidade": "deg C", "timestamp": datetime.now(timezone.utc).isoformat()},
                "Specific conductance": {"valor": 320.0, "unidade": "uS/cm @25C", "timestamp": datetime.now(timezone.utc).isoformat()}
            }
        }

# ─── Carrega modelos ──────────────────────────────────────────────────────────
def carregar_modelos():
    device = torch.device("cpu")
    lstm = LSTMClassifier().to(device)
    lstm.load_state_dict(torch.load("modelos/lstm_agua.pth", map_location=device, weights_only=True))
    lstm.eval()

    with open("modelos/isolation_forest.pkl", "rb") as f:
        if_bundle = pickle.load(f)

    scaler_params = json.load(open("dados/scaler_params.json"))
    return lstm, if_bundle["modelo"], if_bundle["scaler"], scaler_params, device

# ─── Gera série temporal para LSTM a partir de 1 leitura IoT ─────────────────
def snapshot_para_serie(snapshot_6d, ruido=0.05, n_steps=24):
    """
    Expande 1 snapshot de 6 parâmetros em série temporal de 24 timesteps
    com drift suave — simula histórico de sensor IoT.
    """
    serie = np.tile(snapshot_6d, (n_steps, 1)).astype(np.float32)
    for t in range(n_steps):
        serie[t] += np.random.normal(0, ruido, 6) * np.array(snapshot_6d)
    return serie   # (24, 6)

# ─── Firebase Cloud Function Handler ─────────────────────────────────────────
def firebase_cloud_function(request_body: dict) -> dict:
    """
    Simula o handler de uma Firebase Cloud Function.
    Entrada: JSON com leitura do sensor IoT
    Saída:   JSON com classificação LSTM + anomalia IF + dado USGS + alerta

    Em produção seria: functions.https.onRequest(req, res) em Node.js/Python via gcloud.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    ponto     = request_body.get("ponto_id", "PONTO-001")
    lat       = request_body.get("lat", -15.7801)
    lon       = request_body.get("lon", -47.9292)

    # Dados do sensor IoT (ESP32)
    sensor = request_body.get("sensor", {})
    pH            = sensor.get("pH", 7.0)
    turbidez      = sensor.get("turbidez_NTU", 2.0)
    TDS           = sensor.get("TDS_mgL", 280.0)
    temperatura   = sensor.get("temperatura_C", 22.0)
    OD            = sensor.get("OD_mgL", 7.5)
    condutividade = sensor.get("condutividade_uScm", 400.0)
    snapshot = np.array([pH, turbidez, TDS, temperatura, OD, condutividade], dtype=np.float32)

    # Carrega modelos
    lstm_model, iso_model, iso_scaler, scaler_params, device = carregar_modelos()

    # ── LSTM: classifica série temporal ──────────────────────────────────────
    scaler_mean  = np.array(scaler_params["mean"],  dtype=np.float32)
    scaler_scale = np.array(scaler_params["scale"], dtype=np.float32)

    serie = snapshot_para_serie(snapshot)
    serie_norm = (serie - scaler_mean) / scaler_scale
    tensor = torch.FloatTensor(serie_norm).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = lstm_model(tensor)
        probs  = torch.softmax(logits, dim=1)[0].cpu().numpy()
        cls_id = int(probs.argmax())

    lstm_resultado = {
        "classe": CLASSES[cls_id],
        "classe_id": cls_id,
        "confianca": round(float(probs[cls_id]) * 100, 2),
        "probabilidades": {CLASSES[i]: round(float(p)*100, 2) for i, p in enumerate(probs)}
    }

    # ── Isolation Forest: anomalia snapshot ──────────────────────────────────
    snap_norm = iso_scaler.transform(snapshot.reshape(1, -1))
    if_pred   = iso_model.predict(snap_norm)[0]
    if_score  = round(float(iso_model.score_samples(snap_norm)[0]), 4)
    is_anomalia = if_pred == -1

    # ── Consulta USGS API ─────────────────────────────────────────────────────
    usgs_data = consultar_usgs_api()

    # ── Nível de alerta ───────────────────────────────────────────────────────
    niveis = {"normal": "BAIXO", "alerta": "MEDIO", "critico": "ALTO", "toxico": "CRITICO"}
    nivel_alerta = niveis[CLASSES[cls_id]]
    if is_anomalia and nivel_alerta == "BAIXO":
        nivel_alerta = "MEDIO"

    # ── Resposta HTTP 200 ─────────────────────────────────────────────────────
    return {
        "status": 200,
        "timestamp": timestamp,
        "ponto_id": ponto,
        "coordenadas": {"lat": lat, "lon": lon},
        "sensor_esp32": {
            "pH": pH, "turbidez_NTU": turbidez, "TDS_mgL": TDS,
            "temperatura_C": temperatura, "OD_mgL": OD,
            "condutividade_uScm": condutividade
        },
        "lstm_classificacao": lstm_resultado,
        "isolation_forest": {
            "anomalia_detectada": is_anomalia,
            "anomaly_score": if_score,
            "interpretacao": "Leitura anômala — afasta-se do padrão normal" if is_anomalia else "Leitura dentro do padrão"
        },
        "usgs_api": usgs_data,
        "nivel_alerta": nivel_alerta,
        "acao_recomendada": {
            "BAIXO":   "Monitoramento de rotina",
            "MEDIO":   "Aumentar frequência de coleta",
            "ALTO":    "Acionar equipe de campo imediatamente",
            "CRITICO": "EMERGÊNCIA — Notificar autoridades ambientais"
        }[nivel_alerta]
    }

# ─── Salva no banco MongoDB (simulado) ────────────────────────────────────────
def salvar_mongodb(resultado: dict):
    """Simula insert em coleção MongoDB. Em produção: pymongo ou Firebase Firestore."""
    os.makedirs("db", exist_ok=True)
    db_path = "db/historico.json"

    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            historico = json.load(f)
    else:
        historico = {"colecao": "leituras_aquawatch", "documentos": []}

    doc = {
        "_id": f"doc_{len(historico['documentos'])+1:04d}",
        "timestamp": resultado["timestamp"],
        "ponto_id": resultado["ponto_id"],
        "nivel_alerta": resultado["nivel_alerta"],
        "classe_lstm": resultado["lstm_classificacao"]["classe"],
        "confianca_lstm": resultado["lstm_classificacao"]["confianca"],
        "anomalia_if": bool(resultado["isolation_forest"]["anomalia_detectada"]),
        "sensor": resultado["sensor_esp32"],
        "fonte_api": resultado["usgs_api"]["fonte"]
    }
    historico["documentos"].append(doc)
    historico["total_documentos"] = len(historico["documentos"])

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=2, ensure_ascii=True, cls=NpEncoder)

    return doc["_id"]

# ─── Main: 4 cenários de teste ───────────────────────────────────────────────
def main():
    print("=" * 65)
    print("[AQUAWATCH] Firebase Cloud Function — Simulação Local")
    print("=" * 65)
    print("[INFO] Arquitetura: ESP32 -> Firebase Function -> LSTM + IF -> MongoDB")
    print("[INFO] API Externa: USGS Water Quality Web Service (dados reais)")

    # Reset do banco a cada execucao (aprendizado: sem reset acumula entre runs)
    import os as _os
    _os.makedirs("db", exist_ok=True)
    with open("db/historico.json", "w", encoding="utf-8") as _f:
        json.dump({"colecao": "leituras_aquawatch", "documentos": [], "total_documentos": 0},
                  _f, indent=2, ensure_ascii=True)
    print("[MONGODB] Colecao resetada para esta execucao\n")

    cenarios = [
        {
            "nome": "Cenário 1 — Rio Limpo (Parque Nacional)",
            "ponto_id": "PONTO-PN-001",
            "lat": -22.9, "lon": -43.1,
            "sensor": {"pH": 7.2, "turbidez_NTU": 1.1, "TDS_mgL": 195.0,
                        "temperatura_C": 19.0, "OD_mgL": 8.4, "condutividade_uScm": 320.0}
        },
        {
            "nome": "Cenário 2 — Rio com Sedimentação Agrícola",
            "ponto_id": "PONTO-AGR-007",
            "lat": -15.8, "lon": -47.9,
            "sensor": {"pH": 6.1, "turbidez_NTU": 8.5, "TDS_mgL": 490.0,
                        "temperatura_C": 27.0, "OD_mgL": 5.1, "condutividade_uScm": 920.0}
        },
        {
            "nome": "Cenário 3 — Rio com Contaminação Industrial",
            "ponto_id": "PONTO-IND-023",
            "lat": -23.5, "lon": -46.6,
            "sensor": {"pH": 4.8, "turbidez_NTU": 22.0, "TDS_mgL": 810.0,
                        "temperatura_C": 31.0, "OD_mgL": 2.8, "condutividade_uScm": 1750.0}
        },
        {
            "nome": "Cenário 4 — Descarte Ilegal de Efluentes",
            "ponto_id": "PONTO-ALE-099",
            "lat": -3.7, "lon": -38.5,
            "sensor": {"pH": 3.2, "turbidez_NTU": 110.0, "TDS_mgL": 2100.0,
                        "temperatura_C": 37.0, "OD_mgL": 0.4, "condutividade_uScm": 4800.0}
        }
    ]

    resultados_completos = []
    for i, cenario in enumerate(cenarios, 1):
        print(f"\n{'─'*65}")
        print(f"[Firebase] {cenario['nome']}")
        print(f"{'─'*65}")
        print(f"  Ponto ID    : {cenario['ponto_id']}")
        print(f"  Coordenadas : {cenario['lat']}°, {cenario['lon']}°")
        print(f"  Sensor      : pH={cenario['sensor']['pH']} | "
              f"Turbidez={cenario['sensor']['turbidez_NTU']} NTU | "
              f"TDS={cenario['sensor']['TDS_mgL']} mg/L")

        resultado = firebase_cloud_function(cenario)
        doc_id    = salvar_mongodb(resultado)

        lstm_cls  = resultado["lstm_classificacao"]
        if_res    = resultado["isolation_forest"]
        usgs      = resultado["usgs_api"]

        print(f"\n  [LSTM]  Classe: {lstm_cls['classe'].upper():<10} | Confiança: {lstm_cls['confianca']}%")
        print(f"  [IF]    Anomalia: {'SIM ⚠' if if_res['anomalia_detectada'] else 'NÃO ✓':<10} | Score: {if_res['anomaly_score']}")
        print(f"  [USGS]  Fonte: {usgs['fonte']} | Status HTTP: {usgs['status_http']}")
        print(f"  [ALERTA] Nível: {resultado['nivel_alerta']:<10} | Ação: {resultado['acao_recomendada']}")
        print(f"  [MongoDB] Documento salvo: {doc_id}")

        resultados_completos.append(resultado)

    # Salva todos os resultados
    with open("dados/resultados_cloud.json", "w", encoding="utf-8") as f:
        json.dump(resultados_completos, f, indent=2, ensure_ascii=True, cls=NpEncoder)

    print(f"\n{'='*65}")
    print("[OK] Arquivos salvos:")
    print("  → dados/resultados_cloud.json")
    print("  → db/historico.json")
    print("[AQUAWATCH] Firebase Cloud Function executada com sucesso!")

if __name__ == "__main__":
    main()
