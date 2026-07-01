#!/usr/bin/env python3
"""Script para marcar orçamento como processado e sincronizar Google Drive"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("❌ Erro: supabase não está instalado")
    sys.exit(1)

ARQUIVO_SINCRONIZACOES = './.claude/drive_sincronizacoes.json'

def carregar_sincronizacoes():
    Path(os.path.dirname(ARQUIVO_SINCRONIZACOES)).mkdir(parents=True, exist_ok=True)
    if os.path.exists(ARQUIVO_SINCRONIZACOES):
        try:
            with open(ARQUIVO_SINCRONIZACOES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_sincronizacoes(dados):
    Path(os.path.dirname(ARQUIVO_SINCRONIZACOES)).mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_SINCRONIZACOES, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2)

def extrair_dados_inss(arquivo_path):
    """Extrai dados INSS de um arquivo CSV"""
    dados = {
        'inss_cenario_3': None,
        'telefone': None,
        'honorarios': None,
    }

    with open(arquivo_path, 'r', encoding='utf-8') as f:
        content = f.read()

        # Extrai INSS do Cenário 3 (Otimizado)
        if "MATRIZ DE COMPARAÇÃO TRIBUTÁRIA" in content:
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith("3. Otimizado"):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 5:
                        try:
                            dados['inss_cenario_3'] = float(parts[4].replace(',', '.'))
                        except:
                            pass

        # Extrai telefone
        if "[DADOS DO PROJETO]" in content:
            for line in content.split('\n'):
                if "Telefone do Contato" in line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        dados['telefone'] = parts[1]
                    break

        # Extrai honorários
        if "[PARÂMETROS E OPERAÇÃO]" in content:
            for line in content.split('\n'):
                if "Honorários Estimados" in line and "Percentual" not in line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        try:
                            valor_str = parts[1].strip()
                            if 'R$' in valor_str:
                                valor_str = valor_str.replace('R$', '').strip()
                            if ',' in valor_str:
                                valor_str = valor_str.replace('.', '').replace(',', '.')
                            dados['honorarios'] = float(valor_str)
                        except Exception as e:
                            print(f"   ⚠️ Erro ao extrair honorários: {e}")
                    break

    return dados


def inserir_dados_paulo_inss(numero_orcamento):
    """Insere dados resumidos do INSS na tabela paulo_inss"""
    try:
        import glob
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            print("⚠️ Supabase não configurado, pulando paulo_inss")
            return False

        client = create_client(url, key)
        print(f"\n📊 Inserindo dados em paulo_inss...")

        pasta_orcamentos = Path("orcamentos")
        pattern = str(pasta_orcamentos / f"orcamento_{numero_orcamento}_*")
        pastas = glob.glob(pattern)

        if not pastas:
            print(f"⚠️ Pasta do orçamento não encontrada")
            return False

        pasta_orc = Path(pastas[0])
        pasta_nome = os.path.basename(pasta_orc)
        nome_cliente = pasta_nome.replace(f"orcamento_{numero_orcamento}_", "").strip()

        # Procura ambos os arquivos (base e otimizado)
        arquivo_base = None
        arquivo_otimizado = None

        arquivos_inss = list(pasta_orc.glob("inss-*.csv"))
        for arq in arquivos_inss:
            if "otimizado" in arq.name:
                arquivo_otimizado = arq
            else:
                arquivo_base = arq

        if not arquivo_base and not arquivo_otimizado:
            print(f"⚠️ Nenhum arquivo INSS encontrado")
            return False

        # Extrai dados de ambos os arquivos
        dados_base = None
        dados_otimizado = None

        if arquivo_base:
            dados_base = extrair_dados_inss(arquivo_base)
        if arquivo_otimizado:
            dados_otimizado = extrair_dados_inss(arquivo_otimizado)

        # Seleciona o melhor cenário (menor INSS)
        melhor_dados = None
        arquivo_usado = None

        if dados_base and dados_otimizado:
            # Ambos existem - compara
            if dados_base['inss_cenario_3'] and dados_otimizado['inss_cenario_3']:
                if dados_otimizado['inss_cenario_3'] < dados_base['inss_cenario_3']:
                    melhor_dados = dados_otimizado
                    arquivo_usado = "otimizado"
                else:
                    melhor_dados = dados_base
                    arquivo_usado = "base"
        elif dados_otimizado:
            melhor_dados = dados_otimizado
            arquivo_usado = "otimizado"
        elif dados_base:
            melhor_dados = dados_base
            arquivo_usado = "base"

        if not melhor_dados or not melhor_dados['inss_cenario_3']:
            print(f"⚠️ Não foi possível extrair INSS dos arquivos")
            return False

        print(f"   Usando cenário {arquivo_usado} (INSS: R$ {melhor_dados['inss_cenario_3']:,.2f})")

        # Extrai também o INSS do Cenário 1 (sem redução) do melhor arquivo
        inss_sem_reducao = None
        if arquivo_base:
            with open(arquivo_base, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("1. Padrão"):
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 5:
                            try:
                                inss_sem_reducao = float(parts[4].replace(',', '.'))
                            except:
                                pass
                        break

        if not inss_sem_reducao:
            inss_sem_reducao = melhor_dados['inss_cenario_3']  # Fallback

        percentual_economia = ((inss_sem_reducao - melhor_dados['inss_cenario_3']) / inss_sem_reducao) * 100 if inss_sem_reducao > 0 else 0

        # Calcula INSS com honorários (novo)
        honorarios_valor = melhor_dados['honorarios'] or 0.0
        honorarios_valor = max(honorarios_valor, 1500.0)
        inss_com_honorarios = melhor_dados['inss_cenario_3'] + honorarios_valor
        percentual_inss_com_honorarios = ((inss_sem_reducao - inss_com_honorarios) / inss_sem_reducao * 100) if inss_sem_reducao > 0 else 0

        dados_inss = {
            'nome': nome_cliente,
            'telefone': melhor_dados['telefone'] or '',
            'numero_orcamento': int(numero_orcamento),
            'inss_sem_reducao': inss_sem_reducao,
            'inss_otimizado': melhor_dados['inss_cenario_3'],
            'percentual_economia': percentual_economia,
            'honorarios': melhor_dados['honorarios'] or 0.0,
            'inss_com_honorarios': inss_com_honorarios,
            'percentual_inss_com_honorarios': percentual_inss_com_honorarios,
        }

        print(f"   Nome: {nome_cliente}")
        print(f"   INSS sem redução: R$ {inss_sem_reducao:.2f}")
        print(f"   INSS final: R$ {melhor_dados['inss_cenario_3']:.2f}")
        print(f"   Honorários: R$ {honorarios_valor:.2f}")
        print(f"   INSS com honorários: R$ {inss_com_honorarios:.2f}")
        print(f"   Economia: {percentual_economia:.2f}%")
        print(f"   % com Honorários: {percentual_inss_com_honorarios:.2f}%")

        response = client.table('paulo_inss').insert(dados_inss).execute()

        if response.data:
            print(f"\n✓ Dados inseridos em paulo_inss")
            return True
        else:
            print(f"⚠️ Nenhuma linha inserida")
            return False

    except Exception as e:
        print(f"❌ Erro ao inserir em paulo_inss: {e}")
        return False

def marcar_como_processado(numero_orcamento):
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            print("⚠️ Supabase não configurado")
            return False

        client = create_client(url, key)
        print(f"\n📝 Marcando orçamento como processado...")

        response = client.table('paulo_orcamentos').select('id').eq('numero_orcamento', numero_orcamento).eq('status_orcamento', 'processando').execute()
        qtd = len(response.data) if response.data else 0

        if qtd == 0:
            print(f"⚠️ Nenhum registro processando encontrado")
            return False

        client.table('paulo_orcamentos').update({'status_orcamento': 'processado'}).eq('numero_orcamento', numero_orcamento).eq('status_orcamento', 'processando').execute()
        print(f"✓ {qtd} registro(s) marcado(s)")
        return True

    except Exception as e:
        print(f"❌ Erro ao marcar: {e}")
        return False

def sincronizar_google_drive(numero_orcamento):
    try:
        # Tentar usar o script com token do .env (para VPS)
        try:
            from google_drive_sync_with_token import main as sync_drive
            print(f"\n📤 Usando token do .env para sincronização...")
        except ImportError:
            # Fallback para script original (com geração de token)
            from google_drive_sync import main as sync_drive
            print(f"\n📤 Usando script padrão com autorização...")

        print(f"   Orçamento: {numero_orcamento}")

        resultado = sync_drive(numero_orcamento, verbose=True)

        if resultado == 0:
            print(f"\n✅ Sincronização com Google Drive concluída!")
            from datetime import datetime
            sincronizacoes = carregar_sincronizacoes()
            sincronizacoes[numero_orcamento] = {'data': datetime.now().isoformat(), 'status': 'completo'}
            salvar_sincronizacoes(sincronizacoes)
            print(f"📝 Registro salvo em: {ARQUIVO_SINCRONIZACOES}")
            return True
        else:
            print(f"❌ Erro ao sincronizar com Google Drive")
            return False

    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")
        import traceback
        traceback.print_exc()
        return False

def validar_arquivos_inss(numero_orcamento):
    import glob
    pasta_orcamentos = Path("orcamentos")
    pattern = str(pasta_orcamentos / f"orcamento_{numero_orcamento}_*")
    pastas = glob.glob(pattern)

    if not pastas:
        return False

    pasta_orc = Path(pastas[0])
    arquivos_inss = list(pasta_orc.glob("inss-*.csv"))

    if not arquivos_inss:
        return False

    print(f"\n✓ Arquivos INSS validados:")
    for arquivo in sorted(arquivos_inss):
        print(f"   • {arquivo.name}")

    return True

def main():
    print("\n" + "=" * 80)
    print("FINALIZAR CICLO: PAULO_INSS + STATUS PROCESSADO + GOOGLE DRIVE")
    print("=" * 80)

    if len(sys.argv) < 2:
        print("❌ Uso: python3 atualizar_status_processado.py <numero_orcamento>")
        return 1

    numero_orcamento = sys.argv[1]
    print(f"\n📋 Orçamento: {numero_orcamento}\n")

    # ETAPA 1: Validar arquivos INSS
    print("=" * 80)
    print("ETAPA 1: VALIDAR ARQUIVOS INSS")
    print("=" * 80)
    print("🔍 Validando arquivos INSS...")
    if not validar_arquivos_inss(numero_orcamento):
        print("❌ Arquivos INSS não encontrados - ABORTANDO")
        return 1

    # ETAPA 2: Inserir em paulo_inss
    print("\n" + "=" * 80)
    print("ETAPA 2: INSERIR DADOS EM PAULO_INSS")
    print("=" * 80)
    paulo_inss_ok = inserir_dados_paulo_inss(numero_orcamento)
    if not paulo_inss_ok:
        print("❌ Erro ao inserir em paulo_inss - ABORTANDO")
        return 1

    # ETAPA 3: Marcar como processado
    print("\n" + "=" * 80)
    print("ETAPA 3: MARCAR STATUS COMO PROCESSADO")
    print("=" * 80)
    status_ok = marcar_como_processado(numero_orcamento)
    if not status_ok:
        print("❌ Erro ao marcar processado - ABORTANDO")
        return 1

    # ETAPA 4: Sincronizar com Google Drive (SOMENTE após conclusão completa)
    print("\n" + "=" * 80)
    print("ETAPA 4: SINCRONIZAR COM GOOGLE DRIVE (FINAL)")
    print("=" * 80)
    print("📋 Pré-requisitos atendidos:")
    print("   ✅ Arquivos INSS validados")
    print("   ✅ Dados inseridos em paulo_inss")
    print("   ✅ Status marcado como 'processado'")
    print("\n🚀 Iniciando sincronização com Google Drive...")

    drive_ok = sincronizar_google_drive(numero_orcamento)

    if not drive_ok:
        print("\n⚠️ Aviso: Falha ao sincronizar Google Drive")
        print("   (Ciclo completado, mas arquivos não foram sincronizados)")
        return 1

    print("\n" + "=" * 80)
    print("✅ CICLO COMPLETADO COM SUCESSO")
    print("=" * 80)
    print("\n📊 Resumo final:")
    print("   ✅ Arquivos INSS processados")
    print("   ✅ Dados salvos em paulo_inss")
    print("   ✅ Status atualizado para 'processado'")
    print("   ✅ Sincronizado com Google Drive")
    print("\n" + "=" * 80 + "\n")

    return 0

if __name__ == '__main__':
    sys.exit(main())
