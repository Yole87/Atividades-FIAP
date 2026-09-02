import pandas as pd # serve para manipular e analisar dados (criar tabelas/DataFrames)
import random       # serve para gerar números aleatórios (usado para simular os sensores)

# Simulação de 1000 registros históricos
dados = []

print("Gerando dados realistas...")

for _ in range(1000):
    # Gera variáveis climáticas
    temp = round(random.uniform(15.0, 40.0), 2)
    precipitacao = round(random.uniform(0.0, 25.0), 2)
    ph = round(random.uniform(5.0, 8.0), 2)
    
    # Nutrientes (Independentes da chuva)
    n = random.choice([0, 1]) 
    p = random.choice([0, 1])
    k = random.choice([0, 1])
    
    # --- LÓGICA MAIS REALISTA ---
    # A umidade base começa em 50%
    # Cada mm de chuva adiciona 2.5% de umidade
    # Cada grau de calor acima de 20°C remove 1.2% (evaporação)
    umidade = 50 + (precipitacao * 2.5) - ((temp - 20) * 1.2)
    
    # O pH extremo pode afetar levemente a retenção de água (ajuste fino)
    if ph < 5.5 or ph > 7.5:
        umidade -= 5
    
    # Adiciona um pouco de aleatoriedade (ruído natural)
    umidade += random.uniform(-3, 3)
    
    # Garante que fique entre 0 e 100
    umidade = max(0, min(100, umidade))
    
    dados.append([temp, precipitacao, ph, n, p, k, round(umidade, 2)])

df = pd.DataFrame(dados, columns=['Temperatura', 'Precipitacao', 'pH', 'N', 'P', 'K', 'Umidade_Solo'])
df.to_csv('dados_historicos_irrigacao.csv', index=False)
print("Sucesso! Novo dataset gerado com lógica corrigida.")
