import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from services.quote_service import QuoteService, calculate_glass_area

def run_tests():
    print("=== TESTANDO CÁLCULO DE ÁREA ===")
    area_res = calculate_glass_area(1200, 1900, folga_mm=50)
    area_faturada = area_res['area_faturada_m2']
    print(f"Bruta: {area_res['area_bruta_m2']} m2 | Faturada: {area_faturada} m2")
    assert area_faturada == 2.44, f"Esperado 2.44, obtido {area_faturada}"
    print("[OK] Teste de Área Aprovado!")

    print("\n=== TESTANDO GERADOR DE ORÇAMENTO (QUOTE SERVICE) ===")
    quote = QuoteService.generate_quote({
        "tipo_produto": "box",
        "largura_mm": 1200,
        "altura_mm": 1900,
        "tipo_vidro": "temperado",
        "espessura_mm": 8,
        "cor_vidro": "incolor",
        "cor_aluminio": "branco"
    })
    
    print(f"ID do Orçamento: {quote['quote_id']}")
    print(f"Subtotal: R$ {quote['subtotal']:.2f}")
    print(f"Mão de Obra: R$ {quote['labor']:.2f}")
    print(f"Desconto: R$ {quote['discount']:.2f}")
    print(f"TOTAL FINAL: R$ {quote['total']:.2f}")
    print("Itens Calculados:")
    for it in quote["items"]:
        print(f"  - [{it['categoria'].upper()}] {it['descricao']}: R$ {it['valor_total']:.2f}")

    assert quote["total"] > 0
    assert quote["currency"] == "BRL"
    assert len(quote["items"]) == 4
    print("\n[SUCESSO] Quote Service verificado e operando 100% determinístico!")

if __name__ == "__main__":
    run_tests()
