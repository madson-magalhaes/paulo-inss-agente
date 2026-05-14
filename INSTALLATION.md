# 📦 Instalação & Deployment

## 🏠 Local (Mac/Linux/Windows)

### 1. Setup

```bash
git clone https://github.com/seu-usuario/paulo-inss.git
cd paulo-inss
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configurar .env

Edite `.env`:
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave
GOOGLE_DRIVE_FOLDER_ID=seu-folder-id
```

### 3. OAuth (primeira vez)

```bash
mkdir -p .credentials
# Copie client_secret_*.json para .credentials/oauth_credentials.json
python3 google_drive_sync.py 12052601
```

Copie o link do browser, autorize. Token salvo automaticamente.

### 4. Rodar

```bash
python3 auto_pipeline.py
```

---

## 🖥️ VPS (Linux)

### 1. Setup

```bash
ssh seu-usuario@vps.com
cd /home/seu-usuario
git clone https://github.com/seu-usuario/paulo-inss.git
cd paulo-inss
pip install -r requirements.txt
cp .env.example .env
chmod +x *.py
```

### 2. Configurar .env

```bash
nano .env
```

Preencha as mesmas credenciais de LOCAL.

### 3. Copiar Token OAuth

**De LOCAL:**
```bash
scp .credentials/google_token.json seu-usuario@vps.com:/tmp/
```

**Na VPS:**
```bash
mkdir -p .credentials
mv /tmp/google_token.json .credentials/
```

### 4. Testar

```bash
python3 auto_pipeline.py
```

Se rodar sem erros → ✅ Pronto!

### 5. Agendar com Cron

```bash
crontab -e
```

Adicione (exemplo: a cada 5 minutos):
```cron
*/5 * * * * cd /home/seu-usuario/paulo-inss && python3 auto_pipeline.py >> /var/log/paulo-inss.log 2>&1
```

### 6. Monitorar Logs

```bash
tail -f /var/log/paulo-inss.log
```

---

## ✅ Checklist

**Local:**
- [ ] Git clonado
- [ ] `pip install -r requirements.txt`
- [ ] `.env` configurado
- [ ] `.credentials/oauth_credentials.json` copiado
- [ ] `python3 google_drive_sync.py 12052601` (autenticado)
- [ ] `python3 auto_pipeline.py` (testado)

**VPS:**
- [ ] Git clonado
- [ ] `pip install -r requirements.txt`
- [ ] `.env` configurado
- [ ] `.credentials/google_token.json` copiado de LOCAL
- [ ] `python3 auto_pipeline.py` (testado)
- [ ] Cron agendado
- [ ] Logs funcionando

---

**Versão:** 5.0 | **Data:** May 14, 2026
