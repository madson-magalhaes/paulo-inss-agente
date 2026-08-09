"""
Módulo central de conexão com o Supabase com suporte a multi-tenant.

Schema controlado pela env var SUPABASE_SCHEMA (default: "public").
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


def get_client(url: str = None, key: str = None):
    """
    Cria e retorna um client Supabase configurado para o schema correto.
    """
    from supabase import create_client

    _load_env()

    url = url or os.getenv('SUPABASE_URL')
    key = key or os.getenv('SUPABASE_KEY')
    schema = os.getenv('SUPABASE_SCHEMA', 'public')

    if not url or not key:
        raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

    # Criar client base
    base_client = create_client(url, key)
    
    # Se schema é public, retornar direto
    if schema == 'public':
        return base_client
    
    # Se é outro schema, usar wrapper que adiciona headers via .headers()
    return SupabaseSchemaClient(base_client, schema)


def get_schema_name() -> str:
    """Retorna o nome do schema configurado"""
    _load_env()
    return os.getenv('SUPABASE_SCHEMA', 'public')


class SupabaseSchemaClient:
    """
    Wrapper que intercepta table() e adiciona Prefer header para schema.
    
    Uso é idêntico ao client normal:
        client.table('orcamentos').select('*').execute()
        client.table('orcamentos').update({...}).execute()
    """
    
    def __init__(self, base_client, schema_name):
        self._client = base_client
        self._schema = schema_name
    
    def table(self, table_name):
        """Retorna query builder com schema predefinido via .headers()"""
        qb = self._client.table(table_name)
        # Usar método .headers() para adicionar Prefer header
        # Este método retorna um novo query builder com os headers
        return qb.headers({'Prefer': f'schema={self._schema}'})
    
    def __getattr__(self, name):
        """Delegar métodos não definidos ao client base"""
        return getattr(self._client, name)
