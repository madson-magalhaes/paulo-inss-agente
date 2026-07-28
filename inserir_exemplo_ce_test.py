#!/usr/bin/env python3
"""
Script alternativo: insere sem as novas colunas primeiro,
depois você pode fazer UPDATE via dashboard
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from supabase_client import get_client

# Dados sem as colunas novas (para verificar se tabela estava ok)
DADOS_TESTE = {
    'nome': 'Estrutural Engenharia',
    'telefone': '(85) 3199-8855',
    'numero_orcamento': 12052601,
    'inss_sem_reducao': 132256.19,
    'inss_otimizado': 59303.06,
    'percentual_economia': 55.16,
    'honorarios': 21885.94,
}

def main():
    print("\n" + "=" * 80)
    print("INSERIR TESTE (sem novas colunas)")
    print("=" * 80 + "\n")

    try:
        client = get_client()
        print("✅ Conectado\n")

        print("📊 Inserindo dados...")
        response = client.table('inss').insert(DADOS_TESTE).execute()

        if response.data:
            print("✅ Inserção bem-sucedida!\n")
            for item in response.data:
                print(f"ID: {item.get('id')}")
                print(f"Orçamento: {item.get('numero_orcamento')}")
                print(f"Nome: {item.get('nome')}")
            return 0
        else:
            print("❌ Erro na inserção")
            return 1

    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
