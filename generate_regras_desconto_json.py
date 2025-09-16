#!/usr/bin/env python3
"""
Script para gerar regras_desconto.json a partir do banco sinergia.db
"""

import sqlite3
import json
import os

def generate_regras_desconto_json():
    """Gera o arquivo regras_desconto.json a partir dos dados do banco"""
    
    # Caminho do banco de dados
    db_path = os.path.join('database', 'sinergia.db')
    
    # Caminho do arquivo JSON de saída
    json_path = os.path.join('static', 'data', 'regras_desconto.json')
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        
        # Query para buscar regras com informações das distribuidoras
        query = """
        SELECT 
            rd.id,
            rd.distribuidora_id,
            rd.consumo_min,
            rd.consumo_max,
            rd.desconto_percentual,
            rd.tipo_bonus,
            rd.descricao,
            rd.ativo,
            d.nome as distribuidora_nome
        FROM regras_desconto rd
        JOIN distribuidoras d ON rd.distribuidora_id = d.id
        WHERE rd.ativo = 1
        ORDER BY rd.distribuidora_id, rd.consumo_min
        """
        
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        regras = []
        for row in rows:
            regra = {
                "id": row["id"],
                "distribuidora_id": row["distribuidora_id"],
                "distribuidora_nome": row["distribuidora_nome"],
                "consumo_min": row["consumo_min"],
                "consumo_max": row["consumo_max"],
                "desconto_percentual": float(row["desconto_percentual"]),
                "tipo_bonus": row["tipo_bonus"],
                "descricao": row["descricao"],
                "ativo": bool(row["ativo"])
            }
            regras.append(regra)
        
        # Fechar conexão
        conn.close()
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        # Salvar JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(regras, f, ensure_ascii=False, indent=2)
        
        print(f"Arquivo {json_path} gerado com sucesso!")
        print(f"Total de regras exportadas: {len(regras)}")
        
        # Mostrar algumas regras como exemplo
        if regras:
            print("\nPrimeiras 3 regras:")
            for i, regra in enumerate(regras[:3]):
                print(f"{i+1}. {regra['distribuidora_nome']} - Desconto: {regra['desconto_percentual']}%")
        
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")
    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == "__main__":
    generate_regras_desconto_json()