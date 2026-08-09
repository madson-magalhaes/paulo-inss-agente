#!/usr/bin/env python3
"""
Marca orçamento como "erro" no Supabase

Uso:
  python3 marcar_orcamento_erro.py <numero_orcamento> [motivo]

Motivo (opcional):
  - estado_vazio
  - data_invalida
  - arquivo_nao_encontrado
  - erro_processamento
  - outro erro
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def marcar_como_erro(numero_orcamento, motivo="erro_processamento"):
    """
    Marca orçamento como 'erro' no Supabase via REST API direto

    Args:
        numero_orcamento: Número do orçamento (ex: 26080701)
        motivo: Descrição do erro (opcional)

    Returns:
        True se marcado com sucesso, False caso contrário
    """
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Carregar .env
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(str(env_path))
        else:
            load_dotenv()
        
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        schema = os.getenv('SUPABASE_SCHEMA', 'public')

        if not url or not key:
            raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

        # Criar client
        client = create_client(url, key)
        
        # Executar UPDATE direto (Supabase REST API)
        # Funciona com qualquer schema se estiver em "Exposed schemas"
        response = client.table('paulo_orcamentos') \
            .update({'status_orcamento': 'erro'}) \
            .eq('numero_orcamento', str(numero_orcamento)) \
            .execute()

        if response.data and len(response.data) > 0:
            print(f"\n✅ Orçamento {numero_orcamento} marcado como 'erro'")
            print(f"   Schema: {schema}")
            print(f"   Motivo: {motivo}")
            print(f"   Linhas atualizadas: {len(response.data)}")
            return True
        else:
            print(f"\n⚠️  Aviso: Nenhum registro atualizado para {numero_orcamento}")
            print(f"   Verificar se número existe em {schema}.paulo_orcamentos")
            print(f"   (Loop continua mesmo assim)")
            return False

    except Exception as e:
        print(f"\n⚠️  Aviso: Não foi possível marcar erro em Supabase")
        print(f"   Erro: {type(e).__name__}: {e}")
        print(f"   (Loop continua mesmo assim)")
        return False


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python3 marcar_orcamento_erro.py <numero_orcamento> [motivo]")
        print("   Exemplo: python3 marcar_orcamento_erro.py 26080701 estado_vazio")
        return 1

    numero = sys.argv[1]
    motivo = sys.argv[2] if len(sys.argv) > 2 else "erro_processamento"

    sucesso = marcar_como_erro(numero, motivo)
    return 0 if sucesso else 1


if __name__ == '__main__':
    sys.exit(main())
