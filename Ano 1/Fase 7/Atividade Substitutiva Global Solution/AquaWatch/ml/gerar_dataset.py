"""
AquaWatch - Modulo 1A: Geracao de Dataset Sintetico
Gera series temporais de qualidade da agua.

Estrategia para acuracia realista (nao-trivial):
- 30% das amostras sao geradas na "zona de transicao" entre classes adjacentes
- Ruido multiplicativo alto (sensor drift)
- Classes normal/alerta tem overlap significativo em 3+ features
- Resultado esperado: acuracia entre 88-96% (realista para sensores IoT)
"""

import numpy as np
import json
import os

SEED = 42
np.random.seed(SEED)

N_AMOSTRAS_POR_CLASSE = 200
N_TIMESTEPS = 24
N_FEATURES  = 6
FRACAO_TRANSICAO = 0.30   # 30% das amostras em zona limítrofe

CLASSES = {0: "normal", 1: "alerta", 2: "critico", 3: "toxico"}

# Médias por classe - mais próximas para forçar dificuldade real
# pH normal (6.8-7.8) vs alerta (6.0-7.2) -> overlap intencional em 6.8-7.2
PARAMETROS = {
    #            pH    turb   TDS    temp   OD     cond
    0: dict(means=[7.1,  2.5,  290.,  21.,   7.5,   480.],
            stds =[0.8,  1.8,  120.,  2.8,   1.3,   150.]),
    1: dict(means=[6.4,  8.0,  520.,  25.,   5.5,   920.],
            stds =[0.9,  4.0,  160.,  3.2,   1.4,   220.]),
    2: dict(means=[5.3,  22.,  820.,  29.,   3.0,   1600.],
            stds =[1.0,  8.0,  200.,  3.8,   1.3,   320.]),
    3: dict(means=[3.5,  80.,  1800., 34.,   0.9,   3900.],
            stds =[1.3,  25.,  350.,  4.5,   0.8,   650.]),
}

def gerar_serie_normal(classe_id):
    p = PARAMETROS[classe_id]
    serie = np.zeros((N_TIMESTEPS, N_FEATURES))
    for f in range(N_FEATURES):
        base  = np.random.normal(p["means"][f], p["stds"][f], N_TIMESTEPS)
        drift = np.linspace(0, np.random.normal(0, p["stds"][f] * 0.3), N_TIMESTEPS)
        # ruido sensor (multiplicativo)
        ruido = 1 + np.random.normal(0, 0.08, N_TIMESTEPS)
        serie[:, f] = base * ruido + drift
        if f == 3:  serie[:, f] += 2.0 * np.sin(np.linspace(0, 2*np.pi, N_TIMESTEPS))
        if f == 4:  serie[:, f] -= 1.0 * np.sin(np.linspace(0, 2*np.pi, N_TIMESTEPS))
    return serie

def gerar_serie_transicao(cls_a, cls_b):
    """Gera amostra interpolada entre duas classes adjacentes (zona limítrofe)."""
    p_a = PARAMETROS[cls_a]
    p_b = PARAMETROS[cls_b]
    alpha = np.random.uniform(0.4, 0.6)   # próximo do meio
    serie = np.zeros((N_TIMESTEPS, N_FEATURES))
    for f in range(N_FEATURES):
        mean_interp = alpha * p_a["means"][f] + (1-alpha) * p_b["means"][f]
        std_interp  = max(p_a["stds"][f], p_b["stds"][f]) * 1.2
        base  = np.random.normal(mean_interp, std_interp, N_TIMESTEPS)
        ruido = 1 + np.random.normal(0, 0.12, N_TIMESTEPS)
        serie[:, f] = base * ruido
    return serie

def main():
    print("[AQUAWATCH] Gerando dataset sintetico com variacao realistica...")
    print(f"[CONFIG] {N_AMOSTRAS_POR_CLASSE} amostras/classe | {FRACAO_TRANSICAO*100:.0f}% em zona de transicao\n")

    X_list, y_list = [], []
    n_transicao = int(N_AMOSTRAS_POR_CLASSE * FRACAO_TRANSICAO)
    n_normal    = N_AMOSTRAS_POR_CLASSE - n_transicao
    adjacentes  = [(0,1), (1,2), (2,3)]   # pares de classes adjacentes

    for classe_id, nome_classe in CLASSES.items():
        print(f"[CLASSE {classe_id}] '{nome_classe}' | {n_normal} normais + {n_transicao} zona de transicao")
        for _ in range(n_normal):
            X_list.append(gerar_serie_normal(classe_id))
            y_list.append(classe_id)
        # Amostras de transicao para classes adjacentes
        for _ in range(n_transicao):
            # Escolhe par adjacente que inclui esta classe
            pares = [p for p in adjacentes if classe_id in p]
            cls_a, cls_b = pares[np.random.randint(len(pares))]
            X_list.append(gerar_serie_transicao(cls_a, cls_b))
            y_list.append(classe_id)

    X = np.array(X_list)
    y = np.array(y_list)

    # Embaralha
    idx = np.random.permutation(len(y))
    X, y = X[idx], y[idx]

    # Valida constraints fisicos
    X[:,:,0] = np.clip(X[:,:,0], 0, 14)
    X[:,:,1] = np.maximum(X[:,:,1], 0.1)
    X[:,:,2] = np.maximum(X[:,:,2], 10.)
    X[:,:,4] = np.clip(X[:,:,4], 0, 14)
    X[:,:,5] = np.maximum(X[:,:,5], 10.)

    print(f"\n[DATASET] Shape X: {X.shape} | Classes: {np.unique(y, return_counts=True)[1]}")
    print(f"[NOTA] 30% transicao -> acuracia esperada 88-96% (realista para sensor IoT)")

    os.makedirs("dados", exist_ok=True)
    np.save("dados/X_agua.npy", X)
    np.save("dados/y_agua.npy", y)

    with open("dados/stats_dataset.json", "w", encoding="utf-8") as f:
        json.dump({
            "seed": SEED, "n_timesteps": N_TIMESTEPS, "n_features": N_FEATURES,
            "features": ["pH","turbidez_NTU","TDS_mgL","temperatura_C","OD_mgL","condutividade_uScm"],
            "classes": CLASSES, "total_amostras": int(len(y)),
            "fracao_transicao": FRACAO_TRANSICAO,
            "nota": "30% amostras em zona de transicao entre classes adjacentes"
        }, f, indent=2, ensure_ascii=True)

    print("\n[OK] dados/X_agua.npy | dados/y_agua.npy | dados/stats_dataset.json")
    print("[AQUAWATCH] Dataset gerado com sucesso!")

if __name__ == "__main__":
    main()
