# gemini.md — Constituição Normativa do Sistema

Este documento é a **fonte normativa suprema do sistema**. Todas as regras, limites, schemas, contratos e definições contidas aqui devem ser rigorosamente respeitadas por todos os componentes do sistema.

---

## 🔒 1. Invariantes Arquiteturais Supremas

1. **Microserviços Obrigatórios & Desacoplados:** O sistema opera com separação estrita entre inteligência (LLM/LangGraph) e componentes determinísticos.
2. **IA Não é Fonte de Verdade:** Preços de tabela ($/m^2$), estoques, cálculos de área ($m^2$), lista de ferragens, perfis de alumínio e regras financeiras **NUNCA** são gerados ou recalculados pelo LLM. São obtidos via `Quote Service` + Neon PostgreSQL.
3. **Quote Service Isolado:** Toda matemática financeira e técnica da vidraçaria é executada exclusivamente pelo `Quote Service`. O LLM apenas extrai os parâmetros da conversa do cliente e consome a resposta JSON oficial do serviço sem alterar valores.
4. **Separação de Armazenamento:**
   - **Neon PostgreSQL (SQL Relacional):** Fonte da Verdade para dados estruturados (clientes, preços, estoque, orçamentos, agendamentos). Proibido usar RAG para consultar preços/estoque!
   - **PGVector (RAG Semântico):** Exclusivo para busca semântica em textos não estruturados (manuais de instalação, especificações técnicas, garantias).
   - **Redis (Estado Temporário):** Volátil, operando exclusivamente como Session Store (`session_state`), buffer debounce de 15s para mensagens picadas, locks de concorrência e controle de TTL.
5. **Integrações Externas Determinísticas:**
   - **Google Calendar API:** Exclusivo para consulta de vagas, agendamento, atualização e cancelamento de visitas técnicas.
6. **UX Conversacional Humanizada (Telegram):**
   - Emissão do status `ChatAction.TYPING` durante o processamento.
   - Envio de mensagens em blocos naturais com pausas dinâmicas (1.5s a 3.0s), preservando cards de orçamento (`📐`) sem fragmentação.
   - Buffer debounce assíncrono de 15s para concatenar mensagens sequenciais de clientes no Telegram.
   - Ancoragem temporal dinâmica no fuso de Brasília (`America/Sao_Paulo`) a cada mensagem recebida.

---

## 🏛️ 2. Mapeamento de Domínios do Sistema

| Domínio | Responsabilidade | Tipo de Componente | Fonte de Verdade / Tecnologia |
|---|---|---|---|
| **Gateway & Webhook** | Receber requisições do Telegram, aplicar debounce (15s) e formatar saída | FastAPI / Redis / Telegram API | Redis / Python |
| **Orquestração** | Roteamento de intenção e coordenação do fluxo conversacional | LangGraph / OpenAI `gpt-4o-mini` | State Context / LangSmith |
| **Cálculo de Orçamento** | Cálculo de área $m^2$, precificação de vidro, ferragens, kit alumínio, mão de obra e total | `Quote Service` (Determinístico) | Neon PostgreSQL (SQL Relacional) |
| **Conhecimento Técnico** | Esclarecer dúvidas conceituais de materiais, vidros e instalação | `RAG Service` (Semântico) | Neon PGVector |
| **Agendamento** | Checar vagas, agendar, remarcar e cancelar visitas técnicas de medição | `Google Calendar Service` | Google Calendar API REST |
| **Sessão Temporária** | Armazenamento de estado volátil da conversa, buffer e locks | `Redis Service` | Redis (`session_state` + TTL) |

---

## 📐 3. Schemas de Dados Padrão (Contratos Invioláveis)

### 3.1 Input Payload para o Quote Service
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "cliente_id": { "type": "string" },
    "tipo_produto": { "type": "string", "enum": ["box", "janela", "porta", "espelho", "cobertura", "outro"] },
    "largura_mm": { "type": "number", "minimum": 100 },
    "altura_mm": { "type": "number", "minimum": 100 },
    "tipo_vidro": { "type": "string" },
    "espessura_mm": { "type": "number" },
    "cor_vidro": { "type": "string" },
    "cor_aluminio": { "type": "string" },
    "local_instalacao": { "type": "string" }
  },
  "required": ["tipo_produto", "largura_mm", "altura_mm", "tipo_vidro", "espessura_mm"]
}
```

### 3.2 Output Estruturado Oficial do Quote Service
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "quote_id": { "type": "string" },
    "area_m2_bruta": { "type": "number" },
    "area_m2_faturada": { "type": "number" },
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
          "categoria": { "type": "string", "enum": ["vidro", "ferragem", "aluminio", "mao_obra"] },
          "descricao": { "type": "string" },
          "quantidade": { "type": "number" },
          "unidade": { "type": "string" },
          "valor_unitario": { "type": "number" },
          "valor_total": { "type": "number" }
        },
        "required": ["categoria", "descricao", "quantidade", "valor_total"]
      }
    }
  },
  "required": ["quote_id", "subtotal", "labor", "total", "currency", "items"]
}
```

### 3.3 Schema de Agendamento (Google Calendar Integration)
```json
{
  "summary": "Visitação Técnica - Orçamento #{quote_id}",
  "description": "Cliente: {nome} | Telefone: {telefone} | Endereço: {endereco}",
  "start_iso": "2026-08-15T14:00:00-03:00",
  "end_iso": "2026-08-15T15:00:00-03:00"
}
```

---

## 🛡️ 4. Regras de Resiliência, Fallback e Observabilidade
- **Timeout:** 5000ms para chamadas de banco e APIs.
- **Fallback Quote Service:** Se o banco estiver temporariamente indisponível, o agente notifica o cliente que a cotação exata está em revisão técnica e registra no Neon/atendimento humano.
- **Observabilidade:** Todas as mensagens e transições de nós no LangGraph registram rastros com `correlation_id` no LangSmith.
