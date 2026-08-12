-- Habilitar extensao pgvector para busca semantica
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Tabela de Clientes
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    nome VARCHAR(255),
    telefone VARCHAR(50),
    endereco TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabela de Produtos de Vidro (Preço por m²)
CREATE TABLE IF NOT EXISTS produtos_vidro (
    id SERIAL PRIMARY KEY,
    tipo_produto VARCHAR(50) NOT NULL, -- box, janela, porta, espelho, cobertura
    tipo_vidro VARCHAR(50) NOT NULL,   -- temperado, laminado, comum
    espessura_mm INT NOT NULL,         -- 6, 8, 10, 12
    cor_vidro VARCHAR(50) NOT NULL,    -- incolor, fume, verde, bronze
    preco_m2_bruto NUMERIC(10, 2) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    CONSTRAINT unq_vidro UNIQUE (tipo_produto, tipo_vidro, espessura_mm, cor_vidro)
);

-- 3. Tabela de Ferragens
CREATE TABLE IF NOT EXISTS ferragens (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    categoria VARCHAR(50) NOT NULL,    -- kit_box, roldana, dobradica, fechadura, puxador
    preco_unitario NUMERIC(10, 2) NOT NULL,
    produto_compativel VARCHAR(50)     -- box, janela, porta, etc.
);

-- 4. Tabela de Perfis de Alumínio
CREATE TABLE IF NOT EXISTS perfis_aluminio (
    id SERIAL PRIMARY KEY,
    modelo_kit VARCHAR(100) NOT NULL,  -- kit_box_padrao, kit_janela_2folhas, kit_porta_pivotante
    cor_aluminio VARCHAR(50) NOT NULL, -- branco, preto, fosco, bronze
    preco_kit NUMERIC(10, 2) NOT NULL,
    CONSTRAINT unq_aluminio UNIQUE (modelo_kit, cor_aluminio)
);

-- 5. Regras Comerciais & Margens Determinísticas
CREATE TABLE IF NOT EXISTS regras_comerciais (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor_numerico NUMERIC(10, 2) NOT NULL,
    descricao TEXT
);

-- 6. Tabela de Orçamentos (Fonte da Verdade Permanente)
CREATE TABLE IF NOT EXISTS orcamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID REFERENCES clientes(id),
    telegram_chat_id BIGINT NOT NULL,
    tipo_produto VARCHAR(50) NOT NULL,
    medidas_json JSONB NOT NULL,
    quote_result JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'emitido', -- emitido, agendado, fechado, cancelado
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Tabela de Agendamentos de Visita Técnica
CREATE TABLE IF NOT EXISTS agendamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orcamento_id UUID REFERENCES orcamentos(id),
    google_event_id VARCHAR(255),
    data_hora_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    data_hora_fim TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'agendado', -- agendado, concluido, cancelado
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Tabela RAG (PGVector para Conhecimento Semântico / Manuais / NORMAS NBR)
CREATE TABLE IF NOT EXISTS conhecimento_tecnico (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    conteudo TEXT NOT NULL,
    categoria VARCHAR(50),
    metadata JSONB,
    embedding vector(1536) -- OpenAI text-embedding-3-small (1536 dimensions)
);

-- ----------------------------------------------------
-- SEED DATA (Valores Padrão Oficiais da Vidraçaria)
-- ----------------------------------------------------

INSERT INTO regras_comerciais (chave, valor_numerico, descricao) VALUES
('folga_corte_mm', 50.00, 'Folga de corte padrao em mm'),
('mao_obra_base', 150.00, 'Mao de obra base por instalação'),
('mao_obra_m2_adicional', 30.00, 'Adicional de mao de obra por m2 extra'),
('desconto_maximo_pct', 10.00, 'Percentual de desconto maximo permitido')
ON CONFLICT (chave) DO NOTHING;

INSERT INTO produtos_vidro (tipo_produto, tipo_vidro, espessura_mm, cor_vidro, preco_m2_bruto) VALUES
('box', 'temperado', 8, 'incolor', 180.00),
('box', 'temperado', 8, 'fume', 210.00),
('box', 'temperado', 8, 'verde', 220.00),
('box', 'temperado', 8, 'bronze', 210.00),
('janela', 'temperado', 8, 'incolor', 170.00),
('janela', 'temperado', 8, 'fume', 195.00),
('porta', 'temperado', 10, 'incolor', 240.00),
('porta', 'temperado', 10, 'fume', 270.00),
('espelho', 'comum', 4, 'incolor', 150.00),
('espelho', 'comum', 5, 'incolor', 190.00)
ON CONFLICT DO NOTHING;

INSERT INTO perfis_aluminio (modelo_kit, cor_aluminio, preco_kit) VALUES
('kit_box_padrao', 'branco', 140.00),
('kit_box_padrao', 'preto', 150.00),
('kit_box_padrao', 'fosco', 135.00),
('kit_janela_2folhas', 'branco', 180.00),
('kit_janela_2folhas', 'preto', 195.00),
('kit_porta_pivotante', 'branco', 280.00),
('kit_porta_pivotante', 'preto', 310.00)
ON CONFLICT DO NOTHING;

INSERT INTO ferragens (codigo, nome, categoria, preco_unitario, produto_compativel) VALUES
('FER-BOX-01', 'Kit Ferragens Box Padrao (Roldanas + Batedores)', 'kit_box', 90.00, 'box'),
('FER-JAN-01', 'Kit Trincos e Fechaduras Janela', 'kit_janela', 80.00, 'janela'),
('FER-POR-01', 'Mola de Piso + Dobradicas Porta Pivotante', 'kit_porta', 350.00, 'porta')
ON CONFLICT DO NOTHING;
