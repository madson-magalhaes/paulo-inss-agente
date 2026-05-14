#!/usr/bin/env python3
"""
Gerador de Token Google OAuth com Refresh Token
Use isso para gerar um token que possa renovar automaticamente
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("❌ Bibliotecas necessárias não encontradas")
    print("Instale com: pip install google-auth-oauthlib google-auth-httplib2")
    exit(1)

# Configurações
CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_FILE = '.credentials/google_token.json'
ENV_FILE = '.env'


def update_env_with_token(creds):
    """Atualiza o arquivo .env com os novos valores de token"""
    try:
        import re
        from datetime import datetime

        print("\n📝 Atualizando arquivo .env...\n")

        # Lê o arquivo atual
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        expiry_str = creds.expiry.isoformat().replace('+00:00', 'Z') if creds.expiry else ''

        # Atualiza cada valor
        updates = {
            'GOOGLE_OAUTH_TOKEN': creds.token,
            'GOOGLE_OAUTH_TOKEN_REFRESH': creds.refresh_token or '',
            'GOOGLE_OAUTH_TOKEN_URI': creds.token_uri,
            'GOOGLE_OAUTH_EXPIRY': expiry_str,
        }

        for key, value in updates.items():
            # Procura a linha e substitui o valor
            pattern = f'{key}=.*'
            content = re.sub(pattern, f'{key}={value}', content)
            print(f"   ✓ {key}")

        # Escreve de volta
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n✅ Arquivo .env atualizado com sucesso!")
        print(f"\n📋 Valores salvos:")
        print(f"   • Token: {creds.token[:40]}...")
        print(f"   • Refresh Token: {creds.refresh_token[:40] if creds.refresh_token else 'NONE'}...")
        print(f"   • Token URI: {creds.token_uri}")
        print(f"   • Expiry: {expiry_str}")

        return True

    except Exception as e:
        print(f"❌ Erro ao atualizar .env: {e}")
        import traceback
        traceback.print_exc()
        return False


def gerar_token():
    """Gera novo token OAuth com refresh_token"""

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ GOOGLE_OAUTH_CLIENT_ID ou GOOGLE_OAUTH_CLIENT_SECRET não configurados")
        print("   Configure-os no .env primeiro")
        return False

    print("\n" + "=" * 80)
    print("GERADOR DE TOKEN GOOGLE OAUTH COM REFRESH TOKEN")
    print("=" * 80 + "\n")

    print("📋 Configuração:")
    print(f"   • Client ID: {CLIENT_ID[:30]}...")
    print(f"   • Scopes: {', '.join(SCOPES)}")
    print(f"   • Token será salvo em: {TOKEN_FILE}\n")

    try:
        # Cria o flow OAuth com redirect_uri local
        flow = InstalledAppFlow.from_client_secrets_file(
            '.credentials/oauth_credentials.json',
            SCOPES,
            redirect_uri='http://localhost:8080/'  # Especifica o redirect_uri
        )

        print("\n" + "=" * 80)
        print("🔗 ACESSO GOOGLE OAUTH - COPY & PASTE")
        print("=" * 80 + "\n")

        # Gera a URL de autenticação
        auth_uri, _ = flow.authorization_url(prompt='consent')

        print("📋 Copie este link e cole no seu navegador preferido:\n")
        print(f"🔗 {auth_uri}\n")

        print("=" * 80)
        print("\n✅ Após autorizar, você receberá um código na URL")
        print("📝 Cole o código abaixo e pressione ENTER")
        print("   (O código vem depois de 'code=' na URL)\n")

        # Aguarda o código
        auth_code = input("🔑 Digite o código de autorização: ").strip()

        if not auth_code:
            print("❌ Código não fornecido")
            return False

        # Troca o código pelo token
        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            print("\n✅ Autenticação bem-sucedida!")
        except Exception as e:
            print(f"\n❌ Erro ao trocar código por token: {e}")
            print("\n💡 Solução:")
            print("   1. Vá em https://console.cloud.google.com/apis/credentials")
            print("   2. Clique em 'OAuth 2.0 Client ID' (gdrive-inss)")
            print("   3. Em 'URIs autorizados de redirecionamento', adicione:")
            print("      - http://localhost:8080/")
            print("      - http://localhost:8080")
            print("   4. Tente novamente")
            return False

        # Salva o token com refresh_token
        Path('.credentials').mkdir(exist_ok=True)

        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'universe_domain': getattr(creds, 'universe_domain', 'googleapis.com'),
            'account': '',
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }

        # Salva também em arquivo .credentials
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)

        print(f"✅ Token gerado com sucesso!")
        print(f"📁 Arquivo salvo: {TOKEN_FILE}\n")

        # Atualiza o .env com os novos valores
        update_env_with_token(creds)

        print("\n💾 Arquivo .env atualizado automaticamente!")
        print("   Próximo passo: copie o arquivo .credentials/google_token.json para a VPS\n")

        return True

    except FileNotFoundError:
        print("❌ Arquivo .credentials/oauth_credentials.json não encontrado")
        print("   Execute primeiro: python3 test_oauth_google_drive.py\n")
        return False
    except Exception as e:
        print(f"❌ Erro ao gerar token: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import sys
    success = gerar_token()
    sys.exit(0 if success else 1)
