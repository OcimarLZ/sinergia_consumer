#!/usr/bin/env python3
"""
Script para migrar dados da estrutura antiga para a nova estrutura do banco
e gerar JSON atualizado com a nova estrutura
"""

import sqlite3
import json
import os
from datetime import datetime

def backup_current_db():
    """Faz backup do banco atual"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'database/sinergia_backup_{timestamp}.db'
    
    # Copiar arquivo atual
    import shutil
    shutil.copy2('database/sinergia.db', backup_path)
    print(f"Backup criado: {backup_path}")
    return backup_path

def create_new_structure():
    """Cria a nova estrutura no banco existente"""
    conn = sqlite3.connect('database/sinergia.db')
    
    # Ler e executar o script da nova estrutura
    with open('database/schema_nova_estrutura.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Executar comandos SQL
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("Nova estrutura criada com sucesso!")

def migrate_existing_data():
    """Migra dados da estrutura antiga para a nova"""
    conn = sqlite3.connect('database/sinergia.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # 1. Inserir tipos de bônus básicos
        bonus_data = [
            ('A', 'Bônus A', 'Bônus básico com menor desconto', '#FF6B6B'),
            ('B', 'Bônus B', 'Bônus intermediário', '#4ECDC4'),
            ('C', 'Bônus C', 'Bônus avançado', '#45B7D1'),
            ('D', 'Bônus D', 'Bônus premium com maior desconto', '#96CEB4'),
            ('X', 'Não Disponível', 'Bônus não disponível para esta faixa', '#95A5A6')
        ]
        
        for codigo, nome, desc, cor in bonus_data:
            conn.execute("""
                INSERT OR IGNORE INTO tipos_bonus (codigo, nome, descricao, cor_hex) 
                VALUES (?, ?, ?, ?)
            """, (codigo, nome, desc, cor))
        
        # 2. Migrar regras antigas para nova estrutura
        cursor = conn.execute("""
            SELECT rd.*, d.nome as distribuidora_nome 
            FROM regras_desconto rd 
            JOIN distribuidoras d ON rd.distribuidora_id = d.id 
            WHERE rd.ativo = 1
        """)
        
        regras_antigas = cursor.fetchall()
        
        for regra in regras_antigas:
            # Criar faixa de consumo
            faixa_nome = f"{regra['consumo_min']} kWh"
            if regra['consumo_max']:
                if regra['consumo_max'] > 9999999:
                    faixa_nome = f"Acima de {regra['consumo_min']} kWh"
                else:
                    faixa_nome = f"{regra['consumo_min']} a {regra['consumo_max']} kWh"
            
            # Inserir faixa de consumo
            cursor_faixa = conn.execute("""
                INSERT OR IGNORE INTO faixas_consumo 
                (distribuidora_id, consumo_min, consumo_max, nome_faixa, ordem) 
                VALUES (?, ?, ?, ?, 1)
            """, (regra['distribuidora_id'], regra['consumo_min'], 
                   regra['consumo_max'], faixa_nome))
            
            # Obter ID da faixa
            faixa_id = conn.execute("""
                SELECT id FROM faixas_consumo 
                WHERE distribuidora_id = ? AND consumo_min = ? AND 
                      (consumo_max = ? OR (consumo_max IS NULL AND ? IS NULL))
            """, (regra['distribuidora_id'], regra['consumo_min'], 
                   regra['consumo_max'], regra['consumo_max'])).fetchone()
            
            if faixa_id:
                # Obter ID do tipo de bônus
                bonus_id = conn.execute(
                    "SELECT id FROM tipos_bonus WHERE codigo = ?", 
                    (regra['tipo_bonus'],)
                ).fetchone()
                
                if bonus_id:
                    # Inserir regra na nova estrutura
                    conn.execute("""
                        INSERT OR IGNORE INTO regras_desconto 
                        (faixa_consumo_id, tipo_bonus_id, desconto_percentual, observacoes) 
                        VALUES (?, ?, ?, ?)
                    """, (faixa_id['id'], bonus_id['id'], 
                           regra['desconto_percentual'], regra['descricao']))
        
        conn.commit()
        print(f"Migração concluída! {len(regras_antigas)} regras migradas.")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro na migração: {e}")
        raise
    finally:
        conn.close()

def generate_new_json():
    """Gera JSON com a nova estrutura"""
    conn = sqlite3.connect('database/sinergia.db')
    conn.row_factory = sqlite3.Row
    
    # Query usando a view criada
    cursor = conn.execute("""
        SELECT 
            regra_id as id,
            distribuidora_id,
            distribuidora_nome,
            estado_nome,
            estado_sigla,
            faixa_id,
            consumo_min,
            consumo_max,
            nome_faixa,
            bonus_id,
            bonus_codigo,
            bonus_nome,
            desconto_percentual,
            desconto_opcional_1,
            desconto_opcional_2,
            desconto_opcional_3,
            desconto_opcional_4,
            analise_credito,
            forma_pagamento,
            prazo_injecao,
            troca_titularidade,
            regra_observacoes,
            distribuidora_observacoes
        FROM vw_regras_completas
        ORDER BY estado_sigla, distribuidora_nome, consumo_min, bonus_codigo
    """)
    
    rows = cursor.fetchall()
    
    # Estrutura do novo JSON
    data = {
        "metadata": {
            "versao": "2.0",
            "estrutura": "nova_arquitetura",
            "gerado_em": datetime.now().isoformat(),
            "total_regras": len(rows),
            "descricao": "Estrutura robusta com faixas de consumo e tipos de bônus separados"
        },
        "regras": []
    }
    
    for row in rows:
        regra = {
            "id": row["id"],
            "distribuidora": {
                "id": row["distribuidora_id"],
                "nome": row["distribuidora_nome"],
                "estado": {
                    "nome": row["estado_nome"],
                    "sigla": row["estado_sigla"]
                },
                "forma_pagamento": row["forma_pagamento"],
                "prazo_injecao": row["prazo_injecao"],
                "troca_titularidade": bool(row["troca_titularidade"]),
                "observacoes": row["distribuidora_observacoes"]
            },
            "faixa_consumo": {
                "id": row["faixa_id"],
                "nome": row["nome_faixa"],
                "consumo_min": row["consumo_min"],
                "consumo_max": row["consumo_max"]
            },
            "bonus": {
                "id": row["bonus_id"],
                "codigo": row["bonus_codigo"],
                "nome": row["bonus_nome"]
            },
            "descontos": {
                "principal": float(row["desconto_percentual"]),
                "opcional_1": float(row["desconto_opcional_1"]) if row["desconto_opcional_1"] else None,
                "opcional_2": float(row["desconto_opcional_2"]) if row["desconto_opcional_2"] else None,
                "opcional_3": float(row["desconto_opcional_3"]) if row["desconto_opcional_3"] else None,
                "opcional_4": float(row["desconto_opcional_4"]) if row["desconto_opcional_4"] else None
            },
            "analise_credito": bool(row["analise_credito"]),
            "observacoes": row["regra_observacoes"]
        }
        data["regras"].append(regra)
    
    conn.close()
    
    # Salvar JSON
    json_path = 'static/data/regras_desconto_v2.json'
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Novo JSON gerado: {json_path}")
    print(f"Total de regras: {len(rows)}")
    
    return json_path

def main():
    """Função principal"""
    print("=== MIGRAÇÃO PARA NOVA ESTRUTURA ===")
    
    try:
        # 1. Backup
        backup_path = backup_current_db()
        
        # 2. Criar nova estrutura
        create_new_structure()
        
        # 3. Migrar dados
        migrate_existing_data()
        
        # 4. Gerar novo JSON
        json_path = generate_new_json()
        
        print("\n=== MIGRAÇÃO CONCLUÍDA COM SUCESSO! ===")
        print(f"Backup: {backup_path}")
        print(f"Novo JSON: {json_path}")
        
    except Exception as e:
        print(f"\nERRO na migração: {e}")
        print("Restaure o backup se necessário.")
        raise

if __name__ == "__main__":
    main()