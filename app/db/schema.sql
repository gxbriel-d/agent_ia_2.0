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

-- 2. Tabela de Produtos da Confeitaria (Docinhos, Pirulitos, Bolos)
CREATE TABLE IF NOT EXISTS produtos_confeitaria (
    id SERIAL PRIMARY KEY,
    categoria VARCHAR(50) NOT NULL,    -- docinho_13g, docinho_20g, pirulito, bolo_simples, bolo_andar
    modelo_tamanho VARCHAR(100) NOT NULL, -- 100_unids, 50_unids, 15cm_15_fatias, 20cm_25_fatias, 25cm_40_fatias, andar_40_fatias, etc.
    tipo_sabor VARCHAR(50) NOT NULL,   -- tradicional, nobre
    fatias INT DEFAULT 0,
    peso_gr INT DEFAULT 0,
    minimo_unidades INT DEFAULT 1,
    preco_base NUMERIC(10, 2) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);

-- 3. Tabela de Sabores e Recheios
CREATE TABLE IF NOT EXISTS sabores_recheios (
    id SERIAL PRIMARY KEY,
    nome_sabor VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,    -- docinho, recheio_bolo
    tipo VARCHAR(50) NOT NULL,         -- tradicional, nobre
    adicional_preco NUMERIC(10, 2) DEFAULT 0.00
);

-- 4. Tabela de Adicionais e Enfeitos
CREATE TABLE IF NOT EXISTS adicionais (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    preco_unitario NUMERIC(10, 2) NOT NULL,
    unidade VARCHAR(20) DEFAULT 'unid'
);

-- 5. Tabela de Encomendas / Orçamentos (Fonte da Verdade Permanente)
CREATE TABLE IF NOT EXISTS encomendas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID REFERENCES clientes(id),
    telegram_chat_id BIGINT NOT NULL,
    tipo_pedido VARCHAR(50) NOT NULL,
    detalhes_json JSONB NOT NULL,
    quote_result JSONB NOT NULL,
    data_retirada TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'emitido', -- emitido, agendado, concluido, cancelado
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tabela RAG (PGVector para Conhecimento Semântico / Localização / Dicas)
CREATE TABLE IF NOT EXISTS conhecimento_tecnico (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    conteudo TEXT NOT NULL,
    categoria VARCHAR(50),
    metadata JSONB,
    embedding vector(1536) -- OpenAI text-embedding-3-small (1536 dimensions)
);

-- ----------------------------------------------------
-- SEED DATA (Confeitaria Cantinho Doce da Gabi)
-- ----------------------------------------------------

INSERT INTO produtos_confeitaria (categoria, modelo_tamanho, tipo_sabor, peso_gr, minimo_unidades, preco_base) VALUES
('docinho_13g', '100_unidades', 'tradicional', 13, 100, 150.00),
('docinho_13g', '50_unidades', 'tradicional', 13, 50, 75.00),
('docinho_13g', '100_unidades', 'nobre', 13, 100, 170.00),
('docinho_13g', '50_unidades', 'nobre', 13, 50, 85.00),
('docinho_20g', 'unidade_flor', 'tradicional', 20, 1, 2.30),
('docinho_20g', 'unidade_flor', 'nobre', 20, 1, 2.60),
('pirulito', 'unidade_decorada', 'tradicional', 0, 12, 6.00),
('bolo_simples', '15cm_15_fatias', 'tradicional', 0, 1, 150.00),
('bolo_simples', '20cm_25_fatias', 'tradicional', 0, 1, 220.00),
('bolo_simples', '25cm_40_fatias', 'tradicional', 0, 1, 310.00),
('bolo_andar', 'andar_40_fatias', 'tradicional', 0, 1, 395.00),
('bolo_andar', 'andar_55_fatias', 'tradicional', 0, 1, 495.00),
('bolo_andar', 'andar_65_fatias', 'tradicional', 0, 1, 595.00)
ON CONFLICT DO NOTHING;

INSERT INTO sabores_recheios (nome_sabor, categoria, tipo, adicional_preco) VALUES
('Brigadeiro', 'docinho', 'tradicional', 0.00),
('Ninho', 'docinho', 'tradicional', 0.00),
('Beijinho', 'docinho', 'tradicional', 0.00),
('Cajuzinho', 'docinho', 'tradicional', 0.00),
('Ninho c/ Nutella', 'docinho', 'nobre', 0.00),
('Churros c/ Doce de Leite', 'docinho', 'nobre', 0.00)
ON CONFLICT DO NOTHING;

INSERT INTO adicionais (codigo, nome, preco_unitario, unidade) VALUES
('ADD-TOPPER-DOCE', 'Topper Personalizado para Docinhos', 0.40, 'unid')
ON CONFLICT DO NOTHING;

INSERT INTO conhecimento_tecnico (titulo, conteudo, categoria) VALUES
('Localização e Contato - Cantinho Doce da Gabi', 'O Cantinho Doce da Gabi é especialista em docinhos festivos, pirulitos e bolos decorados/andar. Confira nosso perfil no Google Meu Negócio: https://share.google/W4JSgihofaVoJEzVi', 'localizacao'),
('Blindagem de Chocolate em Bolos de Andar', 'Todos os nossos bolos de andar verdadeiros acompanham blindagem de chocolate blend ou meio amargo no bolo inferior para garantir 100% de estabilidade e segurança no transporte.', 'cuidados'),
('Regras de Forminhas de Flor para Lembrancinhas', 'Para docinhos de 20g servidos em forminhas de flor/estilo lembrancinhas, o cliente deve entregar as forminhas ou lembrancinhas personalizadas em nosso atelier com até 2 dias de antecedência da data do evento.', 'regras')
ON CONFLICT DO NOTHING;
