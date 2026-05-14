# 🔐 Google OAuth Setup

Configurar autenticação OAuth 2.0 para Google Drive.

## Por que OAuth?

✅ Funciona com Gmail pessoal  
✅ Token reutilizável em VPS  
✅ Sem browser necessário na VPS  
✅ Seguro e automático

## Google Cloud Console

### 1. Acessar

https://console.cloud.google.com

### 2. Criar OAuth Client

**APIs & Services** → **Credentials** → **+ CREATE CREDENTIALS** → **OAuth client ID**

Se pedir para configurar consent screen:
- Selecione: **External**
- App name: `Paulo INSS`
- Scopes: Procure e selecione `https://www.googleapis.com/auth/drive`
- Test users: Adicione seu email
- Volte para Credentials

### 3. Application Type

**Application type:** Desktop application  
**Name:** Paulo INSS  
Clique: **CREATE**

### 4. Adicionar Redirect URI

Clique no OAuth Client criado.

Em **Authorized redirect URIs**, adicione:
```
http://localhost:8080/
```

Clique: **SAVE**

### 5. Baixar JSON

Clique no ícone de download (⬇️).

Um arquivo `client_secret_*.json` será baixado.

## Copiar para Projeto

```bash
mkdir -p .credentials
cp ~/Downloads/client_secret_*.json .credentials/oauth_credentials.json
```

## Primeira Autenticação

```bash
python3 google_drive_sync.py 12052601
```

**O que acontece:**
1. Script exibe um link
2. Copie e cole no navegador
3. Autorize o acesso
4. Token salvo em `.credentials/google_token.json` ✅

## Usar na VPS

Copie o token:

```bash
scp .credentials/google_token.json seu-usuario@vps:/home/seu-usuario/paulo-inss/.credentials/
```

**Próximas execuções:** Token reutilizado automaticamente, sem browser necessário.

## Troubleshooting

| Erro | Solução |
|------|---------|
| `redirect_uri_mismatch` | Adicionar `http://localhost:8080/` em Authorized redirect URIs |
| Arquivo não encontrado | Executar `mkdir -p .credentials` e copiar JSON |
| Token inválido na VPS | Copiar novo token de LOCAL |

---

**Versão:** 5.0 | **Data:** May 14, 2026
