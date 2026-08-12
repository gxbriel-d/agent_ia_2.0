import re
import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)

def dividir_em_blocos_naturais(texto: str) -> List[str]:
    """
    Divide textos longos em parágrafos coerentes para simular digitação humana.
    Preserva cards estruturados com emoji 📐 sem quebrá-los ao meio.
    (Atualização 03 - updates_agent_1.0.md)
    """
    if not texto:
        return []
    
    # Se houver um card de proposta comercial '📐', isolá-lo em um bloco próprio
    if "📐" in texto:
        partes = re.split(r'(📐[\s\S]*?(?=\n\n|\Z))', texto)
        blocos = [p.strip() for p in partes if p.strip()]
        return blocos
    
    # Caso contrário, dividir por quebras duplas de linha ou parágrafos
    paragrafos = [p.strip() for p in texto.split('\n\n') if p.strip()]
    return paragrafos if paragrafos else [texto]

async def send_telegram_messages_in_blocks(bot_token: str, chat_id: int, full_text: str):
    """
    Envia as mensagens para o cliente no Telegram em blocos naturais com pausas de digitação.
    (Atualizações 02 e 03 - updates_agent_1.0.md)
    """
    if not bot_token:
        logger.info(f"[DEV CONSOLE CHAT {chat_id}]:\n{full_text}")
        return

    import httpx
    url_send_message = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    url_send_action = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
    
    blocos = dividir_em_blocos_naturais(full_text)
    
    async with httpx.AsyncClient() as client:
        for i, bloco in enumerate(blocos):
            # 1. Enviar indicador TYPING ("digitando...")
            try:
                await client.post(url_send_action, json={"chat_id": chat_id, "action": "typing"}, timeout=5.0)
            except Exception as e:
                logger.warning(f"Não foi possível enviar typing action: {e}")
            
            # 2. Pausa assíncrona ágil (0.5s a 1.0s)
            delay = min(1.0, max(0.5, len(bloco) * 0.005))
            await asyncio.sleep(delay)
            
            # 3. Enviar bloco de mensagem via HTTP POST com fallback resiliente
            try:
                res = await client.post(url_send_message, json={
                    "chat_id": chat_id,
                    "text": bloco,
                    "parse_mode": "Markdown"
                }, timeout=10.0)
                
                # Se o Telegram rejeitar o Markdown (HTTP status != 200 ou ok == false), tentar texto puro
                if res.status_code != 200 or not res.json().get("ok"):
                    logger.warning(f"Telegram rejeitou Markdown: {res.text}. Tentando envio em texto simples...")
                    await client.post(url_send_message, json={
                        "chat_id": chat_id,
                        "text": bloco
                    }, timeout=10.0)
            except Exception as e:
                logger.error(f"Erro ao enviar bloco de mensagem no Telegram: {e}")
