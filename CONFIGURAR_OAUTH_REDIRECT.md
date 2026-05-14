# 🔧 Configurar Redirect URI no Google Cloud Console

## ⚠️ Problema Atual
```
Erro: Missing required parameter: redirect_uri
```

## ✅ Solução: Adicionar Redirect URI

### Passo 1: Acessar Google Cloud Console
1. Vá para: https://console.cloud.google.com/
2. Selecione o projeto: **gdrive-inss-agentes-ia**
3. No menu, acesse: **APIs & Services** → **Credentials**

### Passo 2: Editar OAuth Client
1. Encontre a credencial: **gdrive-inss-agentes-ia** (Desktop application)
2. Clique no lápis (Edit)

### Passo 3: Adicionar Redirect URIs
Na seção **"Authorized redirect URIs"**, adicione:

```
http://localhost:8080/
http://localhost:8080/callback/
```

### Passo 4: Salvar
1. Clique em **"Save"**
2. Aguarde a confirmação

---

## ✅ Depois de Configurar

Execute:
```bash
cd /Users/madsonmagalhaes/Documents/Paulo\ Robson\ INSS/v6_agente_ia
rm -f .credentials/google_token.json
python3 google_drive_sync.py 12052603
```

Resultado esperado:
```
🔗 Iniciando servidor local para autorização...

Abra este link no seu navegador com o perfil CORRETO:
https://accounts.google.com/o/oauth2/auth?...

[Você abre no navegador, autoriza, e volta aqui]

✅ Autorização concluída! Token salvo.
```

---

## 📸 Screenshots do Google Cloud Console

1. **OAuth Credentials Page**
   ```
   Authorized redirect URIs
   • http://localhost:8080/
   • http://localhost:8080/callback/
   ```

2. **Após salvar:**
   ```
   ✅ Aplicação salva com sucesso
   ```

---

## 🔗 Link Direto
https://console.cloud.google.com/apis/credentials

