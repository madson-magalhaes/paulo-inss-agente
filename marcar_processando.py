#!/usr/bin/env python3
"""
Marca orçamentos 'aberto' como 'processando'

FLUXO:
1. Coleta itens com status='aberto'
2. Marca cada um como 'processando' em Supabase
3. Próxima execução verifica:
   - Se surgiram novos itens 'aberto' para mesmo numero_orcamento
   - Se não: processa aqueles em 'processando'
   - Se sim: mantém em 'processando'
"""
import os
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = _script_dir
if os.path.exists(os.path.join(_project_root, 'supabase')):
    os.chdir(_project_root)
elif os.path.exists(os.path.join(_project_root, '..', 'supabase')):
    os.chdir(os.path.dirname(_project_root))


import sys
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase_client import get_client
    import pandas as pd
except ImportError as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)


def main():
    """Marca orçamentos como processando"""

    print("\n" + "=" * 80)
    print("MARCAR COMO PROCESSANDO")
    print("=" * 80 + "\n")

    # Conecta
    try:
        client = get_client()
        print("✓ Conexão bem-sucedida!\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return 1

    # Coleta APENAS items em 'aberto'
    print("📥 Coletando orçamentos com status 'aberto'...")
    response = client.table('orcamentos').select(
        'id, numero_orcamento, nome'
    ).eq('status_orcamento', 'aberto').execute()

    if not response.data:
        print("⚠️ Nenhum orçamento em 'aberto'")
        return 0

    df = pd.DataFrame(response.data)
    print(f"✓ {len(df)} item(ns) encontrado(s)\n")

    # Agrupa por numero_orcamento
    agrupados = df.groupby('numero_orcamento')

    print("📌 Marcando como 'processando'...\n")

    total_marcados = 0
    por_orcamento = {}

    for num_orc, grupo in agrupados:
        ids = grupo['id'].tolist()
        qtd = len(ids)

        # Marca como processando
        try:
            for id_item in ids:
                client.table('orcamentos').update(
                    {'status_orcamento': 'processando'}
                ).eq('id', id_item).execute()

            por_orcamento[num_orc] = qtd
            total_marcados += qtd
            print(f"  ✓ {num_orc}: {qtd} item(ns) → processando")

        except Exception as e:
            print(f"  ✗ {num_orc}: erro ao marcar - {e}")

    # Resumo
    print(f"\n📊 RESUMO")
    print(f"  Total marcado: {total_marcados}")
    print(f"  Orçamentos: {len(por_orcamento)}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
