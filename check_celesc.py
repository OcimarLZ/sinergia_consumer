#!/usr/bin/env python3
import sqlite3

# Conectar ao banco
conn = sqlite3.connect('database/sinergia.db')
conn.row_factory = sqlite3.Row

print("=== VERIFICANDO ESTRUTURA DA TABELA DISTRIBUIDORAS ===")
cursor = conn.execute("PRAGMA table_info(distribuidoras)")
colunas = cursor.fetchall()
print("Colunas da tabela distribuidoras:")
for col in colunas:
    print(f"  - {col['name']} ({col['type']})")

print("\n=== VERIFICANDO DISTRIBUIDORAS CELESC ===")
cursor = conn.execute('SELECT * FROM distribuidoras WHERE nome LIKE "%CELESC%"')
distribuidoras = cursor.fetchall()

if distribuidoras:
    for dist in distribuidoras:
        print(f"Distribuidora encontrada:")
        for key in dist.keys():
            print(f"  {key}: {dist[key]}")
else:
    print("Nenhuma distribuidora CELESC encontrada")

print("\n=== VERIFICANDO TODAS AS DISTRIBUIDORAS ===")
cursor = conn.execute('SELECT * FROM distribuidoras ORDER BY nome')
todas_dist = cursor.fetchall()
print(f"Total de distribuidoras: {len(todas_dist)}")
for dist in todas_dist:
    print(f"ID: {dist['id']}, Nome: {dist['nome']}")

print("\n=== VERIFICANDO REGRAS DE DESCONTO ===")
cursor = conn.execute('SELECT COUNT(*) as total FROM regras_desconto')
total_regras = cursor.fetchone()
print(f"Total de regras: {total_regras['total']}")

cursor = conn.execute('SELECT COUNT(*) as total FROM regras_desconto WHERE ativo = 1')
regras_ativas = cursor.fetchone()
print(f"Regras ativas: {regras_ativas['total']}")

conn.close()