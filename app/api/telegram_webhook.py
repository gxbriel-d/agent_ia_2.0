import logging
from fastapi import APIRouter, Request, BackgroundTasks
from app.core.config import settings
from app.core.redis import handle_message_debounce, get_session_state, update_session_state
from app.api.telegram_formatter import send_telegram_messages_in_blocks
from agents.graph import build_agent_graph

logger = logging.getLogger(__name__)
router = APIRouter()

# Instância compilada do Grafo LangGraph
agent_graph = build_agent_graph()

async def process_concatenated_messages(chat_id: int, full_text: str):
    """
    Callback disparado após a janela de 15 segundos sem novas mensagens.
    Envia a frase concatenada para o LangGraph e responde no Telegram em blocos.
    """
    logger.info(f"[DEBOUNCE 15s EXPIRED] Processando mensagem para chat_id {chat_id}: '{full_text}'")
    
    # 1. Carregar estado da sessão volátil no Redis
    session = get_session_state(chat_id)
    history = session.get("messages", [])
    history.append({"role": "user", "content": full_text})
    
    initial_state = {
        "chat_id": chat_id,
        "user_name": session.get("user_name", "Cliente Telegram"),
        "messages": history,
        "tipo_produto": session.get("tipo_produto"),
        "largura_mm": session.get("largura_mm"),
        "altura_mm": session.get("altura_mm"),
        "tipo_vidro": session.get("tipo_vidro"),
        "espessura_mm": session.get("espessura_mm"),
        "cor_vidro": session.get("cor_vidro"),
        "cor_aluminio": session.get("cor_aluminio"),
        "quote_result": None,
        "rag_result": None,
        "calendar_result": None,
        "next_node": ""
    }
    
    # 2. Executar LangGraph
    final_state = agent_graph.invoke(initial_state)
    
    # 3. Atualizar estado volátil no Redis
    update_session_state(chat_id, {
        "user_name": final_state.get("user_name"),
        "messages": final_state.get("messages", [])[-10:], # Manter últimas 10 mensagens
        "tipo_produto": final_state.get("tipo_produto"),
        "largura_mm": final_state.get("largura_mm"),
        "altura_mm": final_state.get("altura_mm"),
        "tipo_vidro": final_state.get("tipo_vidro"),
        "espessura_mm": final_state.get("espessura_mm"),
        "cor_vidro": final_state.get("cor_vidro"),
        "cor_aluminio": final_state.get("cor_aluminio")
    })
    
    # 4. Pegar a última resposta do assistente e enviar no Telegram em blocos
    last_assistant_msg = final_state["messages"][-1].get("content", "")
    await send_telegram_messages_in_blocks(settings.TELEGRAM_BOT_TOKEN, chat_id, last_assistant_msg)

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint de Webhook do Telegram.
    Aplica o buffer debounce de 15 segundos para mensagens picadas.
    """
    try:
        data = await request.json()
        if "message" not in data or "text" not in data["message"]:
            return {"status": "ignored"}
        
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        user_name = data["message"]["from"].get("first_name", "Cliente")
        
        # Salvar o nome do usuário no Redis se não existir
        session = get_session_state(chat_id)
        if not session.get("user_name"):
            session["user_name"] = user_name
            update_session_state(chat_id, session)
            
        # Acionar buffer debounce de 15s
        background_tasks.add_task(
            handle_message_debounce, 
            chat_id, 
            text, 
            process_concatenated_messages, 
            settings.DEBOUNCE_SECONDS
        )
        
        return {"status": "buffered", "debounce_seconds": settings.DEBOUNCE_SECONDS}
    except Exception as e:
        logger.error(f"Erro ao processar webhook do Telegram: {e}")
        return {"status": "error", "message": str(e)}
