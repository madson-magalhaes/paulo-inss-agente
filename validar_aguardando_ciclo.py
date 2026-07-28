#!/usr/bin/env python3
"""
Valida se orçamentos estão prontos para processar

LÓGICA CORRETA:
1. Marca 'aberto' → 'processando'
2. AGUARDA um ciclo completo
3. Verifica se há novos 'aberto' com mesmo numero
   - SIM: reinicia aguardo
   - NÃO: PRONTO para processar

RASTREAMENTO: `.claude/orcamentos_aguardando.json`
Exemplo:
{
  "123": {
    "timestamp_marcado": "2024-05-13T15:00:00",
    "ciclos_aguardados": 0,
    "ultimo_ciclo_verificado": "2024-05-13T15:01:00"
  }
}
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
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase_client import get_client
    import pandas as pd
except ImportError as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)

# Intervalo entre ciclos (segundos)
INTERVALO_CICLO = int(os.getenv('INTERVALO_SEGURANCA_ORCAMENTOS', '60'))

# Arquivo de rastreamento
ARQUIVO_AGUARDANDO = './.claude/orcamentos_aguardando.json'


def garantir_diretorio():
    """Garante que diretório existe"""
    Path(os.path.dirname(ARQUIVO_AGUARDANDO)).mkdir(parents=True, exist_ok=True)


def carregar_aguardando():
    """Carrega registro de orçamentos aguardando"""
    garantir_diretorio()
    if os.path.exists(ARQUIVO_AGUARDANDO):
        try:
            with open(ARQUIVO_AGUARDANDO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def salvar_aguardando(dados):
    """Salva registro de orçamentos aguardando"""
    garantir_diretorio()
    with open(ARQUIVO_AGUARDANDO, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2)


def main():
    """Valida prontos com aguardo de ciclo"""

    print("\n" + "=" * 80)
    print("VALIDAR PRONTOS COM AGUARDO DE CICLO")
    print("=" * 80 + "\n")

    # Conecta
    try:
        client = get_client()
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return {}

    # Carrega histórico
    aguardando = carregar_aguardando()
    agora = datetime.now()

    # PASSO 1: Coleta em 'processando'
    print("📥 Coletando orçamentos em 'processando'...")
    response = client.table('orcamentos').select(
        'numero_orcamento'
    ).eq('status_orcamento', 'processando').execute()

    if not response.data:
        print("⚠️ Nenhum orçamento em 'processando'")
        salvar_aguardando({})
        return {}

    df = pd.DataFrame(response.data)
    numeros_processando = set(df['numero_orcamento'].unique())
    print(f"✓ {len(numeros_processando)} orçamento(s) em 'processando'\n")

    # PASSO 2: Coleta em 'aberto'
    print("📥 Coletando orçamentos em 'aberto'...")
    response = client.table('orcamentos').select(
        'numero_orcamento'
    ).eq('status_orcamento', 'aberto').execute()

    numeros_aberto = set()
    if response.data:
        df = pd.DataFrame(response.data)
        numeros_aberto = set(df['numero_orcamento'].unique())

    print(f"✓ {len(numeros_aberto)} orçamento(s) em 'aberto'\n")

    # PASSO 3: Valida com aguardo
    print("⏳ Validando aguardo de ciclo...\n")

    prontos = {}
    bloqueados = {}
    novo_aguardando = {}

    for numero in sorted(numeros_processando):
        info = aguardando.get(numero, {})

        # Primeira vez que vê este numero em 'processando'
        if not info:
            print(f"  🔄 {numero}: AGUARDANDO (ciclo 1/2)")
            print(f"     └─ Marcado agora, volta no próximo ciclo")

            novo_aguardando[numero] = {
                'timestamp_marcado': agora.isoformat(),
                'ciclos_aguardados': 0,
                'ultimo_check': agora.isoformat()
            }
            bloqueados[numero] = {'motivo': 'primeiro_ciclo'}
            continue

        # Já tem histórico
        timestamp_str = info.get('timestamp_marcado')
        ciclos = info.get('ciclos_aguardados', 0)

        timestamp_marcado = datetime.fromisoformat(timestamp_str)
        tempo_decorrido = (agora - timestamp_marcado).total_seconds()

        # Ainda não passou intervalo para próximo ciclo
        if tempo_decorrido < INTERVALO_CICLO:
            tempo_restante = INTERVALO_CICLO - tempo_decorrido
            print(f"  ⏳ {numero}: AGUARDANDO (faltam {tempo_restante:.0f}s)")

            novo_aguardando[numero] = info
            novo_aguardando[numero]['ultimo_check'] = agora.isoformat()
            bloqueados[numero] = {'motivo': 'intervalo_seguranca'}
            continue

        # Passou intervalo - verifica se há novos 'aberto'
        if numero in numeros_aberto:
            # TEM novo 'aberto'!
            print(f"  ⏳ {numero}: NOVO ITEM DETECTADO")
            print(f"     └─ Reiniciando aguardo (novo 'aberto' encontrado)")

            novo_aguardando[numero] = {
                'timestamp_marcado': agora.isoformat(),
                'ciclos_aguardados': 0,
                'ultimo_check': agora.isoformat()
            }
            bloqueados[numero] = {'motivo': 'novo_aberto_detectado'}
            continue

        # SEM novo 'aberto' - incrementa ciclos
        ciclos_completos = ciclos + 1

        if ciclos_completos < 2:
            # Ainda precisa de mais ciclos
            print(f"  ⏳ {numero}: CICLO {ciclos_completos}/2")
            print(f"     └─ Sem novos items, aguardando próximo ciclo")

            novo_aguardando[numero] = {
                'timestamp_marcado': timestamp_str,
                'ciclos_aguardados': ciclos_completos,
                'ultimo_check': agora.isoformat()
            }
            bloqueados[numero] = {'motivo': 'aguardando_ciclo'}
            continue

        # PRONTO! Passou 2 ciclos sem novos
        print(f"  ✅ {numero}: PRONTO PARA PROCESSAR!")
        print(f"     └─ 2 ciclos sem novos items")

        prontos[numero] = {'validado': True}

    # Resumo
    print(f"\n📊 RESUMO")
    print(f"  ✅ Prontos: {len(prontos)}")
    print(f"  ⏳ Aguardando: {len(bloqueados)}\n")

    if bloqueados:
        print("⏳ AGUARDANDO:")
        for numero in sorted(bloqueados.keys()):
            motivo = bloqueados[numero].get('motivo', 'desconhecido')
            print(f"  • {numero} ({motivo})")
        print()

    # Salva histórico
    salvar_aguardando(novo_aguardando)

    return prontos


if __name__ == '__main__':
    prontos = main()
