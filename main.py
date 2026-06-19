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
    carregar_vau_csv,
    carregar_honorarios_csv,
    obter_percentual_honorario,
    atualizar_honorarios_supabase
)
from optimization_distribution import (
    carregar_tabela_remuneracao,
    carregar_distribuicao_csv,
    otimizar_distribuicao,
    exportar_csv_otimizado,
    coletar_avisos_otimizacao
)
import copy


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

        # OTIMIZAÇÃO - Distribuição otimizada de recibos
        try:
            print("\n" + "=" * 80)
            print("OTIMIZAÇÃO DE DISTRIBUIÇÃO DE RECIBOS")
            print("=" * 80 + "\n")

            # Carrega tabela de limites e distribuição
            print("📊 Carregando dados para otimização...")
            tabela_limites = carregar_tabela_remuneracao()
            meses, _ = carregar_distribuicao_csv(arquivo_distribuicao)

            # Extrai RMT do arquivo de distribuição
            rmt_esperado = 0.0
            with open(arquivo_distribuicao, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if 'RMT Otimizado Final' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            rmt_esperado = float(parts[1].strip())
                        break

            # Otimização automática
            print("\n🔄 Calculando distribuição otimizada...")
            data_analise = datetime.now()
            meses_otimizados = otimizar_distribuicao(
                copy.deepcopy(meses),
                tabela_limites,
                data_analise,
                'autonomo'
            )

            # Resumo
            max_autonomos = max((m.qtd_autonomos for m in meses_otimizados), default=0)
            inss_total = sum(m.total_otimizado for m in meses_otimizados)

            print(f"\n✓ Otimização concluída!")
            print(f"  💼 Autônomos recomendados: {max_autonomos}")
            print(f"  💰 INSS Total: R$ {inss_total:,.2f}")

            # Extrai INSS original do arquivo de distribuição para calcular economia
            inss_original = 0.0
            with open(arquivo_distribuicao, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if 'INSS sem Otimização,' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            inss_original = float(parts[1].strip())
                        break

            # Coleta avisos da otimização
            avisos = coletar_avisos_otimizacao(meses_otimizados, rmt_esperado)

            # Exporta otimização (na mesma pasta da entrada)
            arquivo_otimizado = os.path.join(pasta_entrada, f"inss-{nome_base}-otimizado.csv")
            exportar_csv_otimizado(
                meses_otimizados,
                arquivo_otimizado,
                'autonomo',
                arquivo_distribuicao,
                avisos,
                inss_original,
                data_analise
            )
            print(f"\n💾 Arquivo gerado: {arquivo_otimizado}")

            # Atualiza honorários no Supabase
            economia_real = resultado.inss_original - resultado.inss_otimizado if hasattr(resultado, 'inss_original') else 0
            if economia_real > 0:
                honorarios_dict = carregar_honorarios_csv()
                area_total = sum(area.area_equivalente for area in resultado.calculos_areas) if resultado.calculos_areas else 0
                perc_honorario = obter_percentual_honorario(area_total, honorarios_dict)
                valor_honorarios = economia_real * (perc_honorario / 100.0)

                # Extrai número do orçamento do nome do arquivo (ex: "obra-12052601" -> "12052601")
                numero_orcamento = nome_base.split('-')[-1] if '-' in nome_base else nome_base
                atualizar_honorarios_supabase(numero_orcamento, valor_honorarios)

        except Exception as e:
            print(f"\n⚠️ Aviso: Não foi possível gerar versão otimizada: {e}")
            import traceback
            traceback.print_exc()

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
