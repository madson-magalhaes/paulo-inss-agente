#!/usr/bin/env python3
"""
Script de Automação - Pipeline a cada 60 segundos
Compatível com Windows, Linux e macOS
"""

import subprocess
import time
import sys
import os
from datetime import datetime
from pathlib import Path

INTERVALO = 60


def formatar_hora():
    """Retorna hora formatada"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def imprimir_separador():
    """Imprime separador visual"""
    print("\n" + "=" * 80)


def executar_pipeline():
    """Executa o pipeline completo"""
    print(f"\n🚀 [{formatar_hora()}] Iniciando pipeline...")

    # Usar executar_pipeline.py (compatível com todos os SOs)
    resultado = subprocess.run([sys.executable, "executar_pipeline.py"])

    if resultado.returncode == 0:
        print(f"✅ [{formatar_hora()}] Pipeline concluído com sucesso!")
    else:
        print(f"❌ [{formatar_hora()}] Erro ao executar pipeline (código: {resultado.returncode})")

    return resultado.returncode == 0


def main():
    """Fluxo principal de automação"""

    imprimir_separador()
    print("AUTOMAÇÃO DE PIPELINE - EXECUÇÃO A CADA 60 SEGUNDOS")
    imprimir_separador()

    print(f"\n📋 Configuração:")
    print(f"   • Intervalo: 60 segundos")
    print(f"   • Comando: python3 executar_pipeline.py")
    print(f"   • Diretório: {Path.cwd()}")
    print(f"\n⏱️ Próxima execução: {formatar_hora()}")
    print(f"\n⚠️ Para parar: Pressione Ctrl+C")

    imprimir_separador()

    contador = 0
    sucessos = 0
    erros = 0

    try:
        while True:
            contador += 1

            # Executa pipeline
            sucesso = executar_pipeline()
            if sucesso:
                sucessos += 1
            else:
                erros += 1

            # Calcula próxima execução
            proxima = datetime.fromtimestamp(time.time() + INTERVALO).strftime("%H:%M:%S")

            # Exibe resumo
            print(f"\n📊 Resumo (Execução #{contador}):")
            print(f"   • Sucessos: {sucessos}")
            print(f"   • Erros: {erros}")
            print(f"   • Próxima execução às: {proxima}")
            print(f"\n⏳ Aguardando próxima execução...")

            imprimir_separador()

            # Aguarda intervalo configurado
            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        # Usuário pressionou Ctrl+C
        imprimir_separador()
        print("\n⛔ Automação interrompida pelo usuário\n")

        print(f"📊 Resumo Final:")
        print(f"   • Total de execuções: {contador}")
        print(f"   • Sucessos: {sucessos}")
        print(f"   • Erros: {erros}")
        if contador > 0:
            print(f"   • Taxa de sucesso: {(sucessos/contador*100):.1f}%")

        imprimir_separador()
        print("\n✅ Automação finalizada\n")

        return 0

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
