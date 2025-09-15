from database.db_manager import DatabaseManager

db = DatabaseManager()
distribuidoras = db.get_all_distributors()

print(f'Total de distribuidoras: {len(distribuidoras)}')
print('\nDistribuidoras por estado:')
for d in distribuidoras:
    print(f'{d["estado_nome"]} ({d["estado_sigla"]}) - {d["nome"]}')

# Verificar especificamente Equatorial
equatorial = [d for d in distribuidoras if 'Equatorial' in d['nome']]
print(f'\nDistribuidoras Equatorial encontradas: {len(equatorial)}')
for eq in equatorial:
    print(f'  {eq["estado_nome"]} - {eq["nome"]}')

# Verificar Rio Grande do Sul
rs_distribuidoras = [d for d in distribuidoras if d['estado_sigla'] == 'RS']
print(f'\nDistribuidoras do Rio Grande do Sul: {len(rs_distribuidoras)}')
for rs in rs_distribuidoras:
    print(f'  {rs["nome"]}')