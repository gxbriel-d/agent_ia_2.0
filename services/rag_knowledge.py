import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Base de Conhecimento Semântica do Cantinho Doce da Gabi
_FALLBACK_KNOWLEDGE = [
    {
        "titulo": "Localização e Google Meu Negócio - Cantinho Doce da Gabi",
        "conteudo": "A confeitaria Cantinho Doce da Gabi é especializada em docinhos tradicionais e nobres, pirulitos de chocolate e bolos decorados/andar. Acesse nossa localização oficial no Google Meu Negócio: https://share.google/W4JSgihofaVoJEzVi"
    },
    {
        "titulo": "Regra para Docinhos de 20g em Forminhas de Flor",
        "conteudo": "Para docinhos maiores de 20g servidos em forminhas de flor ou estilo lembrancinha (Tradicionais R$ 2,30 / Nobres R$ 2,60), as forminhas não acompanham o produto. É necessário que o cliente entregue as forminhas ou lembrancinhas em nosso atelier com até 2 dias de antecedência da data da festa."
    },
    {
        "titulo": "Blindagem de Chocolate em Bolos de Andar Verdadeiro",
        "conteudo": "Todos os nossos bolos de andar verdadeiro (40, 55 ou 65 fatias) acompanham blindagem de chocolate blend ou meio amargo no bolo inferior. Isso garante máxima estruturação, firmeza e segurança durante o transporte até a sua festa."
    },
    {
        "titulo": "Especificações dos Bolos em Chantilly",
        "conteudo": "Nossos bolos decorados acompanham tábua branca de MDF de 3mm, 3 discos de massa e 2 camadas de recheios tradicionais, com altura entre 10cm a 12cm. Topo de bolo (topper), flores, frutas e cores fortes são calculados como adicionais conforme o tema."
    }
]

class RAGKnowledgeService:
    @staticmethod
    def search_technical_knowledge(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Realiza busca semântica no PGVector para dúvidas conceituais, localização e regras do Cantinho Doce da Gabi.
        NUNCA retorna preços ou valores financeiros.
        """
        try:
            from app.db.neon import execute_query
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
            logger.warning(f"PGVector não disponível no Neon. Utilizando conhecimento padrão da confeitaria: {e}")

        query_lower = query.lower()
        results = []
        for item in _FALLBACK_KNOWLEDGE:
            if any(w in item["conteudo"].lower() or w in item["titulo"].lower() for w in query_lower.split()):
                results.append(item)
        
        return results if results else _FALLBACK_KNOWLEDGE[:2]
