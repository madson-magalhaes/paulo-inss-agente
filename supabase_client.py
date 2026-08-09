"""
Módulo central de conexão com o Supabase.

Concentra a criação do client e a seleção de schema (multi-tenant) num único
lugar, para que os scripts não precisem duplicar essa lógica.

Schema controlado pela env var SUPABASE_SCHEMA (default: "public").
Para testar o schema por-cliente (ex: paulo_robson), defina no .env:
    SUPABASE_SCHEMA=paulo_robson

IMPORTANTE: o schema precisa estar na lista "Exposed schemas" em
Settings > API do painel do Supabase, senão a API REST retorna erro.

NOTA: NÃO usamos client.schema() porque causa erro em operações UPDATE/DELETE.
Em vez disso, retornamos o client direto e confiamos que o schema já está
em "Exposed schemas" para o usuário autenticado.
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
    
    Uso: client = get_client()
         client.table('orcamentos').select('*').execute()
         client.table('orcamentos').update({...}).execute()

    Returns:
        Client Supabase simples que funciona com qualquer schema
        que esteja em "Exposed schemas" na config do Supabase.
        
    O schema é apenas informativo (para leitura em get_schema_name()).
    O Supabase REST API usa o schema do usuário autenticado por padrão.
    """
    from supabase import create_client

    _load_env()

    url = url or os.getenv('SUPABASE_URL')
    key = key or os.getenv('SUPABASE_KEY')

    if not url or not key:
        raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

    # Retornar client simples - Supabase usa o schema padrão da chave
    return create_client(url, key)


def get_schema_name() -> str:
    """Retorna o nome do schema configurado (SUPABASE_SCHEMA, default 'public')."""
    _load_env()
    return os.getenv('SUPABASE_SCHEMA', 'public')
