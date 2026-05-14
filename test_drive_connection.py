#!/usr/bin/env python3
"""
Teste de conexão e permissões do Google Drive
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')

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

        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES)
        print("✅ Credenciais carregadas com sucesso")
        return creds
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
        return None


def testar_drive_connection():
    """Testa conexão e permissões do Drive"""
    
    print("\n" + "=" * 80)
    print("TESTE DE CONEXÃO - GOOGLE DRIVE")
    print("=" * 80 + "\n")

    # Step 1: Autenticar
    print("1️⃣ Autenticando...")
    creds = obter_credenciais()
    if not creds:
        return False

    # Step 2: Conectar ao Drive
    print("\n2️⃣ Conectando ao Google Drive...")
    try:
        service = build('drive', 'v3', credentials=creds)
        print("✅ Conectado!")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

    # Step 3: Verificar pasta
    print(f"\n3️⃣ Verificando pasta (ID: {DRIVE_FOLDER_ID})...")
    try:
        folder = service.files().get(fileId=DRIVE_FOLDER_ID, fields='id, name, owners').execute()
        print(f"✅ Pasta encontrada: {folder['name']}")
        print(f"   ID: {folder['id']}")
        
        # Verificar proprietários
        owners = folder.get('owners', [])
        print(f"   Proprietários: {len(owners)}")
        for owner in owners:
            print(f"      • {owner.get('displayName')} ({owner.get('emailAddress')})")
    except Exception as e:
        print(f"❌ Erro ao acessar pasta: {e}")
        print(f"\n   SOLUÇÃO: A Service Account NÃO tem acesso à pasta!")
        print(f"   Compartilhe a pasta com: {os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL')}")
        return False

    # Step 4: Listar pastas
    print(f"\n4️⃣ Listando pastas dentro...")
    try:
        query = f"mimeType='application/vnd.google-apps.folder' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=10
        ).execute()

        folders = results.get('files', [])
        
        if folders:
            print(f"✅ Encontradas {len(folders)} pastas:")
            for folder in folders:
                print(f"   • {folder['name']}")
        else:
            print("⚠️ Nenhuma pasta encontrada (normal se vazio)")

    except Exception as e:
        print(f"❌ Erro ao listar pastas: {e}")
        return False

    # Step 5: Teste de upload
    print(f"\n5️⃣ Testando upload de arquivo...")
    try:
        from googleapiclient.http import MediaFileUpload
        
        # Criar arquivo de teste
        test_file = "test_upload.txt"
        with open(test_file, 'w') as f:
            f.write("Teste de upload do Google Drive - Paulo Robson INSS\n")
            f.write(f"Timestamp: {__import__('datetime').datetime.now()}\n")
        
        file_metadata = {
            'name': test_file,
            'parents': [DRIVE_FOLDER_ID]
        }
        media = MediaFileUpload(test_file)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✅ Upload bem-sucedido!")
        print(f"   Arquivo ID: {file['id']}")
        
        # Limpar arquivo local
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ Erro ao fazer upload: {e}")
        return False

    print("\n" + "=" * 80)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 80 + "\n")
    
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Se algum teste falhou, compartilhe a pasta com a Service Account")
    print("2. Execute: python3 google_drive_sync.py <numero_orcamento>")
    print("3. Execute: python3 monitor_drive_uploads.py")
    
    return True


if __name__ == '__main__':
    sucesso = testar_drive_connection()
    sys.exit(0 if sucesso else 1)
