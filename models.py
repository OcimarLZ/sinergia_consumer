from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Estado(Base):
    """Model para tabela de estados"""
    __tablename__ = 'estados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False, unique=True)
    sigla = Column(String(2), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relacionamentos
    distribuidoras = relationship("Distribuidora", back_populates="estado")
    
    def __repr__(self):
        return f"<Estado(id={self.id}, nome='{self.nome}', sigla='{self.sigla}')>"

class Distribuidora(Base):
    """Model para tabela de distribuidoras"""
    __tablename__ = 'distribuidoras'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    estado_id = Column(Integer, ForeignKey('estados.id'), nullable=False)
    consumo_minimo = Column(Integer, nullable=False)  # em kWh
    forma_pagamento = Column(String(50), nullable=False)  # 'Unificado', 'Dois Boletos'
    prazo_injecao = Column(Integer, nullable=False)  # em dias
    troca_titularidade = Column(Boolean, default=False)
    login_senha_necessario = Column(Boolean, default=False)
    aceita_placas = Column(Boolean, default=True)
    icms_minimo = Column(DECIMAL(5, 2), default=17.00)
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relacionamentos
    estado = relationship("Estado", back_populates="distribuidoras")
    faixas_consumo = relationship("FaixaConsumo", back_populates="distribuidora")
    simulacoes = relationship("Simulacao", back_populates="distribuidora")
    
    def __repr__(self):
        return f"<Distribuidora(id={self.id}, nome='{self.nome}', estado_id={self.estado_id})>"

class TipoBonus(Base):
    """Model para tabela de tipos de bônus"""
    __tablename__ = 'tipos_bonus'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(10), nullable=False, unique=True)  # 'A', 'B', 'C', 'D'
    nome = Column(String(50), nullable=False)  # 'Bônus A', 'Bônus B', etc.
    descricao = Column(Text)
    cor_hex = Column(String(7))  # para exibição visual (#FF0000, etc.)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relacionamentos
    regras_desconto = relationship("RegraDesconto", back_populates="tipo_bonus")
    simulacoes = relationship("Simulacao", back_populates="tipo_bonus")
    
    def __repr__(self):
        return f"<TipoBonus(id={self.id}, codigo='{self.codigo}', nome='{self.nome}')>"

class FaixaConsumo(Base):
    """Model para tabela de faixas de consumo por distribuidora"""
    __tablename__ = 'faixas_consumo'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    distribuidora_id = Column(Integer, ForeignKey('distribuidoras.id'), nullable=False)
    consumo_min = Column(Integer, nullable=False)  # kWh mínimo da faixa
    consumo_max = Column(Integer)  # kWh máximo da faixa (NULL = sem limite)
    nome_faixa = Column(String(100))  # ex: "100 kWh", "1.000 a 5.000 kWh"
    ordem = Column(Integer, default=1)  # para ordenação das faixas
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relacionamentos
    distribuidora = relationship("Distribuidora", back_populates="faixas_consumo")
    regras_desconto = relationship("RegraDesconto", back_populates="faixa_consumo")
    simulacoes = relationship("Simulacao", back_populates="faixa_consumo")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('distribuidora_id', 'consumo_min', 'consumo_max', name='uq_faixa_consumo'),
    )
    
    def __repr__(self):
        return f"<FaixaConsumo(id={self.id}, distribuidora_id={self.distribuidora_id}, consumo_min={self.consumo_min}, consumo_max={self.consumo_max})>"

class RegraDesconto(Base):
    """Model para tabela de regras de desconto (relaciona faixas com bônus)"""
    __tablename__ = 'regras_desconto'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    faixa_consumo_id = Column(Integer, ForeignKey('faixas_consumo.id'), nullable=False)
    tipo_bonus_id = Column(Integer, ForeignKey('tipos_bonus.id'), nullable=False)
    desconto_percentual = Column(DECIMAL(5, 2), nullable=False)
    desconto_opcional_1 = Column(DECIMAL(5, 2))  # para casos como "16% ou 20%"
    desconto_opcional_2 = Column(DECIMAL(5, 2))
    desconto_opcional_3 = Column(DECIMAL(5, 2))
    desconto_opcional_4 = Column(DECIMAL(5, 2))
    analise_credito = Column(Boolean, default=False)  # se requer análise de crédito
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relacionamentos
    faixa_consumo = relationship("FaixaConsumo", back_populates="regras_desconto")
    tipo_bonus = relationship("TipoBonus", back_populates="regras_desconto")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('faixa_consumo_id', 'tipo_bonus_id', name='uq_regra_desconto'),
    )
    
    def __repr__(self):
        return f"<RegraDesconto(id={self.id}, faixa_consumo_id={self.faixa_consumo_id}, tipo_bonus_id={self.tipo_bonus_id}, desconto_percentual={self.desconto_percentual})>"

class Simulacao(Base):
    """Model para tabela de simulações (melhorada)"""
    __tablename__ = 'simulacoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    distribuidora_id = Column(Integer, ForeignKey('distribuidoras.id'), nullable=False)
    faixa_consumo_id = Column(Integer, ForeignKey('faixas_consumo.id'))
    tipo_bonus_id = Column(Integer, ForeignKey('tipos_bonus.id'))
    consumo_kwh = Column(Integer, nullable=False)
    desconto_aplicado = Column(DECIMAL(5, 2), nullable=False)
    valor_economia = Column(DECIMAL(10, 2))
    ip_usuario = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relacionamentos
    distribuidora = relationship("Distribuidora", back_populates="simulacoes")
    faixa_consumo = relationship("FaixaConsumo", back_populates="simulacoes")
    tipo_bonus = relationship("TipoBonus", back_populates="simulacoes")
    
    def __repr__(self):
        return f"<Simulacao(id={self.id}, distribuidora_id={self.distribuidora_id}, consumo_kwh={self.consumo_kwh}, desconto_aplicado={self.desconto_aplicado})>"

# Índices adicionais (SQLAlchemy criará automaticamente os índices de FK)
# Os índices definidos no schema SQL serão criados pelo próprio banco

# Exemplo de uso dos models:
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Exemplo de configuração do banco
    engine = create_engine('sqlite:///database/sinergia.db', echo=True)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Exemplo de consulta usando os relacionamentos
    # distribuidoras_com_regras = session.query(Distribuidora).join(FaixaConsumo).join(RegraDesconto).all()
    # print(f"Encontradas {len(distribuidoras_com_regras)} distribuidoras com regras")
    
    session.close()