#!/usr/bin/env python3
"""
Script para inserir exemplo-CE COM as novas colunas no Supabase
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from supabase_client import get_client

# Dados COMPLETOS com as novas colunas
DADOS_COMPLETOS = {
    'nome': 'Estrutural Engenharia',
    'telefone': '(85) 3199-8855',
    'numero_orcamento': 12052602,  # Usando número diferente para novo registro
    'inss_sem_reducao': 132256.19,
    'inss_otimizado': 59303.06,
    'percentual_economia': 55.16,
    'honorarios': 21885.94,
    'inss_com_honorarios': 81189.00,  # NOVO
    'percentual_inss_com_honorarios': 38.61,  # NOVO
}

def main():
    print("\n" + "=" * 80)
    print("INSERIR EXEMPLO-CE (COM NOVAS COLUNAS)")
    print("=" * 80 + "\n")

    try:
        client = get_client()
        print("✅ Conectado ao Supabase\n")

        print("📊 Dados a Inserir:")
        print("-" * 80)
        for chave, valor in DADOS_COMPLETOS.items():
            if isinstance(valor, float):
                if 'percentual' in chave:
                    print(f"   {chave:.<40} {valor:.2f}%")
                else:
                    print(f"   {chave:.<40} R$ {valor:,.2f}")
            else:
                print(f"   {chave:.<40} {valor}")
        print()

        print("🔄 Inserindo no Supabase...")
        response = client.table('inss').insert(DADOS_COMPLETOS).execute()

        if response.data:
            print("✅ Inserção bem-sucedida!\n")
            print("📋 Dados Inseridos:")
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

            print("\n" + "=" * 80)
            print("✅ SUCESSO! Todas as colunas foram inseridas corretamente.")
            print("=" * 80 + "\n")
            return 0
        else:
            print("❌ Erro: Nenhuma linha foi inserida")
            return 1

    except Exception as e:
        print(f"❌ Erro ao inserir: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
