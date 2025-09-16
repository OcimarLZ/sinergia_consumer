#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para carregar dados do arquivo regras.json no banco sinergia.db
usando os models SQLAlchemy criados.
"""

import json
import re
from decimal import Decimal
from models import Base, Estado, Distribuidora, TipoBonus, FaixaConsumo, RegraDesconto
from database.db_config import DatabaseSession, init_database
from sqlalchemy import and_

def extrair_consumo_minimo_maximo(kwh_string):
    """
    Extrai valores mínimo e máximo de consumo de strings como:
    - "100 kWh" -> (100, None)
    - "1.000 a 5.000 kWh" -> (1000, 5000)
    - "Acima de 10.000 kWh" -> (10001, None)
    """
    if not kwh_string:
        return None, None
    
    # Remove pontos de milhares e converte para minúsculas
    kwh_clean = kwh_string.replace('.', '').lower()
    
    # Padrão: "X a Y kwh"
    match_range = re.search(r'(\d+)\s*a\s*(\d+)\s*kwh', kwh_clean)
    if match_range:
        min_val = int(match_range.group(1))
        max_val = int(match_range.group(2))
        return min_val, max_val
    
    # Padrão: "acima de X kwh"
    match_above = re.search(r'acima\s+de\s+(\d+)\s*kwh', kwh_clean)
    if match_above:
        min_val = int(match_above.group(1)) + 1  # Acima = valor + 1
        return min_val, None
    
    # Padrão: "X kwh" (apenas mínimo)
    match_single = re.search(r'(\d+)\s*kwh', kwh_clean)
    if match_single:
        min_val = int(match_single.group(1))
        return min_val, None
    
    print(f"Aviso: Não foi possível extrair consumo de '{kwh_string}'")
    return None, None

def extrair_desconto_e_bonus(desconto_string):
    """
    Extrai percentual de desconto e código do bônus de strings como:
    - "10% Bônus A" -> (10.0, 'A')
    - "16% Bônus B" -> (16.0, 'B')
    """
    if not desconto_string:
        return None, None
    
    # Padrão: "X% Bônus Y"
    match = re.search(r'(\d+(?:\.\d+)?)%\s*bônus\s*([a-z])', desconto_string.lower())
    if match:
        percentual = float(match.group(1))
        bonus_codigo = match.group(2).upper()
        return percentual, bonus_codigo
    
    print(f"Aviso: Não foi possível extrair desconto de '{desconto_string}'")
    return None, None

def criar_tipos_bonus_padrao(session):
    """
    Cria os tipos de bônus padrão se não existirem
    """
    tipos_bonus = [
        {'codigo': 'A', 'nome': 'Bônus A', 'descricao': 'Bônus tipo A', 'cor_hex': '#FF6B6B'},
        {'codigo': 'B', 'nome': 'Bônus B', 'descricao': 'Bônus tipo B', 'cor_hex': '#4ECDC4'},
        {'codigo': 'C', 'nome': 'Bônus C', 'descricao': 'Bônus tipo C', 'cor_hex': '#45B7D1'},
        {'codigo': 'D', 'nome': 'Bônus D', 'descricao': 'Bônus tipo D', 'cor_hex': '#96CEB4'},
        {'codigo': 'E', 'nome': 'Bônus E', 'descricao': 'Bônus tipo E', 'cor_hex': '#FFEAA7'}
    ]
    
    for tipo_data in tipos_bonus:
        tipo_existente = session.query(TipoBonus).filter(
            TipoBonus.codigo == tipo_data['codigo']
        ).first()
        
        if not tipo_existente:
            novo_tipo = TipoBonus(**tipo_data)
            session.add(novo_tipo)
            print(f"Criado tipo de bônus: {tipo_data['codigo']} - {tipo_data['nome']}")
    
    session.commit()

def carregar_regras_json(arquivo_json='regras.json'):
    """
    Carrega os dados do arquivo regras.json no banco de dados
    """
    print(f"Iniciando carregamento de dados de {arquivo_json}...")
    
    # Inicializar banco
     db = init_database('database/sinergia.db', echo=False)
    
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        dados_regras = json.load(f)
    
    with DatabaseSession() as session:
        # Criar tipos de bônus padrão
        criar_tipos_bonus_padrao(session)
        
        # Estatísticas
        distribuidoras_processadas = 0
        faixas_criadas = 0
        regras_criadas = 0
        erros = []
        
        for distribuidora_data in dados_regras:
            try:
                # Buscar ou criar estado
                estado = session.query(Estado).filter(
                    Estado.sigla == distribuidora_data['estado_sigla']
                ).first()
                
                if not estado:
                    estado = Estado(
                        nome=distribuidora_data['estado_nome'],
                        sigla=distribuidora_data['estado_sigla']
                    )
                    session.add(estado)
                    session.flush()  # Para obter o ID
                    print(f"Criado estado: {estado.sigla} - {estado.nome}")
                
                # Buscar distribuidora existente
                distribuidora = session.query(Distribuidora).filter(
                    and_(
                        Distribuidora.nome == distribuidora_data['nome'],
                        Distribuidora.estado_id == estado.id
                    )
                ).first()
                
                if not distribuidora:
                    print(f"Aviso: Distribuidora '{distribuidora_data['nome']}' não encontrada no banco.")
                    print(f"Criando nova distribuidora...")
                    
                    # Extrair dados da primeira regra para configurações gerais
                    primeira_regra = distribuidora_data['regras_desconto'][0] if distribuidora_data['regras_desconto'] else {}
                    
                    # Extrair consumo mínimo da primeira faixa
                    consumo_min, _ = extrair_consumo_minimo_maximo(primeira_regra.get('kwh_minimo', '100 kWh'))
                    
                    distribuidora = Distribuidora(
                        nome=distribuidora_data['nome'],
                        estado_id=estado.id,
                        consumo_minimo=consumo_min or 100,
                        forma_pagamento=primeira_regra.get('forma_pagamento', 'Unificado'),
                        prazo_injecao=int(primeira_regra.get('prazo_injecao', '90').replace(' dias', '')),
                        troca_titularidade=primeira_regra.get('troca_titularidade', False),
                        login_senha_necessario=False,
                        aceita_placas=True,
                        icms_minimo=Decimal('17.00'),
                        observacoes=distribuidora_data.get('regras_gerais_observacoes', ''),
                        ativo=True
                    )
                    session.add(distribuidora)
                    session.flush()
                    print(f"Criada distribuidora: {distribuidora.nome}")
                
                distribuidoras_processadas += 1
                
                # Processar regras de desconto
                for i, regra_data in enumerate(distribuidora_data['regras_desconto']):
                    try:
                        # Extrair faixa de consumo
                        consumo_min, consumo_max = extrair_consumo_minimo_maximo(regra_data['kwh_minimo'])
                        
                        if consumo_min is None:
                            print(f"Erro: Não foi possível extrair consumo mínimo de '{regra_data['kwh_minimo']}'")
                            continue
                        
                        # Buscar ou criar faixa de consumo
                        faixa = session.query(FaixaConsumo).filter(
                            and_(
                                FaixaConsumo.distribuidora_id == distribuidora.id,
                                FaixaConsumo.consumo_min == consumo_min,
                                FaixaConsumo.consumo_max == consumo_max
                            )
                        ).first()
                        
                        if not faixa:
                            faixa = FaixaConsumo(
                                distribuidora_id=distribuidora.id,
                                consumo_min=consumo_min,
                                consumo_max=consumo_max,
                                nome_faixa=regra_data['kwh_minimo'],
                                ordem=i + 1,
                                ativo=True
                            )
                            session.add(faixa)
                            session.flush()
                            faixas_criadas += 1
                            print(f"  Criada faixa: {faixa.nome_faixa}")
                        
                        # Processar desconto padrão
                        desconto_padrao = regra_data.get('desconto_padrao')
                        if desconto_padrao:
                            percentual, bonus_codigo = extrair_desconto_e_bonus(desconto_padrao)
                            
                            if percentual and bonus_codigo:
                                # Buscar tipo de bônus
                                tipo_bonus = session.query(TipoBonus).filter(
                                    TipoBonus.codigo == bonus_codigo
                                ).first()
                                
                                if tipo_bonus:
                                    # Verificar se regra já existe
                                    regra_existente = session.query(RegraDesconto).filter(
                                        and_(
                                            RegraDesconto.faixa_consumo_id == faixa.id,
                                            RegraDesconto.tipo_bonus_id == tipo_bonus.id
                                        )
                                    ).first()
                                    
                                    if not regra_existente:
                                        # Processar descontos opcionais
                                        descontos_opcionais = regra_data.get('descontos_opcionais', [])
                                        opcional_1 = opcional_2 = opcional_3 = opcional_4 = None
                                        
                                        for j, desconto_opcional in enumerate(descontos_opcionais[:4]):
                                            perc_opcional, _ = extrair_desconto_e_bonus(desconto_opcional)
                                            if perc_opcional:
                                                if j == 0:
                                                    opcional_1 = Decimal(str(perc_opcional))
                                                elif j == 1:
                                                    opcional_2 = Decimal(str(perc_opcional))
                                                elif j == 2:
                                                    opcional_3 = Decimal(str(perc_opcional))
                                                elif j == 3:
                                                    opcional_4 = Decimal(str(perc_opcional))
                                        
                                        nova_regra = RegraDesconto(
                                            faixa_consumo_id=faixa.id,
                                            tipo_bonus_id=tipo_bonus.id,
                                            desconto_percentual=Decimal(str(percentual)),
                                            desconto_opcional_1=opcional_1,
                                            desconto_opcional_2=opcional_2,
                                            desconto_opcional_3=opcional_3,
                                            desconto_opcional_4=opcional_4,
                                            analise_credito=regra_data.get('analise_credito', False),
                                            observacoes=f"Importado de regras.json - {regra_data.get('id', '')}",
                                            ativo=True
                                        )
                                        session.add(nova_regra)
                                        regras_criadas += 1
                                        print(f"    Criada regra: Bônus {bonus_codigo} - {percentual}%")
                        
                        # Processar descontos opcionais como regras separadas
                        for desconto_opcional in regra_data.get('descontos_opcionais', []):
                            percentual_opt, bonus_codigo_opt = extrair_desconto_e_bonus(desconto_opcional)
                            
                            if percentual_opt and bonus_codigo_opt:
                                tipo_bonus_opt = session.query(TipoBonus).filter(
                                    TipoBonus.codigo == bonus_codigo_opt
                                ).first()
                                
                                if tipo_bonus_opt:
                                    # Verificar se regra já existe
                                    regra_existente = session.query(RegraDesconto).filter(
                                        and_(
                                            RegraDesconto.faixa_consumo_id == faixa.id,
                                            RegraDesconto.tipo_bonus_id == tipo_bonus_opt.id
                                        )
                                    ).first()
                                    
                                    if not regra_existente:
                                        nova_regra_opt = RegraDesconto(
                                            faixa_consumo_id=faixa.id,
                                            tipo_bonus_id=tipo_bonus_opt.id,
                                            desconto_percentual=Decimal(str(percentual_opt)),
                                            analise_credito=regra_data.get('analise_credito', False),
                                            observacoes=f"Desconto opcional - Importado de regras.json",
                                            ativo=True
                                        )
                                        session.add(nova_regra_opt)
                                        regras_criadas += 1
                                        print(f"    Criada regra opcional: Bônus {bonus_codigo_opt} - {percentual_opt}%")
                    
                    except Exception as e:
                        erro_msg = f"Erro ao processar regra {regra_data.get('id', 'sem_id')} da {distribuidora_data['nome']}: {str(e)}"
                        erros.append(erro_msg)
                        print(f"ERRO: {erro_msg}")
            
            except Exception as e:
                erro_msg = f"Erro ao processar distribuidora {distribuidora_data.get('nome', 'sem_nome')}: {str(e)}"
                erros.append(erro_msg)
                print(f"ERRO: {erro_msg}")
        
        # Commit final
        session.commit()
        
        # Relatório final
        print("\n" + "="*60)
        print("RELATÓRIO DE IMPORTAÇÃO")
        print("="*60)
        print(f"Distribuidoras processadas: {distribuidoras_processadas}")
        print(f"Faixas de consumo criadas: {faixas_criadas}")
        print(f"Regras de desconto criadas: {regras_criadas}")
        print(f"Erros encontrados: {len(erros)}")
        
        if erros:
            print("\nERROS DETALHADOS:")
            for erro in erros:
                print(f"- {erro}")
        
        print("\nImportação concluída!")

def verificar_dados_carregados():
    """
    Verifica os dados carregados no banco
    """
    print("\nVerificando dados carregados...")
    
    with DatabaseSession() as session:
        # Contar registros
        total_estados = session.query(Estado).count()
        total_distribuidoras = session.query(Distribuidora).count()
        total_tipos_bonus = session.query(TipoBonus).count()
        total_faixas = session.query(FaixaConsumo).count()
        total_regras = session.query(RegraDesconto).count()
        
        print(f"Estados: {total_estados}")
        print(f"Distribuidoras: {total_distribuidoras}")
        print(f"Tipos de Bônus: {total_tipos_bonus}")
        print(f"Faixas de Consumo: {total_faixas}")
        print(f"Regras de Desconto: {total_regras}")
        
        # Mostrar alguns exemplos
        print("\nExemplos de dados carregados:")
        
        # Estados
        estados = session.query(Estado).limit(5).all()
        print("\nEstados:")
        for estado in estados:
            print(f"  {estado.sigla} - {estado.nome}")
        
        # Distribuidoras com mais regras
        from sqlalchemy import func
        distribuidoras_com_regras = session.query(
            Distribuidora.nome,
            Estado.sigla,
            func.count(RegraDesconto.id).label('total_regras')
        ).join(Estado).join(FaixaConsumo).join(RegraDesconto).group_by(
            Distribuidora.id
        ).order_by(
            func.count(RegraDesconto.id).desc()
        ).limit(5).all()
        
        print("\nDistribuidoras com mais regras:")
        for dist in distribuidoras_com_regras:
            print(f"  {dist.nome} ({dist.sigla}): {dist.total_regras} regras")

if __name__ == "__main__":
    print("Carregador de dados regras.json para banco sinergia.db")
    print("="*60)
    
    try:
        carregar_regras_json()
        verificar_dados_carregados()
    except Exception as e:
        print(f"Erro geral na importação: {str(e)}")
        import traceback
        traceback.print_exc()