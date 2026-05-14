# 🔴 PROBLEMA ENCONTRADO: Service Account sem Cota de Armazenamento

## O Erro
```
Error 403: Service Accounts do not have storage quota. 
Leverage shared drives or use OAuth delegation instead.
```

## ✅ SOLUÇÃO 1: Usar Google Shared Drive (RECOMENDADO)

### O que é?
Shared Drive é uma pasta de equipe que não conta com a cota individual de armazenamento de ninguém.

### Passo a passo:
1. **No Google Drive (na conta pessoal):**
   - Ir para: https://drive.google.com/drive/shared-drives
   - Clicar em "+ Nova unidade compartilhada"
   - Nomear: "INSS - Orçamentos"
   - Clicar em "Criar"

2. **Adicionar a Service Account:**
   - Abrir a unidade compartilhada
   - Clicar em "Gerenciar membros"
   - Adicionar: `google-drive-agente-inss@gdrive-inss-agentes-ia.iam.gserviceaccount.com`
   - Dar permissão de "Editor"

3. **Copiar o ID da Shared Drive:**
   - URL: `https://drive.google.com/drive/folders/XXXXX`
   - XXXXX é o ID

4. **Atualizar .env:**
   ```bash
   GOOGLE_DRIVE_FOLDER_ID=XXXXX  # ID da Shared Drive
   ```

### Vantagens:
✅ Espaço ilimitado (até o limite da Google Workspace)
✅ Service Account com acesso total
✅ Sem problemas de cota
✅ Perfeito para automação


## ⚠️ SOLUÇÃO 2: Usar OAuth 2.0 com Sua Conta Pessoal

### O que é?
Autenticar com sua conta do Gmail pessoal ao invés de usar Service Account.

### Passo a passo:
1. Mudar `google_drive_sync.py` para usar OAuth flow
2. Na primeira execução, autorizar a aplicação
3. Token é salvo para futuras execuções

### Vantagens:
✅ Usa sua cota de armazenamento pessoal
✅ Funciona imediatamente
✅ Sem custos

### Desvantagens:
❌ Não é ideal para automação (precisa renovar token periodicamente)
❌ Acoplado à conta pessoal
❌ Problema se a conta for desativada


## 🎯 RECOMENDAÇÃO FINAL

**Use SOLUÇÃO 1 (Shared Drive)** porque:
- ✅ Melhor para produção
- ✅ Automação confiável
- ✅ Sem dependência de contas pessoais
- ✅ Escalável

---

## 📋 RESUMO RÁPIDO

### Para Shared Drive:
1. Criar Shared Drive no Google
2. Adicionar Service Account como Editor
3. Atualizar GOOGLE_DRIVE_FOLDER_ID no .env
4. Pronto! ✅

### Para OAuth:
1. Voltar script para OAuth mode
2. Executar uma vez (abre navegador)
3. Autorizar a aplicação
4. Pronto! ✅

---

## 🔗 Links Úteis
- Google Shared Drives: https://drive.google.com/drive/shared-drives
- Documentação Service Account: https://developers.google.com/identity/protocols/oauth2/service-account
- Troubleshooting: https://support.google.com/a/answer/7281227

