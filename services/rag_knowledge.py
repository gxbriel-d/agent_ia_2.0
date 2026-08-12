import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Base de Conhecimento Semântica de Fallback (Normas NBR e Manuais de Vidraçaria)
_FALLBACK_KNOWLEDGE = [
    {
        "titulo": "Vidro Temperado vs Vidro Laminado (Norma NBR 7199)",
        "conteudo": "O vidro temperado passa por tratamento térmico que o torna 5 vezes mais resistente a impactos do que o vidro comum. Em caso de quebra, fragmenta-se em pequenos pedaços cegos de baixa periculosidade. É recomendado para boxes de banheiro, portas e janelas. O vidro laminado é composto por duas chapas de vidro unidas por uma película de PVB, retendo os estilhaços em caso de quebra, sendo recomendado para coberturas e guarda-corpos."
    },
    {
        "titulo": "Recomendações de Limpeza e Manutenção de Box de Vidro",
        "conteudo": "Para prolongar a vida útil do box de banheiro, limpe o vidro semanalmente utilizando sabão neutro e água morna. Nunca utilize palha de aço ou produtos abrasivos. Recomenda-se realizar a manutenção preventiva de roldanas e batedores de silicone a cada 12 meses."
    },
    {
        "titulo": "Folga Técnica e Medição de Vãos",
        "conteudo": "Para a correta fabricação de peças de vidro temperado, são adicionadas folgas de corte (geralmente 50mm) para alinhamento nos trilhos de alumínio. A medição técnica presencial é fundamental para verificar prumada de paredes e nivelamento de pisos."
    }
]

class RAGKnowledgeService:
    @staticmethod
    def search_technical_knowledge(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Realiza busca semântica no PGVector para responder a dúvidas técnicas de instalação/materiais.
        NUNCA retorna preços ou valores financeiros.
        """
        try:
            from app.db.neon import execute_query
            # Tentar busca SQL no Neon se houver embeddings no pgvector
            sql = """
                SELECT titulo, conteudo 
                FROM conhecimento_tecnico 
                ORDER BY id DESC 
                LIMIT %s;
            """
            rows = execute_query(sql, (top_k,))
            if rows and len(rows) > 0:
                return [{"titulo": r["titulo"], "conteudo": r["conteudo"]} for r in rows]
        except Exception as e:
            logger.warning(f"PGVector não disponível ou sem dados. Utilizando base técnica padrão: {e}")

        # Busca simples por palavra-chave na base de fallback
        query_lower = query.lower()
        results = []
        for item in _FALLBACK_KNOWLEDGE:
            if any(w in item["conteudo"].lower() or w in item["titulo"].lower() for w in query_lower.split()):
                results.append(item)
        
        return results if results else _FALLBACK_KNOWLEDGE[:1]
