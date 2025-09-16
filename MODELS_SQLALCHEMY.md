# Models SQLAlchemy - Sistema Sinergia

Este documento descreve os models SQLAlchemy criados para o sistema de simulação de descontos de energia solar.

## Estrutura dos Models

### 1. Estado
```python
class Estado(Base):
    id = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False, unique=True)
    sigla = Column(String(2), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.current_timestamp())
```

### 2. Distribuidora
```python
class Distribuidora(Base):
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    estado_id = Column(Integer, ForeignKey('estados.id'))
    consumo_minimo = Column(Integer, nullable=False)  # em kWh
    forma_pagamento = Column(String(50), nullable=False)
    prazo_injecao = Column(Integer, nullable=False)  # em dias
    troca_titularidade = Column(Boolean, default=False)
    # ... outros campos
```

### 3. TipoBonus
```python
class TipoBonus(Base):
    id = Column(Integer, primary_key=True)
    codigo = Column(String(10), nullable=False, unique=True)  # 'A', 'B', 'C', 'D'
    nome = Column(String(50), nullable=False)
    descricao = Column(Text)
    cor_hex = Column(String(7))  # para exibição visual
```

### 4. FaixaConsumo
```python
class FaixaConsumo(Base):
    id = Column(Integer, primary_key=True)
    distribuidora_id = Column(Integer, ForeignKey('distribuidoras.id'))
    consumo_min = Column(Integer, nullable=False)
    consumo_max = Column(Integer)  # NULL = sem limite
    nome_faixa = Column(String(100))
    ordem = Column(Integer, default=1)
```

### 5. RegraDesconto
```python
class RegraDesconto(Base):
    id = Column(Integer, primary_key=True)
    faixa_consumo_id = Column(Integer, ForeignKey('faixas_consumo.id'))
    tipo_bonus_id = Column(Integer, ForeignKey('tipos_bonus.id'))
    desconto_percentual = Column(DECIMAL(5, 2), nullable=False)
    desconto_opcional_1 = Column(DECIMAL(5, 2))  # para múltiplas opções
    desconto_opcional_2 = Column(DECIMAL(5, 2))
    # ... outros campos opcionais
```

### 6. Simulacao
```python
class Simulacao(Base):
    id = Column(Integer, primary_key=True)
    distribuidora_id = Column(Integer, ForeignKey('distribuidoras.id'))
    faixa_consumo_id = Column(Integer, ForeignKey('faixas_consumo.id'))
    tipo_bonus_id = Column(Integer, ForeignKey('tipos_bonus.id'))
    consumo_kwh = Column(Integer, nullable=False)
    desconto_aplicado = Column(DECIMAL(5, 2), nullable=False)
    valor_economia = Column(DECIMAL(10, 2))
```

## Relacionamentos

Todos os models possuem relacionamentos bidirecionais configurados:

- **Estado** ↔ **Distribuidora** (1:N)
- **Distribuidora** ↔ **FaixaConsumo** (1:N)
- **FaixaConsumo** ↔ **RegraDesconto** (1:N)
- **TipoBonus** ↔ **RegraDesconto** (1:N)
- **Distribuidora** ↔ **Simulacao** (1:N)
- **FaixaConsumo** ↔ **Simulacao** (1:N)
- **TipoBonus** ↔ **Simulacao** (1:N)

## Configuração e Uso

### 1. Instalação das Dependências
```bash
pip install sqlalchemy
```

### 2. Configuração Básica
```python
from database.db_config import init_database, DatabaseSession
from models import *

# Inicializar o banco
db = init_database('database/sinergia.db', echo=True)
```

### 3. Usando Context Manager (Recomendado)
```python
with DatabaseSession() as session:
    # Suas operações aqui
    distribuidoras = session.query(Distribuidora).all()
    # Commit automático no final
```

### 4. Consultas Básicas

#### Buscar distribuidoras ativas
```python
with DatabaseSession() as session:
    distribuidoras = session.query(Distribuidora).filter(
        Distribuidora.ativo == True
    ).all()
```

#### Buscar por estado
```python
with DatabaseSession() as session:
    distribuidoras_mg = session.query(Distribuidora).join(Estado).filter(
        Estado.sigla == 'MG'
    ).all()
```

#### Buscar regras de desconto com relacionamentos
```python
from sqlalchemy.orm import joinedload

with DatabaseSession() as session:
    regras = session.query(RegraDesconto).options(
        joinedload(RegraDesconto.faixa_consumo).joinedload(FaixaConsumo.distribuidora),
        joinedload(RegraDesconto.tipo_bonus)
    ).filter(RegraDesconto.ativo == True).all()
```

### 5. Buscar Regras por Consumo
```python
from sqlalchemy import and_, or_

def buscar_regras_por_consumo(consumo_kwh):
    with DatabaseSession() as session:
        faixas_validas = session.query(FaixaConsumo).filter(
            and_(
                FaixaConsumo.consumo_min <= consumo_kwh,
                or_(
                    FaixaConsumo.consumo_max >= consumo_kwh,
                    FaixaConsumo.consumo_max.is_(None)
                ),
                FaixaConsumo.ativo == True
            )
        ).options(
            joinedload(FaixaConsumo.distribuidora),
            joinedload(FaixaConsumo.regras_desconto).joinedload(RegraDesconto.tipo_bonus)
        ).all()
        
        return faixas_validas
```

### 6. Criar Nova Simulação
```python
def criar_simulacao(distribuidora_id, consumo_kwh, desconto_aplicado, valor_economia):
    with DatabaseSession() as session:
        # Buscar faixa de consumo apropriada
        faixa = session.query(FaixaConsumo).filter(
            and_(
                FaixaConsumo.distribuidora_id == distribuidora_id,
                FaixaConsumo.consumo_min <= consumo_kwh,
                or_(
                    FaixaConsumo.consumo_max >= consumo_kwh,
                    FaixaConsumo.consumo_max.is_(None)
                )
            )
        ).first()
        
        if faixa:
            simulacao = Simulacao(
                distribuidora_id=distribuidora_id,
                faixa_consumo_id=faixa.id,
                consumo_kwh=consumo_kwh,
                desconto_aplicado=desconto_aplicado,
                valor_economia=valor_economia
            )
            session.add(simulacao)
            # Commit automático pelo context manager
            return simulacao.id
        
        return None
```

### 7. Consultas Estatísticas
```python
from sqlalchemy import func

def estatisticas_por_estado():
    with DatabaseSession() as session:
        stats = session.query(
            Estado.sigla,
            Estado.nome,
            func.count(Distribuidora.id).label('total_distribuidoras')
        ).join(Distribuidora).filter(
            Distribuidora.ativo == True
        ).group_by(Estado.id).all()
        
        return [(s.sigla, s.nome, s.total_distribuidoras) for s in stats]
```

## Arquivos Criados

1. **`models.py`** - Definições dos models SQLAlchemy
2. **`database/db_config.py`** - Configuração do banco de dados
3. **`database/models_examples.py`** - Exemplos práticos de uso
4. **`database/schema_nova_estrutura.sql`** - Schema SQL da nova estrutura
5. **`database/populate_nova_estrutura.sql`** - Script para popular o banco

## Vantagens da Nova Estrutura

### 1. **Flexibilidade**
- Suporte a múltiplas faixas de consumo por distribuidora
- Múltiplos tipos de bônus por faixa
- Descontos opcionais (ex: "16% ou 20%")

### 2. **Escalabilidade**
- Fácil adição de novos tipos de bônus
- Estrutura preparada para crescimento
- Índices otimizados para performance

### 3. **Manutenibilidade**
- Relacionamentos claros e bem definidos
- Soft deletes (campo `ativo`)
- Timestamps automáticos

### 4. **Consultas Eficientes**
- Eager loading com `joinedload()`
- Índices estratégicos
- Views pré-definidas no banco

## Migração da Estrutura Antiga

Para migrar da estrutura antiga, execute:

```bash
python migrate_to_new_structure.py
```

Este script:
1. Faz backup do banco atual
2. Cria a nova estrutura
3. Migra os dados existentes
4. Gera novo JSON com a estrutura atualizada

## Próximos Passos

1. **Testar os models** com dados reais
2. **Executar a migração** quando aprovada
3. **Atualizar a API** para usar os novos models
4. **Atualizar o frontend** para consumir a nova estrutura JSON
5. **Implementar testes unitários** para os models

## Exemplo Completo de Uso

```python
# Exemplo completo: buscar melhores descontos para um consumo
def encontrar_melhores_descontos(consumo_kwh, estado_sigla=None):
    with DatabaseSession() as session:
        query = session.query(RegraDesconto).join(
            FaixaConsumo
        ).join(
            Distribuidora
        ).join(
            Estado
        ).join(
            TipoBonus
        ).filter(
            and_(
                FaixaConsumo.consumo_min <= consumo_kwh,
                or_(
                    FaixaConsumo.consumo_max >= consumo_kwh,
                    FaixaConsumo.consumo_max.is_(None)
                ),
                RegraDesconto.ativo == True,
                FaixaConsumo.ativo == True,
                Distribuidora.ativo == True
            )
        )
        
        if estado_sigla:
            query = query.filter(Estado.sigla == estado_sigla)
        
        regras = query.order_by(
            RegraDesconto.desconto_percentual.desc()
        ).all()
        
        resultados = []
        for regra in regras:
            resultados.append({
                'distribuidora': regra.faixa_consumo.distribuidora.nome,
                'estado': regra.faixa_consumo.distribuidora.estado.sigla,
                'faixa': regra.faixa_consumo.nome_faixa,
                'bonus': regra.tipo_bonus.codigo,
                'desconto': float(regra.desconto_percentual),
                'desconto_opcional': float(regra.desconto_opcional_1) if regra.desconto_opcional_1 else None,
                'analise_credito': regra.analise_credito
            })
        
        return resultados

# Uso
melhores_descontos = encontrar_melhores_descontos(2500, 'MG')
for desconto in melhores_descontos[:5]:  # Top 5
    print(f"{desconto['distribuidora']} - Bônus {desconto['bonus']}: {desconto['desconto']}%")
```

Esta estrutura resolve completamente o problema da CELESC e outras distribuidoras, permitindo uma modelagem muito mais rica e flexível dos dados de desconto.