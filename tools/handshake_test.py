import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
import logging
from services.quote_service import QuoteService
from services.rag_knowledge import RAGKnowledgeService
from services.google_calendar import GoogleCalendarService
from agents.graph import build_agent_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("handshake_test")

def main():
    print("=== EXECUTANDO TESTE DE HANDSHAKE DO SISTEMA (V.L.A.E.G.) ===")
    
    # 1. Testar Quote Service
    print("\n1. Testando Quote Service (Determinístico)...")
    quote_res = QuoteService.generate_quote({
        "tipo_produto": "box",
        "largura_mm": 1200,
        "altura_mm": 1900,
        "tipo_vidro": "temperado",
        "espessura_mm": 8,
        "cor_vidro": "incolor"
    })
    print(f"   [OK] Quote ID: {quote_res['quote_id']} | Total: R$ {quote_res['total']:.2f} | Items: {len(quote_res['items'])}")
    
    # 2. Testar RAG Knowledge
    print("\n2. Testando RAG Knowledge Service (Semântico)...")
    rag_res = RAGKnowledgeService.search_technical_knowledge("diferença vidro temperado e laminado")
    print(f"   [OK] Artigos encontrados: {len(rag_res)} | Título: {rag_res[0]['titulo']}")
    
    # 3. Testar Google Calendar
    print("\n3. Testando Google Calendar Service (CRUD)...")
    cal_res = GoogleCalendarService.agendar_visita_tecnica(
        summary="Teste Handshake Medição",
        description="Teste de integridade do sistema",
        start_iso="2026-08-15T14:00:00-03:00",
        end_iso="2026-08-15T15:00:00-03:00"
    )
    print(f"   [OK] Evento: {cal_res['event_id']} | Status: {cal_res['status']}")
    
    # 4. Testar LangGraph
    print("\n4. Testando Grafo do LangGraph...")
    graph = build_agent_graph()
    state = {
        "chat_id": 99999,
        "user_name": "Cliente Teste",
        "messages": [{"role": "user", "content": "Queria um orçamento para box de 1.20 x 1.90"}],
        "timestamp_brasilia": "12/08/2026 (Quarta-feira), 02:05",
        "tipo_produto": None,
        "largura_mm": None,
        "altura_mm": None,
        "tipo_vidro": None,
        "espessura_mm": None,
        "cor_vidro": None,
        "cor_aluminio": None,
        "quote_result": None,
        "rag_result": None,
        "calendar_result": None,
        "next_node": ""
    }
    final_state = graph.invoke(state)
    print(f"   [OK] Resposta Gerada: {final_state['messages'][-1]['content'][:100]}...")
    
    print("\n=== TODOS OS TESTES DE HANDSHAKE FORAM CONCLUÍDOS COM SUCESSO! ===")

if __name__ == "__main__":
    main()
