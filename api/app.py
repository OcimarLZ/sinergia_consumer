from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Adicionar o diretório pai ao path para importar o database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager

app = Flask(__name__)
CORS(app)  # Permitir requisições do frontend

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return jsonify({
        'status': 'ok',
        'message': 'API Sinergia funcionando corretamente'
    })

@app.route('/api/estados', methods=['GET'])
def get_estados():
    """Retorna lista de todos os estados disponíveis"""
    try:
        estados = db_manager.get_all_states()
        return jsonify({
            'success': True,
            'data': estados
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/distribuidoras/<estado_id>', methods=['GET'])
def get_distribuidoras_por_estado(estado_id):
    """Retorna distribuidoras de um estado específico"""
    try:
        distribuidoras = db_manager.get_distributors_by_state(int(estado_id))
        return jsonify({
            'success': True,
            'data': distribuidoras
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/distribuidoras', methods=['GET'])
def get_todas_distribuidoras():
    """Retorna todas as distribuidoras com informações do estado"""
    try:
        distribuidoras = db_manager.get_all_distributors()
        return jsonify({
            'success': True,
            'data': distribuidoras
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/regras/<distribuidor_id>', methods=['GET'])
def get_regras_distribuidor(distribuidor_id):
    """Retorna regras de desconto de uma distribuidora específica"""
    try:
        regras = db_manager.get_discount_rules_by_distributor(int(distribuidor_id))
        return jsonify({
            'success': True,
            'data': regras
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/simular', methods=['POST'])
def simular_desconto():
    """Simula desconto baseado nos parâmetros fornecidos"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['estado_id', 'distribuidor_id', 'perfil_consumidor', 'kwh_consumido']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório ausente: {field}'
                }), 400
        
        estado_id = data['estado_id']
        distribuidor_id = data['distribuidor_id']
        perfil_consumidor = data['perfil_consumidor']
        kwh_consumido = float(data['kwh_consumido'])
        
        # Buscar informações da distribuidora
        distribuidora = db_manager.get_distributor_by_id(distribuidor_id)
        if not distribuidora:
            return jsonify({
                'success': False,
                'error': 'Distribuidora não encontrada'
            }), 404
        
        # Buscar regras de desconto
        regras = db_manager.get_discount_rules_by_distributor(distribuidor_id)
        
        # Calcular desconto
        resultado_simulacao = calcular_desconto(
            distribuidora, regras, perfil_consumidor, kwh_consumido
        )
        
        # Salvar simulação no banco
        simulacao_id = db_manager.create_simulation(
            estado_id, distribuidor_id, perfil_consumidor, 
            kwh_consumido, resultado_simulacao['desconto_percentual'],
            resultado_simulacao['valor_desconto']
        )
        
        resultado_simulacao['simulacao_id'] = simulacao_id
        
        return jsonify({
            'success': True,
            'data': resultado_simulacao
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calcular_desconto(distribuidora, regras, perfil_consumidor, kwh_consumido):
    """Calcula o desconto baseado nas regras da distribuidora"""
    
    # Valores base para cálculo (podem ser ajustados)
    tarifa_kwh = 0.75  # R$ por kWh (valor médio)
    valor_conta = kwh_consumido * tarifa_kwh
    
    # Verificar consumo mínimo
    consumo_minimo = distribuidora.get('consumo_minimo', 0)
    if kwh_consumido < consumo_minimo:
        return {
            'elegivel': False,
            'motivo': f'Consumo mínimo não atingido. Necessário: {consumo_minimo} kWh',
            'desconto_percentual': 0,
            'valor_desconto': 0,
            'valor_original': valor_conta,
            'valor_final': valor_conta
        }
    
    # Calcular desconto baseado nas regras
    desconto_percentual = 0
    
    # Se há regras específicas, usar a primeira aplicável
    if regras:
        for regra in regras:
            # Lógica simples: usar o desconto da regra se aplicável
            if regra.get('desconto_percentual'):
                desconto_percentual = regra['desconto_percentual']
                break
    else:
        # Desconto padrão baseado no perfil e consumo
        if perfil_consumidor.lower() == 'residencial':
            if kwh_consumido >= 500:
                desconto_percentual = 15
            elif kwh_consumido >= 300:
                desconto_percentual = 12
            else:
                desconto_percentual = 8
        elif perfil_consumidor.lower() == 'comercial':
            if kwh_consumido >= 1000:
                desconto_percentual = 20
            elif kwh_consumido >= 500:
                desconto_percentual = 15
            else:
                desconto_percentual = 10
        elif perfil_consumidor.lower() == 'industrial':
            if kwh_consumido >= 2000:
                desconto_percentual = 25
            elif kwh_consumido >= 1000:
                desconto_percentual = 20
            else:
                desconto_percentual = 15
    
    valor_desconto = valor_conta * (desconto_percentual / 100)
    valor_final = valor_conta - valor_desconto
    
    return {
        'elegivel': True,
        'desconto_percentual': desconto_percentual,
        'valor_desconto': round(valor_desconto, 2),
        'valor_original': round(valor_conta, 2),
        'valor_final': round(valor_final, 2),
        'economia_mensal': round(valor_desconto, 2),
        'economia_anual': round(valor_desconto * 12, 2),
        'distribuidora': distribuidora['nome'],
        'perfil': perfil_consumidor,
        'consumo_kwh': kwh_consumido
    }

@app.route('/api/simulacoes', methods=['GET'])
def get_simulacoes():
    """Retorna histórico de simulações"""
    try:
        simulacoes = db_manager.get_all_simulations()
        return jsonify({
            'success': True,
            'data': simulacoes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Iniciando API Sinergia...")
    print("Endpoints disponíveis:")
    print("  GET  /api/health - Status da API")
    print("  GET  /api/estados - Lista de estados")
    print("  GET  /api/distribuidoras/<estado_id> - Distribuidoras por estado")
    print("  GET  /api/distribuidoras - Todas as distribuidoras")
    print("  GET  /api/regras/<distribuidor_id> - Regras de uma distribuidora")
    print("  POST /api/simular - Simular desconto")
    print("  GET  /api/simulacoes - Histórico de simulações")
    print("\nAPI rodando em: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)