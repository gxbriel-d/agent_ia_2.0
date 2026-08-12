import zoneinfo
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict

def get_brasilia_current_time_str() -> str:
    """
    Retorna a ancoragem temporal dinâmica no fuso America/Sao_Paulo (Brasília).
    Exemplo: '12/08/2026 (Quarta-feira), 02:05'
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
    
    # Especificações do Vão em Coleta
    tipo_produto: Optional[str] # box, janela, porta, espelho
    largura_mm: Optional[float]
    altura_mm: Optional[float]
    tipo_vidro: Optional[str]   # temperado, laminado, comum
    espessura_mm: Optional[int] # 8, 10
    cor_vidro: Optional[str]    # incolor, fume, verde, bronze
    cor_aluminio: Optional[str] # branco, preto, fosco
    
    # Orçamento Estruturado Retornado pelo Quote Service
    quote_result: Optional[Dict[str, Any]]
    
    # Resposta RAG
    rag_result: Optional[List[Dict[str, Any]]]
    
    # Resposta Calendar
    calendar_result: Optional[Dict[str, Any]]
    
    # Próxima ação recomendada
    next_node: str
