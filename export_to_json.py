#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para exportar dados do banco SQLite para arquivos JSON
Para uso em landing page estática sem banco de dados
"""

import sqlite3
import json
import os
from pathlib import Path

def connect_db():
    """Conecta ao banco de dados SQLite"""
    db_path = Path(__file__).parent / 'database' / 'sinergia.db'
    return sqlite3.connect(db_path)

def export_estados():
    """Exporta dados dos estados para JSON"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nome, sigla 
        FROM estados 
        ORDER BY nome
    """)
    
    estados = []
    for row in cursor.fetchall():
        estados.append({
            'id': row[0],
            'nome': row[1],
            'sigla': row[2]
        })
    
    conn.close()
    
    # Salvar arquivo JSON
    output_path = Path(__file__).parent / 'static' / 'data' / 'estados.json'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(estados, f, ensure_ascii=False, indent=2)
    
    print(f"Estados exportados: {len(estados)} registros -> {output_path}")
    return estados

def export_distribuidoras():
    """Exporta dados das distribuidoras para JSON"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.id, d.nome, d.estado_id, e.nome as estado_nome, e.sigla,
               d.consumo_minimo, d.forma_pagamento, d.prazo_injecao,
               d.troca_titularidade, d.login_senha_necessario, d.aceita_placas,
               d.icms_minimo, d.observacoes
        FROM distribuidoras d
        JOIN estados e ON d.estado_id = e.id
        ORDER BY e.nome, d.nome
    """)
    
    distribuidoras = []
    for row in cursor.fetchall():
        distribuidoras.append({
            'id': row[0],
            'nome': row[1],
            'estado_id': row[2],
            'estado_nome': row[3],
            'estado_sigla': row[4],
            'consumo_minimo': row[5],
            'forma_pagamento': row[6],
            'prazo_injecao': row[7],
            'troca_titularidade': bool(row[8]),
            'login_senha_necessario': bool(row[9]),
            'aceita_placas': bool(row[10]),
            'icms_minimo': float(row[11]) if row[11] else 17.0,
            'observacoes': row[12]
        })
    
    conn.close()
    
    # Salvar arquivo JSON
    output_path = Path(__file__).parent / 'static' / 'data' / 'distribuidoras.json'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(distribuidoras, f, ensure_ascii=False, indent=2)
    
    print(f"Distribuidoras exportadas: {len(distribuidoras)} registros -> {output_path}")
    return distribuidoras

def export_regras_desconto():
    """Exporta regras de desconto para JSON"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.id, r.distribuidora_id, d.nome as distribuidora_nome,
               r.consumo_min, r.consumo_max, r.desconto_percentual,
               r.tipo_bonus, r.descricao, r.ativo
        FROM regras_desconto r
        JOIN distribuidoras d ON r.distribuidora_id = d.id
        WHERE r.ativo = 1
        ORDER BY r.distribuidora_id, r.consumo_min
    """)
    
    regras = []
    for row in cursor.fetchall():
        regras.append({
            'id': row[0],
            'distribuidora_id': row[1],
            'distribuidora_nome': row[2],
            'consumo_min': row[3],
            'consumo_max': row[4],
            'desconto_percentual': float(row[5]),
            'tipo_bonus': row[6],
            'descricao': row[7],
            'ativo': bool(row[8])
        })
    
    conn.close()
    
    # Salvar arquivo JSON
    output_path = Path(__file__).parent / 'static' / 'data' / 'regras_desconto.json'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(regras, f, ensure_ascii=False, indent=2)
    
    print(f"Regras de desconto exportadas: {len(regras)} registros -> {output_path}")
    return regras

def main():
    """Função principal para exportar todos os dados"""
    print("Iniciando exportação dos dados do banco para JSON...")
    
    try:
        # Exportar dados
        estados = export_estados()
        distribuidoras = export_distribuidoras()
        regras = export_regras_desconto()
        
        print("\n✅ Exportação concluída com sucesso!")
        print(f"📊 Resumo:")
        print(f"   - Estados: {len(estados)}")
        print(f"   - Distribuidoras: {len(distribuidoras)}")
        print(f"   - Regras de desconto: {len(regras)}")
        print(f"\n📁 Arquivos gerados em: static/data/")
        
    except Exception as e:
        print(f"❌ Erro durante a exportação: {e}")
        return False
    
    return True

if __name__ == '__main__':
    main()