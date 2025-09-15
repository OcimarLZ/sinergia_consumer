import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class DatabaseManager:
    """Gerenciador do banco de dados SQLite para o sistema de simulação de descontos"""
    
    def __init__(self, db_path: str = "database/sinergia.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Garante que o banco de dados e as tabelas existam"""
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Criar banco e tabelas
        with sqlite3.connect(self.db_path) as conn:
            # Ler e executar schema
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            conn.executescript(schema)
            conn.commit()
    
    def get_connection(self) -> sqlite3.Connection:
        """Retorna uma conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        return conn
    
    # MÉTODOS PARA ESTADOS
    def inserir_estado(self, nome: str, sigla: str) -> int:
        """Insere um novo estado e retorna o ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO estados (nome, sigla) VALUES (?, ?)",
                (nome, sigla)
            )
            if cursor.rowcount > 0:
                return cursor.lastrowid
            else:
                # Estado já existe, buscar ID
                result = conn.execute(
                    "SELECT id FROM estados WHERE sigla = ?", (sigla,)
                ).fetchone()
                return result['id'] if result else None
    
    def listar_estados(self) -> List[Dict]:
        """Lista todos os estados cadastrados"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM estados ORDER BY nome")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_states(self) -> List[Dict]:
        """Alias para listar_estados - compatibilidade com API"""
        return self.listar_estados()
    
    def get_distributors_by_state(self, estado_id: int) -> List[Dict]:
        """Alias para listar_distribuidoras_por_estado - compatibilidade com API"""
        return self.listar_distribuidoras_por_estado(estado_id)
    
    def get_all_distributors(self) -> List[Dict]:
        """Lista todas as distribuidoras com informações do estado"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT d.*, e.nome as estado_nome, e.sigla as estado_sigla
                FROM distribuidoras d
                JOIN estados e ON d.estado_id = e.id
                ORDER BY e.nome, d.nome
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_distributor_by_id(self, distribuidor_id: int) -> Optional[Dict]:
        """Alias para buscar_distribuidora - compatibilidade com API"""
        return self.buscar_distribuidora(distribuidor_id)
    
    def get_discount_rules_by_distributor(self, distribuidor_id: int) -> List[Dict]:
        """Busca todas as regras de desconto de uma distribuidora"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM regras_desconto 
                WHERE distribuidora_id = ?
                ORDER BY consumo_min
            """, (distribuidor_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def create_simulation(self, estado_id: int, distribuidor_id: int, 
                         perfil_consumidor: str, kwh_consumido: float,
                         desconto_percentual: float, valor_desconto: float) -> int:
        """Cria uma nova simulação no banco de dados"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO simulacoes 
                (distribuidora_id, consumo_kwh, desconto_aplicado, valor_economia)
                VALUES (?, ?, ?, ?)
            """, (distribuidor_id, int(kwh_consumido), desconto_percentual, valor_desconto))
            return cursor.lastrowid
    
    def get_all_simulations(self) -> List[Dict]:
        """Lista todas as simulações realizadas"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT s.*, d.nome as distribuidora_nome, e.nome as estado_nome
                FROM simulacoes s
                JOIN distribuidoras d ON s.distribuidora_id = d.id
                JOIN estados e ON d.estado_id = e.id
                ORDER BY s.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # MÉTODOS PARA DISTRIBUIDORAS
    def inserir_distribuidora(self, nome: str, estado_id: int, consumo_minimo: int,
                            forma_pagamento: str, prazo_injecao: int,
                            troca_titularidade: bool = False,
                            login_senha_necessario: bool = False,
                            aceita_placas: bool = True,
                            icms_minimo: float = 17.0,
                            observacoes: str = "") -> int:
        """Insere uma nova distribuidora e retorna o ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO distribuidoras 
                (nome, estado_id, consumo_minimo, forma_pagamento, prazo_injecao,
                 troca_titularidade, login_senha_necessario, aceita_placas, 
                 icms_minimo, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, estado_id, consumo_minimo, forma_pagamento, prazo_injecao,
                  troca_titularidade, login_senha_necessario, aceita_placas,
                  icms_minimo, observacoes))
            return cursor.lastrowid
    
    def listar_distribuidoras_por_estado(self, estado_id: int) -> List[Dict]:
        """Lista distribuidoras de um estado específico"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT d.*, e.nome as estado_nome, e.sigla as estado_sigla
                FROM distribuidoras d
                JOIN estados e ON d.estado_id = e.id
                WHERE d.estado_id = ?
                ORDER BY d.nome
            """, (estado_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def buscar_distribuidora(self, distribuidora_id: int) -> Optional[Dict]:
        """Busca uma distribuidora específica"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT d.*, e.nome as estado_nome, e.sigla as estado_sigla
                FROM distribuidoras d
                JOIN estados e ON d.estado_id = e.id
                WHERE d.id = ?
            """, (distribuidora_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    # MÉTODOS PARA REGRAS DE DESCONTO
    def inserir_regra_desconto(self, distribuidora_id: int, consumo_min: int,
                             consumo_max: Optional[int], desconto_percentual: float,
                             tipo_bonus: str, descricao: str = "") -> int:
        """Insere uma nova regra de desconto"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO regras_desconto 
                (distribuidora_id, consumo_min, consumo_max, desconto_percentual, 
                 tipo_bonus, descricao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (distribuidora_id, consumo_min, consumo_max, desconto_percentual,
                  tipo_bonus, descricao))
            return cursor.lastrowid
    
    def buscar_regras_desconto(self, distribuidora_id: int, consumo_kwh: int) -> List[Dict]:
        """Busca regras de desconto aplicáveis para um consumo específico"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM regras_desconto 
                WHERE distribuidora_id = ? 
                AND consumo_min <= ?
                AND (consumo_max IS NULL OR consumo_max >= ?)
                AND ativo = TRUE
                ORDER BY desconto_percentual DESC
            """, (distribuidora_id, consumo_kwh, consumo_kwh))
            return [dict(row) for row in cursor.fetchall()]
    
    def listar_regras_distribuidora(self, distribuidora_id: int) -> List[Dict]:
        """Lista todas as regras de uma distribuidora"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM regras_desconto 
                WHERE distribuidora_id = ? AND ativo = TRUE
                ORDER BY consumo_min, desconto_percentual DESC
            """, (distribuidora_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # MÉTODOS PARA SIMULAÇÕES
    def registrar_simulacao(self, distribuidora_id: int, consumo_kwh: int,
                          desconto_aplicado: float, valor_economia: float,
                          tipo_bonus: str, ip_usuario: str = "") -> int:
        """Registra uma simulação realizada"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO simulacoes 
                (distribuidora_id, consumo_kwh, desconto_aplicado, valor_economia,
                 tipo_bonus, ip_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (distribuidora_id, consumo_kwh, desconto_aplicado, valor_economia,
                  tipo_bonus, ip_usuario))
            return cursor.lastrowid
    
    def obter_estatisticas_simulacoes(self) -> Dict:
        """Obtém estatísticas das simulações realizadas"""
        with self.get_connection() as conn:
            # Total de simulações
            total = conn.execute("SELECT COUNT(*) as total FROM simulacoes").fetchone()['total']
            
            # Média de economia
            media_economia = conn.execute(
                "SELECT AVG(valor_economia) as media FROM simulacoes WHERE valor_economia > 0"
            ).fetchone()['media'] or 0
            
            # Distribuidora mais simulada
            mais_simulada = conn.execute("""
                SELECT d.nome, COUNT(*) as total
                FROM simulacoes s
                JOIN distribuidoras d ON s.distribuidora_id = d.id
                GROUP BY s.distribuidora_id
                ORDER BY total DESC
                LIMIT 1
            """).fetchone()
            
            return {
                'total_simulacoes': total,
                'media_economia': round(media_economia, 2),
                'distribuidora_mais_simulada': dict(mais_simulada) if mais_simulada else None
            }
    
    def limpar_dados(self):
        """Remove todos os dados das tabelas (mantém estrutura)"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM simulacoes")
            conn.execute("DELETE FROM regras_desconto")
            conn.execute("DELETE FROM distribuidoras")
            conn.execute("DELETE FROM estados")
            conn.commit()

# Instância global do gerenciador
db_manager = DatabaseManager()

if __name__ == "__main__":
    # Teste básico
    print("Inicializando banco de dados...")
    db = DatabaseManager()
    print("Banco de dados inicializado com sucesso!")
    
    # Inserir um estado de teste
    estado_id = db.inserir_estado("São Paulo", "SP")
    print(f"Estado inserido com ID: {estado_id}")
    
    # Listar estados
    estados = db.listar_estados()
    print(f"Estados cadastrados: {len(estados)}")