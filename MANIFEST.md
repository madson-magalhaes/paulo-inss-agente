# 📦 v6_agente_ia - Manifest

Pasta contém todos os arquivos necessários para funcionamento completo.

## ✅ Arquivos Essenciais

### 🤖 Scripts Python (7 arquivos)
- ✅ `auto_pipeline.py` - Pipeline automático principal
- ✅ `executar_pipeline.py` - Executor do pipeline
- ✅ `google_drive_sync.py` - Sincronização Google Drive (OAuth)
- ✅ `marcar_processando.py` - Marca status no Supabase
- ✅ `utils.py` - Funções utilitárias
- ✅ `io_handlers.py` - Leitura/escrita de CSV

### 📊 Dados de Referência (2 arquivos)
- ✅ `icm.csv` - Tabela ICM (Jan/18 a Mai/26)
- ✅ `vau.csv` - Tabela VAU (Mai/26)

### 📋 Configuração (3 arquivos)
- ✅ `.env.example` - Exemplo de variáveis
- ✅ `requirements.txt` - Dependências Python
- ✅ `.gitignore` - Arquivos a ignorar no Git

### 📚 Documentação (4 arquivos)
- ✅ `README.md` - Overview e quick start
- ✅ `INSTALLATION.md` - Setup local e VPS
- ✅ `SETUP_OAUTH.md` - Google OAuth
- ✅ `.credentials/README.md` - Explicação credenciais

### 📂 Pastas (3 pastas vazias para dados)
- ✅ `.credentials/` - Credenciais OAuth
- ✅ `dados_supabase/` - CSVs coletados (gerado)
- ✅ `orcamentos/` - Orçamentos processados (gerado)

---

## 🚀 Como Usar

### 1. Setup

```bash
git clone https://github.com/seu-usuario/paulo-inss.git
cd paulo-inss
pip install -r requirements.txt
cp .env.example .env
```

### 2. OAuth (primeira vez)

```bash
mkdir -p .credentials
# Copie client_secret_*.json para .credentials/oauth_credentials.json
python3 google_drive_sync.py 12052601
```

### 3. Rodar

```bash
python3 auto_pipeline.py
```

### 4. VPS

```bash
scp .credentials/google_token.json usuario@vps:/home/usuario/paulo-inss/.credentials/
# Cron: */5 * * * * cd /home/usuario/paulo-inss && python3 auto_pipeline.py
```

---

## 📌 Notas Importantes

- **Documentação:** Apenas essencial (3 arquivos)
- **Código:** Limpo e funcional
- **Imports:** Testados e funcionando
- **Git:** Pronto para fazer commit
- **Deploys:** Local e VPS funcionam identicamente

---

**Versão:** 6.0 | **Data:** May 14, 2026
