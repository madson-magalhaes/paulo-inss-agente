#!/usr/bin/env python3
"""
Sincronização com Google Drive - Usando Token do .env
Para uso em VPS (não precisa gerar novo token)
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
OAUTH_TOKEN = os.getenv('GOOGLE_OAUTH_TOKEN', '')
OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')

if DRIVE_ENABLED:
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        DRIVE_ENABLED = False

SCOPES = ['https://www.googleapis.com/auth/drive']


def obter_credenciais_do_env():
    """Carrega credenciais do .env com suporte a refresh_token"""

    if not OAUTH_TOKEN:
        print("❌ Token OAuth não encontrado em .env")
        return None

    try:
        # Tenta obter refresh_token do .env
        refresh_token = os.getenv('GOOGLE_OAUTH_TOKEN_REFRESH', '').strip() or None
        token_uri = os.getenv('GOOGLE_OAUTH_TOKEN_URI', 'https://oauth2.googleapis.com/token')

        print(f"DEBUG - Carregando credenciais do .env")
        print(f"DEBUG - Token: {OAUTH_TOKEN[:30]}...")
        print(f"DEBUG - Refresh Token: {refresh_token[:30] if refresh_token else 'None'}...")
        print(f"DEBUG - Client ID: {OAUTH_CLIENT_ID[:20]}...")
        print(f"DEBUG - Token URI: {token_uri}")

        creds = Credentials(
            token=OAUTH_TOKEN,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET,
            scopes=SCOPES
        )
        print("✅ Credenciais carregadas do .env")
        return creds
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
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
    """Faz upload da pasta para Google Drive usando token do .env"""

    if not DRIVE_ENABLED:
        print("ℹ️ Google Drive desabilitado (GOOGLE_DRIVE_ENABLED=false)")
        return None

    if not DRIVE_FOLDER_ID:
        print("⚠️ Aviso: GOOGLE_DRIVE_FOLDER_ID não configurado em .env")
        return None

    try:
        creds = obter_credenciais_do_env()
        if not creds:
            print("❌ Não foi possível obter credenciais")
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
        from supabase import create_client

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        if not url or not key:
            return None

        client = create_client(url, key)
        response = client.table('paulo_orcamentos').select(
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
        print("SINCRONIZAÇÃO COM GOOGLE DRIVE (Token do .env)")
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
        print("❌ Uso: python3 google_drive_sync_with_token.py <numero_orcamento>")
        print("   Exemplo: python3 google_drive_sync_with_token.py 12052601")
        sys.exit(1)

    numero_orcamento = sys.argv[1]
    sys.exit(main(numero_orcamento))
