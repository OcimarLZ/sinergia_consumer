-- Script para popular a nova estrutura com dados de exemplo
-- Baseado na análise da imagem da CEMIG fornecida

-- Inserir tipos de bônus
INSERT OR IGNORE INTO tipos_bonus (codigo, nome, descricao, cor_hex) VALUES
('A', 'Bônus A', 'Bônus básico com menor desconto', '#FF6B6B'),
('B', 'Bônus B', 'Bônus intermediário', '#4ECDC4'),
('C', 'Bônus C', 'Bônus avançado', '#45B7D1'),
('D', 'Bônus D', 'Bônus premium com maior desconto', '#96CEB4'),
('X', 'Não Disponível', 'Bônus não disponível para esta faixa', '#95A5A6');

-- Exemplo: CEMIG (assumindo que já existe na tabela distribuidoras)
-- Inserir faixas de consumo para CEMIG
INSERT OR IGNORE INTO faixas_consumo (distribuidora_id, consumo_min, consumo_max, nome_faixa, ordem) VALUES
-- Assumindo CEMIG tem ID 19 (baseado no resultado anterior)
(19, 100, 100, '100 kWh', 1),
(19, 1000, 5000, '1.000 a 5.000 kWh', 2),
(19, 5001, 10000, '5.001 a 10.000 kWh', 3),
(19, 10001, NULL, 'Acima de 10.000 kWh', 4);

-- Inserir regras de desconto para CEMIG baseadas na imagem
-- Faixa 1: 100 kWh
INSERT OR IGNORE INTO regras_desconto (faixa_consumo_id, tipo_bonus_id, desconto_percentual, analise_credito) VALUES
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 100), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'A'), 10.0, FALSE),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 100), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'B'), 16.0, FALSE);

-- Faixa 2: 1.000 a 5.000 kWh
INSERT OR IGNORE INTO regras_desconto (faixa_consumo_id, tipo_bonus_id, desconto_percentual, desconto_opcional_1, analise_credito) VALUES
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 1000), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'A'), 10.0, NULL, FALSE),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 1000), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'B'), 16.0, 20.0, FALSE);

-- Faixa 3: 5.001 a 10.000 kWh
INSERT OR IGNORE INTO regras_desconto (faixa_consumo_id, tipo_bonus_id, desconto_percentual, desconto_opcional_1, desconto_opcional_2, analise_credito) VALUES
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 5001), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'A'), 12.0, NULL, NULL, FALSE),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 5001), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'B'), 16.0, 20.0, NULL, FALSE),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 5001), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'C'), 24.0, NULL, NULL, FALSE);

-- Faixa 4: Acima de 10.000 kWh
INSERT OR IGNORE INTO regras_desconto (faixa_consumo_id, tipo_bonus_id, desconto_percentual, desconto_opcional_1, desconto_opcional_2, desconto_opcional_3, analise_credito) VALUES
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 10001), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'A'), 10.0, NULL, NULL, NULL, TRUE),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 10001), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'B'), 16.0, 20.0, NULL, NULL, FALSE),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 10001), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'C'), 24.0, NULL, NULL, NULL, FALSE),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 19 AND consumo_min = 10001), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'D'), 28.0, NULL, NULL, NULL, FALSE);

-- Exemplo para outras distribuidoras (estrutura similar)
-- CELESC (ID 30)
INSERT OR IGNORE INTO faixas_consumo (distribuidora_id, consumo_min, consumo_max, nome_faixa, ordem) VALUES
(30, 1000, NULL, 'Acima de 1.000 kWh', 1);

INSERT OR IGNORE INTO regras_desconto (faixa_consumo_id, tipo_bonus_id, desconto_percentual, observacoes) VALUES
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 30 AND consumo_min = 1000), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'B'), 15.0, 'Desconto padrão CELESC');

-- Equatorial (ID 11)
INSERT OR IGNORE INTO faixas_consumo (distribuidora_id, consumo_min, consumo_max, nome_faixa, ordem) VALUES
(11, 0, NULL, 'Qualquer consumo', 1);

INSERT OR IGNORE INTO regras_desconto (faixa_consumo_id, tipo_bonus_id, desconto_percentual, observacoes) VALUES
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 11 AND consumo_min = 0), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'B'), 10.0, 'Desconto padrão Equatorial');

-- Coelba (ID 12)
INSERT OR IGNORE INTO faixas_consumo (distribuidora_id, consumo_min, consumo_max, nome_faixa, ordem) VALUES
(12, 0, NULL, 'Qualquer consumo', 1);

INSERT OR IGNORE INTO regras_desconto (faixa_consumo_id, tipo_bonus_id, desconto_percentual, desconto_opcional_1, observacoes) VALUES
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 12 AND consumo_min = 0), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'A'), 8.0, NULL, 'Bônus A padrão'),
((SELECT id FROM faixas_consumo WHERE distribuidora_id = 12 AND consumo_min = 0), 
 (SELECT id FROM tipos_bonus WHERE codigo = 'B'), 10.0, NULL, 'Bônus B opcional');

-- Verificar dados inseridos
SELECT 'Tipos de Bônus inseridos:' as info;
SELECT * FROM tipos_bonus;

SELECT 'Faixas de Consumo inseridas:' as info;
SELECT fc.*, d.nome as distribuidora_nome 
FROM faixas_consumo fc 
JOIN distribuidoras d ON fc.distribuidora_id = d.id;

SELECT 'Regras de Desconto inseridas:' as info;
SELECT * FROM vw_regras_completas LIMIT 10;