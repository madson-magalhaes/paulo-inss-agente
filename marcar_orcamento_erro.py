#!/usr/bin/env python3
"""
Marca orçamento como "erro" no Supabase

Usa HTTP direto via urllib (built-in) para funcionar com qualquer schema
"""

import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def marcar_como_erro(numero_orcamento, motivo="erro_processamento"):
    """
    Marca orçamento como 'erro' em paulo_robson.orcamentos via HTTP REST direto

    Args:
        numero_orcamento: Número do orçamento (ex: 26080701)
        motivo: Descrição do erro (opcional)

    Returns:
        True se marcado com sucesso, False caso contrário
    """
    try:
        from dotenv import load_dotenv
        
        # Carregar .env
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(str(env_path))
        else:
            load_dotenv()
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        if not url or not key:
            raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

        # Supabase REST API para paulo_robson.orcamentos
        # Format: /rest/v1/orcamentos com Prefer header indicando schema
        rest_url = f"{url}/rest/v1/orcamentos?numero_orcamento=eq.{numero_orcamento}"
        
        # Payload para UPDATE (PATCH)
        data = json.dumps({'status_orcamento': 'erro'}).encode('utf-8')
        
        # Headers
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'schema=paulo_robson,return=representation'  # Usar schema paulo_robson + retornar dados
        }
        
        # Criar request
        req = urllib.request.Request(
            rest_url,
            data=data,
            headers=headers,
            method='PATCH'
        )
        
        # Executar
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data) if response_data else []
                
                # Verificar se algum registro foi atualizado
                if isinstance(result, list) and len(result) > 0:
                    print(f"\n✅ Orçamento {numero_orcamento} marcado como 'erro'")
                    print(f"   Schema: paulo_robson")
                    print(f"   Tabela: orcamentos")
                    print(f"   Motivo: {motivo}")
                    print(f"   Linhas atualizadas: {len(result)}")
                    return True
                else:
                    print(f"\n⚠️  Aviso: Nenhum registro atualizado para {numero_orcamento}")
                    print(f"   Verificar se número existe em paulo_robson.orcamentos")
                    print(f"   (Loop continua mesmo assim)")
                    return False
        
        except urllib.error.HTTPError as http_err:
            print(f"\n⚠️  Aviso: HTTP {http_err.code} ao atualizar Supabase")
            try:
                error_body = http_err.read().decode('utf-8')
                print(f"   Resposta: {error_body[:200]}")
            except:
                pass
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
