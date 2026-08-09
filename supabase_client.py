"""
Módulo central de conexão com o Supabase com suporte a multi-tenant.

As tabelas estão em schema paulo_robson, não em public.
Supabase REST API acessa automaticamente o schema padrão da chave.
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
    Cria e retorna um client Supabase.
    
    IMPORTANTE: A chave API precisa ter permissão no schema paulo_robson.
    Supabase REST API usa automaticamente o schema padrão da chave,
    então não precisa fazer nada especial - só criar e retornar.
    """
    from supabase import create_client

    _load_env()

    url = url or os.getenv('SUPABASE_URL')
    key = key or os.getenv('SUPABASE_KEY')

    if not url or not key:
        raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

    # Client simples - funciona porque a chave tem permissão em paulo_robson
    return create_client(url, key)


def get_schema_name() -> str:
    """Retorna o schema esperado (apenas para logs)"""
    _load_env()
    return os.getenv('SUPABASE_SCHEMA', 'public')
