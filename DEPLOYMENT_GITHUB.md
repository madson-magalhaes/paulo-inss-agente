# 🚀 Deployment no GitHub e VPS - Guia Completo

## ✅ Status Atual
O sistema está **100% funcional** e pronto para deployment em qualquer plataforma (Windows, Linux, macOS).

---

## 📋 ÍNDICE
1. [Preparação GitHub](#1-preparação-github)
2. [Push para GitHub](#2-push-para-github)
3. [Clone na VPS](#3-clone-na-vps)
4. [Configuração .env na VPS](#4-configuração-env-na-vps)
5. [Autenticação OAuth](#5-autenticação-oauth)
6. [Execução na VPS](#6-execução-na-vps)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Preparação GitHub

### 1.1 Criar repositório no GitHub
```bash
# 1. Acesse https://github.com/new
# 2. Crie um repositório chamado: paulo-inss-agente
# 3. Escolha PRIVATE (recomendado por ter credenciais)
# 4. Não inicialize com README (vamos fazer localmente)
```

### 1.2 Preparar repositório local
```bash
cd "/Users/madsonmagalhaes/Documents/Paulo Robson INSS/v6_agente_ia"

# Se ainda não tem git inicializado:
git init
git config user.email "seu_email@gmail.com"
git config user.name "Seu Nome"

# Se já tem, apenas continue
```

### 1.3 Criar arquivo .env.example (sem credenciais)
```bash
# Este arquivo SERÁ commitado (serve como template)
# Copie o .env atual e remova os valores sensíveis
```

---

## 2. Push para GitHub

### 2.1 Adicionar remote
```bash
# Substitua SEU_USUARIO pelo seu username do GitHub
git remote add origin https://github.com/SEU_USUARIO/paulo-inss-agente.git
git branch -M main
```

### 2.2 Adicionar e commitar todos os arquivos
```bash
# Adiciona apenas arquivos permitidos pelo .gitignore
git add .

# Verifica o que vai ser commitado (nunca deve incluir .env ou .credentials/)
git status

# Commit inicial
git commit -m "chore: initial commit - production ready INSS automation system

- Complete OAuth 2.0 Google Drive integration
- Supabase database integration
- Automated INSS calculation pipeline
- Multi-platform compatible (Windows, Linux, macOS)"
```

### 2.3 Push para GitHub
```bash
git push -u origin main
```

---

## 3. Clone na VPS

### 3.1 Instalar dependências na VPS
```bash
# SSH na VPS
ssh user@seu_vps.com

# Clonar o repositório
git clone https://github.com/SEU_USUARIO/paulo-inss-agente.git
cd paulo-inss-agente

# Instalar Python (se não tiver)
# Ubuntu/Debian:
sudo apt update && sudo apt install -y python3 python3-pip

# Verificar versão
python3 --version  # Deve ser 3.9+
```

### 3.2 Instalar dependências Python
```bash
# Criar virtual environment (recomendado)
python3 -m venv venv

# Ativar (Linux/macOS)
source venv/bin/activate

# Ou no Windows (CMD):
venv\Scripts\activate.bat

# Ou no Windows (PowerShell):
venv\Scripts\Activate.ps1

# Instalar pacotes
pip install -r requirements.txt
```

---

## 4. Configuração .env na VPS

### 4.1 Criar arquivo .env
```bash
# Copie o .env.example como base
cp .env.example .env

# Edite com suas credenciais reais
nano .env  # ou use seu editor favorito
```

### 4.2 Configurar .env (valores necessários)
```env
# ============================================================================
# SUPABASE CONFIGURATION
# ============================================================================
SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_KEY=sb_publishable_SEU_KEY

# ============================================================================
# GOOGLE DRIVE CONFIGURATION
# ============================================================================
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=SEU_FOLDER_ID

# OAuth Client Credentials (do Google Cloud Console)
GOOGLE_OAUTH_CLIENT_ID=SEU_CLIENT_ID.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=SEU_CLIENT_SECRET

# OAuth Token (IMPORTANTE - veja seção 5.1)
GOOGLE_OAUTH_TOKEN=ya29.SEU_TOKEN_COMPLETO
GOOGLE_OAUTH_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_OAUTH_SCOPES=["https://www.googleapis.com/auth/drive"]
GOOGLE_OAUTH_EXPIRY=2026-05-14T15:41:23Z
```

**⚠️ IMPORTANTE**: Os valores acima você encontra em:
- Supabase: Project Settings > API
- Google: Google Cloud Console > Credenciais
- Token OAuth: Veja seção 5

---

## 5. Autenticação OAuth

### 5.1 Usar Token Existente (RECOMENDADO)

Se você já tem o token OAuth funcionando na sua máquina local:

```bash
# Na sua máquina local, copie o token de .env:
cat .env | grep GOOGLE_OAUTH_TOKEN

# Adicione esse valor ao .env da VPS
GOOGLE_OAUTH_TOKEN=ya29.SEU_TOKEN_AQUI
```

**Por que funciona?**
- O token OAuth é **independente da máquina**
- O script `google_drive_sync_with_token.py` usa o token do .env
- Não precisa re-autenticar na VPS

### 5.2 Gerar Novo Token (Se necessário)

Se o token expirar ou precisar de um novo:

```bash
# Na VPS, instale as dependências do OAuth:
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Crie o arquivo de credenciais
mkdir -p .credentials
# Copie oauth_credentials.json para .credentials/ (do seu projeto Google Cloud)

# Execute o script de teste (abre navegador local para autorizar)
python3 test_oauth_google_drive.py

# Após autorizar, o token será salvo em .credentials/google_token.json
# Copie para .env:
cat .credentials/google_token.json

# Cole o token em GOOGLE_OAUTH_TOKEN no .env
```

**⚠️ NOTA**: Se a VPS não tiver interface gráfica:
- Use `google_drive_sync.py` e redirecione a autorização para sua máquina local
- Ou copie o token já autorizado do seu .env local (seção 5.1)

---

## 6. Execução na VPS

### 6.1 Teste Manual
```bash
# Ativar virtual environment
source venv/bin/activate  # Linux/macOS

# Testar conexão Supabase
python3 -c "from supabase import create_client; print('✅ Supabase OK')"

# Testar Google Drive
python3 test_oauth_google_drive.py

# Processar um orçamento (teste)
python3 processar_orcamento.py 12052601
```

### 6.2 Executar Pipeline Manual
```bash
# Uma execução completa do pipeline
python3 executar_pipeline.py

# Com output para arquivo (para logs)
python3 executar_pipeline.py >> pipeline.log 2>&1
```

### 6.3 Executar Pipeline Automático (Recomendado)
```bash
# Rode continuamente a cada 60 segundos
python3 auto_pipeline.py

# Em background (com nohup):
nohup python3 auto_pipeline.py > auto_pipeline.log 2>&1 &

# Ou com screen (para monitorar):
screen -S pipeline_auto
python3 auto_pipeline.py
# Pressione Ctrl+A depois D para desanexar

# Ou com systemd (para iniciar automaticamente na VPS)
# Veja seção 6.4
```

### 6.4 Configurar com Systemd (Auto-iniciar na VPS)

Crie arquivo `/etc/systemd/system/inss-pipeline.service`:

```ini
[Unit]
Description=INSS Automation Pipeline
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/home/seu_usuario/paulo-inss-agente
Environment="PATH=/home/seu_usuario/paulo-inss-agente/venv/bin"
ExecStart=/home/seu_usuario/paulo-inss-agente/venv/bin/python3 auto_pipeline.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable inss-pipeline
sudo systemctl start inss-pipeline

# Verificar status
sudo systemctl status inss-pipeline

# Ver logs
sudo journalctl -u inss-pipeline -f
```

---

## 7. Troubleshooting

### ❌ Erro: "ModuleNotFoundError: No module named 'supabase'"
```bash
# Solução:
pip install supabase python-dotenv pandas google-auth-oauthlib google-api-python-client
```

### ❌ Erro: "Token OAuth inválido"
```bash
# O token expirou - solução:
# 1. Execute test_oauth_google_drive.py para gerar novo
# 2. Copie o novo token para .env
# 3. Atualize GOOGLE_OAUTH_EXPIRY também
```

### ❌ Erro: "SUPABASE_URL not configured"
```bash
# Verifique se .env está no diretório correto:
ls -la .env

# E contém os valores:
grep SUPABASE_URL .env
```

### ❌ Erro: "Pasta não encontrada no Drive"
```bash
# O GOOGLE_DRIVE_FOLDER_ID está incorreto
# Verifique em:
# https://drive.google.com/drive/folders/SEU_ID_AQUI

# Copie o ID exato da URL e atualize .env
```

### ✅ Como Verificar se Tudo Está OK
```bash
# Execute este script de teste:
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("VERIFICAÇÃO DE CONFIGURAÇÃO")
print("=" * 80)

checks = {
    "Supabase URL": os.getenv('SUPABASE_URL'),
    "Supabase Key": os.getenv('SUPABASE_KEY')[:20] + "...",
    "Google Drive Habilitado": os.getenv('GOOGLE_DRIVE_ENABLED'),
    "Google Drive Folder ID": os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
    "OAuth Token": os.getenv('GOOGLE_OAUTH_TOKEN')[:20] + "..." if os.getenv('GOOGLE_OAUTH_TOKEN') else "❌",
    "OAuth Client ID": os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
}

for check, value in checks.items():
    status = "✅" if value else "❌"
    print(f"{status} {check}: {value}")
EOF
```

---

## 📊 Resumo do Fluxo de Deployment

```
1. GitHub
   ├─ Criar repositório PRIVATE
   ├─ Fazer push (sem .env, sem .credentials/)
   └─ .env.example serve como template

2. VPS
   ├─ Clone do repositório
   ├─ Instalar Python e dependências
   ├─ Criar arquivo .env (copiar credenciais da máquina local)
   ├─ Testar conexões (Supabase + Google Drive)
   └─ Rodar auto_pipeline.py (manual ou via systemd)

3. Google Drive OAuth
   ├─ Token do .env local → VPS .env (RECOMENDADO)
   ├─ Ou gerar novo token na VPS se expirar
   └─ Nunca precisa de re-autenticação se token válido
```

---

## 🎯 Checklist Pre-Deploy

- [ ] Repositório GitHub criado (PRIVATE)
- [ ] .gitignore contém `.env` e `.credentials/`
- [ ] Arquivo `.env.example` criado sem valores sensíveis
- [ ] Todos os scripts Python testados localmente
- [ ] VPS tem Python 3.9+
- [ ] SSH access configurado para VPS
- [ ] Credenciais Supabase atualizadas
- [ ] Token OAuth funcionando
- [ ] Google Drive folder ID correto

---

## 📞 Próximas Ações

Após fazer o push:
1. ✅ Comitar e fazer push para GitHub
2. ✅ Clonar na VPS
3. ✅ Configurar .env na VPS
4. ✅ Rodar teste de conexão
5. ✅ Iniciar auto_pipeline.py
6. ✅ Monitorar logs e confirmar processamentos
