#!/usr/bin/env python3
"""
Marca orçamento como "erro" no Supabase
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def marcar_como_erro(numero_orcamento, motivo="erro_processamento"):
    """
    Marca orçamento como 'erro' em paulo_robson.orcamentos

    Args:
        numero_orcamento: Número do orçamento (ex: 26080701)
        motivo: Descrição do erro (opcional)

    Returns:
        True se marcado com sucesso, False caso contrário
    """
    try:
        from supabase_client import get_client, get_schema_name

        client = get_client()
        schema = get_schema_name()

        # Usa client.table() diretamente - funciona com qualquer schema
        # desde que esteja em "Exposed schemas" do Supabase
        response = client.table('orcamentos').update({
            'status_orcamento': 'erro'
        }).eq('numero_orcamento', str(numero_orcamento)).execute()

        if response.data and len(response.data) > 0:
            print(f"\n✅ Orçamento {numero_orcamento} marcado como 'erro'")
            print(f"   Schema: {schema}")
            print(f"   Tabela: orcamentos")
            print(f"   Motivo: {motivo}")
            print(f"   Linhas atualizadas: {len(response.data)}")
            return True
        else:
            print(f"\n⚠️  Aviso: Nenhum registro atualizado para {numero_orcamento}")
            print(f"   Verificar se número existe em {schema}.orcamentos")
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
