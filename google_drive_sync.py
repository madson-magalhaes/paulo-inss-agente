#!/usr/bin/env python3
"""
Sincronização com Google Drive - OAuth 2.0 (Conta Pessoal)
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DRIVE_ENABLED = os.getenv('GOOGLE_DRIVE_ENABLED', 'false').lower() == 'true'
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
OAUTH_CREDS_FILE = os.getenv('GOOGLE_OAUTH_CREDENTIALS_FILE', '.credentials/oauth_credentials.json')
TOKEN_PATH = os.getenv('GOOGLE_OAUTH_TOKEN_PATH', '.credentials/google_token.json')

if DRIVE_ENABLED:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        DRIVE_ENABLED = False

SCOPES = ['https://www.googleapis.com/auth/drive']


def obter_credenciais_oauth():
    """Obtém credenciais OAuth - abre navegador na primeira vez"""

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            return creds

    if not os.path.exists(OAUTH_CREDS_FILE):
        print("❌ Arquivo de credenciais OAuth não encontrado")
        print(f"   Crie em: {OAUTH_CREDS_FILE}")
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CREDS_FILE, SCOPES)

        print("\n" + "=" * 80)
        print("🔗 AUTORIZAÇÃO NECESSÁRIA")
        print("=" * 80)
        print("\n⚠️ IMPORTANTE: Você tem múltiplos perfis!")
        print("   Certifique-se de usar o perfil CORRETO do Google.\n")
        print("📋 Copie e cole este link no seu navegador:\n")

        # Usar servidor local que automaticamente captura o código
        print("Iniciando servidor local na porta 8080...")
        print("Abra o link abaixo no seu navegador:\n")

        creds = flow.run_local_server(
            port=8080,
            open_browser=False,
            authorization_prompt_message='Abra este link no seu navegador com o perfil CORRETO:\n{url}\n'
        )

        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())

        print("\n✅ Autorização concluída! Token salvo.\n")
        return creds
    except Exception as e:
        print(f"❌ Erro ao obter credenciais OAuth: {e}")
        import traceback
        traceback.print_exc()
        return None


def renomear_pasta_orcamento(numero_orcamento, nome_cliente):
    """Renomeia pasta de orçamento para incluir nome do cliente"""
    pasta_orcamentos = './orcamentos'
    pasta_atual = os.path.join(pasta_orcamentos, f'orcamento_{numero_orcamento}')
    pasta_nova = os.path.join(pasta_orcamentos, f'orcamento_{numero_orcamento}_{nome_cliente}')

    if os.path.exists(pasta_nova):
        return pasta_nova

    if os.path.exists(pasta_atual):
        try:
            os.rename(pasta_atual, pasta_nova)
            print(f"✅ Pasta renomeada: {pasta_atual} → {pasta_nova}")
            return pasta_nova
        except Exception as e:
            print(f"❌ Erro ao renomear pasta: {e}")
            return pasta_atual

    print(f"⚠️ Pasta não encontrada: {pasta_atual}")
    return None


def sincronizar_google_drive(caminho_pasta, nome_pasta_destino):
    """Faz upload da pasta para Google Drive usando OAuth

    Nota: Se pasta já existe, apenas atualiza os arquivos sem duplicar.
    Isso evita uploads duplicados quando rodado múltiplas vezes.
    """

    if not DRIVE_ENABLED:
        print("ℹ️ Google Drive desabilitado (GOOGLE_DRIVE_ENABLED=false)")
        return None

    if not DRIVE_FOLDER_ID:
        print("⚠️ Aviso: GOOGLE_DRIVE_FOLDER_ID não configurado em .env")
        return None

    try:
        creds = obter_credenciais_oauth()
        if not creds:
            print("❌ Não foi possível obter credenciais OAuth")
            return None

        service = build('drive', 'v3', credentials=creds)

        # Verifica se pasta já existe no Drive (por nome)
        query = f"name='{nome_pasta_destino}' and mimeType='application/vnd.google-apps.folder' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)', pageSize=1).execute()
        existing_folders = results.get('files', [])

        if existing_folders:
            folder_id = existing_folders[0]['id']
            print(f"📁 Pasta já existe no Drive: {nome_pasta_destino}")
        else:
            # Cria nova pasta
            folder_metadata = {
                'name': nome_pasta_destino,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [DRIVE_FOLDER_ID]
            }

            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"✅ Pasta criada no Drive: {nome_pasta_destino}")

        # Upload dos arquivos
        arquivos_upload = 0
        for arquivo in os.listdir(caminho_pasta):
            caminho_arquivo = os.path.join(caminho_pasta, arquivo)

            if os.path.isfile(caminho_arquivo):
                # Verifica se arquivo já existe na pasta Drive
                query = f"name='{arquivo}' and '{folder_id}' in parents and trashed=false"
                results = service.files().list(q=query, spaces='drive', fields='files(id)', pageSize=1).execute()
                existing_files = results.get('files', [])

                if existing_files:
                    # Atualiza arquivo existente (sobrescreve versão antiga)
                    file_id = existing_files[0]['id']
                    media = MediaFileUpload(caminho_arquivo)
                    service.files().update(fileId=file_id, media_body=media).execute()
                    print(f"   ✓ Atualizado: {arquivo}")
                else:
                    # Cria novo arquivo
                    file_metadata = {
                        'name': arquivo,
                        'parents': [folder_id]
                    }
                    media = MediaFileUpload(caminho_arquivo)
                    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                    print(f"   ✓ Upload: {arquivo}")

                arquivos_upload += 1

        print(f"✅ Sincronização completa para Google Drive ({arquivos_upload} arquivo(s))")
        return folder_id

    except Exception as e:
        print(f"❌ Erro ao sincronizar Drive: {e}")
        import traceback
        traceback.print_exc()
        return None


def obter_nome_cliente_supabase(numero_orcamento):
    """Busca nome do cliente no Supabase"""
    try:
        from supabase_client import get_client

        try:
            client = get_client()
        except ValueError:
            return None

        response = client.table('orcamentos').select(
            'nome'
        ).eq('numero_orcamento', numero_orcamento).limit(1).execute()

        if response.data and len(response.data) > 0:
            nome = response.data[0].get('nome', '')
            return nome.strip() if nome else None

        return None

    except Exception as e:
        print(f"⚠️ Erro ao buscar nome no Supabase: {e}")
        return None


def main(numero_orcamento, verbose=True):
    """Sincroniza orçamento para Google Drive"""
    
    if verbose:
        print("\n" + "=" * 80)
        print("SINCRONIZAÇÃO COM GOOGLE DRIVE (OAuth)")
        print("=" * 80 + "\n")
        print(f"📋 Orçamento: {numero_orcamento}\n")

    if verbose:
        print("🔍 Buscando informações do cliente...")
    nome_cliente = obter_nome_cliente_supabase(numero_orcamento)

    if not nome_cliente:
        if verbose:
            print(f"⚠️ Não foi possível obter nome do cliente")
        nome_cliente = ""

    if verbose:
        print(f"✓ Cliente: {nome_cliente or '(desconhecido)'}\n")

    if nome_cliente:
        if verbose:
            print("📁 Renomeando pasta...")
        pasta_nova = renomear_pasta_orcamento(numero_orcamento, nome_cliente)

        if not pasta_nova:
            if verbose:
                print("❌ Erro ao renomear pasta")
            return 1
    else:
        pasta_nova = f'./orcamentos/orcamento_{numero_orcamento}'

    if DRIVE_ENABLED and DRIVE_FOLDER_ID:
        if verbose:
            print("\n☁️ Sincronizando com Google Drive...")
        nome_destino = os.path.basename(pasta_nova)
        sincronizar_google_drive(pasta_nova, nome_destino)
    else:
        if verbose:
            print("\n⚠️ Google Drive desabilitado ou não configurado")

    if verbose:
        print("\n" + "=" * 80)
        print("✅ SINCRONIZAÇÃO CONCLUÍDA")
        print("=" * 80 + "\n")

    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("❌ Uso: python3 google_drive_sync.py <numero_orcamento>")
        print("   Exemplo: python3 google_drive_sync.py 12052601")
        sys.exit(1)

    numero_orcamento = sys.argv[1]
    sys.exit(main(numero_orcamento))
