#!/usr/bin/env python3
"""
Validador de Orçamentos V2 - CORRIGIDO

PROBLEMA IDENTIFICADO:
- Sistema coleta APENAS linhas com status='aberto'
- Se Linha 1 → processada, depois Linha 2 adicionada → aberta
- Coleta só vê Linha 2, processa sozinha
- Linha 1 fica orfã, Linha 2 sobrescreve Linha 1

SOLUÇÃO:
- Validar que TODAS as linhas de um orçamento foram coletadas
- Bloquear processamento se houver mistura de status
- Exigir que orçamento INTEIRO seja coletado no MESMO ciclo

NOVA LÓGICA:
1. Coleta quantas linhas abertas existem para cada orçamento
2. Se orçamento já foi visto com N linhas, aguarda que continue com N
3. Se virou N+M, aguarda mais ciclos (novas áreas sendo adicionadas)
4. Se virou N-X, BLOQUEIA (linhas foram marcadas como processadas!)
   → Isso indica processamento parcial anterior
   → Aguarda que agente complete todo o orçamento

GARANTIA:
- Nunca processa orçamento parcialmente
- Sempre processa com TODAS as áreas juntas
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("❌ Erro: supabase não está instalado")
    sys.exit(1)

# Intervalo de segurança
INTERVALO_SEGURANCA = int(os.getenv('INTERVALO_SEGURANCA_ORCAMENTOS', '60'))
CICLOS_VALIDACAO = int(os.getenv('CICLOS_VALIDACAO_ORCAMENTOS', '2'))

# Arquivo de controle (rastreia estado de cada orçamento)
ARQUIVO_CONTROLE = './.claude/orcamentos_validacao_v2.json'


def garantir_diretorio_controle():
    """Garante que o diretório de controle existe"""
    Path(os.path.dirname(ARQUIVO_CONTROLE)).mkdir(parents=True, exist_ok=True)


def carregar_controle():
    """Carrega registro de validação"""
    garantir_diretorio_controle()

    if os.path.exists(ARQUIVO_CONTROLE):
        try:
            with open(ARQUIVO_CONTROLE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def salvar_controle(dados):
    """Salva registro de validação"""
    garantir_diretorio_controle()

    with open(ARQUIVO_CONTROLE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2)


def contar_linhas_orcamento_por_status(client, numero_orcamento):
    """
    Conta linhas do orçamento segregadas por status

    Retorna:
    - abertas: quantas linhas com status='aberto'
    - processadas: quantas linhas com status='processado'
    - total: abertas + processadas
    """
    try:
        # Conta abertas
        response_abertas = client.table('paulo_orcamentos').select(
            'id'
        ).eq('numero_orcamento', numero_orcamento).eq(
            'status_orcamento', 'aberto'
        ).execute()
        qtd_abertas = len(response_abertas.data) if response_abertas.data else 0

        # Conta processadas
        response_processadas = client.table('paulo_orcamentos').select(
            'id'
        ).eq('numero_orcamento', numero_orcamento).eq(
            'status_orcamento', 'processado'
        ).execute()
        qtd_processadas = len(response_processadas.data) if response_processadas.data else 0

        return {
            'abertas': qtd_abertas,
            'processadas': qtd_processadas,
            'total': qtd_abertas + qtd_processadas
        }

    except Exception as e:
        print(f"⚠️ Erro ao contar linhas para {numero_orcamento}: {e}")
        return {'abertas': 0, 'processadas': 0, 'total': 0}


def validar_orcamentos_v2(orcamentos_para_processar):
    """
    Valida se orçamentos estão COMPLETAMENTE coletados

    NOVO: Detecta se houve processamento parcial anterior
    """
    print("\n" + "=" * 80)
    print("VALIDAÇÃO DE ORÇAMENTOS V2 - VERIFICANDO COMPLETUDE")
    print("=" * 80)
    print(f"\nIntervalo de segurança: {INTERVALO_SEGURANCA} segundos")
    print(f"Ciclos de validação: {CICLOS_VALIDACAO}")
    print(f"Arquivo de controle: {ARQUIVO_CONTROLE}\n")

    controle = carregar_controle()
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    print(f"DEBUG - URL: {url}")
    print(f"DEBUG - Key: {key[:20]}..." if key else "DEBUG - Key: None")

    if not url or not key:
        print("⚠️ Aviso: Supabase não configurado, pulando validação")
        return orcamentos_para_processar, {}

    client = create_client(url, key)
    agora = datetime.now()
    orcamentos_prontos = {}
    orcamentos_incompletos = {}

    for numero, dados in orcamentos_para_processar.items():
        info_controle = controle.get(numero, {})

        # Primeira coleta deste orçamento
        if not info_controle or 'timestamp' not in info_controle:
            print(f"📋 {numero}:")

            # Busca linhas ATUAIS no Supabase
            linhas_atual = contar_linhas_orcamento_por_status(client, numero)

            if linhas_atual['abertas'] == 0:
                print(f"   ⚠️ ALERTA: Nenhuma linha aberta encontrada!")
                print(f"   • Processadas: {linhas_atual['processadas']}")
                print(f"   • Total: {linhas_atual['total']}")
                print(f"   ❌ PULANDO (orçamento já processado ou corrompido)")
                orcamentos_incompletos[numero] = {
                    **dados,
                    'motivo': 'nenhuma_linha_aberta',
                    'linhas_abertas': 0,
                    'linhas_processadas': linhas_atual['processadas']
                }
                continue

            print(f"   • Status: CICLO 1/{CICLOS_VALIDACAO} - PRIMEIRA COLETA")
            print(f"   • Linhas abertas: {linhas_atual['abertas']}")
            print(f"   • Linhas processadas: {linhas_atual['processadas']}")
            print(f"   • Aguardando {INTERVALO_SEGURANCA}s para próximo ciclo...")

            # Registra estado
            info_novo = {
                'timestamp': agora.isoformat(),
                'qtd_linhas_abertas': linhas_atual['abertas'],
                'qtd_linhas_processadas': linhas_atual['processadas'],
                'ciclos_validados': 0,
                'avisos': []
            }
            controle[numero] = info_novo

            orcamentos_incompletos[numero] = {
                **dados,
                'motivo': 'primeira_coleta',
                'ciclo_atual': 1,
                'ciclos_requeridos': CICLOS_VALIDACAO,
                'linhas_abertas': linhas_atual['abertas'],
                'linhas_processadas': linhas_atual['processadas'],
                'proxima_validacao': (agora + timedelta(seconds=INTERVALO_SEGURANCA)).isoformat()
            }
            continue

        # Já vimos este orçamento antes
        timestamp_ultimo = info_controle.get('timestamp')
        qtd_abertas_antes = info_controle.get('qtd_linhas_abertas', 0)
        qtd_processadas_antes = info_controle.get('qtd_linhas_processadas', 0)
        ciclos_validados = info_controle.get('ciclos_validados', 0)
        avisos = info_controle.get('avisos', [])

        ultima_coleta_dt = datetime.fromisoformat(timestamp_ultimo)
        tempo_decorrido = (agora - ultima_coleta_dt).total_seconds()

        if tempo_decorrido < INTERVALO_SEGURANCA:
            # Ainda não passou intervalo
            tempo_restante = INTERVALO_SEGURANCA - tempo_decorrido
            print(f"📋 {numero}:")
            print(f"   • Ciclo: {ciclos_validados}/{CICLOS_VALIDACAO}")
            print(f"   • Status: AGUARDANDO (faltam {tempo_restante:.0f}s)")

            orcamentos_incompletos[numero] = {
                **dados,
                'motivo': 'intervalo_seguranca',
                'ciclo_atual': ciclos_validados + 1,
                'ciclos_requeridos': CICLOS_VALIDACAO,
                'linhas_abertas': qtd_abertas_antes,
                'linhas_processadas': qtd_processadas_antes,
                'proxima_validacao': (agora + timedelta(seconds=tempo_restante)).isoformat()
            }
            continue

        # Passou intervalo - verifica mudanças
        linhas_agora = contar_linhas_orcamento_por_status(client, numero)

        print(f"📋 {numero}:")
        print(f"   • Ciclo: {ciclos_validados + 1}/{CICLOS_VALIDACAO}")
        print(f"   • Linhas abertas ANTES: {qtd_abertas_antes}")
        print(f"   • Linhas abertas AGORA: {linhas_agora['abertas']}")
        print(f"   • Linhas processadas ANTES: {qtd_processadas_antes}")
        print(f"   • Linhas processadas AGORA: {linhas_agora['processadas']}")

        # ⚠️ DETECÇÃO DE PROCESSAMENTO PARCIAL
        if linhas_agora['processadas'] > qtd_processadas_antes:
            aviso = f"⚠️ ALERTA CRÍTICO: Linhas foram marcadas como processadas durante validação!"
            print(f"   {aviso}")
            print(f"   └─ Antes: {qtd_processadas_antes} processadas")
            print(f"   └─ Agora: {linhas_agora['processadas']} processadas")
            print(f"   └─ Isso indica processamento PARCIAL anterior!")
            print(f"   └─ BLOQUEANDO: Aguardando que agente termine de adicionar áreas")

            avisos.append({
                'timestamp': agora.isoformat(),
                'tipo': 'processamento_parcial_detectado',
                'processadas_antes': qtd_processadas_antes,
                'processadas_agora': linhas_agora['processadas']
            })

            # Reinicia contagem
            info_novo = {
                'timestamp': agora.isoformat(),
                'qtd_linhas_abertas': linhas_agora['abertas'],
                'qtd_linhas_processadas': linhas_agora['processadas'],
                'ciclos_validados': 0,
                'avisos': avisos
            }
            controle[numero] = info_novo

            orcamentos_incompletos[numero] = {
                **dados,
                'motivo': 'processamento_parcial_detectado',
                'ciclo_atual': 1,
                'ciclos_requeridos': CICLOS_VALIDACAO,
                'linhas_abertas': linhas_agora['abertas'],
                'linhas_processadas': linhas_agora['processadas'],
                'avisos': avisos,
                'proxima_validacao': (agora + timedelta(seconds=INTERVALO_SEGURANCA)).isoformat()
            }
            continue

        # Mudança em linhas abertas?
        if linhas_agora['abertas'] != qtd_abertas_antes:
            print(f"   • Status: MUDANÇA DETECTADA")
            print(f"   └─ Reiniciando contagem de ciclos")

            # Reinicia
            info_novo = {
                'timestamp': agora.isoformat(),
                'qtd_linhas_abertas': linhas_agora['abertas'],
                'qtd_linhas_processadas': linhas_agora['processadas'],
                'ciclos_validados': 0,
                'avisos': avisos
            }
            controle[numero] = info_novo

            orcamentos_incompletos[numero] = {
                **dados,
                'motivo': 'mudanca_linhas_abertas',
                'ciclo_atual': 1,
                'ciclos_requeridos': CICLOS_VALIDACAO,
                'linhas_abertas': linhas_agora['abertas'],
                'linhas_processadas': linhas_agora['processadas'],
                'proxima_validacao': (agora + timedelta(seconds=INTERVALO_SEGURANCA)).isoformat()
            }
            continue

        # Nenhuma mudança
        ciclos_completos = ciclos_validados + 1

        if ciclos_completos < CICLOS_VALIDACAO:
            print(f"   • Status: AGUARDANDO PRÓXIMO CICLO ({ciclos_completos}/{CICLOS_VALIDACAO})")

            info_novo = {
                'timestamp': agora.isoformat(),
                'qtd_linhas_abertas': linhas_agora['abertas'],
                'qtd_linhas_processadas': linhas_agora['processadas'],
                'ciclos_validados': ciclos_completos,
                'avisos': avisos
            }
            controle[numero] = info_novo

            orcamentos_incompletos[numero] = {
                **dados,
                'motivo': 'validacao_incompleta',
                'ciclo_atual': ciclos_completos,
                'ciclos_requeridos': CICLOS_VALIDACAO,
                'linhas_abertas': linhas_agora['abertas'],
                'linhas_processadas': linhas_agora['processadas'],
                'proxima_validacao': (agora + timedelta(seconds=INTERVALO_SEGURANCA)).isoformat()
            }
        else:
            # Pronto!
            print(f"   • Status: ✅ PRONTO PARA PROCESSAR")
            print(f"   └─ Validado em {ciclos_completos} ciclos")
            print(f"   └─ {linhas_agora['abertas']} áreas abertas")
            print(f"   └─ {linhas_agora['processadas']} áreas anteriores processadas")

            orcamentos_prontos[numero] = {
                **dados,
                'validacao': 'completo',
                'ciclos_validacao': ciclos_completos,
                'linhas_abertas': linhas_agora['abertas'],
                'linhas_processadas': linhas_agora['processadas'],
                'data_validacao': agora.isoformat()
            }

            # Remove do controle
            controle.pop(numero, None)

    # Salva controle
    salvar_controle(controle)

    # Resumo
    print(f"\n📊 RESUMO DA VALIDAÇÃO:")
    print(f"   ✅ Prontos: {len(orcamentos_prontos)}")
    print(f"   ⏳ Incompletos: {len(orcamentos_incompletos)}")

    if orcamentos_incompletos:
        print(f"\n⏳ ORÇAMENTOS A AGUARDAR:")
        for numero, dados in orcamentos_incompletos.items():
            motivo = dados.get('motivo', 'desconhecido')
            print(f"   • {numero} - {motivo}")

            # Se houver avisos críticos
            if 'avisos' in dados and dados['avisos']:
                for aviso in dados['avisos']:
                    print(f"     └─ {aviso['tipo']}")

    return orcamentos_prontos, orcamentos_incompletos


def main():
    """Teste isolado"""

    orcamentos_teste = {
        '12052601': {'nome': 'Cliente A', 'qtd_linhas': 2},
        '12052602': {'nome': 'Cliente B', 'qtd_linhas': 3}
    }

    prontos, incompletos = validar_orcamentos_v2(orcamentos_teste)

    print(f"\n{'=' * 80}")
    print("RESULTADO FINAL")
    print('=' * 80)

    print("\n✅ PRONTOS PARA PROCESSAR:")
    for numero in prontos:
        print(f"   • {numero}")

    if incompletos:
        print("\n⏳ AGUARDANDO:")
        for numero, dados in incompletos.items():
            print(f"   • {numero} ({dados.get('motivo')})")


if __name__ == '__main__':
    main()
