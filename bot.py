import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
import logging
import httpx
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env local
load_dotenv()

from app.core.config import settings
from app.core.redis import handle_message_debounce, get_session_state, update_session_state, clear_session_state
from app.api.telegram_formatter import send_telegram_messages_in_blocks
from agents.graph import build_agent_graph
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bot_polling")

# Instância compilada do Grafo LangGraph (Cantinho Doce da Gabi)
agent_graph = build_agent_graph()

async def process_concatenated_messages(chat_id: int, full_text: str):
    """
    Callback disparado após o buffer de 3 segundos sem novas mensagens.
    Processa a frase no LangGraph e responde no Telegram.
    """
    logger.info(f"[POLLING 3s EXPIRED] Processando mensagem para chat_id {chat_id}: '{full_text}'")
    try:
        session = get_session_state(chat_id)
        history = session.get("messages", [])
        history.append({"role": "user", "content": full_text})
        
        initial_state = {
            "chat_id": chat_id,
            "user_name": session.get("user_name", "Cliente"),
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
        
        # Executar LangGraph da Confeitaria Cantinho Doce da Gabi
        final_state = agent_graph.invoke(initial_state)
        
        # Sincronizar estado no Redis
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
        logger.error(f"Erro ao processar mensagem no Polling: {e}", exc_info=True)
        fallback_msg = "Olá! Seja bem-vindo ao Cantinho Doce da Gabi! 🍰✨ Recebi seu pedido e nossa consultora já está verificando as delícias da sua encomenda!"
        await send_telegram_messages_in_blocks(settings.TELEGRAM_BOT_TOKEN, chat_id, fallback_msg)

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recebe mensagens do Telegram via Polling e repassa ao Buffer Debounce.
    """
    if not update.message or not update.message.text:
        return
    
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    user_name = update.message.from_user.first_name if update.message.from_user else "Cliente"
    
    # Comandos de limpeza de memória (/reset, /start, /limpar)
    if text.lower() in ["/reset", "/limpar", "/start"]:
        clear_session_state(chat_id)
        reset_msg = f"🔄 Olá, {user_name}! Seja muito bem-vindo ao **Cantinho Doce da Gabi**! 🍰✨ A memória da nossa conversa foi zerada. Como posso ajudar com os seus docinhos e bolos hoje?"
        await send_telegram_messages_in_blocks(settings.TELEGRAM_BOT_TOKEN, chat_id, reset_msg)
        return
        
    session = get_session_state(chat_id)
    if not session.get("user_name"):
        session["user_name"] = user_name
        update_session_state(chat_id, session)
        
    # Acionar buffer debounce
    asyncio.create_task(
        handle_message_debounce(
            chat_id, 
            text, 
            process_concatenated_messages, 
            settings.DEBOUNCE_SECONDS
        )
    )

def remove_webhook_if_exists(token: str):
    """
    Remove qualquer Webhook ativo do Telegram para garantir o funcionamento por Polling local.
    """
    if not token:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        res = httpx.get(url, timeout=5.0)
        logger.info(f"Removendo Webhook para modo Polling local: {res.text}")
    except Exception as e:
        logger.warning(f"Não foi possível deletar Webhook antigo: {e}")

def main():
    token = settings.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("ERRO: TELEGRAM_BOT_TOKEN não encontrado no arquivo .env!")
        sys.exit(1)
        
    print("\n====================================================")
    print("🚀 INICIANDO AGENTE CANTINHO DOCE DA GABI (LOCAL POLLING)")
    print("====================================================\n")
    
    # Garantir que Webhook seja deletado para o Polling funcionar 100%
    remove_webhook_if_exists(token)
    
    app = ApplicationBuilder().token(token).build()
    
    # Handlers para mensagens e comandos
    app.add_handler(CommandHandler(["start", "reset", "limpar"], handle_telegram_message))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_telegram_message))
    
    logger.info("Bot rodando via Polling no Terminal! Pressione Ctrl+C para encerrar.")
    app.run_polling()

if __name__ == "__main__":
    main()
