import pytest
from services.quote_service import QuoteService, calculate_glass_area

def test_calculate_glass_area():
    # Vão de Box 1200mm x 1900mm com folga de 50mm
    # (1.25m * 1.95m) = 2.4375 m² -> Arredondado 2.44 m²
    res = calculate_glass_area(1200, 1900, folga_mm=50)
    assert res["area_bruta_m2"] == 2.28
    assert res["area_faturada_m2"] == 2.44

def test_generate_quote_box():
    params = {
        "tipo_produto": "box",
        "largura_mm": 1200,
        "altura_mm": 1900,
        "tipo_vidro": "temperado",
        "espessura_mm": 8,
        "cor_vidro": "incolor",
        "cor_aluminio": "branco"
    }
    quote = QuoteService.generate_quote(params)
    
    assert "quote_id" in quote
    assert quote["currency"] == "BRL"
    assert quote["area_m2_faturada"] == 2.44
    assert len(quote["items"]) == 4
    assert quote["subtotal"] > 0
    assert quote["labor"] > 0
    assert quote["total"] > 0
    
    # Subtotal + labor - discount == total
    expected_total = round(quote["subtotal"] + quote["labor"] - quote["discount"], 2)
    assert quote["total"] == expected_total

def test_generate_quote_janela():
    params = {
        "tipo_produto": "janela",
        "largura_mm": 1500,
        "altura_mm": 1200,
        "tipo_vidro": "temperado",
        "espessura_mm": 8,
        "cor_vidro": "fume",
        "cor_aluminio": "preto"
    }
    quote = QuoteService.generate_quote(params)
    assert quote["total"] > 0
    assert quote["items"][0]["categoria"] == "vidro"
