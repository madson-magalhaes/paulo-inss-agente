# 🎯 EasyPanel - Passo a Passo Detalhado (Com Screenshots)

## ⚠️ PRÉ-REQUISITO
Você já deve estar logado no **EasyPanel** (seu painel de controle)

---

## PASSO 1️⃣ - Acessar Dashboard

1. Entre no seu EasyPanel (URL do seu painel)
2. Se aparecer login, use suas credenciais
3. Você deve ver um painel com opções como:
   - 🏠 Dashboard
   - 🐳 Applications / Services
   - ⚙️ Settings
   - 🗄️ Databases
   - 📋 Projects

**Você vai clicar em: `Applications` ou `Services` (depende da versão)**

---

## PASSO 2️⃣ - Criar Nova Aplicação

1. Procure por um botão **`+ New Application`** ou **`+ Add Service`**
   - Geralmente fica no topo direito ou centro da página

2. Clique nele

3. Uma lista de opções deve aparecer:
   ```
   ☐ Node.js
   ☐ Python
   ☐ Docker
   ☐ Git Repository
   ☐ Static Site
   ☐ ...
   ```

**Selecione: `Docker`**

---

## PASSO 3️⃣ - Configurar Nome da Aplicação

1. Um formulário vai abrir
2. Procure pelo campo **Application Name** ou **Service Name**
3. Digite:
   ```
   paulo-inss-pipeline
   ```

4. Campos opcionais (você pode preencher ou deixar em branco):
   - Description: `Sistema de automação de cálculos INSS`
   - Environment: `Production`

5. Clique em **`Next`** ou **`Continue`**

---

## PASSO 4️⃣ - Conectar GitHub (Repository)

Agora você vai ver uma seção com títulos como:

### **4.1 - Repository Settings**

Procure pelos campos:

| Campo | Valor |
|-------|-------|
| **Repository URL** | `https://github.com/madson-magalhaes/paulo-inss-agente.git` |
| **Branch** | `main` |
| **Access Token** (se solicitar) | Deixe em branco ou copie seu GitHub PAT |

**⚠️ IMPORTANTE:** Se EasyPanel pedir um token do GitHub:
- Vá em GitHub → Settings → Developer settings → Personal access tokens
- Crie um novo com permissão `repo` (read-only é suficiente)
- Copie o token e cole aqui

### **4.2 - Docker Configuration**

Procure pelos campos:

| Campo | Valor |
|-------|-------|
| **Dockerfile Path** | `Dockerfile` (EasyPanel deve autodetectar) |
| **Build Context** | `/` (raiz) |
| **Docker Image Name** | `paulo-inss` |

5. Clique em **`Next`** ou **`Continue`**

---

## PASSO 5️⃣ - Adicionar Variáveis de Ambiente

Agora você vai ver uma seção chamada:
- **Environment Variables**
- **Env Vars**
- **Configuration**

### **5.1 - Interface**

Você verá algo assim:
```
┌─────────────────────────────────────┐
│ Environment Variables               │
├─────────────────────────────────────┤
│ + Add Variable    [Key] [Value] [X] │
├─────────────────────────────────────┤
│ □ SUPABASE_URL                      │
│ □ SUPABASE_KEY                      │
│ □ ...                               │
└─────────────────────────────────────┘
```

### **5.2 - Adicionar as Variáveis**

Clique em **`+ Add Variable`** (ou semelhante) e adicione **CADA UMA** destas:

#### **Grupo 1: Supabase**
```
Key: SUPABASE_URL
Value: https://pyagqbqzyksbiutkeyzk.supabase.co
```
Clique ✅ ou `Add`

```
Key: SUPABASE_KEY
Value: sb_publishable_YKMHWGCC6E0K3QPX3KIDrQ_vgCOXGEc
```
Clique ✅

#### **Grupo 2: Google Drive**
```
Key: GOOGLE_DRIVE_ENABLED
Value: true
```

```
Key: GOOGLE_DRIVE_FOLDER_ID
Value: 1hh8APinmIZ9CNT98yZ2DJP2H-q0gk1Ou
```

#### **Grupo 3: Google OAuth - Client Credentials**
```
Key: GOOGLE_OAUTH_CLIENT_ID
Value: 874028756707-cksloqplbn0qhbmidudh6l1dub2e91eh.apps.googleusercontent.com
```

```
Key: GOOGLE_OAUTH_CLIENT_SECRET
Value: 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
```

#### **Grupo 4: Google OAuth - Token (CRÍTICO)**
```
Key: GOOGLE_OAUTH_TOKEN
Value: ya29.a0AQvPyINp42oxOF6Rd5uB2jTF3yFLKx5_sFNVU4L5bTT2bxlQXEnP1WUE3htdR4Ip9dHr5hnr5QyI2sfhOp39VLB6h-XOVqwQQonL8jt5sAEL5PV5F9pVL_T9k2hV-sxRzlqWtVZYvYlJ4C8khxRtlrTQYYPt1W2-dzYglsHwz_CpcRLRd43yNSot_FeEbvLQR-iLtvLeVsKJrw8VgoGM4TF_eYsgPuKWKsqNe7zO0EQQV4w39fLoVjlaVnkNQ1MHDV3pqcX-SgTE-XE9iWhNh9oUhRw2aCgYKATgSARESFQHGX2MiqXwben-n2MYthJfzlsA95Q0291
```

```
Key: GOOGLE_OAUTH_TOKEN_URI
Value: https://oauth2.googleapis.com/token
```

```
Key: GOOGLE_OAUTH_EXPIRY
Value: 2026-05-14T15:41:23Z
```

**⚠️ IMPORTANTE:** Se o campo `GOOGLE_OAUTH_TOKEN` for muito longo, pode parecer que não copiou certo. Mas copiou! Não deixe nada de fora.

5. Quando adicionar TODAS as variáveis, clique **`Next`** ou **`Continue`**

---

## PASSO 6️⃣ - Configurar Volumes (Storage/Persistent Data)

Agora você vai ver uma seção chamada:
- **Volumes**
- **Storage**
- **Mounts**
- **Persistent Storage**

### **6.1 - Criar Volumes**

EasyPanel pode ter dois formatos:

#### **FORMATO A - Criar Volumes Nomeados**

Procure por um campo tipo:
```
+ Add Volume
│
├─ Volume Name: [________________]
├─ Mount Path: [________________]
└─ [Add]
```

Adicione estes **4 volumes:**

**Volume 1 - Orçamentos**
```
Volume Name: paulo-inss-orcamentos
Mount Path: /app/orcamentos
```
Clique `Add`

**Volume 2 - Credenciais**
```
Volume Name: paulo-inss-credentials
Mount Path: /app/.credentials
```
Clique `Add`

**Volume 3 - Controle (validação, logs)**
```
Volume Name: paulo-inss-control
Mount Path: /app/.claude
```
Clique `Add`

**Volume 4 - Configuração (.env)**
```
Volume Name: paulo-inss-env
Mount Path: /app/.env
```
Clique `Add`

#### **FORMATO B - Usar Path do Host**

Se EasyPanel permitir apontar para caminho no servidor:

```
Host Path                    Container Path      Type
/data/paulo-inss/orcamentos  /app/orcamentos     (RW)
/data/paulo-inss/.credentials /app/.credentials  (RW)
/data/paulo-inss/.claude     /app/.claude        (RW)
```

**⚠️ NOTA:** Se não entender volumes por enquanto, deixe em branco e configure depois. Não bloqueia o deploy.

6. Clique **`Next`** ou **`Continue`**

---

## PASSO 7️⃣ - Review & Deploy

Agora você vai ver uma tela de **Review** ou **Summary** com:
- ✅ Application Name: `paulo-inss-pipeline`
- ✅ Repository: `https://github.com/madson-magalhaes/paulo-inss-agente.git`
- ✅ Dockerfile: `Dockerfile`
- ✅ Environment Variables: (todas listadas)
- ✅ Volumes: (todos listados)

### **7.1 - Verificar tudo**

Revise cada seção. Se tiver algo errado:
- Clique **`Back`** para voltar
- Corrija
- Volte ao review

### **7.2 - Clicar em Deploy/Create**

Procure por um botão grande:
- **`Deploy`**
- **`Create & Deploy`**
- **`Launch`**
- **`Start`**

**Clique nele!**

---

## PASSO 8️⃣ - Aguardar Build (2-5 minutos)

Depois de clicar em Deploy:

1. EasyPanel vai clonar seu GitHub
2. Vai fazer **Build** da imagem Docker (isso leva 2-5 minutos)
3. Você verá uma tela com:
   ```
   🔨 Building...
   📦 Downloading dependencies...
   ✓ Build completed!
   ```

4. Depois vai fazer **Deploy** (inicia o container):
   ```
   🚀 Deploying...
   ✓ Container started!
   ✓ Application running!
   ```

5. Quando terminar, você deve ver:
   ```
   Status: 🟢 RUNNING
   ```

---

## PASSO 9️⃣ - Verificar Logs (Confirmar que está funcionando)

1. Procure por uma aba **`Logs`** ou **`Container Logs`** no painel da aplicação
2. Clique nela
3. Você deve ver a saída do `auto_pipeline.py` em tempo real:

```
🔌 Conectando ao Supabase...
✓ Conexão bem-sucedida!
📥 Detectando orçamentos...
⏳ Nenhum orçamento em 'aberto'
(aguardando próximo ciclo...)
```

**Se ver isso, significa que está funcionando! ✅**

---

## 🔟 PASSO 10 - Configurações Adicionais (Opcional)

### **10.1 - Auto Deploy on Push**

Procure por uma opção tipo:
- **Webhook**
- **Auto Deploy**
- **Deploy on Push**

Se existir:
```
☑️ Deploy on push (recommended)
```

Isso faz o EasyPanel fazer redeploy automaticamente sempre que você faz `git push`

### **10.2 - Restart Policy**

Procure por:
- **Restart Policy**
- **Restart on Failure**

Se existir, selecione:
```
✓ Always (recomendado)
```

Isso garante que se o container cair, reinicia automaticamente.

### **10.3 - Resource Limits (Opcional)**

Se tiver opção de **Memory/CPU**:
```
Memory: 512 MB (ou 1GB se tiver)
CPU: 0.5 (ou 1 core)
```

Clique **`Save`** ou **`Update`**

---

## ✅ Checklist Final

Depois de tudo pronto, verifique:

- [ ] Aplicação criada no EasyPanel
- [ ] GitHub conectado
- [ ] Dockerfile detectado
- [ ] 8 variáveis de ambiente adicionadas
- [ ] Volumes criados (ou anotado para depois)
- [ ] Status = 🟢 RUNNING
- [ ] Logs mostram "Conectando ao Supabase..." e "✓ Conexão bem-sucedida"
- [ ] Logs continuam atualizando (significa que pipeline está rodando)

---

## 🆘 Se algo der errado:

| Problema | Solução |
|----------|---------|
| ❌ Build falhou | Clique em **Rebuild** → **Force Rebuild** |
| ❌ Container não inicia | Verifique **Logs**. Se vazio = problema na build |
| ❌ Logs vazios | Clique **Restart** na aplicação |
| ❌ "ModuleNotFoundError" | É problema de build. Força rebuild. |
| ❌ Variável faltando | Adicione em **Environment** → **Edit** |

---

## 📞 Resumo Rápido dos Passos

```
1. EasyPanel Dashboard → Applications
2. + New Application → Docker
3. Nome: paulo-inss-pipeline
4. GitHub: https://github.com/madson-magalhaes/paulo-inss-agente.git
5. Branch: main
6. Dockerfile: Dockerfile
7. Add 8 Environment Variables (copy-paste do guia acima)
8. Adicionar Volumes (4 volumes) - ou deixa pra depois
9. Review → Deploy
10. Aguarda 2-5 minutos (Build + Deploy)
11. Verifica Logs → Deve estar rodando
```

**Pronto! Seu pipeline está vivo no EasyPanel! 🚀**

---

## 💡 Dicas Finais

- **Logs em tempo real:** Sempre monitore logs na primeira semana
- **Git push redeploy:** Use `git push` para atualizar código (rápido)
- **Volumes importantes:** Crie volumes logo - dados persistem entre restarts
- **Token expira:** Anote em seu calendário: **14 de maio de 2026** (atualize token antes)

Qualquer dúvida durante esses passos, me chama! 💪

