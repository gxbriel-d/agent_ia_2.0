import uuid
import json
import logging
from typing import Dict, Any, List
try:
    from app.db.neon import execute_query, execute_write
except Exception:
    try:
        import sys, os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from app.db.neon import execute_query, execute_write
    except Exception:
        execute_query = None
        execute_write = None

logger = logging.getLogger(__name__)

class QuoteService:
    @staticmethod
    def generate_quote(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a matemática determinística de orçamento para a Confeitaria Cantinho Doce da Gabi.
        """
        raw_uuid = str(uuid.uuid4())
        quote_id = f"GABI-{raw_uuid[:8].upper()}"
        categoria = params.get("categoria", "docinho_13g").lower()
        tipo_sabor = params.get("tipo_sabor", "tradicional").lower()
        quantidade = int(params.get("quantidade", 50))
        tamanho_cm = int(params.get("tamanho_cm", 15))
        fatias = int(params.get("fatias", 15))
        sabores = params.get("sabores_selecionados", ["Brigadeiro", "Ninho"])
        com_topper = bool(params.get("com_topper", False))
        
        items = []
        subtotal = 0.0
        
        # 1. DOCINHOS 13G (FESTIVOS)
        if categoria in ["docinho_13g", "docinho"]:
            # Pedido mínimo de 50 unidades
            qtd_efetiva = max(50, quantidade)
            unit_price = 1.70 if tipo_sabor == "nobre" else 1.50
            total_doces = round(qtd_efetiva * unit_price, 2)
            subtotal += total_doces
            
            items.append({
                "categoria": "docinho",
                "descricao": f"Docinhos Festivos 13g ({tipo_sabor.title()}) - {', '.join(sabores)}",
                "quantidade": qtd_efetiva,
                "unidade": "unid",
                "valor_unitario": unit_price,
                "valor_total": total_doces
            })
            
            if com_topper:
                val_topper = round(qtd_efetiva * 0.40, 2)
                subtotal += val_topper
                items.append({
                    "categoria": "adicional",
                    "descricao": "Topper Personalizado para Docinhos",
                    "quantidade": qtd_efetiva,
                    "unidade": "unid",
                    "valor_unitario": 0.40,
                    "valor_total": val_topper
                })

        # 2. DOCINHOS 20G (LEMBRANCINHA / FLORES)
        elif categoria in ["docinho_20g", "lembrancinha"]:
            unit_price = 2.60 if tipo_sabor == "nobre" else 2.30
            total_doces = round(quantidade * unit_price, 2)
            subtotal += total_doces
            
            items.append({
                "categoria": "docinho_lembrancinha",
                "descricao": f"Docinhos Especiais 20g para Forminha de Flor ({tipo_sabor.title()})",
                "quantidade": quantidade,
                "unidade": "unid",
                "valor_unitario": unit_price,
                "valor_total": total_doces
            })

        # 3. PIRULITOS DE CHOCOLATE
        elif categoria in ["pirulito", "pirulitos"]:
            qtd_efetiva = max(12, quantidade) # Mínimo de 12 unidades
            unit_price = 6.00
            total_pirulitos = round(qtd_efetiva * unit_price, 2)
            subtotal += total_pirulitos
            
            items.append({
                "categoria": "pirulito",
                "descricao": "Pirulito de Chocolate Decorado (Mínimo 12 unids)",
                "quantidade": qtd_efetiva,
                "unidade": "unid",
                "valor_unitario": unit_price,
                "valor_total": total_pirulitos
            })

        # 4. BOLO SIMPLES / DECORADO CHANTILLY
        elif categoria in ["bolo_simples", "bolo"]:
            if fatias >= 40 or tamanho_cm >= 25:
                preco_bolo = 310.00
                tam_label = "25cm (~40 fatias)"
            elif fatias >= 25 or tamanho_cm >= 20:
                preco_bolo = 220.00
                tam_label = "20cm (~25 fatias)"
            else:
                preco_bolo = 150.00
                tam_label = "15cm (~15 fatias)"
                
            subtotal += preco_bolo
            items.append({
                "categoria": "bolo",
                "descricao": f"Bolo Decorado em Chantilly ({tam_label}) - 2 Recheios Tradicionais + Tábua MDF",
                "quantidade": 1.0,
                "unidade": "unid",
                "valor_unitario": preco_bolo,
                "valor_total": preco_bolo
            })

        # 5. BOLO DE ANDAR VERDADEIRO
        elif categoria in ["bolo_andar", "andar"]:
            if fatias >= 65:
                preco_bolo = 595.00
                tam_label = "65 fatias (Aros 25cm + 20cm)"
            elif fatias >= 55:
                preco_bolo = 495.00
                tam_label = "55 fatias (Aros 25cm + 15cm)"
            else:
                preco_bolo = 395.00
                tam_label = "40 fatias (Aros 20cm + 15cm)"
                
            subtotal += preco_bolo
            items.append({
                "categoria": "bolo_andar",
                "descricao": f"Bolo de Andar Verdadeiro ({tam_label}) c/ Blindagem de Chocolate + Tábua MDF",
                "quantidade": 1.0,
                "unidade": "unid",
                "valor_unitario": preco_bolo,
                "valor_total": preco_bolo
            })
            
        else:
            # Fallback padrão
            subtotal = 75.00
            items.append({
                "categoria": "docinho",
                "descricao": "Combo 50 Docinhos Festivos Tradicionais (13g)",
                "quantidade": 50,
                "unidade": "unid",
                "valor_unitario": 1.50,
                "valor_total": 75.00
            })

        discount = 0.0
        # Desconto de 5% em encomendas acima de R$ 500,00
        if subtotal >= 500.00:
            discount = round(subtotal * 0.05, 2)
            
        total = round(subtotal - discount, 2)
        
        result_payload = {
            "quote_id": quote_id,
            "subtotal": round(subtotal, 2),
            "discount": discount,
            "labor": 0.0, # Retirada no atelier
            "total": total,
            "currency": "BRL",
            "items": items
        }
        
        # Persistir no Neon PostgreSQL (Fonte da Verdade)
        try:
            telegram_chat_id = params.get("telegram_chat_id", 0)
            sql_insert = """
                INSERT INTO encomendas (id, telegram_chat_id, tipo_pedido, detalhes_json, quote_result, status)
                VALUES (%s, %s, %s, %s, %s, 'emitido');
            """
            execute_write(sql_insert, (
                raw_uuid,
                telegram_chat_id,
                categoria,
                json.dumps({"quantidade": quantidade, "sabores": sabores, "tipo_sabor": tipo_sabor}),
                json.dumps(result_payload, ensure_ascii=False)
            ))
        except Exception as e:
            logger.warning(f"Não foi possível salvar histórico no Neon: {e}")
            
        return result_payload
