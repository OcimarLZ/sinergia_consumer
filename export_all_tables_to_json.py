#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para exportar todas as tabelas do banco de dados para arquivos JSON
para uso no site estático.
"""

import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    Distribuidora, Estado, TipoBonus, FaixaConsumo, RegraDesconto
)

# Configuração do banco de dados
DATABASE_URL = "sqlite:///database/sinergia.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def export_distribuidoras(session):
    """Exporta dados da tabela distribuidoras"""
    distribuidoras = session.query(Distribuidora).all()
    data = []
    
    for dist in distribuidoras:
        data.append({
            "id": dist.id,
            "nome": dist.nome,
            "estado_id": dist.estado_id,
            "consumo_minimo": dist.consumo_minimo,
            "forma_pagamento": dist.forma_pagamento,
            "prazo_injecao": dist.prazo_injecao,
            "troca_titularidade": dist.troca_titularidade,
            "login_senha_necessario": dist.login_senha_necessario,
            "aceita_placas": dist.aceita_placas,
            "icms_minimo": float(dist.icms_minimo) if dist.icms_minimo else None,
            "observacoes": dist.observacoes,
            "ativo": dist.ativo
        })
    
    return data

def export_estados(session):
    """Exporta dados da tabela estados"""
    estados = session.query(Estado).all()
    data = []
    
    for estado in estados:
        data.append({
            "id": estado.id,
            "nome": estado.nome,
            "sigla": estado.sigla
        })
    
    return data

def export_tipos_bonus(session):
    """Exporta dados da tabela tipos_bonus"""
    tipos = session.query(TipoBonus).all()
    data = []
    
    for tipo in tipos:
        data.append({
            "id": tipo.id,
            "codigo": tipo.codigo,
            "nome": tipo.nome,
            "descricao": tipo.descricao,
            "cor_hex": tipo.cor_hex,
            "ativo": tipo.ativo
        })
    
    return data

def export_faixas_consumo(session):
    """Exporta dados da tabela faixas_consumo"""
    faixas = session.query(FaixaConsumo).all()
    data = []
    
    for faixa in faixas:
        data.append({
            "id": faixa.id,
            "distribuidora_id": faixa.distribuidora_id,
            "consumo_min": faixa.consumo_min,
            "consumo_max": faixa.consumo_max,
            "nome_faixa": faixa.nome_faixa,
            "ordem": faixa.ordem,
            "ativo": faixa.ativo
        })
    
    return data

def export_regras_desconto(session):
    """Exporta dados da tabela regras_desconto"""
    regras = session.query(RegraDesconto).all()
    data = []
    
    for regra in regras:
        data.append({
            "id": regra.id,
            "faixa_consumo_id": regra.faixa_consumo_id,
            "tipo_bonus_id": regra.tipo_bonus_id,
            "desconto_percentual": float(regra.desconto_percentual) if regra.desconto_percentual else None,
            "desconto_opcional_1": float(regra.desconto_opcional_1) if regra.desconto_opcional_1 else None,
            "desconto_opcional_2": float(regra.desconto_opcional_2) if regra.desconto_opcional_2 else None,
            "desconto_opcional_3": float(regra.desconto_opcional_3) if regra.desconto_opcional_3 else None,
            "analise_credito": regra.analise_credito,
            "observacoes": regra.observacoes
        })
    
    return data

def save_json_file(data, filename):
    """Salva dados em arquivo JSON"""
    # Criar diretório se não existir
    os.makedirs('static/data', exist_ok=True)
    
    filepath = f'static/data/{filename}'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Arquivo {filepath} criado com {len(data)} registros")

def main():
    """Função principal"""
    print("🚀 Iniciando exportação das tabelas para JSON...")
    
    session = Session()
    
    try:
        # Exportar cada tabela
        print("\n📊 Exportando tabelas:")
        
        # Distribuidoras
        distribuidoras_data = export_distribuidoras(session)
        save_json_file(distribuidoras_data, 'distribuidoras.json')
        
        # Estados
        estados_data = export_estados(session)
        save_json_file(estados_data, 'estados.json')
        
        # Tipos de Bônus
        tipos_bonus_data = export_tipos_bonus(session)
        save_json_file(tipos_bonus_data, 'tipos_bonus.json')
        
        # Faixas de Consumo
        faixas_consumo_data = export_faixas_consumo(session)
        save_json_file(faixas_consumo_data, 'faixas_consumo.json')
        
        # Regras de Desconto
        regras_desconto_data = export_regras_desconto(session)
        save_json_file(regras_desconto_data, 'regras_desconto.json')
        
        print("\n✅ Exportação concluída com sucesso!")
        print("\n📁 Arquivos criados em static/data/:")
        print("   - distribuidoras.json")
        print("   - estados.json")
        print("   - tipos_bonus.json")
        print("   - faixas_consumo.json")
        print("   - regras_desconto.json")
        
    except Exception as e:
        print(f"❌ Erro durante a exportação: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()