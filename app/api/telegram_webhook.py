import logging
from fastapi import APIRouter, Request, BackgroundTasks
from app.core.config import settings
from app.core.redis import handle_message_debounce, get_session_state, update_session_state, clear_session_state
from app.api.telegram_formatter import send_telegram_messages_in_blocks
from agents.graph import build_agent_graph

logger = logging.getLogger(__name__)
router = APIRouter()

agent_graph = build_agent_graph()

async def process_concatenated_messages(chat_id: int, full_text: str):
    logger.info(f"[DEBOUNCE 3s EXPIRED] Processando mensagem para chat_id {chat_id}: '{full_text}'")
    try:
        session = get_session_state(chat_id)
        history = session.get("messages", [])
        history.append({"role": "user", "content": full_text})
        
        initial_state = {
            "chat_id": chat_id,
            "user_name": session.get("user_name", "Cliente Telegram"),
            "messages": history,
            "categoria": session.get("categoria"),
            "tipo_sabor": session.get("tipo_sabor"),
            "quantidade": session.get("quantidade"),
            "tamanho_cm": session.get("tamanho_cm"),
            "fatias": session.get("fatias"),
            "sabores_selecionados": session.get("sabores_selecionados"),
            "com_topper": session.get("com_topper"),
            "quote_result": None,
            "rag_result": None,
            "calendar_result": None,
            "next_node": ""
        }
        
        final_state = agent_graph.invoke(initial_state)
        
        update_session_state(chat_id, {
            "user_name": final_state.get("user_name"),
            "messages": final_state.get("messages", [])[-10:],
            "categoria": final_state.get("categoria"),
            "tipo_sabor": final_state.get("tipo_sabor"),
            "quantidade": final_state.get("quantidade"),
            "tamanho_cm": final_state.get("tamanho_cm"),
            "fatias": final_state.get("fatias"),
            "sabores_selecionados": final_state.get("sabores_selecionados"),
            "com_topper": final_state.get("com_topper")
        })
        
        last_assistant_msg = final_state["messages"][-1].get("content", "")
        await send_telegram_messages_in_blocks(settings.TELEGRAM_BOT_TOKEN, chat_id, last_assistant_msg)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem concatenada: {e}", exc_info=True)
        fallback_msg = "Olá! Seja muito bem-vindo ao **Cantinho Doce da Gabi**! 🍰✨ Recebi sua mensagem e nossa consultora já está verificando o seu pedido."
        await send_telegram_messages_in_blocks(settings.TELEGRAM_BOT_TOKEN, chat_id, fallback_msg)

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if "message" not in data or "text" not in data["message"]:
            return {"status": "ignored"}
        
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].strip()
        user_name = data["message"]["from"].get("first_name", "Cliente")
        
        if text.lower() in ["/reset", "/limpar", "/start"]:
            clear_session_state(chat_id)
            reset_msg = f"🔄 Olá, {user_name}! A memória da nossa conversa foi zerada. Como posso ajudar você com os docinhos e bolos da confeitaria hoje?"
            background_tasks.add_task(send_telegram_messages_in_blocks, settings.TELEGRAM_BOT_TOKEN, chat_id, reset_msg)
            return {"status": "session_reset"}
        
        session = get_session_state(chat_id)
        if not session.get("user_name"):
            session["user_name"] = user_name
            update_session_state(chat_id, session)
            
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
