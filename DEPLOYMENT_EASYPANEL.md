# 🚀 Deployment no EasyPanel - Guia Completo

## ✅ Status
Sistema **100% pronto** para rodar no EasyPanel com Docker.

---

## 📋 ÍNDICE
1. [Pré-requisitos](#1-pré-requisitos)
2. [Criar Aplicação no EasyPanel](#2-criar-aplicação-no-easypanel)
3. [Configurar Repository](#3-configurar-repository)
4. [Adicionar Variáveis de Ambiente](#4-adicionar-variáveis-de-ambiente)
5. [Configurar Volumes](#5-configurar-volumes)
6. [Build e Deploy](#6-build-e-deploy)
7. [Monitorar Logs](#7-monitorar-logs)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Pré-requisitos

- ✅ Repositório GitHub público ou privado
- ✅ Acesso ao EasyPanel (admin ou owner)
- ✅ Docker ativado no EasyPanel
- ✅ Espaço em disco (~2GB para dados + cache)

---

## 2. Criar Aplicação no EasyPanel

### 2.1 No painel do EasyPanel:
1. Acesse **Applications** ou **Services**
2. Clique em **+ New Application**
3. Escolha **Docker**
4. Nomeie: `paulo-inss-pipeline` (ou seu nome preferido)

---

## 3. Configurar Repository

### 3.1 Conectar ao GitHub

**Campo: Repository**
```
https://github.com/madson-magalhaes/paulo-inss-agente.git
```

**Branch:** `main`

**Build Path (ou Docker Path):**
```
/
```

**Dockerfile Location:**
```
Dockerfile
```

**Build Context:**
```
/
```

### 3.2 Configurar Deploy Automático (Opcional)
- ☑️ Deploy on push (faz redeploy automaticamente ao fazer push)
- Webhook do GitHub: EasyPanel vai gerar automaticamente

---

## 4. Adicionar Variáveis de Ambiente

### 4.1 No EasyPanel, acesse **Environment Variables** e adicione:

```env
# SUPABASE CONFIGURATION
SUPABASE_URL=https://pyagqbqzyksbiutkeyzk.supabase.co
SUPABASE_KEY=sb_publishable_YKMHWGCC6E0K3QPX3KIDrQ_vgCOXGEc

# GOOGLE DRIVE CONFIGURATION
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=1hh8APinmIZ9CNT98yZ2DJP2H-q0gk1Ou

# GOOGLE OAUTH CREDENTIALS
GOOGLE_OAUTH_CLIENT_ID=874028756707-cksloqplbn0qhbmidudh6l1dub2e91eh.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=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

# GOOGLE OAUTH TOKEN (Essencial para VPS - não precisa re-autorizar)
GOOGLE_OAUTH_TOKEN=ya29.a0AQvPyINp42oxOF6Rd5uB2jTF3yFLKx5_sFNVU4L5bTT2bxlQXEnP1WUE3htdR4Ip9dHr5hnr5QyI2sfhOp39VLB6h-XOVqwQQonL8jt5sAEL5PV5F9pVL_T9k2hV-sxRzlqWtVZYvYlJ4C8khxRtlrTQYYPt1W2-dzYglsHwz_CpcRLRd43yNSot_FeEbvLQR-iLtvLeVsKJrw8VgoGM4TF_eYsgPuKWKsqNe7zO0EQQV4w39fLoVjlaVnkNQ1MHDV3pqcX-SgTE-XE9iWhNh9oUhRw2aCgYKATgSARESFQHGX2MiqXwben-n2MYthJfzlsA95Q0291
GOOGLE_OAUTH_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_OAUTH_EXPIRY=2026-05-14T15:41:23Z

# SMTP (opcional - se quiser emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
```

**⚠️ IMPORTANTE:** Não coloque `.env` no GitHub. Use o formulário do EasyPanel.

---

## 5. Configurar Volumes

No EasyPanel, acesse **Volumes** e crie/adicione:

| Caminho no Container | Caminho no Host | Descrição |
|---|---|---|
| `/app/.env` | `/data/paulo-inss/.env` | Arquivo de configuração (mantém credenciais) |
| `/app/orcamentos` | `/data/paulo-inss/orcamentos` | Dados dos orçamentos (persistência) |
| `/app/.credentials` | `/data/paulo-inss/.credentials` | Credenciais OAuth (se usar local auth) |
| `/app/.claude` | `/data/paulo-inss/.claude` | Arquivos de controle (validação, logs) |

**Ou, se EasyPanel suporta volumes nomeados:**
```
volume-paulo-inss-orcamentos → /app/orcamentos
volume-paulo-inss-control → /app/.claude
volume-paulo-inss-credentials → /app/.credentials
```

---

## 6. Build e Deploy

### 6.1 Primeiro Deploy
1. Clique em **Build** (vai fazer build da imagem Docker)
   - Isso vai levar 2-5 minutos (Python 3.11 + dependências)
   - Você pode monitorar no log

2. Após build bem-sucedido, clique em **Deploy**
   - Container vai iniciar
   - `auto_pipeline.py` vai começar a rodar

### 6.2 Verificar se está rodando
- Acesse **Containers** ou **Services**
- Status deve ser 🟢 **Running**

---

## 7. Monitorar Logs

### 7.1 Logs em tempo real
1. No EasyPanel, acesse **Logs** ou **Container Logs**
2. Você verá a saída do `auto_pipeline.py` em tempo real

**O que procurar:**
```
✓ Conexão bem-sucedida!           ← Supabase OK
✓ 1 orçamento(s) encontrado(s)    ← Detectou trabalho
✓ 1 CSV(s) criado(s)              ← Exportou dados
```

### 7.2 Rotação de logs
- EasyPanel geralmente mantém 7-30 dias de logs
- Use **Download Logs** se precisar arquivo completo

---

## 8. Troubleshooting

### ❌ "Failed to build image"

**Solução:**
1. Verifique se `requirements.txt` está na raiz
2. Verifique se `Dockerfile` está na raiz
3. Tente rebuild: **Build** → **Force Rebuild**

```bash
# No seu PC, teste localmente:
docker build -t paulo-inss:test .
docker run paulo-inss:test
```

### ❌ "ModuleNotFoundError: No module named 'supabase'"

**Solução:**
- Rode `pip install -r requirements.txt` localmente
- Verifique se `requirements.txt` está atualizado
- Force rebuild no EasyPanel

### ❌ "GOOGLE_OAUTH_TOKEN inválido"

**Solução:**
1. Copie token atualizado do seu `.env` local
2. Atualize em **Environment Variables** no EasyPanel
3. Redeploy a aplicação

### ❌ "Pasta /app/orcamentos não encontrada"

**Solução:**
- Verifique se volumes estão criados
- Se não, crie manualmente:
  ```bash
  docker exec <container_id> mkdir -p /app/orcamentos /app/.credentials /app/.claude
  ```

### ❌ Logs vazios / aplicação não inicia

**Solução:**
1. Verifique **Environment Variables** (todas configuradas?)
2. Verifique **Volumes** (estão mounted?)
3. Tente **Restart Container**
4. Se nada funcionar: **Rebuild** + **Redeploy**

---

## 📊 Checklist de Configuração

- [ ] Repositório conectado ao GitHub
- [ ] Branch = `main`
- [ ] Dockerfile detectado e configurado
- [ ] Todas as 10+ variáveis de ambiente adicionadas
- [ ] Volumes criados para: orcamentos, .credentials, .claude
- [ ] Build bem-sucedido (status 🟢)
- [ ] Container rodando (status 🟢)
- [ ] Logs mostram "auto_pipeline.py" rodando
- [ ] Primeiro ciclo completo (verificar logs por "✓ Coleta concluída")

---

## 🎯 Fluxo de Atualização

Sempre que quiser atualizar código no EasyPanel:

**Local (seu PC):**
```bash
cd /path/to/paulo-inss-agente
git add .
git commit -m "update: descrição"
git push origin main
```

**EasyPanel (automático se "Deploy on push" habilitado):**
- GitHub webhook notifica EasyPanel
- EasyPanel faz pull, rebuild, redeploy
- Novo código está vivo em 2-5 minutos

**Ou manual no EasyPanel:**
1. **Redeploy** (usa código já puxado)
2. **Rebuild** (puxa código novo + rebuild)

---

## 📞 Próximos Passos

1. ✅ Copiar **Dockerfile** para seu repositório local
2. ✅ Fazer push para GitHub: `git add Dockerfile && git commit -m "add: Dockerfile for EasyPanel deployment" && git push`
3. ✅ No EasyPanel: **New Application** → **Docker** → Conectar GitHub
4. ✅ Adicionar variáveis de ambiente
5. ✅ Configurar volumes
6. ✅ Build → Deploy
7. ✅ Monitorar logs e confirmar funcionamento

Tá pronto! Qualquer dúvida durante config no EasyPanel, me chama 🚀

