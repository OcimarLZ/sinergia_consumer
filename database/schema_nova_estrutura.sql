-- Nova estrutura do banco de dados para sistema de simulação de descontos
-- Estrutura mais robusta baseada na análise das regras reais das distribuidoras

-- Tabela de Estados (mantida)
CREATE TABLE IF NOT EXISTS estados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL UNIQUE,
    sigla VARCHAR(2) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Distribuidoras (mantida com algumas melhorias)
CREATE TABLE IF NOT EXISTS distribuidoras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    estado_id INTEGER NOT NULL,
    consumo_minimo INTEGER NOT NULL, -- em kWh
    forma_pagamento VARCHAR(50) NOT NULL, -- 'Unificado', 'Dois Boletos'
    prazo_injecao INTEGER NOT NULL, -- em dias
    troca_titularidade BOOLEAN DEFAULT FALSE,
    login_senha_necessario BOOLEAN DEFAULT FALSE,
    aceita_placas BOOLEAN DEFAULT TRUE,
    icms_minimo DECIMAL(5,2) DEFAULT 17.00,
    observacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estado_id) REFERENCES estados(id)
);

-- Nova tabela: Tipos de Bônus
CREATE TABLE IF NOT EXISTS tipos_bonus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(10) NOT NULL UNIQUE, -- 'A', 'B', 'C', 'D'
    nome VARCHAR(50) NOT NULL, -- 'Bônus A', 'Bônus B', etc.
    descricao TEXT,
    cor_hex VARCHAR(7), -- para exibição visual (#FF0000, etc.)
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nova tabela: Faixas de Consumo por Distribuidora
CREATE TABLE IF NOT EXISTS faixas_consumo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distribuidora_id INTEGER NOT NULL,
    consumo_min INTEGER NOT NULL, -- kWh mínimo da faixa
    consumo_max INTEGER, -- kWh máximo da faixa (NULL = sem limite)
    nome_faixa VARCHAR(100), -- ex: "100 kWh", "1.000 a 5.000 kWh"
    ordem INTEGER DEFAULT 1, -- para ordenação das faixas
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (distribuidora_id) REFERENCES distribuidoras(id),
    UNIQUE(distribuidora_id, consumo_min, consumo_max)
);

-- Nova tabela: Regras de Desconto (relaciona faixas com bônus)
CREATE TABLE IF NOT EXISTS regras_desconto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faixa_consumo_id INTEGER NOT NULL,
    tipo_bonus_id INTEGER NOT NULL,
    desconto_percentual DECIMAL(5,2) NOT NULL,
    desconto_opcional_1 DECIMAL(5,2), -- para casos como "16% ou 20%"
    desconto_opcional_2 DECIMAL(5,2),
    desconto_opcional_3 DECIMAL(5,2),
    desconto_opcional_4 DECIMAL(5,2),
    analise_credito BOOLEAN DEFAULT FALSE, -- se requer análise de crédito
    observacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faixa_consumo_id) REFERENCES faixas_consumo(id),
    FOREIGN KEY (tipo_bonus_id) REFERENCES tipos_bonus(id),
    UNIQUE(faixa_consumo_id, tipo_bonus_id)
);

-- Tabela de Simulações (melhorada)
CREATE TABLE IF NOT EXISTS simulacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distribuidora_id INTEGER NOT NULL,
    faixa_consumo_id INTEGER,
    tipo_bonus_id INTEGER,
    consumo_kwh INTEGER NOT NULL,
    desconto_aplicado DECIMAL(5,2) NOT NULL,
    valor_economia DECIMAL(10,2),
    ip_usuario VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (distribuidora_id) REFERENCES distribuidoras(id),
    FOREIGN KEY (faixa_consumo_id) REFERENCES faixas_consumo(id),
    FOREIGN KEY (tipo_bonus_id) REFERENCES tipos_bonus(id)
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_distribuidoras_estado ON distribuidoras(estado_id);
CREATE INDEX IF NOT EXISTS idx_distribuidoras_ativo ON distribuidoras(ativo);
CREATE INDEX IF NOT EXISTS idx_faixas_distribuidora ON faixas_consumo(distribuidora_id);
CREATE INDEX IF NOT EXISTS idx_faixas_consumo_range ON faixas_consumo(consumo_min, consumo_max);
CREATE INDEX IF NOT EXISTS idx_faixas_ativo ON faixas_consumo(ativo);
CREATE INDEX IF NOT EXISTS idx_regras_faixa ON regras_desconto(faixa_consumo_id);
CREATE INDEX IF NOT EXISTS idx_regras_bonus ON regras_desconto(tipo_bonus_id);
CREATE INDEX IF NOT EXISTS idx_regras_ativo ON regras_desconto(ativo);
CREATE INDEX IF NOT EXISTS idx_simulacoes_distribuidora ON simulacoes(distribuidora_id);
CREATE INDEX IF NOT EXISTS idx_simulacoes_data ON simulacoes(created_at);
CREATE INDEX IF NOT EXISTS idx_tipos_bonus_codigo ON tipos_bonus(codigo);
CREATE INDEX IF NOT EXISTS idx_tipos_bonus_ativo ON tipos_bonus(ativo);

-- Views para facilitar consultas

-- View: Regras completas com todas as informações
CREATE VIEW IF NOT EXISTS vw_regras_completas AS
SELECT 
    r.id as regra_id,
    d.id as distribuidora_id,
    d.nome as distribuidora_nome,
    e.nome as estado_nome,
    e.sigla as estado_sigla,
    fc.id as faixa_id,
    fc.consumo_min,
    fc.consumo_max,
    fc.nome_faixa,
    tb.id as bonus_id,
    tb.codigo as bonus_codigo,
    tb.nome as bonus_nome,
    r.desconto_percentual,
    r.desconto_opcional_1,
    r.desconto_opcional_2,
    r.desconto_opcional_3,
    r.desconto_opcional_4,
    r.analise_credito,
    d.forma_pagamento,
    d.prazo_injecao,
    d.troca_titularidade,
    r.observacoes as regra_observacoes,
    d.observacoes as distribuidora_observacoes
FROM regras_desconto r
JOIN faixas_consumo fc ON r.faixa_consumo_id = fc.id
JOIN distribuidoras d ON fc.distribuidora_id = d.id
JOIN estados e ON d.estado_id = e.id
JOIN tipos_bonus tb ON r.tipo_bonus_id = tb.id
WHERE r.ativo = 1 AND fc.ativo = 1 AND d.ativo = 1 AND tb.ativo = 1;

-- View: Faixas de consumo por distribuidora
CREATE VIEW IF NOT EXISTS vw_faixas_por_distribuidora AS
SELECT 
    d.id as distribuidora_id,
    d.nome as distribuidora_nome,
    e.sigla as estado_sigla,
    fc.id as faixa_id,
    fc.consumo_min,
    fc.consumo_max,
    fc.nome_faixa,
    fc.ordem,
    COUNT(r.id) as total_bonus_disponiveis
FROM distribuidoras d
JOIN estados e ON d.estado_id = e.id
JOIN faixas_consumo fc ON d.id = fc.distribuidora_id
LEFT JOIN regras_desconto r ON fc.id = r.faixa_consumo_id AND r.ativo = 1
WHERE d.ativo = 1 AND fc.ativo = 1
GROUP BY d.id, fc.id
ORDER BY d.nome, fc.ordem, fc.consumo_min;