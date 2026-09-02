"""
FarmTech Solutions - Agricultura Digital (versão em VETORES)

- Estrutura de dados: VETORES (listas paralelas).
- Cada índice i representa uma cultura/registro.
- Subáreas: vetores de listas (um vetor por coluna de subáreas).

Executar: python farmtech.py
"""

import csv
import math
import sys

# ============================
# VETORES (listas paralelas)
# ============================
nomes = []                 # str: nome da cultura
subareas_tipos = []        # list[list[str]]: tipos das subáreas do registro i
subareas_areas = []        # list[list[float]]: áreas (m²) das subáreas do registro i
area_total_m2 = []         # float: área total da cultura em m²
insumo_nomes = []          # str: nome do insumo
insumo_modos = []          # str: "por_area_m2" | "por_area_ha" | "por_rua"
insumo_taxas = []          # float: taxa informada (L/m², L/ha ou mL/m), quando fizer sentido
insumo_unidades = []       # str: unidade da taxa
insumo_hectares = []       # float: área em ha (só faz sentido quando modo for por_area_ha, senão 0)
insumo_num_ruas = []       # int: número de ruas (modo por_rua; senão 0)
insumo_comp_medio_rua = [] # float: comprimento médio da rua (modo por_rua; senão 0)
insumo_total_metros = []   # float: total de metros (modo por_rua; senão 0)
insumo_total_l = []        # float: total em litros (modo por_area_ha e por_rua; por_area_m2 pode ser genérico)
insumo_total_unid = []     # float: total em “unidades” (modo por_area_m2), senão 0

# ============================
# Utilitários
# ============================
def leia_opcao(msg, opcoes=None):
    while True:
        v = input(msg).strip()
        if opcoes:
            if v in opcoes:
                return v
            print("Opção inválida. Escolha entre:", opcoes)
        else:
            if v == "":
                print("Entrada vazia. Tente novamente.")
                continue
            return v

def leia_float(msg, minimo=None):
    while True:
        s = input(msg).strip().replace(",", ".")
        try:
            v = float(s)
            if minimo is not None and v < minimo:
                print(f"Valor deve ser >= {minimo}.")
                continue
            return v
        except ValueError:
            print("Número inválido. Ex.: 1234.5")

def calcular_area_por_geometria():
    print("\nTipos de geometria:")
    print("1 - Retângulo (comprimento × largura)")
    print("2 - Triângulo (base × altura / 2)")
    print("3 - Círculo (π × raio²)")
    print("4 - Inserir área direta (m²)")
    opc = leia_opcao("Escolha (1-4): ", ["1", "2", "3", "4"])
    if opc == "1":
        c = leia_float("Comprimento (m): ", 0)
        l = leia_float("Largura (m): ", 0)
        return c * l, f"Retângulo ({c}×{l} m)"
    if opc == "2":
        b = leia_float("Base (m): ", 0)
        h = leia_float("Altura (m): ", 0)
        return (b * h) / 2, f"Triângulo (base {b} m × altura {h} m)"
    if opc == "3":
        r = leia_float("Raio (m): ", 0)
        return math.pi * r**2, f"Círculo (raio {r} m)"
    # 4
    a = leia_float("Área da sub-área (m²): ", 0)
    return a, f"Área direta ({a} m²)"

# ============================
# CRUD
# ============================
def inserir_registro():
    print("\n=== Inserir nova cultura ===")
    nome = leia_opcao("Nome da cultura (ex: Milho, Soja): ")

    # Subáreas (listas para este registro)
    tipos_local = []
    areas_local = []
    while True:
        print(f"\nInserindo sub-área para {nome}")
        a, t = calcular_area_por_geometria()
        tipos_local.append(t)
        areas_local.append(a)
        if leia_opcao("Adicionar outra sub-área? (s/n): ", ["s", "n"]) == "n":
            break

    total = sum(areas_local)
    print(f"Área total para {nome}: {total:.2f} m² ({total/10000:.4f} ha)")

    # Insumo
    ins_nome = leia_opcao("\nNome do insumo (ex: Fosfato): ")
    print("Modos de aplicação:")
    print("1 - por área (m²)")
    print("2 - por área (hectare)")
    print("3 - por rua (mL por metro)")
    modo_escolha = leia_opcao("Escolha (1-3): ", ["1", "2", "3"])

    if modo_escolha == "1":
        taxa = leia_float("Taxa (unidades por m²), ex: 0.0005 L/m²: ", 0)
        qtd_total_unid = taxa * total
        # preencher vetores
        nomes.append(nome)
        subareas_tipos.append(tipos_local)
        subareas_areas.append(areas_local)
        area_total_m2.append(total)
        insumo_nomes.append(ins_nome)
        insumo_modos.append("por_area_m2")
        insumo_taxas.append(taxa)
        insumo_unidades.append("unid/m²")
        insumo_hectares.append(0.0)
        insumo_num_ruas.append(0)
        insumo_comp_medio_rua.append(0.0)
        insumo_total_metros.append(0.0)
        insumo_total_l.append(0.0)          # não é L garantido; guardamos em “unid”
        insumo_total_unid.append(qtd_total_unid)
        print(f"Total do insumo (unidades): {qtd_total_unid:.4f}")

    elif modo_escolha == "2":
        taxa = leia_float("Taxa (L por ha), ex: 5 L/ha: ", 0)
        ha = total / 10000.0
        qtd_total_l = taxa * ha
        nomes.append(nome)
        subareas_tipos.append(tipos_local)
        subareas_areas.append(areas_local)
        area_total_m2.append(total)
        insumo_nomes.append(ins_nome)
        insumo_modos.append("por_area_ha")
        insumo_taxas.append(taxa)
        insumo_unidades.append("L/ha")
        insumo_hectares.append(ha)
        insumo_num_ruas.append(0)
        insumo_comp_medio_rua.append(0.0)
        insumo_total_metros.append(0.0)
        insumo_total_l.append(qtd_total_l)
        insumo_total_unid.append(0.0)
        print(f"Total do insumo: {qtd_total_l:.4f} L")

    else:
        taxa_ml_m = leia_float("Taxa (mL por metro de rua): ", 0)
        if leia_opcao("Sabe o número de ruas? (s/n): ", ["s", "n"]) == "s":
            n_ruas = int(leia_float("Número de ruas: ", 0))
            comp = leia_float("Comprimento médio por rua (m): ", 0)
            total_m = n_ruas * comp
        else:
            largura = leia_float("Largura aproximada do campo (m): ", 0.01)
            espac = leia_float("Espaçamento entre ruas (m): ", 0.01)
            n_ruas = int(max(1, largura // espac))
            comp = total / largura
            total_m = n_ruas * comp
            print(f"Estimativa: {n_ruas} ruas × {comp:.2f} m = {total_m:.2f} m")
        qtd_total_ml = taxa_ml_m * total_m
        qtd_total_l = qtd_total_ml / 1000.0

        nomes.append(nome)
        subareas_tipos.append(tipos_local)
        subareas_areas.append(areas_local)
        area_total_m2.append(total)
        insumo_nomes.append(ins_nome)
        insumo_modos.append("por_rua")
        insumo_taxas.append(taxa_ml_m)
        insumo_unidades.append("mL/m")
        insumo_hectares.append(0.0)
        insumo_num_ruas.append(n_ruas)
        insumo_comp_medio_rua.append(comp)
        insumo_total_metros.append(total_m)
        insumo_total_l.append(qtd_total_l)
        insumo_total_unid.append(0.0)
        print(f"Total do insumo: {qtd_total_ml:.2f} mL = {qtd_total_l:.4f} L")

def mostrar_dados():
    if not nomes:
        print("\nNenhum registro.")
        return
    print("\n=== Registros ===")
    for i in range(len(nomes)):
        print(f"\n[{i}] Cultura: {nomes[i]}")
        tot = area_total_m2[i]
        print(f"    Área total: {tot:.2f} m² ({tot/10000:.4f} ha)")
        print("    Sub-áreas:")
        for j, (t, a) in enumerate(zip(subareas_tipos[i], subareas_areas[i])):
            print(f"       - {j}: {t} => {a:.2f} m²")
        print(f"    Insumo: {insumo_nomes[i]} ({insumo_modos[i]})")
        modo = insumo_modos[i]
        if modo == "por_area_m2":
            print(f"       taxa {insumo_taxas[i]} {insumo_unidades[i]} => total {insumo_total_unid[i]:.4f} unid")
        elif modo == "por_area_ha":
            print(f"       taxa {insumo_taxas[i]} {insumo_unidades[i]} | ha {insumo_hectares[i]:.4f} => total {insumo_total_l[i]:.4f} L")
        else:
            print(f"       {insumo_taxas[i]} {insumo_unidades[i]} | ruas {insumo_num_ruas[i]} | comp médio {insumo_comp_medio_rua[i]:.2f} m | total {insumo_total_metros[i]:.2f} m")
            print(f"       Total: {insumo_total_l[i]:.4f} L")

def atualizar_registro():
    if not nomes:
        print("\nNada para atualizar.")
        return
    mostrar_dados()
    pos = int(leia_float("\nÍndice do registro a atualizar: ", 0))
    if not (0 <= pos < len(nomes)):
        print("Índice inválido.")
        return
    # estratégia simples: deletar e re-inserir
    print(f"Atualizando [{pos}] - {nomes[pos]} (os dados atuais serão substituídos)")
    deletar_registro(pos, silencioso=True)
    inserir_registro()
    print("Registro atualizado.")

def deletar_registro(pos=None, silencioso=False):
    if not nomes:
        if not silencioso:
            print("\nNada para deletar.")
        return
    if pos is None:
        mostrar_dados()
        pos = int(leia_float("\nÍndice do registro a deletar: ", 0))
    if not (0 <= pos < len(nomes)):
        print("Índice inválido.")
        return
    # Remover em TODOS os vetores
    for vetor in (nomes, subareas_tipos, subareas_areas, area_total_m2,
                  insumo_nomes, insumo_modos, insumo_taxas, insumo_unidades,
                  insumo_hectares, insumo_num_ruas, insumo_comp_medio_rua,
                  insumo_total_metros, insumo_total_l, insumo_total_unid):
        vetor.pop(pos)
    if not silencioso:
        print("Registro deletado.")

def exportar_csv(nome_arquivo="farmtech_export.csv"):
    if not nomes:
        print("Nada para exportar.")
        return
    with open(nome_arquivo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "indice","nome","area_total_m2","area_ha",
            "insumo_nome","insumo_modo","insumo_taxa","insumo_unidade",
            "insumo_hectares","insumo_num_ruas","insumo_comp_medio_rua",
            "insumo_total_metros","insumo_total_l","insumo_total_unid"
        ])
        for i in range(len(nomes)):
            w.writerow([
                i, nomes[i],
                f"{area_total_m2[i]:.6f}",
                f"{area_total_m2[i]/10000.0:.6f}",
                insumo_nomes[i], insumo_modos[i],
                f"{insumo_taxas[i]:.6f}",
                insumo_unidades[i],
                f"{insumo_hectares[i]:.6f}",
                insumo_num_ruas[i],
                f"{insumo_comp_medio_rua[i]:.6f}",
                f"{insumo_total_metros[i]:.6f}",
                f"{insumo_total_l[i]:.6f}",
                f"{insumo_total_unid[i]:.6f}",
            ])
    print(f"Exportado para {nome_arquivo}. Abra no R com read.csv().")

# ============================
# Menu
# ============================
def menu():
    while True:
        print("\n=== FarmTech (VETORES) ===")
        print("1 - Inserir nova cultura")
        print("2 - Mostrar dados")
        print("3 - Atualizar registro")
        print("4 - Deletar registro")
        print("5 - Exportar CSV (para R)")
        print("6 - Sair")
        op = leia_opcao("Escolha (1-6): ", [str(i) for i in range(1,7)])
        if op == "1": inserir_registro()
        elif op == "2": mostrar_dados()
        elif op == "3": atualizar_registro()
        elif op == "4": deletar_registro()
        elif op == "5":
            nome = input("Nome do CSV (enter para 'farmtech_export.csv'): ").strip() or "farmtech_export.csv"
            exportar_csv(nome)
        else:
            print("Até logo!")
            break

# ============================
# Main
# ============================
if __name__ == "__main__":
    print("Bem-vindo ao FarmTech - Estrutura em Vetores")
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
        sys.exit(0)
