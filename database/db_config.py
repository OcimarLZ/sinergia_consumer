"""Configuração do banco de dados para os models SQLAlchemy"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from models import Base

class DatabaseConfig:
    """Classe para configuração do banco de dados"""
    
    def __init__(self, db_path=None, echo=False):
        """
        Inicializa a configuração do banco
        
        Args:
            db_path (str): Caminho para o arquivo do banco SQLite
            echo (bool): Se True, mostra as queries SQL no console
        """
        if db_path is None:
            # Caminho padrão relativo ao diretório atual
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, 'sinergia.db')
        
        self.db_path = db_path
        self.echo = echo
        self.engine = None
        self.Session = None
        self._session = None
    
    def create_engine(self):
        """Cria o engine do SQLAlchemy"""
        if self.engine is None:
            # Configurações específicas para SQLite
            self.engine = create_engine(
                f'sqlite:///{self.db_path}',
                echo=self.echo,
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,  # Permite uso em múltiplas threads
                    'timeout': 20  # Timeout de 20 segundos
                },
                pool_pre_ping=True  # Verifica conexões antes de usar
            )
        return self.engine
    
    def create_tables(self):
        """Cria todas as tabelas no banco de dados"""
        engine = self.create_engine()
        Base.metadata.create_all(engine)
        print(f"Tabelas criadas/verificadas no banco: {self.db_path}")
    
    def get_session_factory(self):
        """Retorna uma factory de sessões"""
        if self.Session is None:
            engine = self.create_engine()
            self.Session = sessionmaker(bind=engine)
        return self.Session
    
    def get_scoped_session(self):
        """Retorna uma sessão com escopo (thread-safe)"""
        if self._session is None:
            engine = self.create_engine()
            session_factory = sessionmaker(bind=engine)
            self._session = scoped_session(session_factory)
        return self._session
    
    def get_session(self):
        """Retorna uma nova sessão"""
        Session = self.get_session_factory()
        return Session()
    
    def close_all_sessions(self):
        """Fecha todas as sessões ativas"""
        if self._session:
            self._session.remove()
        if self.engine:
            self.engine.dispose()

# Instância global padrão
default_db = DatabaseConfig()

def get_db_session():
    """Função utilitária para obter uma sessão do banco padrão"""
    return default_db.get_session()

def init_database(db_path=None, echo=False, create_tables=True):
    """
    Inicializa o banco de dados
    
    Args:
        db_path (str): Caminho para o arquivo do banco
        echo (bool): Se True, mostra as queries SQL
        create_tables (bool): Se True, cria as tabelas automaticamente
    
    Returns:
        DatabaseConfig: Instância configurada do banco
    """
    global default_db
    default_db = DatabaseConfig(db_path, echo)
    
    if create_tables:
        default_db.create_tables()
    
    return default_db

def setup_test_database():
    """
    Configura um banco de dados em memória para testes
    
    Returns:
        DatabaseConfig: Instância configurada para testes
    """
    test_db = DatabaseConfig(':memory:', echo=False)
    test_db.create_tables()
    return test_db

class DatabaseSession:
    """Context manager para sessões do banco de dados"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or default_db
        self.session = None
    
    def __enter__(self):
        self.session = self.db_config.get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Em caso de erro, faz rollback
            self.session.rollback()
        else:
            # Se tudo correu bem, faz commit
            self.session.commit()
        
        self.session.close()

# Exemplo de uso do context manager
def exemplo_uso_context_manager():
    """Exemplo de como usar o context manager"""
    from models import Distribuidora, Estado
    
    # Usando o context manager
    with DatabaseSession() as session:
        # Todas as operações dentro do 'with' são automaticamente
        # commitadas ou sofrem rollback em caso de erro
        distribuidoras = session.query(Distribuidora).join(Estado).filter(
            Estado.sigla == 'MG'
        ).all()
        
        print(f"Encontradas {len(distribuidoras)} distribuidoras em MG")
        
        # Se chegou até aqui sem erro, será feito commit automaticamente
        # Se houvesse erro, seria feito rollback automaticamente

if __name__ == "__main__":
    # Exemplo de inicialização
    print("Inicializando banco de dados...")
    
    # Inicializar com configurações padrão
    db = init_database(echo=True)
    
    # Testar uma consulta simples
    with DatabaseSession() as session:
        from models import Estado
        estados = session.query(Estado).all()
        print(f"Estados encontrados: {len(estados)}")
    
    print("Configuração concluída!")