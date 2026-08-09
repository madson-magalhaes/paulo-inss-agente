"""
Módulo central de conexão com o Supabase.

Concentra a criação do client e a seleção de schema (multi-tenant) num único
lugar, para que os scripts não precisem duplicar essa lógica.

Schema controlado pela env var SUPABASE_SCHEMA (default: "public").
Para testar o schema por-cliente (ex: paulo_robson), defina no .env:
    SUPABASE_SCHEMA=paulo_robson
Sem essa variável, o comportamento é idêntico ao de produção (schema public).

IMPORTANTE: o schema precisa estar na lista "Exposed schemas" em
Settings > API do painel do Supabase, senão a API REST retorna erro.
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
    Cria e retorna um client Supabase já apontando para o schema configurado
    (SUPABASE_SCHEMA no .env, default "public").

    Uso: client = get_client()
         client.table('orcamentos').select('*').execute()

    Nota: quando SUPABASE_SCHEMA != "public", o retorno é o resultado de
    client.schema(nome) (um SyncPostgrestClient), que expõe os mesmos
    métodos .table()/.rpc() usados nos scripts — a troca é transparente.
    """
    from supabase import create_client

    _load_env()

    url = url or os.getenv('SUPABASE_URL')
    key = key or os.getenv('SUPABASE_KEY')

    if not url or not key:
        raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

    client = create_client(url, key)

    schema = os.getenv('SUPABASE_SCHEMA', 'public')
    if schema != 'public':
        return client.schema(schema)

    return client


def get_schema_name() -> str:
    """Retorna o nome do schema configurado (SUPABASE_SCHEMA, default 'public')."""
    _load_env()
    return os.getenv('SUPABASE_SCHEMA', 'public')
