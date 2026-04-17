import time
import random
import requests

# --- CONFIGURAÇÕES ---
API_URL_INTERACT = "http://localhost:8000/api/sensor/interact"
API_URL_CHAT = "http://localhost:8000/api/ai/chat"
API_KEY = "flexmedia-sprint3-secure-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Variáveis ricas para simular a Visão Computacional exigida na Sprint 4
AGE_GROUPS = ["child", "teen", "adult", "senior"]
LANGUAGES = ["pt-BR", "en-US", "es-ES"]
INTERACTION_TYPES = ["TOUCH_SCREEN", "VOICE_COMMAND", "GESTURE", "QR_CODE_SCAN"]

# Perguntas simuladas para a IA do Totem
QUESTIONS = [
    "Onde fica o leão?",
    "Onde tem banheiro?",
    "Estou com fome, onde posso comer?",
    "Qual o animal mais rápido daqui?"
]

def simulate_totem():
    print("🚀 [SIMULADOR AVANÇADO SPRINT 4] Iniciando Visão Computacional e Sensores...")
    print("Pressione Ctrl+C para parar.\n")

    try:
        visitor_count = 100
        while True:
            # 1. Simulação de Visão Computacional (Detecção de Perfil)
            user_id = f"Visitor_{visitor_count}"
            age = random.choice(AGE_GROUPS)
            lang = random.choice(LANGUAGES)
            
            print(f"👁️ [VISÃO COMPUTACIONAL] Visitante detectado: {user_id} | Perfil: {age}, {lang}")

            # 2. Simulação de Interação com o Totem
            interaction = random.choice(INTERACTION_TYPES)
            duration = round(random.uniform(5.0, 120.0), 2)
            success = random.choice([True, True, True, False]) # 75% de chance de sucesso geral

            payload_interact = {
                "user_id_anon": user_id,
                "age_group": age,
                "preferred_language": lang,
                "totem_id": 1,
                "interaction_type": interaction,
                "duration_seconds": duration,
                "success": success
            }

            # Injetando dados ricos no nosso backend seguro
            response = requests.post(API_URL_INTERACT, json=payload_interact, headers=HEADERS)
            if response.status_code == 200:
                print(f"📡 [SENSOR] Dados salvos no BD: {interaction} ({duration}s) - Sucesso: {success}")
            else:
                print(f"❌ [ERRO] Falha ao enviar dados: {response.text}")

            # 3. Simulação de Conversa com IA (Aleatoriamente, alguns visitantes fazem perguntas)
            if random.random() > 0.6:
                pergunta = random.choice(QUESTIONS)
                print(f"🗣️ [USUÁRIO] Perguntou: '{pergunta}'")
                
                payload_chat = {
                    "user_id_anon": user_id,
                    "message": pergunta
                }
                chat_response = requests.post(API_URL_CHAT, json=payload_chat, headers=HEADERS)
                
                if chat_response.status_code == 200:
                    resposta_ia = chat_response.json().get("ai_response")
                    print(f"🤖 [IA FLEXMEDIA] Respondeu: '{resposta_ia}'")

            print("-" * 50)
            visitor_count += 1
            time.sleep(random.uniform(3, 6)) # Aguarda alguns segundos antes do próximo visitante

    except KeyboardInterrupt:
        print("\n🛑 Simulador interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro de conexão com a API: {e}. O main.py está rodando?")

if __name__ == "__main__":
    simulate_totem()