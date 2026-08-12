import json
import logging
import asyncio
import redis
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback local em memória caso Redis esteja indisponível em dev local sem Docker
_in_memory_session_store: Dict[str, Any] = {}
_in_memory_buffers: Dict[int, list] = {}
_in_memory_tasks: Dict[int, asyncio.Task] = {}

def get_redis_client():
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis indisponível em {settings.REDIS_URL}. Utilizando fallback em memória. Erro: {e}")
        return None

# ----------------------------------------------------
# 1. Gerenciamento de Session State (Operacional / Volátil)
# ----------------------------------------------------

def get_session_state(chat_id: int) -> Dict[str, Any]:
    r = get_redis_client()
    if r:
        try:
            data = r.get(f"session:{chat_id}")
            return json.loads(data) if data else {}
        except Exception as e:
            logger.error(f"Erro ao buscar sessão no Redis: {e}")
    return _in_memory_session_store.get(str(chat_id), {})

def update_session_state(chat_id: int, state_dict: Dict[str, Any], ttl_seconds: int = 86400):
    r = get_redis_client()
    if r:
        try:
            r.setex(f"session:{chat_id}", ttl_seconds, json.dumps(state_dict, ensure_ascii=False))
            return
        except Exception as e:
            logger.error(f"Erro ao salvar sessão no Redis: {e}")
    _in_memory_session_store[str(chat_id)] = state_dict

def clear_session_state(chat_id: int):
    r = get_redis_client()
    if r:
        try:
            r.delete(f"session:{chat_id}")
        except Exception as e:
            logger.error(f"Erro ao limpar sessão no Redis: {e}")
    _in_memory_session_store.pop(str(chat_id), None)

# ----------------------------------------------------
# 2. Buffer Debounce de 15 Segundos para Mensagens Picadas
# (Atualização 01 - updates_agent_1.0.md)
# ----------------------------------------------------

async def handle_message_debounce(chat_id: int, text: str, callback_coro, debounce_seconds: int = 15):
    """
    Acumula mensagens enviadas dentro de uma janela de `debounce_seconds` (15s).
    Quando o temporizador expira sem novas mensagens, chama a corrotina callback_coro com a string concatenada.
    """
    if chat_id not in _in_memory_buffers:
        _in_memory_buffers[chat_id] = []
    
    _in_memory_buffers[chat_id].append(text)

    # Se já existir uma tarefa agendada para este chat, cancela para reiniciar a contagem de 15s
    if chat_id in _in_memory_tasks and not _in_memory_tasks[chat_id].done():
        _in_memory_tasks[chat_id].cancel()

    async def _wait_and_flush():
        try:
            await asyncio.sleep(debounce_seconds)
            # Concatenar todas as mensagens acumuladas
            full_text = " ".join(_in_memory_buffers.get(chat_id, []))
            _in_memory_buffers[chat_id] = []
            if full_text.strip():
                await callback_coro(chat_id, full_text.strip())
        except asyncio.CancelledError:
            pass # Task foi cancelada para reiniciar o debounce
        finally:
            _in_memory_tasks.pop(chat_id, None)

    task = asyncio.create_task(_wait_and_flush())
    _in_memory_tasks[chat_id] = task
