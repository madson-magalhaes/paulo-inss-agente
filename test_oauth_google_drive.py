#!/usr/bin/env python3
"""
Teste de autenticação OAuth com Google Drive
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DRIVE_ENABLED = os.getenv('GOOGLE_DRIVE_ENABLED', 'false').lower() == 'true'
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
OAUTH_CREDS_FILE = os.getenv('GOOGLE_OAUTH_CREDENTIALS_FILE', '.credentials/oauth_credentials.json')
TOKEN_PATH = os.getenv('GOOGLE_OAUTH_TOKEN_PATH', '.credentials/google_token.json')

print("\n" + "=" * 80)
print("TESTE DE AUTENTICAÇÃO OAUTH - GOOGLE DRIVE")
print("=" * 80 + "\n")

print("📋 Verificando configuração:")
print(f"   ✓ GOOGLE_DRIVE_ENABLED: {DRIVE_ENABLED}")
print(f"   ✓ GOOGLE_DRIVE_FOLDER_ID: {DRIVE_FOLDER_ID}")
print(f"   ✓ OAUTH_CREDS_FILE: {OAUTH_CREDS_FILE}")
print(f"   ✓ TOKEN_PATH: {TOKEN_PATH}")

if not os.path.exists(OAUTH_CREDS_FILE):
    print(f"\n❌ Arquivo não encontrado: {OAUTH_CREDS_FILE}")
    exit(1)

print(f"\n✅ Arquivo de credenciais encontrado!")

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("❌ Bibliotecas Google não instaladas")
    print("   Execute: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

SCOPES = ['https://www.googleapis.com/auth/drive']

def obter_credenciais():
    """Obtém credenciais OAuth com controle manual de múltiplos perfis"""

    # Verificar se token já existe
    if os.path.exists(TOKEN_PATH):
        print(f"\n🔍 Verificando token existente em {TOKEN_PATH}...")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.valid:
            print("✅ Token válido encontrado!")
            return creds
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token expirado...")
            creds.refresh(Request())
            return creds

    # Gerar novo token com servidor local
    print(f"\n🔗 Iniciando servidor local para autorização...")
    print(f"   Credenciais: {OAUTH_CREDS_FILE}\n")

    flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CREDS_FILE, SCOPES)

    print("=" * 80)
    print("⚠️ IMPORTANTE: Você tem múltiplos perfis!")
    print("=" * 80)
    print("\nPRINCIPAL: Abra o link abaixo no seu navegador com o perfil CORRETO!\n")

    # Usar servidor local que automaticamente captura o código
    creds = flow.run_local_server(
        port=8080,
        open_browser=False,
        authorization_prompt_message='Abra este link no seu navegador com o perfil CORRETO:\n{url}\n'
    )

    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, 'w') as token_file:
        token_file.write(creds.to_json())

    print(f"\n✅ Token salvo em: {TOKEN_PATH}")
    return creds

print("\n" + "=" * 80)
print("1️⃣ AUTENTICANDO COM GOOGLE")
print("=" * 80)

try:
    creds = obter_credenciais()
    print("\n✅ Autenticação bem-sucedida!")
except Exception as e:
    print(f"\n❌ Erro: {e}")
    exit(1)

print("\n" + "=" * 80)
print("2️⃣ CONECTANDO AO GOOGLE DRIVE")
print("=" * 80)

try:
    service = build('drive', 'v3', credentials=creds)
    print("\n✅ Conectado ao Google Drive!")
except Exception as e:
    print(f"\n❌ Erro: {e}")
    exit(1)

print("\n" + "=" * 80)
print("3️⃣ VERIFICANDO ACESSO À PASTA")
print("=" * 80)

try:
    folder = service.files().get(fileId=DRIVE_FOLDER_ID, fields='id, name').execute()
    print(f"\n✅ Pasta acessível: {folder['name']}")
    print(f"   ID: {folder['id']}")
except Exception as e:
    print(f"\n❌ Erro ao acessar pasta: {e}")
    exit(1)

print("\n" + "=" * 80)
print("4️⃣ LISTANDO PASTAS")
print("=" * 80)

try:
    query = f"mimeType='application/vnd.google-apps.folder' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)', pageSize=10).execute()
    folders = results.get('files', [])
    
    print(f"\n📁 Total de pastas: {len(folders)}")
    if folders:
        print("\nPastas encontradas:")
        for folder in folders:
            print(f"   • {folder['name']}")
    else:
        print("   (Nenhuma pasta encontrada - normal se vazio)")
except Exception as e:
    print(f"\n❌ Erro: {e}")
    exit(1)

print("\n" + "=" * 80)
print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 80)
print("\n✨ Sistema pronto para fazer upload de orçamentos!")
print("   Execute: python3 atualizar_status_processado.py <numero_orcamento>\n")

