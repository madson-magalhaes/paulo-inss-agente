# ✅ CONFIGURAÇÃO OAUTH GOOGLE DRIVE - COMPLETO

## Status: ✅ FUNCIONANDO

### Teste Realizado
- ✅ Autenticação OAuth com Google
- ✅ Acesso à pasta "Orcamentos INSS de obra"
- ✅ Token salvo e renovado automaticamente

---

## 📁 Arquivos de Configuração

### `.env` (Variáveis de Ambiente)
```bash
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=1hh8APinmIZ9CNT98yZ2DJP2H-q0gk1Ou
GOOGLE_OAUTH_CLIENT_ID=874028756707-cksloqplbn0qhbmidudh6l1dub2e91eh.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=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
GOOGLE_OAUTH_CREDENTIALS_FILE=.credentials/oauth_credentials.json
GOOGLE_OAUTH_TOKEN_PATH=.credentials/google_token.json
```

### `.credentials/oauth_credentials.json`
- ✅ Arquivo criado e configurado
- ✅ Contém client_id e client_secret
- ⚠️ NÃO commitar no Git (está em .gitignore)

### `.credentials/google_token.json`
- ✅ Token OAuth gerado automaticamente
- ✅ Renovado automaticamente quando expira
- ⚠️ NÃO commitar no Git (está em .gitignore)

---

## 🔄 Fluxo de Processamento

```
Entrada → Processamento → paulo_inss → Status Processado → Google Drive Upload
  ↓            ↓              ✅             ✅                  ✅
 OK          OK           Inserido      Atualizado          Sincronizado
```

### Etapas (Ordem Crítica):

1. **Validar Arquivos INSS**
   - Verifica se CSV foi gerado
   - Se falhar: ❌ ABORTA

2. **Inserir em paulo_inss**
   - Extrai valores de INSS otimizado
   - Calcula percentual de economia
   - Se falhar: ❌ ABORTA

3. **Marcar como 'processado'**
   - Atualiza status em paulo_orcamentos
   - Se falhar: ❌ ABORTA

4. **Upload para Google Drive** (ÚLTIMO PASSO)
   - Só executa se tudo anterior foi OK
   - Se falhar: ⚠️ AVISO (não cancela o ciclo)

---

## 🚀 Como Usar

### Opção 1: Teste Rápido
```bash
python3 test_oauth_google_drive.py
```

Resultado esperado:
```
✅ Autenticação bem-sucedida!
✅ Conectado ao Google Drive!
✅ Pasta acessível: Orcamentos INSS de obra
✅ TODOS OS TESTES PASSARAM!
```

### Opção 2: Processar um Orçamento Completo
```bash
# Isso executará TODO o ciclo:
# 1. Validar INSS
# 2. Inserir em paulo_inss
# 3. Marcar como processado
# 4. Upload para Google Drive
python3 atualizar_status_processado.py 12052601
```

Resultado esperado:
```
================================================================================
FINALIZAR CICLO: PAULO_INSS + STATUS PROCESSADO + GOOGLE DRIVE
================================================================================

ETAPA 1: VALIDAR ARQUIVOS INSS
✓ Arquivos INSS validados

ETAPA 2: INSERIR DADOS EM PAULO_INSS
✓ Dados inseridos em paulo_inss

ETAPA 3: MARCAR STATUS COMO PROCESSADO
✓ 1 registro(s) marcado(s)

ETAPA 4: SINCRONIZAR COM GOOGLE DRIVE (FINAL)
✅ Sincronização com Google Drive concluída!

================================================================================
✅ CICLO COMPLETADO COM SUCESSO
================================================================================
```

---

## 🔐 Segurança

### ✅ Boas Práticas Implementadas

1. **Credenciais no `.env`**
   - Não hardcodadas no código
   - Variavelizadas em um único lugar
   - Fácil de rotacionar

2. **Token OAuth**
   - Gerado automaticamente na primeira execução
   - Renovado automaticamente quando expira
   - Salvo localmente (seguro)

3. **Git Protection**
   - `.env` está em `.gitignore`
   - `.credentials/` está em `.gitignore`
   - Apenas `.env.example` é versionado

4. **Ordem de Execução**
   - Google Drive é **ÚLTIMO passo**
   - Só executa após paulo_inss + status OK
   - Garante consistência de dados

---

## 📊 Monitoramento

### Verificar Uploads no Drive
```bash
python3 monitor_drive_uploads.py
```

### Ver Sincronizações Realizadas
```bash
cat .claude/drive_sincronizacoes.json
```

Exemplo:
```json
{
  "12052601": {
    "data": "2026-05-14T11:35:22.123456",
    "status": "completo"
  }
}
```

---

## 🐛 Troubleshooting

### Erro: "Token expirado"
```
Solução: Execute qualquer script uma vez
→ Token será renovado automaticamente
```

### Erro: "Pasta não acessível"
```
Solução: Compartilhe a pasta com sua conta Google
→ Ou use a conta que gerou o OAuth
```

### Erro: "Credenciais inválidas"
```
Solução: Regenere o token
$ rm .credentials/google_token.json
$ python3 test_oauth_google_drive.py  # Refaz autenticação
```

---

## 📋 Checklist

- [x] Client ID configurado no .env
- [x] Client Secret configurado no .env
- [x] Arquivo oauth_credentials.json criado
- [x] Token OAuth gerado
- [x] Acesso à pasta verificado
- [x] Script google_drive_sync.py usando OAuth
- [x] Fluxo: paulo_inss → processado → Google Drive
- [x] Monitoramento implementado

---

## 🔗 Links Úteis

- Google Drive API: https://developers.google.com/drive/api/guides/about-files
- OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Troubleshooting: https://support.google.com/drive

