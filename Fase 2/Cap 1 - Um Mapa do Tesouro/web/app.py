#!/usr/bin/env python3
"""
Servidor Web Flask para visualização do projeto FarmTech-Fase2
Dashboard interativo com dados em tempo real
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime, timedelta
import random
from collections import deque
import statistics
from flask import Flask, render_template, jsonify, request

# Adicionar o diretório python ao path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))

try:
    from justificativa_irrigacao import JustificativaIrrigacao
    justificador_disponivel = True
except ImportError:
    justificador_disponivel = False
    print("Módulo de justificativas não disponível")

app = Flask(__name__)

# Configurações
PYTHON_DIR = os.path.join(os.path.dirname(__file__), '..', 'python')
# Após a reestruturação, os arquivos JSON residem em web/data
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Estado global da irrigação manual
irrigacao_manual_ativa = False
timestamp_irrigacao_manual = None
ultima_irrigacao_timestamp = None  # Timestamp da última irrigação (manual ou automática)

# ===== SISTEMA DE ARMAZENAMENTO EM MEMÓRIA =====
class HistoricoSistema:
    def __init__(self, max_registros=1000):
        self.max_registros = max_registros
        self.dados_historicos = deque(maxlen=max_registros)
        self.estatisticas_cache = {}
        self.alertas_ativos = []
        self.ultima_atualizacao = None
        
    def adicionar_registro(self, dados_sensores, dados_meteorologicos, recomendacao):
        """Adiciona um novo registro ao histórico"""
        timestamp = datetime.now()
        
        registro = {
            'timestamp': timestamp,
            'sensores': {
                'umidade_solo': dados_sensores.get('umidade_solo', 0),
                'ph_solo': dados_sensores.get('ph_solo', 7.0),
                'temperatura': dados_sensores.get('temperatura', 25),
                'umidade_ar': dados_sensores.get('umidade_ar', 50),
                'npk': {
                    'nitrogenio': dados_sensores.get('nitrogenio', 0),
                    'fosforo': dados_sensores.get('fosforo', 0),
                    'potassio': dados_sensores.get('potassio', 0)
                },
                'qualidade_solo': dados_sensores.get('qualidade_solo', 50),
                'salinidade': dados_sensores.get('salinidade', 0.5),
                'evapotranspiracao': dados_sensores.get('evapotranspiracao', 5.0)
            },
            'meteorologia': {
                'cenario': dados_meteorologicos.get('cenario', 'Desconhecido'),
                'temperatura': dados_meteorologicos.get('temperatura', 25),
                'umidade': dados_meteorologicos.get('umidade', 50),
                'pressao': dados_meteorologicos.get('pressao', 1013),
                'vento': dados_meteorologicos.get('vento', 0),
                'chuva_prevista': dados_meteorologicos.get('chuva_prevista', False)
            },
            'irrigacao': {
                'ativa': recomendacao.get('irrigar', False),
                'motivo': recomendacao.get('motivo', ''),
                'confiabilidade': recomendacao.get('confiabilidade', 'BAIXA')
            }
        }
        
        self.dados_historicos.append(registro)
        self.ultima_atualizacao = timestamp
        self._atualizar_estatisticas()
        self._verificar_alertas(registro)
        
    def _atualizar_estatisticas(self):
        """Calcula estatísticas baseadas no histórico"""
        if not self.dados_historicos:
            return
            
        # Dados das últimas 24 horas
        agora = datetime.now()
        dados_24h = [r for r in self.dados_historicos 
                    if (agora - r['timestamp']).total_seconds() <= 86400]
        
        if not dados_24h:
            return
            
        # Estatísticas de sensores
        umidades = [r['sensores']['umidade_solo'] for r in dados_24h]
        temperaturas = [r['sensores']['temperatura'] for r in dados_24h]
        ph_valores = [r['sensores']['ph_solo'] for r in dados_24h]
        qualidade_valores = [r['sensores']['qualidade_solo'] for r in dados_24h]
        
        # NPK médios
        npk_n = [r['sensores']['npk']['nitrogenio'] for r in dados_24h]
        npk_p = [r['sensores']['npk']['fosforo'] for r in dados_24h]
        npk_k = [r['sensores']['npk']['potassio'] for r in dados_24h]
        
        # Irrigações nas últimas 24h
        irrigacoes = [r for r in dados_24h if r['irrigacao']['ativa']]
        
        self.estatisticas_cache = {
            'periodo': '24h',
            'total_registros': len(dados_24h),
            'sensores': {
                'umidade_solo': {
                    'atual': umidades[-1] if umidades else 0,
                    'media': statistics.mean(umidades) if umidades else 0,
                    'minima': min(umidades) if umidades else 0,
                    'maxima': max(umidades) if umidades else 0,
                    'tendencia': self._calcular_tendencia(umidades)
                },
                'temperatura': {
                    'atual': temperaturas[-1] if temperaturas else 0,
                    'media': statistics.mean(temperaturas) if temperaturas else 0,
                    'minima': min(temperaturas) if temperaturas else 0,
                    'maxima': max(temperaturas) if temperaturas else 0,
                    'tendencia': self._calcular_tendencia(temperaturas)
                },
                'ph_solo': {
                    'atual': ph_valores[-1] if ph_valores else 7.0,
                    'media': statistics.mean(ph_valores) if ph_valores else 7.0,
                    'minima': min(ph_valores) if ph_valores else 7.0,
                    'maxima': max(ph_valores) if ph_valores else 7.0,
                    'tendencia': self._calcular_tendencia(ph_valores)
                },
                'qualidade_solo': {
                    'atual': qualidade_valores[-1] if qualidade_valores else 50,
                    'media': statistics.mean(qualidade_valores) if qualidade_valores else 50,
                    'classificacao': self._classificar_qualidade_solo(
                        statistics.mean(qualidade_valores) if qualidade_valores else 50
                    )
                }
            },
            'npk': {
                'nitrogenio': {
                    'atual': npk_n[-1] if npk_n else 0,
                    'media': statistics.mean(npk_n) if npk_n else 0,
                    'status': self._classificar_npk('N', statistics.mean(npk_n) if npk_n else 0)
                },
                'fosforo': {
                    'atual': npk_p[-1] if npk_p else 0,
                    'media': statistics.mean(npk_p) if npk_p else 0,
                    'status': self._classificar_npk('P', statistics.mean(npk_p) if npk_p else 0)
                },
                'potassio': {
                    'atual': npk_k[-1] if npk_k else 0,
                    'media': statistics.mean(npk_k) if npk_k else 0,
                    'status': self._classificar_npk('K', statistics.mean(npk_k) if npk_k else 0)
                }
            },
            'irrigacao': {
                'total_ativacoes': len(irrigacoes),
                'tempo_total_ativo': len(irrigacoes) * 15,  # Assumindo 15min por irrigação
                'eficiencia': self._calcular_eficiencia_irrigacao(dados_24h),
                'ultima_irrigacao': irrigacoes[-1]['timestamp'].strftime('%H:%M') if irrigacoes else 'Nenhuma'
            },
            'alertas_ativos': len(self.alertas_ativos),
            'ultima_atualizacao': self.ultima_atualizacao.strftime('%d/%m/%Y %H:%M:%S')
        }
    
    def _calcular_tendencia(self, valores):
        """Calcula tendência dos valores (crescente, decrescente, estável)"""
        if len(valores) < 2:
            return 'estável'
            
        # Pegar últimos 10 valores para tendência
        ultimos = valores[-10:] if len(valores) >= 10 else valores
        
        if len(ultimos) < 2:
            return 'estável'
            
        # Calcular diferença média
        diferencas = [ultimos[i+1] - ultimos[i] for i in range(len(ultimos)-1)]
        media_diferenca = statistics.mean(diferencas)
        
        if media_diferenca > 0.5:
            return 'crescente'
        elif media_diferenca < -0.5:
            return 'decrescente'
        else:
            return 'estável'
    
    def _classificar_qualidade_solo(self, valor):
        """Classifica a qualidade do solo"""
        if valor >= 80:
            return 'Excelente'
        elif valor >= 60:
            return 'Boa'
        elif valor >= 40:
            return 'Regular'
        elif valor >= 20:
            return 'Ruim'
        else:
            return 'Crítica'
    
    def _classificar_npk(self, nutriente, valor):
        """Classifica o status do NPK"""
        if nutriente == 'N':  # Nitrogênio
            if valor >= 80: return 'Alto'
            elif valor >= 40: return 'Adequado'
            elif valor >= 20: return 'Baixo'
            else: return 'Crítico'
        elif nutriente == 'P':  # Fósforo
            if valor >= 70: return 'Alto'
            elif valor >= 35: return 'Adequado'
            elif valor >= 15: return 'Baixo'
            else: return 'Crítico'
        elif nutriente == 'K':  # Potássio
            if valor >= 75: return 'Alto'
            elif valor >= 40: return 'Adequado'
            elif valor >= 20: return 'Baixo'
            else: return 'Crítico'
    
    def _calcular_eficiencia_irrigacao(self, dados_24h):
        """Calcula eficiência da irrigação baseada na resposta da umidade"""
        if not dados_24h:
            return 0
            
        irrigacoes_com_resposta = 0
        total_irrigacoes = 0
        
        for i, registro in enumerate(dados_24h):
            if registro['irrigacao']['ativa']:
                total_irrigacoes += 1
                # Verificar se umidade aumentou nas próximas 2 horas
                timestamp_irrigacao = registro['timestamp']
                for j in range(i+1, min(i+8, len(dados_24h))):  # Próximas 8 medições (2h)
                    if (dados_24h[j]['timestamp'] - timestamp_irrigacao).total_seconds() <= 7200:
                        if dados_24h[j]['sensores']['umidade_solo'] > registro['sensores']['umidade_solo']:
                            irrigacoes_com_resposta += 1
                            break
        
        return (irrigacoes_com_resposta / total_irrigacoes * 100) if total_irrigacoes > 0 else 0
    
    def _verificar_alertas(self, registro):
        """Verifica e atualiza alertas baseados no registro atual"""
        self.alertas_ativos = []  # Reset alertas
        
        sensores = registro['sensores']
        
        # Alerta: Umidade crítica
        if sensores['umidade_solo'] < 20:
            self.alertas_ativos.append({
                'tipo': 'critico',
                'titulo': 'Umidade Crítica',
                'mensagem': f'Umidade do solo muito baixa: {sensores["umidade_solo"]:.1f}%',
                'timestamp': registro['timestamp']
            })
        
        # Alerta: pH fora da faixa ideal
        if sensores['ph_solo'] < 6.0 or sensores['ph_solo'] > 7.5:
            tipo_ph = 'ácido' if sensores['ph_solo'] < 6.0 else 'alcalino'
            self.alertas_ativos.append({
                'tipo': 'aviso',
                'titulo': f'pH {tipo_ph.title()}',
                'mensagem': f'pH do solo fora da faixa ideal: {sensores["ph_solo"]:.1f}',
                'timestamp': registro['timestamp']
            })
        
        # Alerta: NPK crítico
        npk = sensores['npk']
        for nutriente, valor in npk.items():
            if valor < 15:
                nome_nutriente = {'nitrogenio': 'Nitrogênio', 'fosforo': 'Fósforo', 'potassio': 'Potássio'}
                self.alertas_ativos.append({
                    'tipo': 'aviso',
                    'titulo': f'{nome_nutriente[nutriente]} Baixo',
                    'mensagem': f'{nome_nutriente[nutriente]} crítico: {valor:.1f} ppm',
                    'timestamp': registro['timestamp']
                })
        
        # Alerta: Temperatura extrema
        if sensores['temperatura'] > 35 or sensores['temperatura'] < 5:
            self.alertas_ativos.append({
                'tipo': 'critico',
                'titulo': 'Temperatura Extrema',
                'mensagem': f'Temperatura crítica para as plantas: {sensores["temperatura"]:.1f}°C',
                'timestamp': registro['timestamp']
            })
        
        # Alerta: Salinidade alta
        if sensores['salinidade'] > 2.0:
            self.alertas_ativos.append({
                'tipo': 'aviso',
                'titulo': 'Salinidade Alta',
                'mensagem': f'Salinidade do solo elevada: {sensores["salinidade"]:.1f} dS/m',
                'timestamp': registro['timestamp']
            })
    
    def obter_estatisticas(self):
        """Retorna as estatísticas calculadas"""
        return self.estatisticas_cache
    
    def obter_historico_grafico(self, horas=24):
        """Retorna dados formatados para gráficos"""
        agora = datetime.now()
        dados_periodo = [r for r in self.dados_historicos 
                        if (agora - r['timestamp']).total_seconds() <= (horas * 3600)]
        
        # Ordenar por timestamp para garantir ordem cronológica
        dados_periodo.sort(key=lambda x: x['timestamp'])
        
        return [{
            'timestamp': r['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp_grafico': r['timestamp'].strftime('%H:%M'),
            'umidade': round(r['sensores']['umidade_solo'], 1),
            'temperatura': round(r['sensores']['temperatura'], 1),
            'ph': round(r['sensores']['ph_solo'], 1),
            'irrigacao': r['irrigacao'].get('ativa', False) if isinstance(r['irrigacao'], dict) else bool(r['irrigacao'])
        } for r in dados_periodo]

# Instância global do sistema de histórico
historico_sistema = HistoricoSistema()

def carregar_dados_json(arquivo):
    """Carrega dados de um arquivo JSON"""
    try:
        caminho_arquivo = os.path.join(DATA_DIR, arquivo)
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar {arquivo}: {e}")
    return {}

def obter_dados_meteorologicos():
    """Simula dados meteorológicos com múltiplos cenários diversos que alternam automaticamente"""
    # Usar timestamp para alternar entre 6 cenários diferentes a cada 10 segundos
    tempo_atual = int(time.time())
    ciclo_cenario = (tempo_atual // 10) % 6  # Alterna entre 0-5 a cada 10 segundos
    
    # Definir cenários meteorológicos diversos
    cenarios = {
        0: {  # SOL FORTE E AR SECO
            'nome': 'Sol Forte e Ar Seco',
            'atual': {
                'cidade': 'Fazenda Simulada',
                'temperatura': round(random.uniform(35, 42), 1),
                'umidade': round(random.uniform(15, 30), 1),
                'pressao': round(random.uniform(1015, 1025), 1),
                'vento': round(random.uniform(8, 20), 1),
                'condicao': 'Sol forte',
                'precipitacao': 0.0,
                'visibilidade': round(random.uniform(12, 20), 1)
            },
            'recomendacao': {
                'irrigar': True,
                'chuva_prevista': False,
                'precipitacao_24h': 0,
                'motivo': 'Sol intenso e ar muito seco - Irrigação urgente necessária'
            }
        },
        1: {  # CHUVA MODERADA
            'nome': 'Chuva Moderada',
            'atual': {
                'cidade': 'Fazenda Simulada',
                'temperatura': round(random.uniform(18, 25), 1),
                'umidade': round(random.uniform(80, 95), 1),
                'pressao': round(random.uniform(995, 1005), 1),
                'vento': round(random.uniform(10, 25), 1),
                'condicao': 'Chuva moderada',
                'precipitacao': round(random.uniform(5, 15), 1),
                'visibilidade': round(random.uniform(3, 8), 1)
            },
            'recomendacao': {
                'irrigar': False,
                'chuva_prevista': True,
                'precipitacao_24h': round(random.uniform(15, 35), 1),
                'motivo': 'Chuva em andamento - Irrigação desnecessária'
            }
        },
        2: {  # TEMPESTADE
            'nome': 'Tempestade',
            'atual': {
                'cidade': 'Fazenda Simulada',
                'temperatura': round(random.uniform(16, 22), 1),
                'umidade': round(random.uniform(85, 98), 1),
                'pressao': round(random.uniform(985, 995), 1),
                'vento': round(random.uniform(35, 60), 1),
                'condicao': 'Tempestade',
                'precipitacao': round(random.uniform(20, 50), 1),
                'visibilidade': round(random.uniform(1, 4), 1)
            },
            'recomendacao': {
                'irrigar': False,
                'chuva_prevista': True,
                'precipitacao_24h': round(random.uniform(40, 80), 1),
                'motivo': 'Tempestade ativa - Sistema de irrigação suspenso por segurança'
            }
        },
        3: {  # CLIMA AMENO E ÚMIDO
            'nome': 'Clima Ameno e Úmido',
            'atual': {
                'cidade': 'Fazenda Simulada',
                'temperatura': round(random.uniform(20, 26), 1),
                'umidade': round(random.uniform(65, 80), 1),
                'pressao': round(random.uniform(1008, 1018), 1),
                'vento': round(random.uniform(5, 12), 1),
                'condicao': 'Nublado',
                'precipitacao': 0.0,
                'visibilidade': round(random.uniform(8, 12), 1)
            },
            'recomendacao': {
                'irrigar': False,
                'chuva_prevista': True,
                'precipitacao_24h': round(random.uniform(8, 20), 1),
                'motivo': 'Umidade adequada e chuva prevista - Irrigação não necessária'
            }
        },
        4: {  # GEADA/FRIO INTENSO
            'nome': 'Frio Intenso com Geada',
            'atual': {
                'cidade': 'Fazenda Simulada',
                'temperatura': round(random.uniform(-2, 5), 1),
                'umidade': round(random.uniform(70, 90), 1),
                'pressao': round(random.uniform(1020, 1030), 1),
                'vento': round(random.uniform(2, 8), 1),
                'condicao': 'Geada',
                'precipitacao': 0.0,
                'visibilidade': round(random.uniform(5, 10), 1)
            },
            'recomendacao': {
                'irrigar': False,
                'chuva_prevista': False,
                'precipitacao_24h': 0,
                'motivo': 'Temperatura muito baixa - Sistema suspenso para proteção das plantas'
            }
        },
        5: {  # VENTO FORTE E SECO
            'nome': 'Vento Forte e Seco',
            'atual': {
                'cidade': 'Fazenda Simulada',
                'temperatura': round(random.uniform(28, 35), 1),
                'umidade': round(random.uniform(25, 45), 1),
                'pressao': round(random.uniform(1012, 1022), 1),
                'vento': round(random.uniform(25, 45), 1),
                'condicao': 'Ventoso',
                'precipitacao': 0.0,
                'visibilidade': round(random.uniform(6, 12), 1)
            },
            'recomendacao': {
                'irrigar': True,
                'chuva_prevista': False,
                'precipitacao_24h': 0,
                'motivo': 'Vento forte resseca o solo - Irrigação recomendada com cuidado'
            }
        }
    }
    
    # Selecionar cenário atual
    cenario_atual = cenarios[ciclo_cenario]
    
    return {
        'atual': cenario_atual['atual'],
        'recomendacao': cenario_atual['recomendacao'],
        'cenario_info': {
            'nome': cenario_atual['nome'],
            'ciclo': ciclo_cenario,
            'proximo_em': 10 - (tempo_atual % 10)
        }
    }

def simular_dados_sensores():
    """Simula dados dos sensores com alternância entre SISTEMA ATIVO e INATIVO a cada 10 segundos"""
    global irrigacao_manual_ativa, timestamp_irrigacao_manual, ultima_irrigacao_timestamp
    
    # Verificar se a irrigação manual deve ser desativada (após 5 minutos)
    if irrigacao_manual_ativa and timestamp_irrigacao_manual:
        tempo_decorrido = datetime.now() - timestamp_irrigacao_manual
        if tempo_decorrido.total_seconds() > 300:  # 5 minutos
            irrigacao_manual_ativa = False
            timestamp_irrigacao_manual = None
    
    # Lógica de alternância: ATIVO/INATIVO a cada 10 segundos
    tempo_atual = int(time.time())
    ciclo_sistema = (tempo_atual // 10) % 2  # Alterna entre 0 (INATIVO) e 1 (ATIVO)
    sistema_ativo = ciclo_sistema == 1
    
    # Usar cenário meteorológico para variar os dados dos sensores
    ciclo_cenario = (tempo_atual // 10) % 6  # Mesmo ciclo da meteorologia
    
    # Obter dados meteorológicos para correlacionar parâmetros
    dados_meteorologicos = obter_dados_meteorologicos()
    condicoes_clima = dados_meteorologicos['atual']
    
    # Definir dados dos sensores baseados CIENTIFICAMENTE no cenário meteorológico
    cenarios_sensores = {
        0: {  # SOL FORTE E AR SECO - Estresse hídrico severo
            'umidade_solo': round(random.uniform(15, 30), 1),  # Solo muito seco por evapotranspiração
            'ph_solo': round(random.uniform(6.8, 7.4), 1),     # pH sobe com concentração de sais
            'npk': {
                'nitrogenio': False,  # Volatilização por calor
                'fosforo': False,     # Fixação em solo seco
                'potassio': False     # Concentração salina impede absorção
            },
            'irrigacao_ativa': True,
            'qualidade_solo': round(random.uniform(35, 50), 1),  # Qualidade crítica por estresse
            'temperatura': round(condicoes_clima['temperatura'] + random.uniform(5, 10), 1),  # Solo mais quente que ar
            'umidade_ar': round(condicoes_clima['umidade'], 1),
            'evapotranspiracao': round(random.uniform(8, 12), 1),  # Alta perda de água
            'salinidade': round(random.uniform(1.2, 2.0), 1)      # Concentração de sais
        },
        1: {  # CHUVA MODERADA - Condições de recuperação
            'umidade_solo': round(random.uniform(65, 80), 1),   # Solo bem hidratado
            'ph_solo': round(random.uniform(6.2, 6.8), 1),      # pH normaliza com diluição
            'npk': {
                'nitrogenio': True,   # Disponível com umidade adequada
                'fosforo': True,      # Mobilizado pela água
                'potassio': False     # Parcialmente lixiviado pela chuva
            },
            'irrigacao_ativa': False,
            'qualidade_solo': round(random.uniform(70, 85), 1),  # Boa qualidade com hidratação
            'temperatura': round(condicoes_clima['temperatura'] + random.uniform(0, 3), 1),  # Solo próximo ao ar
            'umidade_ar': round(condicoes_clima['umidade'], 1),
            'evapotranspiracao': round(random.uniform(3, 5), 1),   # Baixa perda
            'salinidade': round(random.uniform(0.3, 0.8), 1)       # Sais diluídos
        },
        2: {  # TEMPESTADE - Lixiviação severa
            'umidade_solo': round(random.uniform(90, 98), 1),   # Solo saturado/encharcado
            'ph_solo': round(random.uniform(5.8, 6.4), 1),      # pH baixa por lixiviação de bases
            'npk': {
                'nitrogenio': False,  # Lixiviado pela chuva intensa
                'fosforo': False,     # Carreado pela enxurrada
                'potassio': False     # Totalmente lixiviado
            },
            'irrigacao_ativa': False,
            'qualidade_solo': round(random.uniform(45, 65), 1),  # Qualidade comprometida por lixiviação
            'temperatura': round(condicoes_clima['temperatura'] - random.uniform(2, 5), 1),  # Solo resfriado
            'umidade_ar': round(condicoes_clima['umidade'], 1),
            'evapotranspiracao': round(random.uniform(0.5, 1.5), 1),  # Mínima por saturação
            'salinidade': round(random.uniform(0.1, 0.3), 1)          # Sais totalmente diluídos
        },
        3: {  # CLIMA AMENO E ÚMIDO - Condições ideais
            'umidade_solo': round(random.uniform(55, 70), 1),   # Umidade ótima para plantas
            'ph_solo': round(random.uniform(6.4, 7.0), 1),      # pH ideal para absorção
            'npk': {
                'nitrogenio': True,   # Disponível em condições ideais
                'fosforo': True,      # Bem mobilizado
                'potassio': True      # Adequadamente disponível
            },
            'irrigacao_ativa': False,
            'qualidade_solo': round(random.uniform(80, 95), 1),  # Excelente qualidade
            'temperatura': round(condicoes_clima['temperatura'] + random.uniform(1, 4), 1),  # Solo levemente mais quente
            'umidade_ar': round(condicoes_clima['umidade'], 1),
            'evapotranspiracao': round(random.uniform(4, 6), 1),   # Taxa ideal
            'salinidade': round(random.uniform(0.4, 0.7), 1)       # Salinidade adequada
        },
        4: {  # GEADA/FRIO INTENSO - Metabolismo reduzido
            'umidade_solo': round(random.uniform(60, 80), 1),   # Solo úmido mas congelado
            'ph_solo': round(random.uniform(6.0, 6.6), 1),      # pH estável no frio
            'npk': {
                'nitrogenio': False,  # Indisponível por baixa atividade microbiana
                'fosforo': False,     # Fixado pelo frio
                'potassio': False     # Absorção bloqueada pelo frio
            },
            'irrigacao_ativa': False,
            'qualidade_solo': round(random.uniform(30, 50), 1),  # Qualidade baixa por inatividade biológica
            'temperatura': round(condicoes_clima['temperatura'] + random.uniform(-1, 2), 1),  # Solo próximo ao ar frio
            'umidade_ar': round(condicoes_clima['umidade'], 1),
            'evapotranspiracao': round(random.uniform(0.2, 1.0), 1),  # Quase nula
            'salinidade': round(random.uniform(0.8, 1.5), 1)          # Concentração por baixa mobilidade
        },
        5: {  # VENTO FORTE E SECO - Desidratação acelerada
            'umidade_solo': round(random.uniform(25, 45), 1),   # Solo ressecando rapidamente
            'ph_solo': round(random.uniform(6.6, 7.2), 1),      # pH sobe com concentração
            'npk': {
                'nitrogenio': False,  # Perdido por volatilização
                'fosforo': True,      # Concentrado mas pouco móvel
                'potassio': False     # Carreado pelo vento (erosão)
            },
            'irrigacao_ativa': True,
            'qualidade_solo': round(random.uniform(40, 60), 1),  # Qualidade comprometida por erosão
            'temperatura': round(condicoes_clima['temperatura'] + random.uniform(3, 8), 1),  # Solo aquecido pelo vento
            'umidade_ar': round(condicoes_clima['umidade'], 1),
            'evapotranspiracao': round(random.uniform(7, 11), 1),  # Muito alta pelo vento
            'salinidade': round(random.uniform(1.0, 1.8), 1)       # Alta concentração salina
        }
    }
    
    # Selecionar cenário atual
    cenario = cenarios_sensores[ciclo_cenario]
    
    # Obter dados meteorológicos para verificar condições
    dados_meteorologicos = obter_dados_meteorologicos()
    recomendacao_meteorologica = dados_meteorologicos['recomendacao']
    
    # LÓGICA INTELIGENTE: Ajustar parâmetros baseado nas condições reais
    
    # 1. AJUSTE DINÂMICO DE UMIDADE DO SOLO baseado na irrigação e clima
    if cenario['irrigacao_ativa'] and sistema_ativo:
        # Sistema ativo: solo deve estar secando (necessita irrigação)
        if cenario['umidade_solo'] > 50:
            cenario['umidade_solo'] = round(random.uniform(25, 45), 1)
    elif recomendacao_meteorologica['chuva_prevista']:
        # Chuva prevista: solo deve estar úmido
        if cenario['umidade_solo'] < 60:
            cenario['umidade_solo'] = round(random.uniform(65, 85), 1)
    
    # 2. AJUSTE DINÂMICO DE NPK baseado nas condições meteorológicas
    # Lógica científica: NPK é afetado por temperatura, umidade e pH
    
    # Fator de disponibilidade baseado na temperatura do solo
    temp_solo = cenario['temperatura']
    if temp_solo < 10:  # Muito frio - baixa atividade microbiana
        fator_temp = 0.2
    elif temp_solo < 20:  # Frio - atividade reduzida
        fator_temp = 0.6
    elif temp_solo > 35:  # Muito quente - volatilização
        fator_temp = 0.4
    else:  # Temperatura ideal
        fator_temp = 1.0
    
    # Fator de disponibilidade baseado na umidade do solo
    umidade_solo = cenario['umidade_solo']
    if umidade_solo < 30:  # Solo seco - nutrientes concentrados mas imóveis
        fator_umidade = 0.3
    elif umidade_solo > 85:  # Solo encharcado - lixiviação
        fator_umidade = 0.5
    else:  # Umidade adequada
        fator_umidade = 1.0
    
    # Fator de disponibilidade baseado no pH
    ph_solo = cenario['ph_solo']
    if ph_solo < 6.0 or ph_solo > 7.5:  # pH inadequado
        fator_ph = 0.6
    else:  # pH ideal
        fator_ph = 1.0
    
    # Calcular disponibilidade final de cada nutriente
    disponibilidade_geral = fator_temp * fator_umidade * fator_ph
    
    # Aplicar lógica específica para cada nutriente
    # Nitrogênio: mais sensível à temperatura e umidade
    prob_n = disponibilidade_geral * 0.8
    if temp_solo > 30:  # Volatilização do nitrogênio
        prob_n *= 0.5
    if umidade_solo > 90:  # Lixiviação por excesso de água
        prob_n *= 0.3
    
    # Fósforo: mais sensível ao pH
    prob_p = disponibilidade_geral * 0.9
    if ph_solo < 6.0 or ph_solo > 7.0:  # Fixação em pH inadequado
        prob_p *= 0.4
    
    # Potássio: mais sensível à lixiviação
    prob_k = disponibilidade_geral * 0.7
    if umidade_solo > 80:  # Lixiviação por chuva
        prob_k *= 0.6
    if cenario.get('evapotranspiracao', 5) > 8:  # Perda por evapotranspiração alta
        prob_k *= 0.7
    
    # Atualizar NPK baseado nas probabilidades calculadas
    cenario['npk'] = {
        'nitrogenio': random.random() < prob_n,
        'fosforo': random.random() < prob_p,
        'potassio': random.random() < prob_k
    }
    
    # 3. AJUSTE DE QUALIDADE DO SOLO baseado em múltiplos fatores
    qualidade_base = cenario['qualidade_solo']
    
    # Penalizar por condições extremas
    if temp_solo < 5 or temp_solo > 40:
        qualidade_base *= 0.7
    if umidade_solo < 20 or umidade_solo > 95:
        qualidade_base *= 0.8
    if ph_solo < 5.5 or ph_solo > 8.0:
        qualidade_base *= 0.6
    
    # Bonificar por condições ideais
    npk_count = sum([cenario['npk']['nitrogenio'], cenario['npk']['fosforo'], cenario['npk']['potassio']])
    if npk_count >= 2:
        qualidade_base *= 1.1
    
    cenario['qualidade_solo'] = min(100, max(20, round(qualidade_base, 1)))
    
    # Aplicar lógica inteligente baseada nas condições meteorológicas
    if not irrigacao_manual_ativa:  # Se não há irrigação manual
        # Verificar se há chuva prevista ou condições que impedem irrigação
        if recomendacao_meteorologica['chuva_prevista'] or not recomendacao_meteorologica['irrigar']:
            # Se há chuva prevista ou meteorologia não recomenda irrigação, sistema deve estar INATIVO
            cenario['irrigacao_ativa'] = False
            cenario['status_sistema'] = 'SISTEMA INATIVO'
            # Ajustar umidade do solo para refletir condições adequadas (chuva aumenta umidade)
            if recomendacao_meteorologica['chuva_prevista']:
                cenario['umidade_solo'] = round(random.uniform(70, 90), 1)  # Solo úmido devido à chuva
            else:
                cenario['umidade_solo'] = round(random.uniform(60, 75), 1)  # Solo adequado
        else:
            # Se não há chuva e meteorologia recomenda irrigação, verificar necessidade real
            # Usar lógica baseada na umidade do solo atual
            if cenario['umidade_solo'] < 40:  # Solo realmente seco
                cenario['irrigacao_ativa'] = True
                cenario['status_sistema'] = 'SISTEMA ATIVO'
            elif cenario['umidade_solo'] > 70:  # Solo já adequado
                cenario['irrigacao_ativa'] = False
                cenario['status_sistema'] = 'SISTEMA INATIVO'
            else:
                # Usar lógica de alternância apenas quando há dúvida
                cenario['irrigacao_ativa'] = sistema_ativo
                if sistema_ativo:
                    cenario['status_sistema'] = 'SISTEMA ATIVO'
                    # Ajustar para condições que requerem irrigação
                    if cenario['umidade_solo'] > 60:
                        cenario['umidade_solo'] = round(random.uniform(30, 50), 1)
                else:
                    cenario['status_sistema'] = 'SISTEMA INATIVO'
                    # Ajustar para condições adequadas
                    if cenario['umidade_solo'] < 60:
                        cenario['umidade_solo'] = round(random.uniform(60, 85), 1)
    else:  # Se irrigação manual está ativa, força o status
        cenario['irrigacao_ativa'] = True
        cenario['status_sistema'] = 'SISTEMA ATIVO (MANUAL)'
    
    # Atualizar timestamp da última irrigação quando o sistema está ativo
    # Só atualizar se não havia irrigação antes ou se passou muito tempo
    if cenario['irrigacao_ativa'] and not ultima_irrigacao_timestamp:
        # Primeira vez que a irrigação é ativada
        ultima_irrigacao_timestamp = datetime.now()
    
    # Adicionar timestamp da última irrigação aos dados do cenário
    if ultima_irrigacao_timestamp:
        tempo_decorrido = datetime.now() - ultima_irrigacao_timestamp
        if tempo_decorrido.total_seconds() < 60:
            cenario['ultima_irrigacao'] = 'Agora'
        elif tempo_decorrido.total_seconds() < 3600:  # Menos de 1 hora
            minutos = int(tempo_decorrido.total_seconds() // 60)
            cenario['ultima_irrigacao'] = f'Há {minutos} min'
        else:  # Mais de 1 hora
            horas = int(tempo_decorrido.total_seconds() // 3600)
            minutos = int((tempo_decorrido.total_seconds() % 3600) // 60)
            if minutos > 0:
                cenario['ultima_irrigacao'] = f'Há {horas}h {minutos}min'
            else:
                cenario['ultima_irrigacao'] = f'Há {horas}h'
    else:
        cenario['ultima_irrigacao'] = 'Nunca'
    
    cenario['timestamp'] = datetime.now().isoformat()
    cenario['ciclo_atual'] = f'CENÁRIO {ciclo_cenario} - {cenario["status_sistema"]}'
    
    # Adicionar informações de contexto científico para justificativa
    cenario['contexto_cientifico'] = {
        'fator_temperatura': round(fator_temp, 2),
        'fator_umidade': round(fator_umidade, 2), 
        'fator_ph': round(fator_ph, 2),
        'disponibilidade_npk': round(disponibilidade_geral, 2),
        'evapotranspiracao_atual': cenario.get('evapotranspiracao', 5),
        'salinidade_atual': cenario.get('salinidade', 0.5)
    }
    
    # Obter dados meteorológicos para integração
    dados_meteorologicos = obter_dados_meteorologicos()
    
    # Converter NPK booleano para valores numéricos
    npk_valores = {
        'nitrogenio': random.uniform(40, 80) if cenario['npk']['nitrogenio'] else random.uniform(10, 35),
        'fosforo': random.uniform(35, 70) if cenario['npk']['fosforo'] else random.uniform(5, 30),
        'potassio': random.uniform(40, 75) if cenario['npk']['potassio'] else random.uniform(10, 35)
    }
    
    # Preparar recomendação de irrigação
    recomendacao_irrigacao = {
        'irrigar': cenario['irrigacao_ativa'],
        'motivo': f"Sistema {cenario['status_sistema']} - Cenário {ciclo_cenario}",
        'confiabilidade': 'ALTA' if disponibilidade_geral > 0.7 else 'MEDIA' if disponibilidade_geral > 0.4 else 'BAIXA'
    }
    
    # Integrar dados no sistema de histórico
    dados_sensores_completos = {
        'umidade_solo': cenario['umidade_solo'],
        'ph_solo': cenario['ph_solo'],
        'temperatura': cenario['temperatura'],
        'umidade_ar': cenario['umidade_ar'],
        'nitrogenio': npk_valores['nitrogenio'],
        'fosforo': npk_valores['fosforo'],
        'potassio': npk_valores['potassio'],
        'qualidade_solo': cenario['qualidade_solo'],
        'salinidade': cenario['salinidade'],
        'evapotranspiracao': cenario['evapotranspiracao']
    }
    
    # Adicionar registro ao histórico
    historico_sistema.adicionar_registro(
        dados_sensores_completos,
        dados_meteorologicos['atual'],
        recomendacao_irrigacao
    )
    
    return cenario

def executar_script_python(nome_script):
    """
    Executa um script Python e retorna informações detalhadas sobre a execução
    
    Args:
        nome_script (str): Nome do script Python a ser executado
        
    Returns:
        dict: Informações sobre a execução incluindo sucesso, saída, erros, etc.
    """
    script_path = os.path.join(PYTHON_DIR, nome_script)
    
    if not os.path.exists(script_path):
        return {
            'sucesso': False,
            'codigo_saida': -1,
            'stdout': '',
            'stderr': f'Script {nome_script} não encontrado',
            'timestamp': datetime.now().isoformat()
        }
    
    try:
        resultado = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            'sucesso': resultado.returncode == 0,
            'codigo_saida': resultado.returncode,
            'stdout': resultado.stdout,
            'stderr': resultado.stderr,
            'timestamp': datetime.now().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        return {
            'sucesso': False,
            'codigo_saida': -2,
            'stdout': '',
            'stderr': 'Script excedeu tempo limite de 30 segundos',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'sucesso': False,
            'codigo_saida': -3,
            'stdout': '',
            'stderr': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.route('/')
def index():
    """Página principal do dashboard"""
    return render_template('index.html')

@app.route('/api/dados')
def api_dados():
    """API principal que retorna todos os dados do sistema com justificativas técnicas"""
    try:
        # Carregar dados existentes (ajustado para web/data)
        dados_clima = carregar_dados_json('clima_resultado.json')
        dados_analise = carregar_dados_json('analise_resultado.json')
        dados_meteorologicos = obter_dados_meteorologicos()
        dados_sensores = simular_dados_sensores()
        
        # Gerar justificativa técnica se o módulo estiver disponível
        justificativa_tecnica = None
        if justificador_disponivel:
            try:
                justificador = JustificativaIrrigacao()
                justificativa_tecnica = justificador.gerar_justificativa_completa(
                    dados_sensores, 
                    dados_meteorologicos, 
                    dados_analise
                )
                
                # Se irrigação manual está ativa, sobrescrever a justificativa
                if irrigacao_manual_ativa:
                    justificativa_tecnica['justificativa']['titulo'] = 'Sistema em modo manual'
                    justificativa_tecnica['justificativa']['resumo'] = 'Irrigação ativada manualmente pelo usuário'
                    justificativa_tecnica['decisao']['acao'] = 'ATIVAR'
                    justificativa_tecnica['decisao']['motivo_principal'] = 'Ativação manual'
                    justificativa_tecnica['decisao']['prioridade'] = 'ALTA'
                    
            except Exception as e:
                print(f"Erro ao gerar justificativa: {e}")
                # Criar justificativa padrão em caso de erro
                justificativa_tecnica = {
                    'decisao': {
                        'acao': 'AGUARDAR',
                        'motivo_principal': 'Erro na análise técnica',
                        'prioridade': 'MÉDIA'
                    },
                    'justificativa': {
                        'titulo': 'Análise técnica indisponível',
                        'resumo': 'Sistema em modo de segurança devido a erro na análise',
                        'razoes_principais': ['Erro no processamento dos dados dos sensores'],
                        'razoes_secundarias': [],
                        'alertas': ['Sistema operando em modo de segurança']
                    },
                    'parametros_analisados': ['Erro na análise'],
                    'recomendacoes_adicionais': ['Verificar configuração do sistema'],
                    'timestamp': datetime.now().isoformat(),
                    'confiabilidade': 0.0
                }
        
        # Se não há justificador disponível, criar justificativa básica
        if justificativa_tecnica is None:
            if irrigacao_manual_ativa:
                justificativa_tecnica = {
                    'decisao': {
                        'acao': 'ATIVAR',
                        'motivo_principal': 'Irrigação ativada manualmente pelo usuário',
                        'prioridade': 'ALTA'
                    },
                    'justificativa': {
                        'titulo': 'Sistema em modo manual',
                        'resumo': 'O sistema foi ativado manualmente e permanecerá ativo independente das condições dos sensores.',
                        'razoes_principais': ['Ativação manual pelo usuário'],
                        'razoes_secundarias': [],
                        'alertas': []
                    },
                    'parametros_analisados': ['Comando manual'],
                    'recomendacoes_adicionais': ['Sistema operando conforme solicitação manual'],
                    'timestamp': timestamp_irrigacao_manual.isoformat() if timestamp_irrigacao_manual else datetime.now().isoformat(),
                    'confiabilidade': 1.0
                }
            else:
                # Criar justificativa básica baseada nos dados dos sensores
                umidade_solo = dados_sensores.get('umidade_solo', 50)
                irrigacao_ativa = dados_sensores.get('irrigacao_ativa', False)
                
                if irrigacao_ativa:
                    acao = 'ATIVAR'
                    titulo = 'Sistema ativo'
                    resumo = 'Sistema de irrigação em funcionamento'
                elif umidade_solo < 40:
                    acao = 'ATIVAR'
                    titulo = 'Irrigação necessária'
                    resumo = f'Umidade do solo baixa ({umidade_solo}%)'
                else:
                    acao = 'AGUARDAR'
                    titulo = 'Condições adequadas'
                    resumo = f'Umidade do solo adequada ({umidade_solo}%)'
                
                justificativa_tecnica = {
                    'decisao': {
                        'acao': acao,
                        'motivo_principal': resumo,
                        'prioridade': 'MÉDIA'
                    },
                    'justificativa': {
                        'titulo': titulo,
                        'resumo': resumo,
                        'razoes_principais': [f'Umidade do solo: {umidade_solo}%'],
                        'razoes_secundarias': [],
                        'alertas': []
                    },
                    'parametros_analisados': ['Umidade do solo', 'Status da irrigação'],
                    'recomendacoes_adicionais': ['Monitoramento contínuo dos sensores'],
                    'timestamp': datetime.now().isoformat(),
                    'confiabilidade': 0.7
                }
        
        resposta = {
            'sucesso': True,
            'dados': {
                'clima': dados_clima,
                'analise': dados_analise,
                'meteorologia': dados_meteorologicos,
                'sensores': dados_sensores,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Adicionar justificativa sempre (agora sempre existe)
        resposta['dados']['justificativa_tecnica'] = justificativa_tecnica
        
        return jsonify(resposta)
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 500

@app.route('/api/sensores')
def api_sensores():
    """API específica para dados dos sensores de irrigação"""
    try:
        dados_sensores = simular_dados_sensores()
        dados_meteorologicos = obter_dados_meteorologicos()
        
        return jsonify({
            'sucesso': True,
            'sensores': dados_sensores,
            'meteorologia': dados_meteorologicos,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 500

@app.route('/api/meteorologia')
def api_meteorologia():
    """API específica para dados meteorológicos"""
    try:
        dados = obter_dados_meteorologicos()
        if dados:
            return jsonify({
                'sucesso': True,
                'meteorologia': dados
            })
        else:
            return jsonify({
                'sucesso': False,
                'erro': 'Dados meteorológicos não disponíveis'
            }), 404
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 500

@app.route('/api/atualizar')
def api_atualizar():
    """API para executar scripts de atualização de dados"""
    try:
        # Executa script de clima
        resultado_clima = executar_script_python('clima.py')
        
        # Executa script de análise
        resultado_analise = executar_script_python('analise.py')
        
        # Executa script meteorológico (simulador se API não disponível)
        resultado_meteorologia = executar_script_python('weather_simulator.py')
        
        return jsonify({
            'sucesso': True,
            'resultados': {
                'clima': resultado_clima,
                'analise': resultado_analise,
                'meteorologia': resultado_meteorologia
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/irrigacao/manual', methods=['POST'])
def api_irrigacao_manual():
    """API para controle manual da irrigação"""
    global irrigacao_manual_ativa, timestamp_irrigacao_manual, ultima_irrigacao_timestamp
    
    try:
        # Ativar irrigação manual
        irrigacao_manual_ativa = True
        timestamp_irrigacao_manual = datetime.now()
        ultima_irrigacao_timestamp = datetime.now()  # Atualizar também o timestamp geral
        
        # Simula comando para ESP32
        comando = "IRRIGACAO:MANUAL"
        
        return jsonify({
            'sucesso': True,
            'comando': comando,
            'mensagem': 'Comando de irrigação manual enviado',
            'timestamp': timestamp_irrigacao_manual.isoformat(),
            'irrigacao_ativa': True
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 500

@app.route('/api/historico')
def api_historico():
    """API para dados históricos do sistema"""
    return jsonify(historico_sistema.obter_historico_grafico())

@app.route('/api/estatisticas')
def api_estatisticas():
    """API para estatísticas detalhadas do sistema"""
    return jsonify(historico_sistema.obter_estatisticas())

@app.route('/api/alertas')
def api_alertas():
    """API para alertas ativos do sistema"""
    return jsonify({
        'alertas': historico_sistema.alertas_ativos,
        'total': len(historico_sistema.alertas_ativos),
        'ultima_verificacao': historico_sistema.ultima_atualizacao.isoformat() if historico_sistema.ultima_atualizacao else None
    })

@app.route('/wokwi')
def wokwi():
    """Página do simulador Wokwi"""
    return render_template('wokwi.html')

if __name__ == '__main__':
    print("🌱 Iniciando FarmTech Dashboard...")
    print("📊 Acesse: http://localhost:5000")
    print("🔧 Simulador: http://localhost:5000/wokwi")
    
    app.run(debug=True, host='0.0.0.0', port=5000)