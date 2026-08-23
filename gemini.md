# gemini.md — Constituição Normativa do Sistema (Cantinho Doce da Gabi)

Este documento é a **fonte normativa suprema do sistema**. Todas as regras, limites, schemas, contratos e definições contidas aqui devem ser rigorosamente respeitadas por todos os componentes do sistema.

---

## 🔒 1. Invariantes Arquiteturais Supremas

1. **Domínio do Sistema:** Agente Inteligente de Atendimento e Encomendas da Confeitaria **Cantinho Doce da Gabi**.
2. **IA Não é Fonte de Verdade:** Preços de docinhos, bolos, pirulitos, adicionais de topper, taxas e regras de quantidade mínima **NUNCA** são gerados ou recalculados pelo LLM. São obtidos via `Quote Service` + Neon PostgreSQL.
3. **Quote Service Isolado:** Toda matemática financeira e técnica da confeitaria é executada exclusivamente pelo `Quote Service`. O LLM apenas extrai os parâmetros da conversa do cliente e consome a resposta JSON oficial do serviço sem alterar valores.
4. **Regras Invioláveis do Catálogo:**
   - **Docinhos Festivos (13g):** Pedido mínimo de 50 unidades. Mínimo de 25 unidades por sabor.
     - Tradicionais (Brigadeiro, Ninho, Beijinho, Cajuzinho): 100 unids R$ 150,00 (até 4 sabores) | 50 unids R$ 75,00 (até 2 sabores).
     - Nobres (Ninho c/ Nutella, Churros c/ Doce de Leite): 100 unids R$ 170,00 (até 2 sabores) | 50 unids R$ 85,00 (até 2 sabores).
     - Adicional Topper Personalizado: R$ 0,40 por unidade.
   - **Docinhos Lembrancinha (20g em Forminha de Flor):** Tradicional R$ 2,30/unid | Nobre R$ 2,60/unid. Não acompanha forminhas de flor (cliente deve entregar 2 dias antes da data).
   - **Pirulito de Chocolate Decorado:** R$ 6,00/unid. Pedido mínimo de 12 unidades (R$ 72,00).
   - **Bolo Decorado em Chantilly:** 15cm (~15 fatias) a partir de R$ 150,00 | 20cm (~25 fatias) a partir de R$ 220,00 | 25cm (~40 fatias) a partir de R$ 310,00. Inclui 2 recheios tradicionais.
   - **Bolo de Andar Verdadeiro:** 40 fatias (Aros 20cm+15cm) a partir de R$ 395,00 | 55 fatias (Aros 25cm+15cm) a partir de R$ 495,00 | 65 fatias (Aros 25cm+20cm) a partir de R$ 595,00. Inclui blindagem de chocolate no bolo de baixo.
5. **Separação de Armazenamento:**
   - **Neon PostgreSQL (SQL Relacional):** Fonte da Verdade para preços, catálogo de sabores, regras de pedido mínimo, encomendas e agendamentos.
   - **PGVector (RAG Semântico):** Exclusivo para dúvidas de transporte, cuidados com bolos de chantilly/andar, sabores recomendados e o link do Google Meu Negócio (`https://share.google/W4JSgihofaVoJEzVi`).
   - **Redis (Estado Temporário):** Session store volátil com buffer debounce de 3s para mensagens picadas.

---

## 🏛️ 2. Mapeamento de Domínios do Sistema

| Domínio | Responsabilidade | Tipo de Componente | Fonte de Verdade / Tecnologia |
|---|---|---|---|
| **Gateway & Webhook** | Receber requisições do Telegram, aplicar debounce (3s) e formatar saída | FastAPI / Redis / Telegram API | Redis / Python |
| **Orquestração** | Roteamento de intenção e atendimento carismático do Cantinho Doce da Gabi | LangGraph / OpenAI `gpt-4o-mini` | State Context / LangSmith |
| **Cálculo de Encomenda** | Cálculo de docinhos, pirulitos, bolos e adicionais de toppers/recheios nobres | `Quote Service` (Determinístico) | Neon PostgreSQL (SQL Relacional) |
| **Conhecimento Técnico** | Esclarecer dúvidas conceituais de massas, recheios, localização e entregas | `RAG Service` (Semântico) | Neon PGVector |
| **Agendamento** | Agendamento de data e horário para retirada/entrega da encomenda | `Google Calendar Service` | Google Calendar API REST |

---

## 📐 3. Schemas de Dados Padrão (Contratos Invioláveis)

### 3.1 Input Payload para o Quote Service de Confeitaria
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "cliente_id": { "type": "string" },
    "categoria": { "type": "string", "enum": ["docinho_13g", "docinho_20g", "pirulito", "bolo_simples", "bolo_andar"] },
    "tipo_sabor": { "type": "string", "enum": ["tradicional", "nobre"] },
    "quantidade": { "type": "number" },
    "tamanho_cm": { "type": "number" },
    "fatias": { "type": "number" },
    "sabores_selecionados": { "type": "array", "items": { "type": "string" } },
    "com_topper": { "type": "boolean" }
  },
  "required": ["categoria"]
}
```

### 3.2 Output Estruturado Oficial do Quote Service de Confeitaria
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "quote_id": { "type": "string" },
    "subtotal": { "type": "number" },
    "discount": { "type": "number" },
    "labor": { "type": "number" },
    "total": { "type": "number" },
    "currency": { "type": "string", "default": "BRL" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "categoria": { "type": "string" },
          "descricao": { "type": "string" },
          "quantidade": { "type": "number" },
          "unidade": { "type": "string" },
          "valor_unitario": { "type": "number" },
          "valor_total": { "type": "number" }
        }
      }
    }
  },
  "required": ["quote_id", "subtotal", "total", "currency", "items"]
}
```
