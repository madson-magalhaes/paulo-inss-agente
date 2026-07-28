#!/usr/bin/env python3
"""
Script para inserir dados do exemplo-CE diretamente no Supabase
com as novas colunas (inss_com_honorarios e percentual_inss_com_honorarios)
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase_client import get_client
except ImportError:
    print("❌ Erro: supabase não está instalado")
    print("Instale com: pip install supabase")
    sys.exit(1)

# Dados do exemplo-CE.csv
DADOS_EXEMPLO_CE = {
    'nome': 'Estrutural Engenharia',
    'telefone': '(85) 3199-8855',
    'numero_orcamento': 12052601,
    'inss_sem_reducao': 132256.19,
    'inss_otimizado': 59303.06,
    'percentual_economia': 55.16,
    'honorarios': 21885.94,
    'inss_com_honorarios': 81189.00,
    'percentual_inss_com_honorarios': 38.61,
}

def main():
    print("\n" + "=" * 80)
    print("INSERIR EXEMPLO-CE NO SUPABASE")
    print("=" * 80 + "\n")

    try:
        # Conecta ao Supabase
        client = get_client()
        print("✅ Conectado ao Supabase\n")

        # Exibe dados a inserir
        print("📊 Dados a Inserir:")
        print("-" * 80)
        for chave, valor in DADOS_EXEMPLO_CE.items():
            if isinstance(valor, float):
                if 'percentual' in chave:
                    print(f"   {chave:.<35} {valor:.2f}%")
                else:
                    print(f"   {chave:.<35} R$ {valor:,.2f}")
            else:
                print(f"   {chave:.<35} {valor}")
        print()

        # Insere dados
        print("🔄 Inserindo em inss...")
        response = client.table('inss').insert(DADOS_EXEMPLO_CE).execute()

        if response.data:
            print("✅ Inserção bem-sucedida!\n")
            print("📋 Dados inseridos:")
            print("-" * 80)
            for item in response.data:
                print(f"\nID: {item.get('id')}")
                print(f"Número Orçamento: {item.get('numero_orcamento')}")
                print(f"Nome: {item.get('nome')}")
                print(f"INSS sem redução: R$ {item.get('inss_sem_reducao', 0):,.2f}")
                print(f"INSS otimizado: R$ {item.get('inss_otimizado', 0):,.2f}")
                print(f"INSS com honorários: R$ {item.get('inss_com_honorarios', 0):,.2f}")
                print(f"Percentual economia: {item.get('percentual_economia', 0):.2f}%")
                print(f"Percentual com honorários: {item.get('percentual_inss_com_honorarios', 0):.2f}%")

            return 0
        else:
            print("❌ Erro: Nenhuma linha foi inserida")
            print(f"Resposta: {response}")
            return 1

    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
