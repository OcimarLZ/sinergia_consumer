#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('database/sinergia.db')
conn.row_factory = sqlite3.Row

print("=== VERIFICANDO REGRAS DA CELESC ===")
cursor = conn.execute('SELECT * FROM regras_desconto WHERE distribuidora_id = 30')
regras = cursor.fetchall()

print(f"Regras para CELESC (ID 30): {len(regras)}")
for regra in regras:
    print(f"ID: {regra['id']}, Desconto: {regra['desconto_percentual']}%, Ativo: {regra['ativo']}")

print("\n=== VERIFICANDO QUERY DO SCRIPT ORIGINAL ===")
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
WHERE rd.ativo = 1 AND rd.distribuidora_id = 30
ORDER BY rd.distribuidora_id, rd.consumo_min
"""

cursor = conn.execute(query)
regras_ativas = cursor.fetchall()
print(f"Regras ativas da CELESC: {len(regras_ativas)}")
for regra in regras_ativas:
    print(f"ID: {regra['id']}, Nome: {regra['distribuidora_nome']}, Desconto: {regra['desconto_percentual']}%")

conn.close()