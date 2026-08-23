import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from services.quote_service import QuoteService

def run_tests():
    print("=== TESTANDO CONFEITERIA CANTINHO DOCE DA GABI ===")
    
    # Teste 1: 50 Docinhos Festivos 13g Tradicionais
    print("\n1. Testando 50 Docinhos Tradicionais (13g)...")
    q1 = QuoteService.generate_quote({
        "categoria": "docinho_13g",
        "tipo_sabor": "tradicional",
        "quantidade": 50,
        "sabores_selecionados": ["Brigadeiro", "Ninho"]
    })
    print(f"   ID: {q1['quote_id']} | Subtotal: R$ {q1['subtotal']:.2f} | Total: R$ {q1['total']:.2f}")
    assert q1["total"] == 75.00, f"Esperado R$ 75.00, obtido {q1['total']}"
    print("   [OK] Teste 1 Aprovado!")

    # Teste 2: 100 Docinhos Festivos 13g Nobres c/ Topper
    print("\n2. Testando 100 Docinhos Nobres (13g) c/ Topper...")
    q2 = QuoteService.generate_quote({
        "categoria": "docinho_13g",
        "tipo_sabor": "nobre",
        "quantidade": 100,
        "sabores_selecionados": ["Ninho c/ Nutella", "Churros c/ Doce de Leite"],
        "com_topper": True
    })
    print(f"   ID: {q2['quote_id']} | Subtotal: R$ {q2['subtotal']:.2f} | Total: R$ {q2['total']:.2f}")
    # 100 * 1.70 = 170.00 + (100 * 0.40 = 40.00) = 210.00
    assert q2["total"] == 210.00, f"Esperado R$ 210.00, obtido {q2['total']}"
    print("   [OK] Teste 2 Aprovado!")

    # Teste 3: Bolo de Andar 55 Fatias
    print("\n3. Testando Bolo de Andar Verdadeiro (55 fatias)...")
    q3 = QuoteService.generate_quote({
        "categoria": "bolo_andar",
        "fatias": 55
    })
    print(f"   ID: {q3['quote_id']} | Total: R$ {q3['total']:.2f}")
    # R$ 495,00 - 5% desc (acima de R$ 500) = 495 - 24.75 = 470.25
    assert q3["subtotal"] == 495.00, f"Esperado R$ 495.00, obtido {q3['subtotal']}"
    print("   [OK] Teste 3 Aprovado!")

    print("\n=== TODOS OS TESTES DA CONFEITARIA CANTINHO DOCE DA GABI FORAM APROVADOS COM SUCESSO! ===")

if __name__ == "__main__":
    run_tests()
