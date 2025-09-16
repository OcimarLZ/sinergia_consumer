#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para recriar o banco de dados com a nova estrutura
"""

import sqlite3
import os
import time
import gc

def recreate_database():
    """Recria o banco de dados com a nova estrutura"""
    
    db_path = 'database/sinergia.db'
    backup_path = 'database/sinergia_backup.db'
    schema_path = 'database/schema_nova_estrutura.sql'
    
    try:
        # Força garbage collection para fechar conexões
        gc.collect()
        time.sleep(1)
        
        # Remove o banco antigo se existir
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"✅ Banco antigo removido: {db_path}")
            except PermissionError:
                print(f"⚠️  Não foi possível remover {db_path} - arquivo em uso")
                print("Tentando criar novo banco com nome diferente...")
                db_path = 'database/sinergia_new.db'
        
        # Lê o schema SQL
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Cria novo banco com a estrutura correta
        print(f"🔨 Criando novo banco: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Aplica o schema
        print("📋 Aplicando schema...")
        cursor.executescript(schema_sql)
        
        # Confirma as mudanças
        conn.commit()
        
        # Verifica as tabelas criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n✅ Banco criado com sucesso!")
        print("\n📋 Tabelas criadas:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Fecha a conexão
        conn.close()
        
        print(f"\n🎯 Banco pronto para uso: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao recriar banco: {e}")
        return False

if __name__ == "__main__":
    recreate_database()