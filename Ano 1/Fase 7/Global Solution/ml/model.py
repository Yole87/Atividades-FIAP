"""
AgroSat - Módulo de Machine Learning
Consome dados climáticos reais da NASA POWER API e treina
um modelo de regressão para prever produtividade agrícola.
"""

import requests
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import json
import sqlite3
from datetime import datetime

# ──────────────────────────────────────────────
# 1. COLETA DE DADOS — NASA POWER API
# ──────────────────────────────────────────────

def fetch_nasa_power(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    """
    Busca dados climáticos reais da NASA POWER API.
    Parâmetros: temperatura média, precipitação, radiação solar.
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
    }

    print(f"[NASA POWER] Buscando dados para lat={lat}, lon={lon}...")
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        props = data["properties"]["parameter"]
        df = pd.DataFrame({
            "temperatura":  list(props["T2M"].values()),
            "precipitacao": list(props["PRECTOTCORR"].values()),
            "radiacao":     list(props["ALLSKY_SFC_SW_DWN"].values()),
            "data":         list(props["T2M"].keys()),
        })
        df["data"] = pd.to_datetime(df["data"], format="%Y%m%d")
        print(f"[NASA POWER] {len(df)} registros coletados.")
        return df

    except Exception as e:
        print(f"[NASA POWER] Erro na API: {e}. Usando dados sintéticos.")
        return gerar_dados_sinteticos()


def gerar_dados_sinteticos() -> pd.DataFrame:
    """
    Gera dados climáticos sintéticos realistas para simulação
    quando a API não está disponível (ex: sem internet).
    Baseado em médias históricas do cerrado brasileiro.
    """
    np.random.seed(42)
    n = 365 * 5  # 5 anos de dados diários

    datas = pd.date_range("2019-01-01", periods=n, freq="D")
    # Simula sazonalidade climática (verão chuvoso, inverno seco)
    dia_do_ano = np.array([d.dayofyear for d in datas])
    ciclo = np.sin(2 * np.pi * dia_do_ano / 365)

    temperatura  = 26 + 6 * ciclo + np.random.normal(0, 1.5, n)
    precipitacao = np.clip(3 + 4 * ciclo + np.random.exponential(2, n), 0, 50)
    radiacao     = 18 + 5 * ciclo + np.random.normal(0, 1, n)

    return pd.DataFrame({
        "data":         datas,
        "temperatura":  temperatura,
        "precipitacao": precipitacao,
        "radiacao":     radiacao,
    })


# ──────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ──────────────────────────────────────────────

def agregar_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega dados diários em médias mensais e cria features."""
    df["mes"]  = df["data"].dt.month
    df["ano"]  = df["data"].dt.year

    mensal = df.groupby(["ano", "mes"]).agg(
        temp_media   = ("temperatura",  "mean"),
        temp_max     = ("temperatura",  "max"),
        precip_total = ("precipitacao", "sum"),
        rad_media    = ("radiacao",     "mean"),
        dias_chuva   = ("precipitacao", lambda x: (x > 1).sum()),
    ).reset_index()

    # Produtividade simulada (kg/ha) baseada em relações agroclimáticas reais
    # Função inspirada em modelos de cultura do milho (Doorenbos & Kassam)
    mensal["produtividade"] = (
        4000
        + 80  * mensal["temp_media"]
        - 3   * mensal["temp_media"] ** 2
        + 15  * mensal["precip_total"]
        - 0.1 * mensal["precip_total"] ** 2
        + 60  * mensal["rad_media"]
        + np.random.normal(0, 150, len(mensal))
    ).clip(500, 12000)

    return mensal


# ──────────────────────────────────────────────
# 3. TREINAMENTO DO MODELO
# ──────────────────────────────────────────────

def treinar_modelo(df: pd.DataFrame):
    """Treina Random Forest Regressor e salva o modelo."""
    features = ["temp_media", "temp_max", "precip_total", "rad_media", "dias_chuva", "mes"]
    target   = "produtividade"

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    modelo = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    modelo.fit(X_train_s, y_train)

    y_pred = modelo.predict(X_test_s)
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    print(f"\n[MODELO] Random Forest treinado com sucesso!")
    print(f"  MAE : {mae:.1f} kg/ha")
    print(f"  R²  : {r2:.4f}")

    # Importância das features
    importancias = pd.Series(modelo.feature_importances_, index=features).sort_values(ascending=False)
    print(f"\n[MODELO] Importância das variáveis:")
    for feat, imp in importancias.items():
        print(f"  {feat:<20} {imp:.3f}")

    # Salva modelo e scaler
    joblib.dump(modelo, "ml/modelo_agrosat.pkl")
    joblib.dump(scaler, "ml/scaler_agrosat.pkl")

    # Salva métricas
    metricas = {"mae": round(mae, 2), "r2": round(r2, 4), "n_amostras": len(df)}
    with open("ml/metricas.json", "w") as f:
        json.dump(metricas, f)

    return modelo, scaler, metricas


def prever(modelo, scaler, entrada: dict) -> float:
    """
    Faz uma previsão pontual de produtividade.
    entrada: dict com as features climáticas do mês
    """
    features = ["temp_media", "temp_max", "precip_total", "rad_media", "dias_chuva", "mes"]
    X = pd.DataFrame([entrada])[features]
    X_s = scaler.transform(X)
    return float(modelo.predict(X_s)[0])


# ──────────────────────────────────────────────
# 4. PERSISTÊNCIA — SQLite
# ──────────────────────────────────────────────

DB_PATH = "ml/agrosat.db"

def inicializar_banco():
    """Cria as tabelas do banco de dados caso não existam."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de previsões realizadas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS previsoes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            lat         REAL,
            lon         REAL,
            mes         INTEGER,
            temp_media  REAL,
            precip_total REAL,
            rad_media   REAL,
            dias_chuva  INTEGER,
            produtividade_prevista REAL,
            nivel_risco TEXT
        )
    """)

    # Tabela de métricas do modelo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metricas_modelo (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            r2          REAL,
            mae         REAL,
            n_amostras  INTEGER
        )
    """)

    conn.commit()
    conn.close()
    print(f"[SQLite] Banco inicializado em {DB_PATH}")


def salvar_previsao(lat: float, lon: float, entrada: dict, produtividade: float):
    """Persiste uma previsão no banco SQLite."""
    nivel = "alta" if produtividade > 7000 else "media" if produtividade > 4500 else "baixa"
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO previsoes
        (timestamp, lat, lon, mes, temp_media, precip_total, rad_media, dias_chuva, produtividade_prevista, nivel_risco)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        lat, lon,
        entrada["mes"],
        entrada["temp_media"],
        entrada["precip_total"],
        entrada["rad_media"],
        entrada["dias_chuva"],
        round(produtividade, 2),
        nivel
    ))
    conn.commit()
    conn.close()
    print(f"[SQLite] Previsão salva: {produtividade:.0f} kg/ha ({nivel})")


def salvar_metricas(metricas: dict):
    """Persiste as métricas do modelo treinado."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO metricas_modelo (timestamp, r2, mae, n_amostras)
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        metricas["r2"],
        metricas["mae"],
        metricas["n_amostras"]
    ))
    conn.commit()
    conn.close()
    print(f"[SQLite] Métricas salvas: R²={metricas['r2']} | MAE={metricas['mae']}")


def consultar_historico(n: int = 10) -> pd.DataFrame:
    """Retorna as últimas N previsões do banco."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"SELECT * FROM previsoes ORDER BY id DESC LIMIT {n}",
        conn
    )
    conn.close()
    return df


# ──────────────────────────────────────────────
# 5. EXECUÇÃO PRINCIPAL
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  AgroSat — Pipeline de ML")
    print("=" * 50)

    # Região: Cerrado Brasileiro (Sorriso/MT — maior produção de soja do país)
    LAT, LON = -12.55, -55.72

    # Tenta buscar dados reais; cai para sintético se necessário
    df_diario = fetch_nasa_power(LAT, LON, "20190101", "20231231")
    df_mensal = agregar_mensal(df_diario)

    print(f"\n[DADOS] {len(df_mensal)} meses de dados preparados.")
    print(df_mensal.describe().round(2))

    # Inicializa banco SQLite
    inicializar_banco()

    modelo, scaler, metricas = treinar_modelo(df_mensal)

    # Persiste métricas do modelo no banco
    salvar_metricas(metricas)

    # Exemplo de previsão
    print("\n[PREVISÃO] Cenário exemplo — Janeiro, condições médias:")
    cenario = {
        "temp_media":   28.5,
        "temp_max":     34.0,
        "precip_total": 180.0,
        "rad_media":    20.0,
        "dias_chuva":   15,
        "mes":          1,
    }
    prod = prever(modelo, scaler, cenario)
    print(f"  Produtividade prevista: {prod:.0f} kg/ha")

    # Persiste a previsão no banco
    salvar_previsao(LAT, LON, cenario, prod)

    # Simula mais alguns cenários para popular o histórico
    cenarios_extra = [
        {"temp_media": 24.0, "temp_max": 30.0, "precip_total": 20.0,  "rad_media": 17.0, "dias_chuva": 3,  "mes": 7},
        {"temp_media": 27.0, "temp_max": 33.0, "precip_total": 250.0, "rad_media": 21.0, "dias_chuva": 20, "mes": 12},
        {"temp_media": 30.0, "temp_max": 36.0, "precip_total": 0.0,   "rad_media": 22.0, "dias_chuva": 0,  "mes": 8},
        {"temp_media": 25.0, "temp_max": 31.0, "precip_total": 150.0, "rad_media": 19.5, "dias_chuva": 14, "mes": 3},
    ]
    for c in cenarios_extra:
        c["temp_max"] = c["temp_media"] + 6
        p = prever(modelo, scaler, c)
        salvar_previsao(LAT, LON, c, p)

    # Exibe histórico
    print("\n[SQLite] Histórico de previsões:")
    historico = consultar_historico(5)
    print(historico[["timestamp", "mes", "precip_total", "produtividade_prevista", "nivel_risco"]].to_string(index=False))

    # Salva dados para o dashboard
    df_mensal.to_csv("ml/dados_mensais.csv", index=False)
    print("\n[OK] Arquivos salvos em ml/")
    print("     → ml/modelo_agrosat.pkl")
    print("     → ml/scaler_agrosat.pkl")
    print("     → ml/dados_mensais.csv")
    print("     → ml/metricas.json")
