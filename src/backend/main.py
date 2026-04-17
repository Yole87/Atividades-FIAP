from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uvicorn
import random

# Importação relativa da nossa base normalizada
from .database import get_db_connection, init_db

# --- CONFIGURAÇÃO DA API ---
app = FastAPI(
    title="API Totem Inteligente FlexMedia - Sprint 4",
    description="Backend com rotas de ingestão normalizada e processamento de IA.",
    version="2.0.0"
)

# --- CYBERSECURITY ---
SECRET_API_KEY = "flexmedia-sprint3-secure-key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def check_api_key(api_key: str = Security(api_key_header)):
    if api_key != SECRET_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso Negado: Chave de API inválida ou ausente.",
        )
    return api_key

# --- MODELOS DE DADOS (Pydantic atualizado para o novo BD) ---
class InteractionPayload(BaseModel):
    user_id_anon: str
    age_group: Optional[str] = "adult"
    preferred_language: Optional[str] = "pt-BR"
    totem_id: int = 1
    interaction_type: str
    duration_seconds: float
    success: bool

class ChatPayload(BaseModel):
    user_id_anon: str
    message: str

# --- EVENTOS ---
@app.on_event("startup")
def on_startup():
    """Garante que o banco inicie ao rodar a API."""
    init_db()

# --- ROTAS DE INGESTÃO (SENSORES) ---
@app.post("/api/sensor/interact", dependencies=[Depends(check_api_key)])
def register_interaction(payload: InteractionPayload):
    """Rota protegida: Salva dados nas tabelas normalizadas (Visitors e Interactions)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Salva ou atualiza o perfil do visitante
        cursor.execute('''
            INSERT OR IGNORE INTO visitors (user_id_anon, age_group, preferred_language)
            VALUES (?, ?, ?)
        ''', (payload.user_id_anon, payload.age_group, payload.preferred_language))
        
        # 2. Salva a interação interligada ao totem e ao visitante
        cursor.execute('''
            INSERT INTO interactions (timestamp, totem_id, user_id_anon, interaction_type, duration_seconds, success)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, payload.totem_id, payload.user_id_anon, payload.interaction_type, payload.duration_seconds, payload.success))
        
        conn.commit()
        conn.close()
        
        return {"status": "sucesso", "mensagem": "Dados normalizados e salvos."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no BD: {str(e)}")

# --- ROTAS DE INTELIGÊNCIA ARTIFICIAL (SPRINT 4) ---
@app.post("/api/ai/chat", dependencies=[Depends(check_api_key)])
def ai_interaction(payload: ChatPayload):
    """
    Rota de IA: Recebe uma pergunta do visitante e retorna uma resposta inteligente.
    Simula um LLM (como Gemini ou ChatGPT) gerando fluxos de diálogo focados no Zoo.
    """
    pergunta = payload.message.lower()
    
    # Lógica simples de NLP (Processamento de Linguagem Natural) baseada em palavras-chave
    if "leão" in pergunta or "felino" in pergunta:
        resposta = "Os leões do nosso zoológico são da espécie Panthera leo. Eles dormem cerca de 20 horas por dia! Gostaria de saber onde fica o recinto deles?"
    elif "banheiro" in pergunta or "onde" in pergunta:
        resposta = "O banheiro mais próximo está a 50 metros à sua direita, logo após o recinto dos primatas."
    elif "comer" in pergunta or "fome" in pergunta:
        resposta = "Temos uma praça de alimentação com opções variadas a 3 minutos de caminhada daqui. Deseja que eu exiba o mapa no totem?"
    else:
        respostas_genericas = [
            "Que pergunta interessante! Sabia que a preservação ambiental é o principal foco do nosso espaço?",
            "Não tenho certeza sobre isso, mas posso te mostrar o nosso mapa interativo se desejar explorar mais!",
            "Como sou um Totem em fase de aprendizado, vou registrar sua dúvida. Gostaria de ouvir curiosidades sobre os animais próximos?"
        ]
        resposta = random.choice(respostas_genericas)
        
    return {
        "status": "sucesso",
        "visitor": payload.user_id_anon,
        "ai_response": resposta,
        "action": "display_text_and_audio"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)