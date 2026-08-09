#!/usr/bin/env python3
"""
Script wrapper para processar um orçamento automaticamente

Fluxo:
1. Encontra pasta do orçamento (orcamentos/orcamento_XXXX_Nome/)
2. Localiza arquivos de entrada (obra-*.csv, paralisacao_*.csv)
3. Executa main.py para calcular INSS
4. MANTÉM arquivos de entrada para conferência e rastreabilidade
5. Gera arquivos de saída (inss-*.csv, inss-*-otimizado.csv)

Benefícios:
- Entrada preservada para auditoria e conferência
- Rastreabilidade completa do processamento
- Fácil revisar dados originais vs resultados

Aceita: número do orçamento como argumento
Exemplo: python3 processar_orcamento.py 12052601
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
import shutil
import subprocess
from pathlib import Path

# Adiciona diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def encontrar_pasta_orcamento(numero_orcamento):
    """Encontra pasta do orçamento"""
    pasta_orcamentos = './orcamentos'

    if not os.path.exists(pasta_orcamentos):
        return None

    pasta_orc = None
    # Procura pasta com padrão orcamento_XXXX_NomeCliente
    import glob
    pattern = os.path.join(pasta_orcamentos, f'orcamento_{numero_orcamento}_*')
    pastas = glob.glob(pattern)
    if pastas:
        pasta_orc = pastas[0]
    else:
        # Se não encontrar com sufixo, tenta sem (compatibilidade)
        pasta_orc = os.path.join(pasta_orcamentos, f'orcamento_{numero_orcamento}')

    if os.path.exists(pasta_orc):
        return pasta_orc

    return None


def listar_arquivos_orcamento(pasta_orc):
    """Lista arquivos CSV da pasta"""
    arquivos = {
        'obra': None,
        'paralisacao': None
    }

    for arquivo in os.listdir(pasta_orc):
        if arquivo.startswith('obra-') and arquivo.endswith('.csv'):
            arquivos['obra'] = os.path.join(pasta_orc, arquivo)
        elif arquivo.startswith('paralisacao_obra-') and arquivo.endswith('.csv'):
            arquivos['paralisacao'] = os.path.join(pasta_orc, arquivo)

    return arquivos


def main():
    """Fluxo principal"""

    print("\n" + "=" * 80)
    print("PROCESSAR ORÇAMENTO - AUTOMÁTICO")
    print("=" * 80 + "\n")

    if len(sys.argv) < 2:
        print("❌ Uso: python3 processar_orcamento.py <numero_orcamento>")
        print("   Exemplo: python3 processar_orcamento.py 12052601")
        return 1

    numero_orcamento = sys.argv[1]

    print(f"🔍 Procurando orçamento: {numero_orcamento}\n")

    # 1. Encontra pasta
    pasta_orc = encontrar_pasta_orcamento(numero_orcamento)

    if not pasta_orc:
        print(f"❌ Pasta não encontrada para orçamento {numero_orcamento}")
        print(f"   Esperado em: ./orcamentos/orcamento_{numero_orcamento}/")
        return 1

    print(f"✓ Pasta encontrada: {pasta_orc}\n")

    # 2. Lista arquivos
    arquivos = listar_arquivos_orcamento(pasta_orc)

    if not arquivos['obra']:
        print(f"❌ Arquivo 'obra-*.csv' não encontrado em {pasta_orc}")
        return 1

    print("📄 Arquivos:")
    print(f"   ✓ Obra: {os.path.basename(arquivos['obra'])}")

    if arquivos['paralisacao']:
        print(f"   ✓ Paralisação: {os.path.basename(arquivos['paralisacao'])}")
    else:
        print(f"   ⚠️ Paralisação: não encontrada (ok se não houver)")

    # 3. Prepara paralisacao para main.py
    paralisacao_dest = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'paralisacao.csv'
    )

    print(f"📋 Atualizando paralisacao.csv para main.py...")

    # Se tiver paralisacao específica do orçamento, copia
    if arquivos['paralisacao']:
        shutil.copy(arquivos['paralisacao'], paralisacao_dest)
        print(f"   ✓ Paralisacao do orçamento {numero_orcamento} copiada")
        print(f"   ✓ Arquivo: {paralisacao_dest}\n")
    else:
        # Se não tiver paralisacao, cria com data teórica 01/1900 (não afeta)
        print(f"   ⚠️ Orçamento {numero_orcamento} sem paralisacao")
        print(f"   📝 Criando paralisacao teórica (01/1900)...")
        with open(paralisacao_dest, 'w', encoding='utf-8') as f:
            f.write("Mês/Ano\n")
            f.write("01/1900\n")
        print(f"   ✓ Paralisacao teórica criada")
        print(f"   ✓ Arquivo: {paralisacao_dest}\n")

    # 4. Executa main.py para cálculo INSS
    print("\n" + "=" * 80)
    print("EXECUTANDO MAIN.PY - CÁLCULO INSS")
    print("=" * 80 + "\n")

    # Chama main.py diretamente (todos os imports locais, caminhos relativos)
    # paralisacao.csv já foi atualizado e está pronto para uso
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Arquivo de entrada (pode ser relativo ou absoluto)
    resultado = subprocess.run(
        [sys.executable, 'main.py', arquivos['obra']],
        cwd=script_dir
    )

    if resultado.returncode != 0:
        print(f"\n❌ Erro ao processar orçamento {numero_orcamento}")
        print(f"   Marcando como 'erro' no Supabase...\n")

        # Marca como erro no Supabase para não tentar reprocessar
        subprocess.run(
            [sys.executable, 'marcar_orcamento_erro.py', numero_orcamento, 'erro_processamento'],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        return 1

    print("\n" + "=" * 80)
    print("✅ PROCESSAMENTO CONCLUÍDO")
    print("=" * 80 + "\n")

    print(f"Resultados em: {pasta_orc}/")
    print("  • obra-*.csv (entrada - mantido para conferência)")
    print("  • paralisacao_obra-*.csv (entrada - mantido para conferência, se houver)")
    print("  • inss-*.csv (saída)")
    print("  • inss-*-otimizado.csv (saída otimizada)")
    print("\n📌 Nota: Google Drive será sincronizado após populate de paulo_inss")
    print("         na ETAPA 4 (Atualizar Status)\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
