# Findings — Descobertas e Decisões Técnicas

## 📌 Protocolo Arquitetural
- **Protocolo Utilizado:** Protocolo V.L.A.E.G. (Visão, Link, Arquitetura, Estilo, Gatilho) com Arquitetura A.N.T.
- **Regra Fundamental:** Arquitetura baseada em microserviços determinísticos. A IA (LLM) nunca é fonte de verdade para preços, regras de cálculo ou dados cadastrais.

---

## 🔍 Registros de Pesquisa e Decisões

### 1. Separação de Responsabilidades
- **LLM / Agentes:** Responsáveis por raciocínio, intenção, classificação, conversação e solicitação de ferramentas.
- **Serviços Determinísticos:** Responsáveis por matemática de orçamentos (m², folga de corte, ferragens por tipo de vão, cálculo de margem e descontos).

### 2. Estrutura de Memória e Observabilidade
- Todos os contratos de entrada, saída, ferramentas e erros devem ser documentados em `gemini.md` antes de qualquer codificação de serviços ou prompts.
- Logs temporários e artefatos de testes intermediários devem ser mantidos na pasta `.tmp/`.

---

## ⚠️ Restrições Técnicas & Invariantes
- Proibido monolito final.
- Proibido adivinhar regras de cálculo de vidro e alumínio sem validação na fonte de verdade.
- Proibido prosseguir para implementação de serviços ou agents antes da Fase de Descoberta ser concluída.
