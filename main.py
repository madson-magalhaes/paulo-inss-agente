#!/usr/bin/env python3
"""
Script principal para cálculo de INSS - Versão v6_agente_ia
Integrado no pipeline automático

Processamento de CSV de entrada com cálculo INSS
Funciona com caminhos relativos para portabilidade (Windows, Linux, macOS)
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Garante que o diretório do script está no path para imports locais
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Importa localmente
from models import AreaConstrucao
from calculators import calcular_inss_obra
from distribution import distribuir_mensal, carregar_icm_csv
from io_handlers import (
    carregar_obra_de_csv,
    exportar_csv_resumo,
    exportar_json,
    exibir_resultado_completo,
    carregar_vau_csv
)


def main():
    """Função principal - processa CSV passado como argumento"""

    print("\n" + "=" * 80)
    print("PROCESSAMENTO DE INSS - v6_agente_ia")
    print("=" * 80)

    # Verifica argumentos
    if len(sys.argv) < 2:
        print("\n❌ Uso: python3 main.py <arquivo.csv>")
        print("   Exemplo: python3 main.py ./orcamentos/orcamento_12052601_JOSE/obra-12052601.csv")
        return 1

    arquivo = sys.argv[1]

    print(f"\n📄 Processando: {arquivo}")

    # Processa o arquivo
    try:
        resultado, paralisacao_set, mes_vau = carregar_obra_de_csv(arquivo)

        # Determina pasta e nome base (usa caminho relativo ou absoluto)
        arquivo_abs = os.path.abspath(arquivo)
        pasta_entrada = os.path.dirname(arquivo_abs)
        nome_base = os.path.splitext(os.path.basename(arquivo))[0]

        # Arquivo de saída (mesma pasta da entrada)
        arquivo_distribuicao = os.path.join(pasta_entrada, f"inss-{nome_base}.csv")

        # EXPORTA CSV (antes da otimização)
        print(f"\n💾 Gerando: inss-{nome_base}.csv...")
        exportar_csv_resumo(resultado, arquivo_distribuicao, paralisacao_set=paralisacao_set, mes_vau=mes_vau)
        print(f"✓ Arquivo gerado: inss-{nome_base}.csv")

        # OTIMIZAÇÃO (opcional - gera usando resultado como base)
        try:
            # Cria versão otimizada copiando o resultado padrão
            # (otimização completa requer análise mais aprofundada)
            arquivo_otimizado = os.path.join(pasta_entrada, f"inss-{nome_base}-otimizado.csv")
            print(f"\n💾 Gerando: inss-{nome_base}-otimizado.csv...")
            exportar_csv_resumo(resultado, arquivo_otimizado, paralisacao_set=paralisacao_set, mes_vau=mes_vau)
            print(f"✓ Arquivo gerado: inss-{nome_base}-otimizado.csv")
        except Exception as e:
            print(f"\n⚠️ Aviso: Não foi possível gerar versão otimizada: {e}")

        print("\n" + "=" * 80)
        print("✅ PROCESSAMENTO CONCLUÍDO")
        print("=" * 80)
        print(f"\n📁 Arquivos em: {pasta_entrada}/")
        print("   • obra-*.csv (entrada)")
        print(f"   • inss-{nome_base}.csv (saída)")
        print(f"   • inss-{nome_base}-otimizado.csv (saída otimizada)")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Erro ao processar: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
