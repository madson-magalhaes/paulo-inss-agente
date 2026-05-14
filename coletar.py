#!/usr/bin/env python3
"""
Script de Coleta - Busca orçamentos do Supabase
Compatível com Windows, Linux e macOS
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
    import pandas as pd
except ImportError as e:
    print(f"❌ Erro: {e}")
    print("Instale com: pip install supabase pandas python-dotenv")
    sys.exit(1)


def formatar_data(data_str):
    """Formata data de MM/YYYY para DD/MM/YYYY (usa primeiro dia do mês)"""
    data_str = str(data_str).strip()

    if not data_str or '/' not in data_str:
        return data_str

    partes = data_str.split('/')

    if len(partes) == 3 and len(partes[0]) == 2 and len(partes[0]) <= 2:
        return data_str

    if len(partes) == 2:
        mes, ano = partes
        return f"01/{mes}/{ano}"

    return data_str


def coletar_orcamentos():
    """Coleta orçamentos do Supabase e exporta CSVs direto nas pastas dos orçamentos"""
    try:
        print("\n" + "=" * 80)
        print("COLETA DE ORÇAMENTOS - SUPABASE")
        print("=" * 80 + "\n")

        tabela = 'paulo_orcamentos'
        col_status = 'status_orcamento'
        prefixo = 'obra'

        colunas_esperadas = [
            'nome', 'telefone', 'estado', 'tipo', 'categoria', 'material', 'area_m2',
            'is_principal', 'coberta', 'data_inicio', 'data_fim',
            'concreto_usinado', 'paralisacao', 'prefabricado'
        ]

        print("🔌 Conectando ao Supabase...")
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        if not url or not key:
            print("❌ SUPABASE_URL ou SUPABASE_KEY não configurado em .env")
            return {}

        client = create_client(url, key)
        print("✓ Conexão bem-sucedida!\n")

        print("📥 Detectando orçamentos com items em 'aberto' ou 'processando'...")

        response_ativos = client.table(tabela).select(
            'numero_orcamento'
        ).in_(col_status, ['aberto', 'processando']).execute()

        if not response_ativos.data:
            print("⚠️ Nenhum orçamento encontrado com items em 'aberto' ou 'processando'")
            return {}

        df_ativos = pd.DataFrame(response_ativos.data)
        numeros_ativos = set(df_ativos['numero_orcamento'].unique())
        print(f"✓ {len(numeros_ativos)} orçamento(s) encontrado(s)\n")

        print("🔄 Coletando dados COMPLETOS para cada orçamento...")

        pasta_orcamentos = Path("orcamentos")
        pasta_orcamentos.mkdir(exist_ok=True)

        print(f"✓ {len(numeros_ativos)} orçamento(s) identificado(s)\n")

        print("💾 Exportando CSVs nas pastas dos orçamentos...")
        orcamentos = {}
        csvs_criados = 0

        for numero_orc in sorted(numeros_ativos):
            response = client.table(tabela).select("*").eq(
                'numero_orcamento', numero_orc
            ).execute()

            if not response.data:
                print(f"  ⚠️ {numero_orc}: Nenhum item encontrado (skip)")
                continue

            df = pd.DataFrame(response.data)
            orcamentos[numero_orc] = response.data[0]

            nome_cliente = orcamentos[numero_orc].get('nome', '').strip()
            if nome_cliente:
                pasta_orc = pasta_orcamentos / f"orcamento_{numero_orc}_{nome_cliente}"
            else:
                pasta_orc = pasta_orcamentos / f"orcamento_{numero_orc}"

            pasta_orc.mkdir(exist_ok=True)

            df_formatado = df[colunas_esperadas].copy()

            for col_data in ['data_inicio', 'data_fim']:
                if col_data in df_formatado.columns:
                    df_formatado[col_data] = df_formatado[col_data].apply(
                        lambda x: formatar_data(str(x)) if pd.notna(x) else x
                    )

            if 'prefabricado' in df_formatado.columns:
                df_formatado['prefabricado'] = df_formatado['prefabricado'].fillna('nao')

            nome_arquivo = f"{prefixo}-{numero_orc}.csv"
            arquivo_destino = pasta_orc / nome_arquivo

            df_formatado.to_csv(
                arquivo_destino,
                sep=',',
                index=False,
                encoding='utf-8'
            )

            csvs_criados += 1
            print(f"  ✓ {pasta_orc.name}/{nome_arquivo} ({len(df_formatado)} linha(s))")

            meses_para = df['meses_paralisados'].iloc[0] if 'meses_paralisados' in df.columns else None

            if meses_para and not pd.isna(meses_para) and str(meses_para).strip():
                meses_list = str(meses_para).strip().split(',')
                df_paralisacao = pd.DataFrame({
                    'Mês/Ano': [m.strip() for m in meses_list]
                })

                nome_arquivo_para = f"paralisacao_{prefixo}-{numero_orc}.csv"
                arquivo_para_destino = pasta_orc / nome_arquivo_para

                df_paralisacao.to_csv(
                    arquivo_para_destino,
                    sep=',',
                    index=False,
                    encoding='utf-8'
                )

                print(f"    ✓ {pasta_orc.name}/{nome_arquivo_para} ({len(df_paralisacao)} mês/meses)")

        print("\n" + "=" * 80)
        print("✅ COLETA CONCLUÍDA")
        print("=" * 80)
        print(f"Total: {csvs_criados} CSV(s) criado(s)")
        print(f"Localização: ./orcamentos/orcamento_XXXXX_ClientName/\n")

        return orcamentos

    except Exception as e:
        print(f"❌ Erro ao coletar: {e}")
        import traceback
        traceback.print_exc()
        return {}


if __name__ == '__main__':
    orcamentos = coletar_orcamentos()
    sys.exit(0)
