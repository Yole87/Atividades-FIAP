import json
from datetime import datetime
import locale
from db_operations import salvar_analise_db, carregar_historico_db, excluir_analise_db # Importa as funções que criamos no outro arquivo, incluindo a nova 'excluir_analise_db'

# --- CONFIGURAÇÃO GLOBAL ---
USAR_BANCO_DE_DADOS = True # Mude para False para usar o sistema de arquivos JSON

# --- BASE DE CONHECIMENTO DO CHECKLIST ---
CHECKLIST_ITENS = [
    {"chave": "manutencao_em_dia", "pergunta": "A manutenção da colhedora (lâminas, etc.) estava em dia?", "recomendacao": "Lâminas cegas ou mal reguladas rasgam a cana em vez de cortá-la, causando perdas de sacarose e danos à soqueira (raiz)."},
    {"chave": "velocidade_ideal", "pergunta": "A velocidade de operação foi mantida no ideal recomendado?", "recomendacao": "Operar a colhedora em alta velocidade aumenta drasticamente as perdas, pois a máquina não consegue processar o volume de cana eficientemente."},
    {"chave": "regulagem_extratores", "pergunta": "Os extratores (ventiladores) da colhedora foram regulados para este talhão?", "recomendacao": "Extratores mal regulados podem jogar pedaços de cana (toletes) para fora junto com a palha, resultando em perda direta de produto."},
    {"chave": "calibracao_corte", "pergunta": "A altura de corte da colhedora foi calibrada corretamente?", "recomendacao": "Um corte muito alto deixa cana valiosa no campo. Um corte muito baixo danifica a soqueira, prejudicando a próxima safra."},
    {"chave": "solo_seco", "pergunta": "A colheita foi realizada com o solo predominantemente seco?", "recomendacao": "Colher com solo úmido aumenta a compactação, prejudica a saúde do solo e faz com que mais impurezas (terra) sejam levadas para a usina."},
    {"chave": "cana_em_pe", "pergunta": "A cana no talhão estava predominantemente em pé (não tombada)?", "recomendacao": "A colheita de cana tombada (acamada) é inerentemente menos eficiente e sempre resulta em maiores índices de perda."},
    {"chave": "operador_treinado", "pergunta": "O operador da máquina possui treinamento recente?", "recomendacao": "Um operador bem treinado é o fator mais crítico para a eficiência da colheita, sabendo ajustar a máquina às condições do campo em tempo real."},
    {"chave": "logistica_rapida", "pergunta": "O tempo entre o corte e o transporte para a usina foi mínimo?", "recomendacao": "A cana cortada perde teor de açúcar (sacarose) rapidamente. Atrasos na logística representam perda de qualidade e valor do produto."}
]

# --- Funções de arquivo JSON (permanecem para fallback) ---
def carregar_historico_json():
    try:
        with open('historico.json', 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError: return []

def salvar_historico_json(historico):
    with open('historico.json', 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

# --- Funções de Lógica de Negócio ---
def calcular_perda(toneladas_potenciais, toneladas_reais_colhidas, preco_por_tonelada):
    if toneladas_potenciais <= 0: return None
    toneladas_perdidas = toneladas_potenciais - toneladas_reais_colhidas
    percentual_perda = (toneladas_perdidas / toneladas_potenciais) * 100
    prejuizo_financeiro = toneladas_perdidas * preco_por_tonelada
    return {"toneladas_perdidas": toneladas_perdidas, "percentual_perda": percentual_perda, "prejuizo_financeiro": prejuizo_financeiro}

def coletar_dados_qualitativos():
    print("\n--- CHECKLIST DE DIAGNÓSTICO (FATORES DE PERDA) ---")
    print("Por favor, responda com 'S' para Sim ou 'N' para Não.")
    respostas = {}
    for item in CHECKLIST_ITENS:
        chave, pergunta_texto = item["chave"], item["pergunta"]
        while True:
            resposta = input(f"- {pergunta_texto} (S/N): ").upper()
            if resposta in ['S', 'N']:
                respostas[chave] = resposta
                break
            else:
                print("Resposta inválida. Por favor, digite apenas S ou N.")
    return respostas

def exibir_recomendacoes(respostas_checklist):
    print("\n--- RELATÓRIO DE RECOMENDAÇÕES PARA MELHORIA ---")
    respostas_negativas = {chave for chave, resposta in respostas_checklist.items() if resposta == 'N'}
    if not respostas_negativas:
        print("Parabéns! Todas as boas práticas foram seguidas nesta colheita.")
        return
    print("Com base nas suas respostas, foram identificados os seguintes pontos de melhoria:")
    for item in CHECKLIST_ITENS:
        if item["chave"] in respostas_negativas:
            print(f"\n  [!] Ponto de Atenção: {item['pergunta']}")
            print(f"      -> Recomendação: {item['recomendacao']}")
            
# --- Funções de Fluxo de Trabalho ---
def executar_nova_analise():
    print("\n--- REGISTRAR NOVA ANÁLISE DE PERDA ---")
    while True:
        try:
            input_potencial = input("1. Toneladas que deveriam ser colhidas (potencial total): ")
            input_colhidas = input("2. Toneladas que foram realmente colhidas: ")
            input_preco = input("3. Preço por tonelada (R$): ")
            potencial = float(input_potencial.replace('.', '').replace(',', '.'))
            colhidas = float(input_colhidas.replace('.', '').replace(',', '.'))
            preco = float(input_preco.replace('.', '').replace(',', '.'))
            if colhidas > potencial:
                print(f"\nATENÇÃO: O valor colhido ({colhidas}) é maior que o potencial ({potencial}).")
                print("Isso parece ser um erro de digitação. Por favor, verifique os dados e tente novamente.\n")
                continue
            break
        except ValueError:
            print("\nERRO: Valor inválido. Digite apenas números, por exemplo: 20000\n")

    dados_perda = calcular_perda(potencial, colhidas, preco)
    if dados_perda:
        print("\n--- RESULTADO DA ANÁLISE QUANTITATIVA ---")
        print(f"Perda em Toneladas: {dados_perda['toneladas_perdidas']:n} t")
        print(f"Percentual de Perda: {dados_perda['percentual_perda']:.2f}%")
        print(f"Prejuízo Financeiro: {locale.currency(dados_perda['prejuizo_financeiro'], grouping=True)}")
        print("-----------------------------------------")
        respostas_checklist = coletar_dados_qualitativos()
        exibir_recomendacoes(respostas_checklist)
        registro = {"data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "potencial_colheita_t": potencial, "real_colhido_t": colhidas, "preco_tonelada_rs": preco, "analise_resultado": dados_perda, "checklist": respostas_checklist}
        if USAR_BANCO_DE_DADOS:
            if salvar_analise_db(registro): print("\nAnálise salva no banco de dados com sucesso!")
        else:
            historico = carregar_historico_json()
            historico.append(registro)
            salvar_historico_json(historico)
            print("\nAnálise salva no arquivo JSON com sucesso!")
    else:
        print("Não foi possível calcular o resultado.")

def exibir_resumo_historico():
    print("\n--- RESUMO DO HISTÓRICO DE ANÁLISES ---")
    historico = carregar_historico_db() if USAR_BANCO_DE_DADOS else carregar_historico_json()
    if not historico:
        print("Nenhuma análise foi registrada ainda.")
        return None
    
    for i, registro in enumerate(historico, 1):
        if USAR_BANCO_DE_DADOS:
            data = registro['data_analise'].strftime('%d/%m/%Y %H:%M:%S')
            potencial, colhido = registro['potencial_toneladas'], registro['colhido_toneladas']
            prejuizo = registro['prejuizo_financeiro']
            checklist_data_str = registro.get('observacoes_checklist')
            checklist_data = json.loads(checklist_data_str) if checklist_data_str else None
        else:
            resultado = registro['analise_resultado']
            data = registro['data']
            potencial, colhido = registro.get('potencial_colheita_t', 0), registro.get('real_colhido_t', 0)
            prejuizo = resultado['prejuizo_financeiro']
            checklist_data = registro.get('checklist')

        print(f"\n--- Análise #{i} | Data: {data} ---")
        print(f"  - Potencial: {potencial:n} t | Colhido: {colhido:n} t")
        print(f"  - Prejuízo Financeiro Estimado: {locale.currency(prejuizo, grouping=True)}")
        
        if checklist_data:
            pontos_de_atencao = [key for key, val in checklist_data.items() if val == 'N']
            if pontos_de_atencao:
                print(f"  - Pontos de Atenção: {', '.join(pontos_de_atencao)}")
    
    print("\n------------------------------------")
    return historico

def exibir_detalhes_analise():
    historico = exibir_resumo_historico()
    if not historico: return
    while True:
        try:
            escolha = input("Digite o número da análise que deseja detalhar (ou 0 para voltar): ")
            num_analise = int(escolha)
            if num_analise == 0: return
            if 1 <= num_analise <= len(historico):
                analise_selecionada = historico[num_analise - 1]
                break
            else: print("Número de análise inválido.")
        except ValueError: print("Entrada inválida. Por favor, digite um número.")

    print("\n--- DIAGNÓSTICO COMPLETO DA ANÁLISE ---")
    checklist = {}
    if USAR_BANCO_DE_DADOS:
        checklist_str = analise_selecionada.get('observacoes_checklist')
        if checklist_str: checklist = json.loads(checklist_str)
        print(f"Data: {analise_selecionada['data_analise'].strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Potencial de Colheita: {analise_selecionada['potencial_toneladas']:n} t")
        print(f"Real Colhido: {analise_selecionada['colhido_toneladas']:n} t")
        print(f"Preço por Tonelada: {locale.currency(analise_selecionada['preco_tonelada'], grouping=True)}")
        print(f"\nPrejuízo Financeiro: {locale.currency(analise_selecionada['prejuizo_financeiro'], grouping=True)}")
    else: pass
    
    if not checklist:
        print("\nNenhum dado de checklist foi registrado para esta análise.")
    else:
        respostas_negativas = [item for item in CHECKLIST_ITENS if checklist.get(item["chave"]) == 'N']
        print("\n[Checklist de Boas Práticas]")
        for item in CHECKLIST_ITENS:
            print(f"- {item['pergunta']} -> Resposta: {checklist.get(item['chave'], 'N/A')}")
        if respostas_negativas:
            print("\n[Orientações para Melhoria]")
            for item in respostas_negativas:
                print(f"- {item['pergunta']}")
                print(f"  -> Recomendação: {item['recomendacao']}")
    print("--------------------------------------")

def excluir_analise():
    historico = exibir_resumo_historico()
    if not historico: return
    while True:
        try:
            escolha = input("Digite o número da análise que deseja EXCLUIR (ou 0 para cancelar): ")
            num_analise = int(escolha)
            if num_analise == 0:
                print("Operação cancelada.")
                return
            if 1 <= num_analise <= len(historico):
                analise_para_excluir = historico[num_analise - 1]
                break
            else: print("Número de análise inválido.")
        except ValueError: print("Entrada inválida. Por favor, digite um número.")
    
    confirmacao = input(f"Tem certeza que deseja excluir permanentemente a Análise #{num_analise}? (S/N): ").upper()
    if confirmacao == 'S':
        analise_id = analise_para_excluir['id']
        if excluir_analise_db(analise_id):
            print(f"Análise #{num_analise} foi excluída com sucesso.")
        else:
            print("Ocorreu um erro ao tentar excluir a análise.")
    else:
        print("Exclusão cancelada.")

# --- Função Principal (Ponto de Entrada) ---
def main():
    try: locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error: locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    
    while True:
        print("\n--- SISTEMA DE GESTÃO DE PERDAS AGRÍCOLAS ---")
        print("Escolha uma opção:")
        print("[1] Registrar Nova Análise")
        print("[2] Ver Resumo do Histórico")
        print("[3] Ver Detalhes de uma Análise")
        print("[4] Excluir uma Análise")
        print("[5] Sair")
        
        escolha = input(">> Digite sua escolha: ")
        
        if escolha == '1': executar_nova_analise()
        elif escolha == '2': exibir_resumo_historico()
        elif escolha == '3': exibir_detalhes_analise()
        elif escolha == '4': excluir_analise()
        elif escolha == '5':
            print("Encerrando o sistema. Até logo!")
            break
        else:
            print("\nOpção inválida. Por favor, escolha uma das opções do menu.")

# --- Execução do Programa ---
if __name__ == "__main__":
    main()