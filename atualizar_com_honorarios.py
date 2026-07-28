#!/usr/bin/env python3
"""
Script para atualizar o registro inserido com as novas colunas
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from supabase_client import get_client

def main():
    print("\n" + "=" * 80)
    print("ATUALIZAR REGISTRO COM NOVAS COLUNAS")
    print("=" * 80 + "\n")

    try:
        client = get_client()
        print("✅ Conectado ao Supabase\n")

        # Dados para atualizar
        atualizacao = {
            'inss_com_honorarios': 81189.00,
            'percentual_inss_com_honorarios': 38.61,
        }

        print("🔄 Atualizando registro 12052601...\n")

        response = client.table('inss') \
            .update(atualizacao) \
            .eq('numero_orcamento', 12052601) \
            .execute()

        if response.data:
            print("✅ Atualização bem-sucedida!\n")
            print("📋 Registro atualizado:")
            print("-" * 80)
            for item in response.data:
                print(f"\nID: {item.get('id')}")
                print(f"Orçamento: {item.get('numero_orcamento')}")
                print(f"Nome: {item.get('nome')}")
                print(f"INSS sem redução: R$ {item.get('inss_sem_reducao', 0):,.2f}")
                print(f"INSS otimizado: R$ {item.get('inss_otimizado', 0):,.2f}")
                print(f"Honorários: R$ {item.get('honorarios', 0):,.2f}")
                print(f"INSS com honorários: R$ {item.get('inss_com_honorarios', 0):,.2f}")
                print(f"Percentual economia: {item.get('percentual_economia', 0):.2f}%")
                print(f"Percentual com honorários: {item.get('percentual_inss_com_honorarios', 0):.2f}%")
            return 0
        else:
            print("❌ Erro na atualização")
            return 1

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
