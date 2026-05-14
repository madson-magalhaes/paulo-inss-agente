# 🏗️ Paulo INSS - Agente de Automação de Orçamentos

Sistema de automação completo para processamento de orçamentos INSS com otimização tributária e sincronização automática com Google Drive.

## ✨ Features

- ✅ **Pipeline Automático**: Processa orçamentos continuamente a cada 60 segundos
- ✅ **OAuth 2.0 Google Drive**: Sincronização automática com Google Drive (VPS-ready)
- ✅ **Supabase Integration**: Coleta e armazenamento de dados em tempo real
- ✅ **INSS Optimization**: Cálculo automático de estratégias de otimização tributária
- ✅ **Multi-plataforma**: Windows, Linux, macOS, VPS
- ✅ **Sem Interface Gráfica**: Funciona 100% em VPS sem navegador

## 🚀 Quick Start

### Instalação Local

```bash
# Clonar repositório
git clone https://github.com/SEU_USUARIO/paulo-inss-agente.git
cd paulo-inss-agente

# Criar virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou venv\Scripts\activate.bat  # Windows CMD
# ou venv\Scripts\Activate.ps1  # Windows PowerShell

# Instalar dependências
pip install -r requirements.txt

# Configurar credenciais
cp .env.example .env
# Edite .env com suas credenciais Supabase e Google Drive

# Executar pipeline manual
python3 executar_pipeline.py

# Ou rodar automático (a cada 60s)
python3 auto_pipeline.py
```

## 📦 Estrutura do Projeto

```
v6_agente_ia/
├── auto_pipeline.py              # ⭐ Pipeline automático principal
├── executar_pipeline.py          # Execução manual
├── coletar.py                    # Coleta Supabase
├── processar_orcamento.py        # Processamento INSS
├── main.py                       # Engine INSS
├── atualizar_status_processado.py # Status + Google Drive
├── google_drive_sync_with_token.py # Upload (VPS-ready)
├── test_oauth_google_drive.py    # Teste OAuth
├── .env.example                  # Template
├── requirements.txt              # Dependências
├── DEPLOYMENT_GITHUB.md          # ⭐ Guia deploy
└── orcamentos/                   # Pastas de orçamentos
```

## 🔧 Configuração

Veja `DEPLOYMENT_GITHUB.md` para setup completo.

## 🔄 Fluxo de Processamento

1. **COLETA** (Supabase) → Detecta 'aberto'
2. **VALIDAÇÃO** → Aguarda 2 ciclos (segurança)
3. **PROCESSAMENTO** → Calcula INSS
4. **FINALIZAÇÃO** → Status + Google Drive

## ✅ OAuth Google Drive na VPS

**Recomendado**: Copie o token do `.env` local para VPS `.env`

```bash
# Máquina local
cat .env | grep GOOGLE_OAUTH_TOKEN

# Cole no .env da VPS - funciona perfeitamente!
# Não precisa re-autenticar
```

**Por que funciona:**
- Token é independente da máquina
- Válido ~1 ano
- Script usa apenas token do .env
- Sem necessidade de navegador na VPS

## 📞 Deploy

Guia completo em **DEPLOYMENT_GITHUB.md**:
- Push GitHub
- Clone VPS
- Setup .env
- Systemd auto-start

## 🔐 Segurança

- ✅ `.env` no .gitignore
- ✅ Credenciais apenas locais
- ✅ Recomenda-se repositório PRIVATE

---

**Status**: ✅ Production Ready | **Maio 2026**
