#!/usr/bin/env python3
"""
Script orquestrador do pipeline completo - v6_agente_ia
Compatível com Windows, Linux e macOS
Executa: Coleta → Organiza → Marca → Valida → Processa → Sincroniza
"""

import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.absolute()))


def executar_comando(script_name, descricao):
    """Executa script Python e trata erros"""
    print(f"\n{'=' * 80}")
    print(descricao)
    print('=' * 80 + "\n")

    # Usar sys.executable para compatibilidade entre SOs
    resultado = subprocess.run([sys.executable, script_name])

    if resultado.returncode != 0:
        print(f"\n❌ Erro ao executar: {descricao}")
        return False

    return True


def main():
    """Fluxo principal do pipeline"""

    print("\n" + "=" * 80)
    print("PIPELINE AUTOMÁTICO - COLETA E PROCESSAMENTO")
    print("=" * 80)

    # ETAPA 1: Coletar dados do Supabase
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + "ETAPA 1: COLETAR DADOS DO SUPABASE".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    if not executar_comando("coletar.py", "Coletando orçamentos..."):
        return 1

    # ETAPA 2: Validar e organizar
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + "ETAPA 2: VALIDAR E ORGANIZAR PASTAS".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    if not executar_comando("validador_orcamentos_v2.py", "Organizando pastas..."):
        return 1

    # ETAPA 2.5: Marcar como 'processando'
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + "ETAPA 2.5: MARCAR COMO 'PROCESSANDO'".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    if not executar_comando("marcar_processando.py", "Marcando 'aberto' → 'processando'..."):
        print("\n⚠️ Aviso: Erro ao marcar processando, mas pipeline continua")

    # ETAPA 2.6: Validar aguardo de ciclo
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + "ETAPA 2.6: VALIDAR AGUARDO DE CICLO".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        from validar_aguardando_ciclo import main as validar
        orcamentos_prontos = validar()
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível validar: {e}")
        print("   Pipeline continua...")
        orcamentos_prontos = {}

    # ETAPA 3: Processar cada orçamento PRONTO
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + "ETAPA 3: PROCESSAR ORÇAMENTOS PRONTOS".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    if not orcamentos_prontos:
        print("\n⏳ Nenhum orçamento pronto para processar")
        print("   (Aguardando próximo ciclo)\n")
        return 0

    print(f"\n📋 Orçamentos prontos: {len(orcamentos_prontos)}\n")
    for numero in sorted(orcamentos_prontos.keys()):
        print(f"   • {numero}")

    resultados = {}
    for numero in sorted(orcamentos_prontos.keys()):
        try:
            print(f"\n{'─' * 80}")
            print(f"Processando: {numero}")
            print('─' * 80)

            # Usar lista de argumentos para compatibilidade com todos os SOs
            resultado = subprocess.run([sys.executable, "processar_orcamento.py", str(numero)])
            sucesso = resultado.returncode == 0
            resultados[numero] = sucesso

            if sucesso:
                print(f"✅ Processado: {numero}")

                # ETAPA 4: Atualizar status para 'processado' + Google Drive sync
                print(f"\n{'─' * 80}")
                print(f"Finalizando: {numero}")
                print('─' * 80)

                resultado_finalizacao = subprocess.run([sys.executable, "atualizar_status_processado.py", str(numero)])

                if resultado_finalizacao.returncode != 0:
                    print(f"⚠️ Aviso: Erro ao finalizar {numero}, mas processamento completou")
            else:
                print(f"❌ Erro ao processar: {numero}")
                print(f"   Orçamento marcado como 'erro' no Supabase")
                print(f"   Não será reprocessado nos próximos ciclos")

        except Exception as e:
            print(f"\n❌ EXCEÇÃO ao processar {numero}: {e}")
            import traceback
            traceback.print_exc()
            resultados[numero] = False
            print(f"   Loop continua com próximo orçamento...")

    # Resumo
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + "RESUMO FINAL".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    sucessos = sum(1 for v in resultados.values() if v)
    print(f"\n✅ Processados: {sucessos}/{len(resultados)}")

    print("\n" + "=" * 80)
    print("✅ PIPELINE CONCLUÍDO!")
    print("=" * 80 + "\n")

    return 0 if sucessos == len(resultados) else 1


if __name__ == '__main__':
    sys.exit(main())
