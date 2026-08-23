import json
import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from agents.state import AgentState, get_brasilia_current_time_str
from services.quote_service import QuoteService
from services.rag_knowledge import RAGKnowledgeService
from services.google_calendar import GoogleCalendarService
from app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

import os

def load_prompt(name: str) -> str:
    """Carrega o prompt markdown correspondente da pasta prompts/"""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{name}.md")
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Não foi possível ler {prompt_path}: {e}")
    return ""

SYSTEM_PROMPT = """Você é a Consultora de Atendimento e Encomendas da confeitaria **Cantinho Doce da Gabi**! 🍰✨
Sua missão é atender os clientes com carinho, doçura e profissionalismo, tirando dúvidas sobre nossos docinhos, pirulitos e bolos decorados/andar, montando os orçamentos oficiais e agendando a retirada ou entrega do pedido.

REGRAS INVIOLÁVEIS:
1. NUNCA faça cálculos de preços, valores de doces ou combos por conta própria.
2. Quando o cliente solicitar um orçamento de docinhos, pirulitos ou bolos, acione o Quote Service determinístico.
3. Apresente exatamente a proposta comercial gerada pelo Quote Service sem inventar valores ou adicionais.
4. Para dúvidas técnicas sobre localização, consulte nossa base RAG e informe nosso link do Google Meu Negócio: https://share.google/W4JSgihofaVoJEzVi
5. Lembre os clientes das nossas regras carinhosas:
   - Docinhos 13g: pedido mínimo de 50 unids (mínimo 25 por sabor).
   - Pirulitos: mínimo de 12 unids.
   - Forminhas de flor (20g): trazer as forminhas até 2 dias antes da festa.
   - Bolos de andar: acompanham blindagem de chocolate no bolo inferior para segurança no transporte.

Data e hora atual de Brasília: {timestamp_brasilia}
"""

def node_process_intent(state: AgentState) -> AgentState:
    """
    Analisa a mensagem recebida e identifica a intenção do cliente na confeitaria.
    """
    state["timestamp_brasilia"] = get_brasilia_current_time_str()
    messages = state.get("messages", [])
    if not messages:
        state["next_node"] = END
        return state
    
    last_user_msg = messages[-1].get("content", "")
    text_lower = last_user_msg.lower()
    
    # Intenções de Cotação de Confeitaria
    if any(k in text_lower for k in ["docinho", "doce", "brigadeiro", "ninho", "beijinho", "cajuzinho", "churros", "nutella"]):
        state["categoria"] = "docinho_13g"
        if "ninho c/ nutella" in text_lower or "churros" in text_lower or "nobre" in text_lower:
            state["tipo_sabor"] = "nobre"
        else:
            state["tipo_sabor"] = "tradicional"
        if not state.get("quantidade"):
            state["quantidade"] = 50
        state["next_node"] = "node_quote"

    elif any(k in text_lower for k in ["bolo", "fatia", "andar", "chantilly"]):
        if "andar" in text_lower:
            state["categoria"] = "bolo_andar"
            state["fatias"] = 40
        else:
            state["categoria"] = "bolo_simples"
            state["fatias"] = 15
        state["next_node"] = "node_quote"

    elif any(k in text_lower for k in ["pirulito", "chocolate"]):
        state["categoria"] = "pirulito"
        state["quantidade"] = 12
        state["next_node"] = "node_quote"

    elif any(k in text_lower for k in ["agendar", "retirada", "entrega", "festa", "data"]):
        state["next_node"] = "node_calendar"

    elif any(k in text_lower for k in ["onde fica", "endereço", "endereco", "localização", "localizacao", "google", "blindagem", "flor"]):
        state["next_node"] = "node_rag"

    else:
        state["next_node"] = "node_llm_chat"
        
    return state

def node_execute_quote(state: AgentState) -> AgentState:
    """
    Nó determinístico que executa o Confectionery Quote Service sem interferência do LLM.
    """
    params = {
        "telegram_chat_id": state.get("chat_id", 0),
        "categoria": state.get("categoria", "docinho_13g"),
        "tipo_sabor": state.get("tipo_sabor", "tradicional"),
        "quantidade": state.get("quantidade", 50),
        "tamanho_cm": state.get("tamanho_cm", 15),
        "fatias": state.get("fatias", 15),
        "sabores_selecionados": state.get("sabores_selecionados", ["Brigadeiro", "Ninho"]),
        "com_topper": state.get("com_topper", False)
    }
    quote_json = QuoteService.generate_quote(params)
    state["quote_result"] = quote_json
    state["next_node"] = "node_llm_chat"
    return state

def node_execute_rag(state: AgentState) -> AgentState:
    """
    Nó que realiza busca de informações do Cantinho Doce da Gabi no RAG PGVector.
    """
    last_msg = state["messages"][-1].get("content", "")
    rag_docs = RAGKnowledgeService.search_technical_knowledge(last_msg)
    state["rag_result"] = rag_docs
    state["next_node"] = "node_llm_chat"
    return state

def node_execute_calendar(state: AgentState) -> AgentState:
    """
    Nó que realiza o agendamento de data de retirada ou entrega do pedido.
    """
    vagas = GoogleCalendarService.verificar_disponibilidade("2026-08-25")
    res = GoogleCalendarService.agendar_visita_tecnica(
        summary=f"Retirada de Encomenda - Cliente {state.get('user_name', 'Telegram')}",
        description="Retirada/entrega de encomenda do Cantinho Doce da Gabi.",
        start_iso="2026-08-25T14:00:00-03:00",
        end_iso="2026-08-25T15:00:00-03:00"
    )
    state["calendar_result"] = res
    state["next_node"] = "node_llm_chat"
    return state

def node_llm_chat(state: AgentState) -> AgentState:
    """
    Sintetiza a resposta final carismática da confeitaria utilizando OpenAI gpt-4o-mini.
    """
    quote_res = state.get("quote_result")
    rag_res = state.get("rag_result")
    cal_res = state.get("calendar_result")
    
    context_addon = ""
    if quote_res:
        context_addon += f"\n\n📐 ORÇAMENTO OFICIAL DO CANTINHO DOCE DA GABI:\n{json.dumps(quote_res, ensure_ascii=False, indent=2)}"
    if rag_res:
        context_addon += f"\n\n📚 INFORMAÇÕES DA CONFEITARIA RAG:\n{json.dumps(rag_res, ensure_ascii=False, indent=2)}"
    if cal_res:
        context_addon += f"\n\n📅 AGENDAMENTO DE RETIRADA:\n{json.dumps(cal_res, ensure_ascii=False, indent=2)}"
        
    prompt = SYSTEM_PROMPT.format(timestamp_brasilia=state.get("timestamp_brasilia", "")) + context_addon
    
    if settings.OPENAI_API_KEY:
        try:
            llm = ChatOpenAI(model_name=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.4)
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
            f"Olá! Seja muito bem-vindo ao **Cantinho Doce da Gabi**! 🍰✨\n\n"
            f"🍰 **Proposta Comercial #{quote_res.get('quote_id')}**\n\n"
            f"**Itens da Encomenda:**\n{items_summary}\n\n"
            f"💰 **Subtotal:** R$ {quote_res.get('subtotal'):.2f}\n"
            f"🏷️ **Desconto Especial:** R$ {quote_res.get('discount'):.2f}\n"
            f"💵 **VALOR TOTAL FINAL:** R$ {quote_res.get('total'):.2f}\n\n"
            f"Gostaria de agendar a data de retirada da sua encomenda conosco?"
        )
    if cal_res:
        return f"📅 **Retirada de Encomenda Agendada!**\n{cal_res.get('mensagem')}\nSua data está reservada no Cantinho Doce da Gabi!"
    return "Olá! Seja muito bem-vindo ao **Cantinho Doce da Gabi**! 🍰✨ Como posso ajudar você hoje com docinhos festivos, pirulitos ou bolos decorados?"

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
