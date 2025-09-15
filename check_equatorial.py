from database.db_manager import DatabaseManager

db = DatabaseManager()
distribuidoras = db.get_all_distributors()

equatorial = [d for d in distribuidoras if 'Equatorial' in d['nome']]
print(f'Distribuidoras Equatorial encontradas: {len(equatorial)}')
for d in equatorial:
    print(f'  {d["nome"]} - {d["estado_nome"]}')

print(f'\nTotal de distribuidoras: {len(distribuidoras)}')
print('\nDistribuidoras do Rio Grande do Sul:')
rs_distribuidoras = [d for d in distribuidoras if d['estado_nome'] == 'Rio Grande do Sul']
for d in rs_distribuidoras:
    print(f'  {d["nome"]} - {d["estado_nome"]}')