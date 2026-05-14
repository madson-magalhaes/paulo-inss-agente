#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    client = create_client(url, key)
    
    response = client.table('paulo_orcamentos').update(
        {'status_orcamento': 'processando'}
    ).eq('numero_orcamento', 12052603).execute()
    
    print("✅ Orçamento 12052603 resetado para 'processando'")
    print("   Próxima execução do pipeline fará o upload ao Google Drive")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
