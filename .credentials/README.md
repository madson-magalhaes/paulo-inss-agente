# 🔐 Pasta .credentials - OAuth 2.0

Esta pasta armazena as credenciais e tokens para autenticação Google Drive via OAuth 2.0.

## 📁 Conteúdo

### `oauth_credentials.json` ⚠️
- **Descrição:** Cliente ID e Secret do Google Cloud Console
- **Criado em:** Google Cloud Console → APIs & Services → Credentials
- **Tamanho:** ~500 bytes
- **Commitar no Git:** ❌ **NÃO**
- **Copiar para VPS:** ❌ **NÃO** (já está configurado no Google Cloud)
- **Sensível:** Sim, contém informações de autenticação

### `google_token.json` ✅
- **Descrição:** Token de acesso OAuth 2.0 (gerado automaticamente)
- **Criado em:** Primeira execução do script (com autenticação browser)
- **Tamanho:** ~1-2 KB
- **Commitar no Git:** ❌ **NÃO**
- **Copiar para VPS:** ✅ **SIM** (reutilizar token em VPS)
- **Reutilizável:** Sim, entre máquinas
- **Expira:** Automaticamente (renova sozinho)

---

## 🔄 Fluxo de Funcionamento

### 1️⃣ Primeira Execução (LOCAL)

```
LOCAL
├─ Executa: python3 google_drive_sync.py
├─ Lê: .credentials/oauth_credentials.json
├─ Abre: Browser (http://localhost:8080)
├─ Usuário: Autoriza acesso ao Google Drive
└─ Salva: .credentials/google_token.json ✅
```

### 2️⃣ Próximas Execuções (LOCAL)

```
LOCAL
├─ Executa: python3 auto_pipeline.py
├─ Lê: .credentials/google_token.json
├─ Verifica: Token válido?
│  ├─ SIM: Usa token existente
│  └─ NÃO: Renova automaticamente
└─ Upload: Google Drive ✅
```

### 3️⃣ VPS (sem browser)

```
VPS
├─ Copia: .credentials/google_token.json (de LOCAL)
├─ Executa: python3 auto_pipeline.py
├─ Lê: .credentials/google_token.json
├─ Verifica: Token válido?
│  ├─ SIM: Usa token
│  └─ NÃO: Renova automaticamente
└─ Upload: Google Drive ✅
```

---

## 📋 .gitignore

```gitignore
.credentials/oauth_credentials.json  # NUNCA commitar
.credentials/google_token.json       # NUNCA commitar
```

---

## 🚀 Como Usar

### Setup Local

```bash
# 1. Criar pasta
mkdir -p .credentials

# 2. Copiar arquivo do Google Cloud Console
cp ~/Downloads/client_secret_*.json .credentials/oauth_credentials.json

# 3. Primeira autenticação (gera token)
python3 google_drive_sync.py 12052601

# 4. Resultado
# ✅ .credentials/google_token.json criado
```

### Setup VPS

```bash
# 1. Copiar token de LOCAL
scp .credentials/google_token.json usuario@vps.com:/path/paulo-inss/.credentials/

# 2. Na VPS, certificar que arquivo está lá
ls -la .credentials/google_token.json

# 3. Agendar cron
crontab -e
# */5 * * * * cd /path/paulo-inss && python3 auto_pipeline.py
```

---

## ✅ Checklist

- [ ] `.credentials/oauth_credentials.json` existe (baixado de Google Cloud)
- [ ] `.credentials/google_token.json` criado (após primeira autenticação)
- [ ] Ambos os arquivos estão em `.gitignore`
- [ ] Token copiado para VPS (via scp ou manual)
- [ ] Teste em VPS: `python3 auto_pipeline.py`

---

## 🐛 Troubleshooting

### Erro: "Arquivo de credenciais não encontrado"

```bash
mkdir -p .credentials
# Certifique que .credentials/oauth_credentials.json existe
```

### Erro: "No token found"

```bash
# Executar autenticação novamente
python3 google_drive_sync.py 12052601
```

### VPS: "Token inválido/expirado"

- Token se renova automaticamente
- Se erro persistir, copie novo token de LOCAL

---

## 📝 Segurança

✅ **SAFE:**
- Copiar `google_token.json` entre máquinas
- Revisar em backups
- Armazenar em `.credentials/`

❌ **NÃO FAZER:**
- Commitar em Git
- Expor em logs
- Compartilhar credenciais pessoais

---

**Nota:** O token OAuth é vinculado à conta Gmail que o gerou. Se trocar de conta, repita a autenticação.
