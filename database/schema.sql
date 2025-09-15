-- Estrutura do banco de dados para sistema de simulação de descontos
-- Criado para gerenciar regras de distribuidoras por estado

-- Tabela de Estados
CREATE TABLE IF NOT EXISTS estados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL UNIQUE,
    sigla VARCHAR(2) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Distribuidoras
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estado_id) REFERENCES estados(id)
);

-- Tabela de Regras de Desconto
CREATE TABLE IF NOT EXISTS regras_desconto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distribuidora_id INTEGER NOT NULL,
    consumo_min INTEGER NOT NULL, -- faixa mínima de consumo em kWh
    consumo_max INTEGER, -- faixa máxima de consumo em kWh (NULL = sem limite)
    desconto_percentual DECIMAL(5,2) NOT NULL,
    tipo_bonus VARCHAR(10) NOT NULL, -- 'A', 'B', 'C', 'D'
    descricao VARCHAR(200),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (distribuidora_id) REFERENCES distribuidoras(id)
);

-- Tabela de Simulações (para histórico)
CREATE TABLE IF NOT EXISTS simulacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distribuidora_id INTEGER NOT NULL,
    consumo_kwh INTEGER NOT NULL,
    desconto_aplicado DECIMAL(5,2) NOT NULL,
    valor_economia DECIMAL(10,2),
    tipo_bonus VARCHAR(10),
    ip_usuario VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (distribuidora_id) REFERENCES distribuidoras(id)
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_distribuidoras_estado ON distribuidoras(estado_id);
CREATE INDEX IF NOT EXISTS idx_regras_distribuidora ON regras_desconto(distribuidora_id);
CREATE INDEX IF NOT EXISTS idx_regras_consumo ON regras_desconto(consumo_min, consumo_max);
CREATE INDEX IF NOT EXISTS idx_simulacoes_distribuidora ON simulacoes(distribuidora_id);
CREATE INDEX IF NOT EXISTS idx_simulacoes_data ON simulacoes(created_at);