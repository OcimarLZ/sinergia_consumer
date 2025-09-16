"""Exemplos práticos de uso dos models SQLAlchemy"""

from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker, joinedload
from models import Base, Estado, Distribuidora, TipoBonus, FaixaConsumo, RegraDesconto, Simulacao
from decimal import Decimal

def setup_database(db_path='database/sinergia.db'):
    """Configura a conexão com o banco de dados"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def exemplo_consultas_basicas():
    """Exemplos de consultas básicas"""
    session = setup_database()
    
    try:
        print("=== CONSULTAS BÁSICAS ===")
        
        # 1. Buscar todas as distribuidoras ativas
        distribuidoras_ativas = session.query(Distribuidora).filter(Distribuidora.ativo == True).all()
        print(f"Distribuidoras ativas: {len(distribuidoras_ativas)}")
        
        # 2. Buscar distribuidoras por estado
        distribuidoras_mg = session.query(Distribuidora).join(Estado).filter(Estado.sigla == 'MG').all()
        print(f"Distribuidoras em MG: {len(distribuidoras_mg)}")
        
        # 3. Buscar tipos de bônus disponíveis
        tipos_bonus = session.query(TipoBonus).filter(TipoBonus.ativo == True).all()
        print(f"Tipos de bônus disponíveis: {[tb.codigo for tb in tipos_bonus]}")
        
        # 4. Buscar faixas de consumo de uma distribuidora específica
        cemig = session.query(Distribuidora).filter(Distribuidora.nome.like('%CEMIG%')).first()
        if cemig:
            faixas = session.query(FaixaConsumo).filter(
                and_(FaixaConsumo.distribuidora_id == cemig.id, FaixaConsumo.ativo == True)
            ).order_by(FaixaConsumo.ordem, FaixaConsumo.consumo_min).all()
            print(f"Faixas de consumo CEMIG: {len(faixas)}")
            for faixa in faixas:
                print(f"  - {faixa.nome_faixa}: {faixa.consumo_min} a {faixa.consumo_max or 'sem limite'} kWh")
        
    finally:
        session.close()

def exemplo_consultas_com_relacionamentos():
    """Exemplos de consultas usando relacionamentos"""
    session = setup_database()
    
    try:
        print("\n=== CONSULTAS COM RELACIONAMENTOS ===")
        
        # 1. Buscar regras de desconto com todas as informações relacionadas
        regras_completas = session.query(RegraDesconto).options(
            joinedload(RegraDesconto.faixa_consumo).joinedload(FaixaConsumo.distribuidora).joinedload(Distribuidora.estado),
            joinedload(RegraDesconto.tipo_bonus)
        ).filter(RegraDesconto.ativo == True).limit(5).all()
        
        print(f"Primeiras 5 regras de desconto:")
        for regra in regras_completas:
            print(f"  - {regra.faixa_consumo.distribuidora.nome} ({regra.faixa_consumo.distribuidora.estado.sigla})")
            print(f"    Faixa: {regra.faixa_consumo.nome_faixa}")
            print(f"    Bônus {regra.tipo_bonus.codigo}: {regra.desconto_percentual}%")
            if regra.desconto_opcional_1:
                print(f"    Opcional: {regra.desconto_opcional_1}%")
            print()
        
        # 2. Buscar distribuidoras com suas faixas e regras
        distribuidora_com_regras = session.query(Distribuidora).options(
            joinedload(Distribuidora.faixas_consumo).joinedload(FaixaConsumo.regras_desconto).joinedload(RegraDesconto.tipo_bonus)
        ).filter(Distribuidora.nome.like('%CEMIG%')).first()
        
        if distribuidora_com_regras:
            print(f"Regras da {distribuidora_com_regras.nome}:")
            for faixa in distribuidora_com_regras.faixas_consumo:
                if faixa.ativo:
                    print(f"  Faixa: {faixa.nome_faixa}")
                    for regra in faixa.regras_desconto:
                        if regra.ativo:
                            print(f"    Bônus {regra.tipo_bonus.codigo}: {regra.desconto_percentual}%")
        
    finally:
        session.close()

def exemplo_busca_por_consumo():
    """Exemplo de busca de regras por consumo específico"""
    session = setup_database()
    
    try:
        print("\n=== BUSCA POR CONSUMO ===")
        
        consumo_teste = 2500  # kWh
        
        # Buscar faixas que atendem o consumo
        faixas_validas = session.query(FaixaConsumo).filter(
            and_(
                FaixaConsumo.consumo_min <= consumo_teste,
                or_(
                    FaixaConsumo.consumo_max >= consumo_teste,
                    FaixaConsumo.consumo_max.is_(None)
                ),
                FaixaConsumo.ativo == True
            )
        ).options(
            joinedload(FaixaConsumo.distribuidora).joinedload(Distribuidora.estado),
            joinedload(FaixaConsumo.regras_desconto).joinedload(RegraDesconto.tipo_bonus)
        ).all()
        
        print(f"Faixas válidas para consumo de {consumo_teste} kWh:")
        for faixa in faixas_validas:
            print(f"\n{faixa.distribuidora.nome} ({faixa.distribuidora.estado.sigla})")
            print(f"  Faixa: {faixa.nome_faixa}")
            print(f"  Regras disponíveis:")
            for regra in faixa.regras_desconto:
                if regra.ativo:
                    descontos = [str(regra.desconto_percentual)]
                    if regra.desconto_opcional_1:
                        descontos.append(str(regra.desconto_opcional_1))
                    if regra.desconto_opcional_2:
                        descontos.append(str(regra.desconto_opcional_2))
                    print(f"    Bônus {regra.tipo_bonus.codigo}: {' ou '.join(descontos)}%")
                    if regra.analise_credito:
                        print(f"      (Requer análise de crédito)")
        
    finally:
        session.close()

def exemplo_operacoes_crud():
    """Exemplos de operações CRUD (Create, Read, Update, Delete)"""
    session = setup_database()
    
    try:
        print("\n=== OPERAÇÕES CRUD ===")
        
        # CREATE - Criar um novo tipo de bônus
        novo_bonus = TipoBonus(
            codigo='E',
            nome='Bônus E',
            descricao='Bônus especial para testes',
            cor_hex='#00FF00',
            ativo=True
        )
        session.add(novo_bonus)
        session.commit()
        print(f"Criado novo bônus: {novo_bonus.codigo}")
        
        # READ - Ler o bônus criado
        bonus_criado = session.query(TipoBonus).filter(TipoBonus.codigo == 'E').first()
        if bonus_criado:
            print(f"Bônus encontrado: {bonus_criado.nome}")
        
        # UPDATE - Atualizar a descrição
        if bonus_criado:
            bonus_criado.descricao = 'Bônus especial atualizado'
            session.commit()
            print(f"Descrição atualizada: {bonus_criado.descricao}")
        
        # DELETE - Desativar o bônus (soft delete)
        if bonus_criado:
            bonus_criado.ativo = False
            session.commit()
            print(f"Bônus {bonus_criado.codigo} desativado")
        
        # Verificar se ainda aparece nas consultas de ativos
        bonus_ativo = session.query(TipoBonus).filter(
            and_(TipoBonus.codigo == 'E', TipoBonus.ativo == True)
        ).first()
        print(f"Bônus E ainda ativo: {bonus_ativo is not None}")
        
    finally:
        session.close()

def exemplo_simulacao():
    """Exemplo de criação de simulação"""
    session = setup_database()
    
    try:
        print("\n=== EXEMPLO DE SIMULAÇÃO ===")
        
        # Buscar uma distribuidora e regra para simular
        cemig = session.query(Distribuidora).filter(Distribuidora.nome.like('%CEMIG%')).first()
        if cemig:
            # Buscar uma faixa de consumo
            faixa = session.query(FaixaConsumo).filter(
                and_(
                    FaixaConsumo.distribuidora_id == cemig.id,
                    FaixaConsumo.ativo == True
                )
            ).first()
            
            if faixa:
                # Buscar uma regra para essa faixa
                regra = session.query(RegraDesconto).filter(
                    and_(
                        RegraDesconto.faixa_consumo_id == faixa.id,
                        RegraDesconto.ativo == True
                    )
                ).first()
                
                if regra:
                    # Criar simulação
                    simulacao = Simulacao(
                        distribuidora_id=cemig.id,
                        faixa_consumo_id=faixa.id,
                        tipo_bonus_id=regra.tipo_bonus_id,
                        consumo_kwh=2000,
                        desconto_aplicado=regra.desconto_percentual,
                        valor_economia=Decimal('150.00'),
                        ip_usuario='192.168.1.1',
                        user_agent='Test User Agent'
                    )
                    session.add(simulacao)
                    session.commit()
                    
                    print(f"Simulação criada:")
                    print(f"  Distribuidora: {cemig.nome}")
                    print(f"  Consumo: {simulacao.consumo_kwh} kWh")
                    print(f"  Desconto: {simulacao.desconto_aplicado}%")
                    print(f"  Economia: R$ {simulacao.valor_economia}")
        
    finally:
        session.close()

def exemplo_estatisticas():
    """Exemplos de consultas estatísticas"""
    session = setup_database()
    
    try:
        print("\n=== ESTATÍSTICAS ===")
        
        # Contar distribuidoras por estado
        from sqlalchemy import func
        
        stats_por_estado = session.query(
            Estado.sigla,
            Estado.nome,
            func.count(Distribuidora.id).label('total_distribuidoras')
        ).join(Distribuidora).filter(Distribuidora.ativo == True).group_by(Estado.id).all()
        
        print("Distribuidoras por estado:")
        for stat in stats_por_estado:
            print(f"  {stat.sigla} ({stat.nome}): {stat.total_distribuidoras}")
        
        # Contar regras por tipo de bônus
        stats_bonus = session.query(
            TipoBonus.codigo,
            TipoBonus.nome,
            func.count(RegraDesconto.id).label('total_regras')
        ).join(RegraDesconto).filter(
            and_(TipoBonus.ativo == True, RegraDesconto.ativo == True)
        ).group_by(TipoBonus.id).all()
        
        print("\nRegras por tipo de bônus:")
        for stat in stats_bonus:
            print(f"  Bônus {stat.codigo} ({stat.nome}): {stat.total_regras} regras")
        
        # Média de desconto por tipo de bônus
        media_descontos = session.query(
            TipoBonus.codigo,
            func.avg(RegraDesconto.desconto_percentual).label('media_desconto'),
            func.min(RegraDesconto.desconto_percentual).label('min_desconto'),
            func.max(RegraDesconto.desconto_percentual).label('max_desconto')
        ).join(RegraDesconto).filter(
            and_(TipoBonus.ativo == True, RegraDesconto.ativo == True)
        ).group_by(TipoBonus.id).all()
        
        print("\nEstatísticas de desconto por bônus:")
        for stat in media_descontos:
            print(f"  Bônus {stat.codigo}:")
            print(f"    Média: {float(stat.media_desconto):.2f}%")
            print(f"    Mín: {float(stat.min_desconto):.2f}%")
            print(f"    Máx: {float(stat.max_desconto):.2f}%")
        
    finally:
        session.close()

if __name__ == "__main__":
    print("Executando exemplos de uso dos models SQLAlchemy...\n")
    
    exemplo_consultas_basicas()
    exemplo_consultas_com_relacionamentos()
    exemplo_busca_por_consumo()
    exemplo_operacoes_crud()
    exemplo_simulacao()
    exemplo_estatisticas()
    
    print("\n=== EXEMPLOS CONCLUÍDOS ===")