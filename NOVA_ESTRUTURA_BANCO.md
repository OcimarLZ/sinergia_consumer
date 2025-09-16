# Nova Estrutura do Banco de Dados - Sistema Sinergia

## Análise do Problema Atual

A estrutura atual do banco é muito simplificada e não consegue representar adequadamente a complexidade real das regras das distribuidoras, como evidenciado pela tabela da CEMIG que você compartilhou.

### Limitações da Estrutura Atual:
1. **Uma regra por linha**: Cada combinação distribuidora + faixa + bônus precisa de uma linha separada
2. **Redundância**: Informações da distribuidora se repetem para cada regra
3. **Inflexibilidade**: Não suporta múltiplos descontos opcionais por bônus
4. **Falta de organização**: Não há separação clara entre faixas de consumo e tipos de bônus

## Nova Estrutura Proposta

### 1. Tabela `tipos_bonus`
```sql
CREATE TABLE tipos_bonus (
    id INTEGER PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE,  -- 'A', 'B', 'C', 'D'
    nome VARCHAR(50),           -- 'Bônus A', 'Bônus B'
    descricao TEXT,
    cor_hex VARCHAR(7),         -- Para UI (#FF0000)
    ativo BOOLEAN
);
```

**Vantagens:**
- Centraliza informações dos tipos de bônus
- Facilita manutenção (mudou nome do Bônus A? Muda em um lugar só)
- Permite adicionar novos tipos facilmente
- Suporte a cores para interface visual

### 2. Tabela `faixas_consumo`
```sql
CREATE TABLE faixas_consumo (
    id INTEGER PRIMARY KEY,
    distribuidora_id INTEGER,
    consumo_min INTEGER,
    consumo_max INTEGER,
    nome_faixa VARCHAR(100),    -- "100 kWh", "1.000 a 5.000 kWh"
    ordem INTEGER,              -- Para ordenação
    ativo BOOLEAN
);
```

**Vantagens:**
- Define claramente as faixas de cada distribuidora
- Permite nomes descritivos para as faixas
- Suporte a ordenação customizada
- Facilita validação de sobreposições

### 3. Tabela `regras_desconto` (reformulada)
```sql
CREATE TABLE regras_desconto (
    id INTEGER PRIMARY KEY,
    faixa_consumo_id INTEGER,
    tipo_bonus_id INTEGER,
    desconto_percentual DECIMAL(5,2),
    desconto_opcional_1 DECIMAL(5,2),  -- Para casos "16% ou 20%"
    desconto_opcional_2 DECIMAL(5,2),
    desconto_opcional_3 DECIMAL(5,2),
    desconto_opcional_4 DECIMAL(5,2),
    analise_credito BOOLEAN,
    observacoes TEXT
);
```

**Vantagens:**
- Suporte a múltiplos descontos opcionais
- Relacionamento claro entre faixa e bônus
- Campo específico para análise de crédito
- Elimina redundância

## Exemplo Prático: CEMIG

Baseado na imagem que você compartilhou:

### Dados na Nova Estrutura:

**tipos_bonus:**
```
ID | Codigo | Nome     | Cor
1  | A      | Bônus A  | #FF6B6B
2  | B      | Bônus B  | #4ECDC4
3  | C      | Bônus C  | #45B7D1
4  | D      | Bônus D  | #96CEB4
```

**faixas_consumo (CEMIG):**
```
ID | Distribuidora | Min   | Max   | Nome Faixa
1  | CEMIG        | 100   | 100   | 100 kWh
2  | CEMIG        | 1000  | 5000  | 1.000 a 5.000 kWh
3  | CEMIG        | 5001  | 10000 | 5.001 a 10.000 kWh
4  | CEMIG        | 10001 | NULL  | Acima de 10.000 kWh
```

**regras_desconto:**
```
Faixa | Bônus | Principal | Opcional1 | Opcional2 | Análise
1     | A     | 10%       | -         | -         | Não
1     | B     | 16%       | -         | -         | Não
2     | A     | 10%       | -         | -         | Não
2     | B     | 16%       | 20%       | -         | Não
3     | A     | 12%       | -         | -         | Não
3     | B     | 16%       | 20%       | -         | Não
3     | C     | 24%       | -         | -         | Não
4     | A     | 10%       | -         | -         | Sim
4     | B     | 16%       | 20%       | -         | Não
4     | C     | 24%       | -         | -         | Não
4     | D     | 28%       | -         | -         | Não
```

## Vantagens da Nova Estrutura

### 1. **Flexibilidade**
- Suporte a múltiplos descontos por bônus
- Fácil adição de novos tipos de bônus
- Faixas de consumo customizáveis por distribuidora

### 2. **Manutenibilidade**
- Menos redundância de dados
- Mudanças centralizadas
- Estrutura mais organizada

### 3. **Escalabilidade**
- Suporte a regras complexas
- Preparado para futuras funcionalidades
- Performance otimizada com índices adequados

### 4. **Consultas Mais Ricas**
- View `vw_regras_completas` para consultas complexas
- Facilita relatórios e análises
- JSON mais estruturado e informativo

## Processo de Migração

1. **Backup**: Cópia de segurança do banco atual
2. **Criação**: Nova estrutura no mesmo banco
3. **Migração**: Dados existentes para nova estrutura
4. **Validação**: Verificação da integridade
5. **JSON**: Geração do novo formato

## Novo Formato JSON

```json
{
  "metadata": {
    "versao": "2.0",
    "estrutura": "nova_arquitetura",
    "total_regras": 45
  },
  "regras": [
    {
      "id": 1,
      "distribuidora": {
        "id": 19,
        "nome": "CEMIG",
        "estado": {"nome": "Minas Gerais", "sigla": "MG"}
      },
      "faixa_consumo": {
        "id": 1,
        "nome": "100 kWh",
        "consumo_min": 100,
        "consumo_max": 100
      },
      "bonus": {
        "id": 1,
        "codigo": "A",
        "nome": "Bônus A"
      },
      "descontos": {
        "principal": 10.0,
        "opcional_1": null,
        "opcional_2": null
      },
      "analise_credito": false
    }
  ]
}
```

## Próximos Passos

1. **Revisar** esta proposta
2. **Executar** o script de migração se aprovado
3. **Testar** a nova estrutura
4. **Atualizar** o frontend para usar o novo JSON
5. **Documentar** as mudanças

---

**Arquivos Criados:**
- `schema_nova_estrutura.sql` - Definição das tabelas
- `populate_nova_estrutura.sql` - Dados de exemplo
- `migrate_to_new_structure.py` - Script de migração
- Este documento explicativo

**Quer prosseguir com a migração?**