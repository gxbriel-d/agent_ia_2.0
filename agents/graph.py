import json
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from agents.state import AgentState, get_brasilia_current_time_str
from services.quote_service import QuoteService
from services.rag_knowledge import RAGKnowledgeService
from services.google_calendar import GoogleCalendarService
from app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# Prompt do Consultor de Orçamentos de Vidraçaria
SYSTEM_PROMPT = """Você é o Consultor Técnico de Orçamentos Profissionais da Vidraçaria & Esquadrias.
Seu objetivo é conduzir um atendimento prestativo, profissional e eficiente, desde o primeiro contato até o orçamento oficial e agendamento da visita técnica.

REGRAS INVIOLÁVEIS:
1. NUNCA realize cálculos financeiros, multiplicações de m² ou precificação por conta própria.
2. Quando o cliente fornecer o tipo de vão (box, janela, porta, espelho) e as medidas (largura e altura em mm ou metros), acione o Quote Service determinístico.
3. Não invente preços, ferragens ou descontos. Apresente os dados exatos fornecidos pelo Quote Service.
4. Para dúvidas técnicas conceituais sobre vidros (ex: temperado vs laminado), utilize as informações da base técnica (RAG).
5. Mantenha um tom profissional, cordialmente técnico e focado no fechamento de vendas.

Data e hora atual de Brasília: {timestamp_brasilia}
"""

def node_process_intent(state: AgentState) -> AgentState:
    """
    Analisa a mensagem recebida e extrai especificações do vão ou identifica a intenção.
    """
    state["timestamp_brasilia"] = get_brasilia_current_time_str()
    messages = state.get("messages", [])
    if not messages:
        state["next_node"] = END
        return state
    
    last_user_msg = messages[-1].get("content", "")
    
    # Heurística simples de extração / intenção para demonstração
    text_lower = last_user_msg.lower()
    
    if any(k in text_lower for k in ["orcamento", "orçamento", "box", "janela", "porta", "espelho", "preço", "quanto custa"]):
        # Tentar extrair medidas padrão se mencionadas
        if "box" in text_lower or state.get("tipo_produto") is None:
            state["tipo_produto"] = "box"
        if not state.get("largura_mm"):
            state["largura_mm"] = 1200.0
        if not state.get("altura_mm"):
            state["altura_mm"] = 1900.0
        if not state.get("tipo_vidro"):
            state["tipo_vidro"] = "temperado"
        if not state.get("espessura_mm"):
            state["espessura_mm"] = 8
        if not state.get("cor_vidro"):
            state["cor_vidro"] = "incolor"
            
        state["next_node"] = "node_quote"
    elif any(k in text_lower for k in ["agendar", "visita", "medição", "medicao", "horario"]):
        state["next_node"] = "node_calendar"
    elif any(k in text_lower for k in ["diferenca", "diferença", "laminado", "norma", "limpeza", "garantia"]):
        state["next_node"] = "node_rag"
    else:
        state["next_node"] = "node_llm_chat"
        
    return state

def node_execute_quote(state: AgentState) -> AgentState:
    """
    Nó determinístico que executa o Quote Service sem interferência do LLM.
    """
    params = {
        "telegram_chat_id": state.get("chat_id", 0),
        "tipo_produto": state.get("tipo_produto", "box"),
        "largura_mm": state.get("largura_mm", 1200),
        "altura_mm": state.get("altura_mm", 1900),
        "tipo_vidro": state.get("tipo_vidro", "temperado"),
        "espessura_mm": state.get("espessura_mm", 8),
        "cor_vidro": state.get("cor_vidro", "incolor"),
        "cor_aluminio": state.get("cor_aluminio", "branco")
    }
    quote_json = QuoteService.generate_quote(params)
    state["quote_result"] = quote_json
    state["next_node"] = "node_llm_chat"
    return state

def node_execute_rag(state: AgentState) -> AgentState:
    """
    Nó que realiza busca no RAG PGVector.
    """
    last_msg = state["messages"][-1].get("content", "")
    rag_docs = RAGKnowledgeService.search_technical_knowledge(last_msg)
    state["rag_result"] = rag_docs
    state["next_node"] = "node_llm_chat"
    return state

def node_execute_calendar(state: AgentState) -> AgentState:
    """
    Nó que realiza o agendamento de visita técnica no Google Calendar.
    """
    vagas = GoogleCalendarService.verificar_disponibilidade("2026-08-15")
    res = GoogleCalendarService.agendar_visita_tecnica(
        summary=f"Medição Técnica - Cliente {state.get('user_name', 'Telegram')}",
        description="Medição técnica presencial de vão para orçamento de vidraçaria.",
        start_iso="2026-08-15T14:00:00-03:00",
        end_iso="2026-08-15T15:00:00-03:00"
    )
    state["calendar_result"] = res
    state["next_node"] = "node_llm_chat"
    return state

def node_llm_chat(state: AgentState) -> AgentState:
    """
    Sintetiza a resposta final ao cliente utilizando OpenAI gpt-4o-mini com base no resultado determinístico.
    """
    quote_res = state.get("quote_result")
    rag_res = state.get("rag_result")
    cal_res = state.get("calendar_result")
    
    context_addon = ""
    if quote_res:
        context_addon += f"\n\n📐 RESULTADO OFICIAL DO QUOTE SERVICE:\n{json.dumps(quote_res, ensure_ascii=False, indent=2)}"
    if rag_res:
        context_addon += f"\n\n📚 INFORMACÕES TÉCNICAS RAG:\n{json.dumps(rag_res, ensure_ascii=False, indent=2)}"
    if cal_res:
        context_addon += f"\n\n📅 AGENDAMENTO GOOGLE CALENDAR:\n{json.dumps(cal_res, ensure_ascii=False, indent=2)}"
        
    prompt = SYSTEM_PROMPT.format(timestamp_brasilia=state.get("timestamp_brasilia", "")) + context_addon
    
    if settings.OPENAI_API_KEY:
        try:
            llm = ChatOpenAI(model_name=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.3)
            system_msg = SystemMessage(content=prompt)
            human_msgs = [HumanMessage(content=m.get("content", "")) for m in state.get("messages", [])[-3:]]
            response = llm.invoke([system_msg] + human_msgs)
            reply_text = response.content
        except Exception as e:
            logger.error(f"Erro ao chamar OpenAI: {e}")
            reply_text = _format_fallback_response(quote_res, cal_res)
    else:
        reply_text = _format_fallback_response(quote_res, cal_res)
        
    state["messages"].append({"role": "assistant", "content": reply_text})
    return state

def _format_fallback_response(quote_res: Optional[Dict], cal_res: Optional[Dict]) -> str:
    if quote_res:
        items_summary = "\n".join([f"- {it['descricao']}: R$ {it['valor_total']:.2f}" for it in quote_res.get('items', [])])
        return (
            f"Olá! Aqui está a sua Proposta Comercial Oficial:\n\n"
            f"📐 **Orçamento #{quote_res.get('quote_id')}**\n"
            f"Área Faturada: {quote_res.get('area_m2_faturada')} m²\n\n"
            f"**Composição:**\n{items_summary}\n\n"
            f"💰 **Subtotal:** R$ {quote_res.get('subtotal'):.2f}\n"
            f"🏷️ **Desconto:** R$ {quote_res.get('discount'):.2f}\n"
            f"💵 **VALOR TOTAL FINAL:** R$ {quote_res.get('total'):.2f}\n\n"
            f"Deseja agendar uma medição técnica gratuita no local?"
        )
    if cal_res:
        return f"📅 **Visita Técnica Confirmada!**\n{cal_res.get('mensagem')}\nCompromisso salvo no Google Agenda."
    return "Olá! Sou o consultor de orçamentos de vidraçaria. Como posso ajudar com o seu projeto de box, janela, porta ou espelho hoje?"

def build_agent_graph():
    """
    Monta e compila o grafo de estados do LangGraph.
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("process_intent", node_process_intent)
    workflow.add_node("node_quote", node_execute_quote)
    workflow.add_node("node_rag", node_execute_rag)
    workflow.add_node("node_calendar", node_execute_calendar)
    workflow.add_node("node_llm_chat", node_llm_chat)
    
    workflow.set_entry_point("process_intent")
    
    workflow.add_conditional_edges(
        "process_intent",
        lambda x: x.get("next_node", "node_llm_chat"),
        {
            "node_quote": "node_quote",
            "node_rag": "node_rag",
            "node_calendar": "node_calendar",
            "node_llm_chat": "node_llm_chat",
            END: END
        }
    )
    
    workflow.add_edge("node_quote", "node_llm_chat")
    workflow.add_edge("node_rag", "node_llm_chat")
    workflow.add_edge("node_calendar", "node_llm_chat")
    workflow.add_edge("node_llm_chat", END)
    
    return workflow.compile()
