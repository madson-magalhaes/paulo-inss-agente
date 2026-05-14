#!/usr/bin/env python3
"""
Script de Renovação Automática de Token Google OAuth
Para uso em VPS sem intervenção manual
"""

import os
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()

# Variáveis do .env
TOKEN = os.getenv('GOOGLE_OAUTH_TOKEN', '')
REFRESH_TOKEN = os.getenv('GOOGLE_OAUTH_TOKEN_REFRESH', '').strip() or None
CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
TOKEN_URI = os.getenv('GOOGLE_OAUTH_TOKEN_URI', 'https://oauth2.googleapis.com/token')
EXPIRY_STR = os.getenv('GOOGLE_OAUTH_EXPIRY', '')

ENV_FILE = '.env'


def parse_expiry(expiry_str):
    """Parse ISO 8601 datetime string"""
    try:
        return datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
    except:
        return None


def is_token_expired():
    """Verifica se o token expirou ou está prestes a expirar (menos de 5 minutos)"""
    if not EXPIRY_STR:
        print("⚠️ GOOGLE_OAUTH_EXPIRY não definido")
        return False

    expiry = parse_expiry(EXPIRY_STR)
    if not expiry:
        print(f"❌ Não consegui parsear GOOGLE_OAUTH_EXPIRY: {EXPIRY_STR}")
        return False

    time_until_expiry = expiry - datetime.now(expiry.tzinfo)
    minutes_left = time_until_expiry.total_seconds() / 60

    print(f"DEBUG - Token expira em: {expiry}")
    print(f"DEBUG - Tempo restante: {minutes_left:.1f} minutos")

    # Se faltam menos de 5 minutos, considera expirado
    return minutes_left < 5


def refresh_access_token():
    """Renova o access token usando refresh_token ou credentials"""

    print("\n" + "=" * 80)
    print("RENOVAÇÃO DE TOKEN GOOGLE OAUTH")
    print("=" * 80 + "\n")

    # Tenta renovar com refresh_token se disponível
    if REFRESH_TOKEN:
        print(f"DEBUG - Tentando renovar com refresh_token...")
        return refresh_with_refresh_token()

    # Se não tiver refresh_token, tenta usar o fluxo de credenciais
    print(f"DEBUG - Refresh token não disponível")
    print(f"DEBUG - O token será renovado apenas quando expirar e houver nova autenticação")
    return False


def refresh_with_refresh_token():
    """Renova token usando refresh_token"""
    try:
        print(f"🔄 Renovando token com refresh_token...")

        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }

        response = requests.post(TOKEN_URI, data=data)

        if response.status_code != 200:
            print(f"❌ Erro ao renovar token: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        new_data = response.json()
        new_token = new_data.get('access_token')
        new_expiry_seconds = new_data.get('expires_in', 3600)

        # Calcula nova data de expiração
        new_expiry = datetime.utcnow() + timedelta(seconds=new_expiry_seconds)
        new_expiry_str = new_expiry.strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"✅ Token renovado com sucesso!")
        print(f"DEBUG - Novo token: {new_token[:30]}...")
        print(f"DEBUG - Nova expiração: {new_expiry_str}")

        # Atualiza o .env
        update_env_token(new_token, new_expiry_str)
        return True

    except Exception as e:
        print(f"❌ Erro ao renovar token: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_env_token(new_token, new_expiry):
    """Atualiza o arquivo .env com novo token e expiração"""
    try:
        print(f"\n📝 Atualizando .env...")

        # Lê o arquivo atual
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substitui o token
        import re
        content = re.sub(
            r'GOOGLE_OAUTH_TOKEN=.*',
            f'GOOGLE_OAUTH_TOKEN={new_token}',
            content
        )

        # Substitui a expiração
        content = re.sub(
            r'GOOGLE_OAUTH_EXPIRY=.*',
            f'GOOGLE_OAUTH_EXPIRY={new_expiry}',
            content
        )

        # Escreve de volta
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ .env atualizado com novo token")
        return True

    except Exception as e:
        print(f"❌ Erro ao atualizar .env: {e}")
        return False


def check_and_refresh():
    """Verifica e renova o token se necessário"""
    print(f"\n🔍 Verificando expiração do token Google OAuth...")

    if is_token_expired():
        print(f"\n⚠️ Token expirado ou prestes a expirar!")
        return refresh_access_token()
    else:
        print(f"✅ Token ainda válido")
        return True


if __name__ == '__main__':
    # Se passarem --force como argumento, força renovação
    force_refresh = '--force' in sys.argv

    if force_refresh:
        print("⚡ Forçando renovação de token...")
        success = refresh_access_token()
    else:
        success = check_and_refresh()

    sys.exit(0 if success else 1)
