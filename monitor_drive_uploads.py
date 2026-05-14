#!/usr/bin/env python3
"""
Monitor uploads ao Google Drive em tempo real
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DRIVE_ENABLED = os.getenv('GOOGLE_DRIVE_ENABLED', 'false').lower() == 'true'
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')

if DRIVE_ENABLED:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("❌ google-api-client não instalado")
        sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/drive']


def obter_credenciais():
    """Obtém credenciais do .env"""
    try:
        creds_dict = {
            "type": os.getenv('GOOGLE_SERVICE_ACCOUNT_TYPE', 'service_account'),
            "project_id": os.getenv('GOOGLE_SERVICE_ACCOUNT_PROJECT_ID'),
            "private_key_id": os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID'),
            "private_key": os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY'),
            "client_email": os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL'),
            "client_id": os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_ID'),
            "auth_uri": os.getenv('GOOGLE_SERVICE_ACCOUNT_AUTH_URI'),
            "token_uri": os.getenv('GOOGLE_SERVICE_ACCOUNT_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL'),
            "client_x509_cert_url": os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL'),
            "universe_domain": os.getenv('GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN', 'googleapis.com')
        }

        if not all([creds_dict['project_id'], creds_dict['private_key'], creds_dict['client_email']]):
            print("❌ Credenciais incompletas no .env")
            return None

        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES)
        return creds
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
        return None


def listar_pastas_recentes(minutos=5):
    """Lista pastas criadas/modificadas nos últimos N minutos"""
    
    if not DRIVE_ENABLED:
        print("❌ Google Drive desabilitado")
        return

    creds = obter_credenciais()
    if not creds:
        print("❌ Não foi possível autenticar")
        return

    try:
        service = build('drive', 'v3', credentials=creds)

        # Busca pastas na pasta raiz
        query = f"mimeType='application/vnd.google-apps.folder' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
        
        print("\n" + "=" * 80)
        print("📁 PASTAS NO GOOGLE DRIVE")
        print("=" * 80 + "\n")

        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, createdTime, modifiedTime, mimeType)',
            pageSize=20,
            orderBy='modifiedTime desc'
        ).execute()

        folders = results.get('files', [])

        if not folders:
            print("⚠️ Nenhuma pasta encontrada")
            return

        print(f"📊 Total de pastas: {len(folders)}\n")

        for folder in folders:
            modified = folder['modifiedTime']
            created = folder['createdTime']
            
            print(f"📁 {folder['name']}")
            print(f"   ID: {folder['id']}")
            print(f"   Criada: {created}")
            print(f"   Modificada: {modified}")
            
            # Contar arquivos na pasta
            files_query = f"'{folder['id']}' in parents and trashed=false"
            files_result = service.files().list(
                q=files_query,
                spaces='drive',
                fields='files(id, name, size)',
                pageSize=100
            ).execute()

            files = files_result.get('files', [])
            total_size = sum(int(f.get('size', 0)) for f in files)
            
            print(f"   📄 Arquivos: {len(files)}")
            print(f"   💾 Tamanho: {total_size / (1024*1024):.2f} MB")
            
            if files:
                print(f"   Últimos arquivos:")
                for file in files[:5]:
                    size_mb = int(file.get('size', 0)) / (1024*1024)
                    print(f"      • {file['name']} ({size_mb:.2f} MB)")
            print()

    except Exception as e:
        print(f"❌ Erro ao listar pastas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print(f"\n🔍 Verificando uploads ao Google Drive...")
    print(f"⏰ Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    listar_pastas_recentes()
