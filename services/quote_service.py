import uuid
import math
import logging
from typing import Dict, Any, List
from app.db.neon import execute_query, execute_write

logger = logging.getLogger(__name__)

def calculate_glass_area(largura_mm: float, altura_mm: float, folga_mm: float = 50.0) -> Dict[str, float]:
    """
    Calcula a área bruta e a área faturada em m² (com folga mínima de corte técnica).
    """
    largura_m = (largura_mm + folga_mm) / 1000.0
    altura_m = (altura_mm + folga_mm) / 1000.0
    area_bruta = (largura_mm / 1000.0) * (altura_mm / 1000.0)
    area_faturada = largura_m * altura_m
    
    # Arredondar area faturada para 2 casas decimais (minimo 0.5m² em vidraçaria)
    area_faturada = max(0.5, round(area_faturada, 2))
    area_bruta = round(area_bruta, 2)
    
    return {
        "area_bruta_m2": area_bruta,
        "area_faturada_m2": area_faturada
    }

def get_glass_price_from_db(tipo_produto: str, tipo_vidro: str, espessura_mm: int, cor_vidro: str) -> float:
    """
    Consulta o preço por m² do vidro no Neon PostgreSQL.
    """
    try:
        sql = """
            SELECT preco_m2_bruto 
            FROM produtos_vidro 
            WHERE LOWER(tipo_produto) = LOWER(%s) 
              AND LOWER(tipo_vidro) = LOWER(%s) 
              AND espessura_mm = %s 
              AND LOWER(cor_vidro) = LOWER(%s)
              AND ativo = TRUE
            LIMIT 1;
        """
        rows = execute_query(sql, (tipo_produto, tipo_vidro, espessura_mm, cor_vidro))
        if rows and len(rows) > 0:
            return float(rows[0]['preco_m2_bruto'])
    except Exception as e:
        logger.warning(f"Erro ao consultar preço do vidro no banco: {e}. Usando fallback determinístico.")
    
    # Fallbacks determinísticos padrão por tipo de vidro
    precos_fallback = {
        ("temperado", 8, "incolor"): 180.0,
        ("temperado", 8, "fume"): 210.0,
        ("temperado", 8, "verde"): 220.0,
        ("temperado", 8, "bronze"): 210.0,
        ("temperado", 10, "incolor"): 240.0,
        ("comum", 4, "incolor"): 150.0
    }
    return precos_fallback.get((tipo_vidro.lower(), espessura_mm, cor_vidro.lower()), 190.0)

def get_aluminum_price_from_db(tipo_produto: str, cor_aluminio: str) -> float:
    """
    Consulta o preço do kit de alumínio no Neon PostgreSQL.
    """
    modelo_map = {
        "box": "kit_box_padrao",
        "janela": "kit_janela_2folhas",
        "porta": "kit_porta_pivotante"
    }
    modelo = modelo_map.get(tipo_produto.lower(), "kit_box_padrao")
    try:
        sql = "SELECT preco_kit FROM perfis_aluminio WHERE modelo_kit = %s AND LOWER(cor_aluminio) = LOWER(%s) LIMIT 1;"
        rows = execute_query(sql, (modelo, cor_aluminio))
        if rows and len(rows) > 0:
            return float(rows[0]['preco_kit'])
    except Exception as e:
        logger.warning(f"Erro ao consultar preço de alumínio no banco: {e}")
    
    fallback_alum = {"branco": 140.0, "preto": 150.0, "fosco": 135.0, "bronze": 145.0}
    return fallback_alum.get(cor_aluminio.lower(), 140.0)

def get_hardware_price_from_db(tipo_produto: str) -> float:
    """
    Consulta o preço do kit de ferragens no Neon PostgreSQL.
    """
    try:
        sql = "SELECT preco_unitario FROM ferragens WHERE produto_compativel = %s LIMIT 1;"
        rows = execute_query(sql, (tipo_produto.lower(),))
        if rows and len(rows) > 0:
            return float(rows[0]['preco_unitario'])
    except Exception as e:
        logger.warning(f"Erro ao consultar ferragens no banco: {e}")
    
    fallback_ferr = {"box": 90.0, "janela": 80.0, "porta": 350.0, "espelho": 40.0}
    return fallback_ferr.get(tipo_produto.lower(), 70.0)

class QuoteService:
    @staticmethod
    def generate_quote(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a matemática determinística completa e gera o orçamento oficial.
        """
        quote_id = f"ORC-{uuid.uuid4().hex[:8].upper()}"
        
        tipo_produto = params.get("tipo_produto", "box").lower()
        largura_mm = float(params.get("largura_mm", 1200))
        altura_mm = float(params.get("altura_mm", 1900))
        tipo_vidro = params.get("tipo_vidro", "temperado").lower()
        espessura_mm = int(params.get("espessura_mm", 8))
        cor_vidro = params.get("cor_vidro", "incolor").lower()
        cor_aluminio = params.get("cor_aluminio", "branco").lower()
        
        # 1. Área
        areas = calculate_glass_area(largura_mm, altura_mm)
        area_faturada = areas["area_faturada_m2"]
        
        # 2. Vidro
        preco_m2_vidro = get_glass_price_from_db(tipo_produto, tipo_vidro, espessura_mm, cor_vidro)
        valor_total_vidro = round(area_faturada * preco_m2_vidro, 2)
        
        # 3. Alumínio
        valor_aluminio = get_aluminum_price_from_db(tipo_produto, cor_aluminio)
        
        # 4. Ferragens
        valor_ferragens = get_hardware_price_from_db(tipo_produto)
        
        # 5. Mão de Obra (R$ 150 base + R$ 30 por m² faturado)
        valor_mao_obra = round(150.0 + (area_faturada * 30.0), 2)
        
        # 6. Subtotal
        subtotal = round(valor_total_vidro + valor_aluminio + valor_ferragens, 2)
        discount = 0.0
        
        # Desconto de 5% se o valor total passar de R$ 1.000,00
        if (subtotal + valor_mao_obra) > 1000.0:
            discount = round((subtotal + valor_mao_obra) * 0.05, 2)
            
        total = round(subtotal + valor_mao_obra - discount, 2)
        
        # Montar lista de itens
        items = [
            {
                "categoria": "vidro",
                "descricao": f"Vidro {tipo_vidro.title()} {espessura_mm}mm {cor_vidro.title()} ({largura_mm:.0f}x{altura_mm:.0f}mm)",
                "quantidade": area_faturada,
                "unidade": "m²",
                "valor_unitario": preco_m2_vidro,
                "valor_total": valor_total_vidro
            },
            {
                "categoria": "aluminio",
                "descricao": f"Kit Perfis de Alumínio Cor {cor_aluminio.title()}",
                "quantidade": 1.0,
                "unidade": "kit",
                "valor_unitario": valor_aluminio,
                "valor_total": valor_aluminio
            },
            {
                "categoria": "ferragem",
                "descricao": f"Kit de Ferragens e Acessórios para {tipo_produto.title()}",
                "quantidade": 1.0,
                "unidade": "kit",
                "valor_unitario": valor_ferragens,
                "valor_total": valor_ferragens
            },
            {
                "categoria": "mao_obra",
                "descricao": "Mão de Obra Especializada de Instalação e Vedação",
                "quantidade": 1.0,
                "unidade": "serviço",
                "valor_unitario": valor_mao_obra,
                "valor_total": valor_mao_obra
            }
        ]
        
        result_payload = {
            "quote_id": quote_id,
            "area_m2_bruta": areas["area_bruta_m2"],
            "area_m2_faturada": area_faturada,
            "subtotal": subtotal,
            "discount": discount,
            "labor": valor_mao_obra,
            "total": total,
            "currency": "BRL",
            "items": items
        }
        
        # Persistir no Neon PostgreSQL (Fonte da Verdade)
        try:
            telegram_chat_id = params.get("telegram_chat_id", 0)
            sql_insert = """
                INSERT INTO orcamentos (id, telegram_chat_id, tipo_produto, medidas_json, quote_result, status)
                VALUES (%s, %s, %s, %s, %s, 'emitido');
            """
            import json
            execute_write(sql_insert, (
                quote_id.replace("ORC-", ""),
                telegram_chat_id,
                tipo_produto,
                json.dumps({"largura_mm": largura_mm, "altura_mm": altura_mm, "cor_vidro": cor_vidro}),
                json.dumps(result_payload, ensure_ascii=False)
            ))
        except Exception as e:
            logger.warning(f"Não foi possível salvar histórico no Neon: {e}")
            
        return result_payload
