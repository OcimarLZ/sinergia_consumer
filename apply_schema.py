#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar o novo schema no banco de dados SQLite
"""

import sqlite3
import os

def apply_schema():
    """Aplica o novo schema no banco de dados"""
    
    # Caminhos dos arquivos
    db_path = 'database/sinergia.db'
    schema_path = 'database/schema_nova_estrutura.sql'
    
    # Verifica se o arquivo de schema existe
    if not os.path.exists(schema_path):
        print(f"Erro: Arquivo {schema_path} não encontrado!")
        return False
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lê o arquivo SQL
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Executa o schema SQL
        print("Aplicando novo schema...")
        cursor.executescript(schema_sql)
        
        # Confirma as mudanças
        conn.commit()
        
        print("✅ Schema aplicado com sucesso!")
        
        # Verifica as tabelas criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n📋 Tabelas no banco de dados:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Fecha a conexão
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar schema: {e}")
        return False

if __name__ == "__main__":
    apply_schema()