import zoneinfo
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict

def get_brasilia_current_time_str() -> str:
    """
    Retorna a ancoragem temporal dinâmica no fuso America/Sao_Paulo (Brasília).
    Exemplo: '22/08/2026 (Sábado), 21:45'
    """
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    now = datetime.now(tz)
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_str = dias_semana[now.weekday()]
    return f"{now.strftime('%d/%m/%Y')} ({dia_str}), {now.strftime('%H:%M')}"

class AgentState(TypedDict):
    chat_id: int
    user_name: str
    messages: List[Dict[str, str]]
    timestamp_brasilia: str
    
    # Especificações da Encomenda de Confeitaria
    categoria: Optional[str]        # docinho_13g, docinho_20g, pirulito, bolo_simples, bolo_andar
    tipo_sabor: Optional[str]       # tradicional, nobre
    quantidade: Optional[int]
    tamanho_cm: Optional[int]
    fatias: Optional[int]
    sabores_selecionados: Optional[List[str]]
    com_topper: Optional[bool]
    
    # Orçamento Estruturado Retornado pelo Quote Service
    quote_result: Optional[Dict[str, Any]]
    
    # Resposta RAG
    rag_result: Optional[List[Dict[str, Any]]]
    
    # Resposta Calendar
    calendar_result: Optional[Dict[str, Any]]
    
    # Próxima ação recomendada
    next_node: str
