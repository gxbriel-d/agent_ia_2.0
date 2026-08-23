# Task Plan — Confeitaria Cantinho Doce da Gabi (Protocolo V.L.A.E.G.)

## 🎯 Objetivos do Projeto
Projetar e construir um sistema de agentes de IA baseado em microserviços e componentes determinísticos para atendimento e orçamento de encomendas da confeitaria **Cantinho Doce da Gabi**, garantindo isolamento de responsabilidades, cálculo determinístico de doces/bolos e busca semântica de localização/cuidados.

---

## 📐 Blueprint Arquitetural

```text
                     CLIENTE (Telegram / WhatsApp)
                                  │
                                  ▼ (Webhook com Debounce de 3s)
                          FastAPI Gateway
                                  │
                                  ▼
                    Redis Session Store (Estado Volátil)
                                  │
                                  ▼
               LangGraph Orchestrator (Cantinho Doce da Gabi)
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐           ┌──────────────┐
│  CÁLCULO     │          │ CATÁLOGO &   │           │ AGENDAMENTO  │
│ DETERMINÍS.  │          │ RAG SERVICE  │           │   SERVICE    │
│ (Doces 13g/  │          │ (PGVector)   │           │ (Google Cal  │
│  20g, Bolos, │          │ - Meu Negócio│           │  Retiradas)  │
│  Pirulitos)  │          │ - Blindagem  │           └──────────────┘
└──────┬───────┘          └──────────────┘
       │
       ▼
 Neon PostgreSQL DB (SQL Relacional - Fonte da Verdade)
```

---

## 🛠️ Tabela de Produtos & Preços Oficiais

| Categoria | Item / Tamanho | Sabores / Detalhes | Preço / Regra |
|---|---|---|---|
| **Docinhos 13g** | Tradicionais (50 unids) | Brigadeiro, Ninho, Beijinho, Cajuzinho (até 2 sabores) | R$ 75,00 (min. 25/sabor) |
| **Docinhos 13g** | Tradicionais (100 unids) | Brigadeiro, Ninho, Beijinho, Cajuzinho (até 4 sabores) | R$ 150,00 |
| **Docinhos 13g** | Nobres (50 unids) | Ninho c/ Nutella, Churros c/ Doce de Leite (até 2 sabores) | R$ 85,00 |
| **Docinhos 13g** | Nobres (100 unids) | Ninho c/ Nutella, Churros c/ Doce de Leite (até 2 sabores) | R$ 170,00 |
| **Docinhos 20g** | Lembrancinhas (Flor) | Tradicional R$ 2,30 | Nobre R$ 2,60 (cliente traz forminhas 2 dias antes) |
| **Pirulitos** | Chocolate Decorado | Mínimo 12 unidades | R$ 6,00/unid (R$ 72,00) |
| **Bolo Simples** | 15cm (~15 fatias) | Chantilly + 2 recheios tradicionais + Tábua MDF | A partir de R$ 150,00 |
| **Bolo Simples** | 20cm (~25 fatias) | Chantilly + 2 recheios tradicionais + Tábua MDF | A partir de R$ 220,00 |
| **Bolo Simples** | 25cm (~40 fatias) | Chantilly + 2 recheios tradicionais + Tábua MDF | A partir de R$ 310,00 |
| **Bolo de Andar**| 40 fatias (Aros 20+15) | 2 recheios + blindagem de chocolate + Tábua MDF | A partir de R$ 395,00 |
| **Bolo de Andar**| 55 fatias (Aros 25+15) | 2 recheios + blindagem de chocolate + Tábua MDF | A partir de R$ 495,00 |
| **Bolo de Andar**| 65 fatias (Aros 25+20) | 2 recheios + blindagem de chocolate + Tábua MDF | A partir de R$ 595,00 |
| **Adicional** | Topper Personalizado | Docinhos (R$ 0,40/unid) / Bolos (sob consulta) | Sob consulta |
