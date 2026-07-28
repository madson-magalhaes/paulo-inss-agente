#!/usr/bin/env python3
"""
Script para criar as novas colunas no Supabase via SQL
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("❌ Erro: supabase não está instalado")
    sys.exit(1)

def main():
    print("\n" + "=" * 80)
    print("CRIAR COLUNAS NO SUPABASE: paulo_inss")
    print("=" * 80 + "\n")

    # Carrega credenciais
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        print("❌ Erro: Credenciais não configuradas")
        return 1

    try:
        client = create_client(url, key)
        print("✅ Conectado ao Supabase\n")

        # SQL para criar colunas
        sql_queries = [
            """
            ALTER TABLE paulo_inss
            ADD COLUMN IF NOT EXISTS inss_com_honorarios NUMERIC;
            """,
            """
            ALTER TABLE paulo_inss
            ADD COLUMN IF NOT EXISTS percentual_inss_com_honorarios NUMERIC;
            """
        ]

        print("🔄 Criando colunas...\n")

        for i, sql in enumerate(sql_queries, 1):
            try:
                response = client.rpc('exec_sql', {'sql': sql}).execute()
                print(f"✅ Coluna {i} criada com sucesso")
            except Exception as e:
                # Tenta método alternativo (via postgrest)
                # Se a coluna já existe, a API pode retornar erro mesmo que OK
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print(f"✅ Coluna {i} já existe (OK)")
                else:
                    print(f"⚠️  Coluna {i}: {e}")

        print("\n" + "=" * 80)
        print("COLUNAS A CRIAR:")
        print("=" * 80)
        print("""
1. inss_com_honorarios NUMERIC
   └─ Valor = INSS otimizado + Honorários

2. percentual_inss_com_honorarios NUMERIC
   └─ Valor = (INSS sem redução - INSS com honorários) / INSS sem redução × 100
        """)

        print("\n" + "=" * 80)
        print("SQL DIRETO (se preferir executar manualmente no Supabase):")
        print("=" * 80)
        print("""
ALTER TABLE paulo_inss ADD COLUMN IF NOT EXISTS inss_com_honorarios NUMERIC;
ALTER TABLE paulo_inss ADD COLUMN IF NOT EXISTS percentual_inss_com_honorarios NUMERIC;
        """)

        print("\n✅ INSTRUÇÕES:")
        print("=" * 80)
        print("""
1. Copie o SQL acima
2. Vá para: https://app.supabase.com/project/[seu-projeto]/sql/new
3. Cole o SQL
4. Clique em "RUN" (ou Ctrl+Enter)
5. Após isso, execute novamente: python3 inserir_exemplo_ce_supabase.py
        """)

        return 0

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
