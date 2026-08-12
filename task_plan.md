# Task Plan — Sistema de Orçamentos IA (Protocolo V.L.A.E.G.)

## 🎯 Objetivos do Projeto
Projetar e construir um sistema de agentes de IA baseado em microserviços e componentes determinísticos para orçamentos de vidraçaria, garantindo isolamento de responsabilidades, confiabilidade nos cálculos e fonte de verdade bem definida.

---

## 📐 Blueprint Arquitetural (Preliminar)

```text
                        CLIENTE (WhatsApp / Web)
                                   │
                                   ▼
                           ┌───────────────┐
                           │ API / GATEWAY │
                           └───────┬───────┘
                                   │
                                   ▼
                           ┌───────────────┐
                           │ ORQUESTRADOR  │
                           └───────┬───────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
  │ AGENTE IA   │           │ AGENTE IA   │           │ AGENTE IA   │
  │ ATENDIMENTO │           │ ORÇAMENTOS  │           │   SUPORTE   │
  └──────┬──────┘           └──────┬──────┘           └──────┬──────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
      ┌───────────┐          ┌───────────┐          ┌───────────┐
      │  SERVIÇO  │          │  SERVIÇO  │          │  SERVIÇO  │
      │ CÁLCULO   │          │ ESTOQUE / │          │ CLIENTES  │
      │ ORÇAMENTO │          │ PREÇOS    │          │  / CRM    │
      └───────────┘          └───────────┘          └───────────┘
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   ▼
                            FONTE DE VERDADE
                       (PostgreSQL / Banco Dados)
```

---

## 🛠️ Microserviços Planejados (Em definição de Contratos)
1. **Orchestrator Service:** Roteamento e orquestração dos fluxos.
2. **Pricing & Calculation Service:** Serviço determinístico para cálculo exato de m², ferragens, perfis, mão de obra e margem.
3. **Inventory & Product Catalog Service:** Fonte de verdade de preços, modelos de vidros (temperado, laminado, comum) e acessórios.
4. **Customer & CRM Service:** Gestão de clientes e histórico de orçamentos.

---

## 📋 Checklist Arquitetural por Fases

### Protocolo 0 — Inicialização
- [x] Memória do projeto criada (`task_plan.md`, `findings.md`, `progress.md`).
- [x] Constituição do sistema criada (`gemini.md`).
- [x] Estrutura de diretórios `architecture/`, `services/`, `agents/`, `tools/`, `.tmp/` inicializada.
- [ ] Fase 1 — V: Visão e Descoberta concluída com o usuário.

### Fase 1 — V: Visão e Lógica
- [ ] Objetivo principal (Estrela Guia) confirmado.
- [ ] Domínios de negócio formalizados.
- [ ] Integrantes e integrações definidos.
- [ ] Contratos de Schemas (Input/Output/Error) especificados no `gemini.md`.

### Fase 2 — L: Link e Conectividade
- [ ] Scripts de Handshake em `tools/` funcionais.
- [ ] Teste individual de microserviços e conexões externas.

### Fase 3 — A: Arquitetura
- [ ] Procedimentos Operacionais Padrão (POPs) escritos em `architecture/pops/`.
- [ ] Separação total de código determinístico vs LLM.

### Fase 4 — E: Estilo
- [ ] Formatação dos payloads finais (WhatsApp/PDF/JSON).
- [ ] Definição de personas e limites conversacionais.

### Fase 5 — G: Gatilho e Implantação
- [ ] Webhooks e gatilhos configurados.
- [ ] Observabilidade, logs e correlação ID ativos.

---

## 🏁 Critérios de Conclusão da Fase Atual
- Confirmação das respostas da Fase de Descoberta (Fase 1 - V) pelo usuário.
- Aprovação dos esquemas de dados (JSON Schema) no `gemini.md`.
