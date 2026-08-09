"""
Módulo central de conexão com o Supabase.

Tabelas estão em paulo_robson, não em public.
Usa header Prefer: schema=paulo_robson em TODOS os requests.
"""
import os
from pathlib import Path


def _load_env():
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(str(env_path))
    else:
        load_dotenv()


class SchemaClient:
    """Wrapper que adiciona Prefer header com schema em todo request"""
    
    def __init__(self, base_client, schema):
        self.base = base_client
        self.schema = schema
    
    def table(self, name):
        qb = self.base.table(name)
        # Adicionar Prefer header
        return qb.headers({'Prefer': f'schema={self.schema}'})
    
    def rpc(self, name, params=None):
        return self.base.rpc(name, params)
    
    def __getattr__(self, name):
        return getattr(self.base, name)


def get_client(url: str = None, key: str = None):
    """
    Cria client que usa paulo_robson automaticamente.
    """
    from supabase import create_client

    _load_env()

    url = url or os.getenv('SUPABASE_URL')
    key = key or os.getenv('SUPABASE_KEY')
    schema = os.getenv('SUPABASE_SCHEMA', 'public')

    if not url or not key:
        raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

    base = create_client(url, key)
    
    # Se não é public, usar SchemaClient que adiciona header
    if schema != 'public':
        return SchemaClient(base, schema)
    
    return base


def get_schema_name() -> str:
    _load_env()
    return os.getenv('SUPABASE_SCHEMA', 'public')
