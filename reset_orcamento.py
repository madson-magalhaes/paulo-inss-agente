#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase_client import get_client

    client = get_client()

    response = client.table('orcamentos').update(
        {'status_orcamento': 'processando'}
    ).eq('numero_orcamento', 12052603).execute()
    
    print("✅ Orçamento 12052603 resetado para 'processando'")
    print("   Próxima execução do pipeline fará o upload ao Google Drive")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
