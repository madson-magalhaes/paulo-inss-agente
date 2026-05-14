# 🚀 Setup OAuth Google Drive para VPS

## ✅ Token Já Gerado e Salvo

O token OAuth foi gerado e salvo em `.env`:

```env
# Token OAuth (Salvo após primeira autenticação)
GOOGLE_OAUTH_TOKEN=ya29.a0AQvPyINp42oxOF6Rd5uB2jTF3yFLKx5_sFNVU4L5bTT2bxlQXEnP1WUE3htdR4Ip9dHr5hnr5QyI2sfhOp39VLB6h-XOVqwQQonL8jt5sAEL5PV5F9pVL_T9k2hV-sxRzlqWtVZYvYlJ4C8khxRtlrTQYYPt1W2-dzYglsHwz_CpcRLRd43yNSot_FeEbvLQR-iLtvLeVsKJrw8VgoGM4TF_eYsgPuKWKsqNe7zO0EQQV4w39fLoVjlaVnkNQ1MHDV3pqcX-SgTE-XE9iWhNh9oUhRw2aCgYKATgSARESFQHGX2MiqXwben-n2MYthJfzlsA95Q0291
GOOGLE_OAUTH_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_OAUTH_SCOPES=["https://www.googleapis.com/auth/drive"]
GOOGLE_OAUTH_EXPIRY=2026-05-14T15:41:23Z
```

---

## 📋 Arquivos para VPS

### Necessários:
1. ✅ `.env` - com o token OAuth
2. ✅ `google_drive_sync_with_token.py` - usa token do .env
3. ✅ `atualizar_status_processado.py` - atualizado para usar novo script
4. ✅ `auto_pipeline.py` - rodar continuamente
5. ✅ `executar_pipeline.py` - orquestrador

### Não Necessários:
- ❌ `.credentials/google_token.json` - não precisa em VPS (token está no .env)
- ❌ `.credentials/oauth_credentials.json` - não precisa em VPS
- ❌ `google_drive_sync.py` - versão antiga (só com novo token)

---

## 🔄 Fluxo na VPS

```
1. Clonar repositório
   $ git clone seu_repo

2. Copiar .env com token
   $ scp .env seu_usuario@vps:/var/www/v6_agente_ia/

3. Instalar dependências
   $ pip install -r requirements.txt

4. Rodar auto_pipeline
   $ python3 auto_pipeline.py

5. Sistema roda a cada 60 segundos:
   - Coleta dados
   - Processa orçamentos
   - Insere em paulo_inss
   - Atualiza status
   - Faz upload no Google Drive (usando token do .env)
```

---

## ✅ Teste Rápido em VPS

```bash
# Verificar se token está carregado
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Token:', os.getenv('GOOGLE_OAUTH_TOKEN')[:50] + '...')"

# Testar sincronização
python3 google_drive_sync_with_token.py 12052603
```

Resultado esperado:
```
================================================================================
SINCRONIZAÇÃO COM GOOGLE DRIVE (Token do .env)
================================================================================

📋 Orçamento: 12052603

✅ Credenciais carregadas do .env
✅ Pasta criada no Drive: orcamento_12052603_Luis Augusto
   ✓ Upload: arquivo1.csv
   ✓ Upload: arquivo2.csv
✅ Sincronização completa para Google Drive (2 arquivo(s))
```

---

## 🔒 Segurança

### ✅ Implementado:
- Token armazenado em `.env` (protegido)
- `.env` não versionado (no .gitignore)
- Token automático na primeira execução
- Sem necessidade de arquivo de credenciais

### ⚠️ Cuidados:
1. **Backup do .env** em local seguro
2. **Permissões do arquivo**: `chmod 600 .env`
3. **Não compartilhe o token** com terceiros
4. **Regenere o token** se comprometido

---

## 🔄 Renovação do Token (se expirar)

Se o token expirar, execute localmente:
```bash
rm -f .credentials/google_token.json
python3 google_drive_sync.py <numero_orcamento>
# Siga as instruções de autorização
# Copie o novo token para .env
```

Depois atualize a VPS com o novo `.env`:
```bash
scp .env seu_usuario@vps:/var/www/v6_agente_ia/
```

---

## 📊 Monitoramento

### Ver logs
```bash
tail -f /var/log/agente-ia.log
```

### Ver uploads realizados
```bash
cat .claude/drive_sincronizacoes.json
```

### Teste manual
```bash
python3 atualizar_status_processado.py 12052603
```

---

## 🆘 Troubleshooting

### "Token expirado"
```
Solução: Regenerar token localmente e copiar .env para VPS
```

### "Pasta não encontrada"
```
Solução: Verifique se a pasta existe em ./orcamentos/
```

### "Erro ao sincronizar"
```
Solução: Verifique .env com todas as variáveis corretas
$ grep GOOGLE .env
```

---

## 📝 Checklist VPS

- [ ] `.env` copiado com token
- [ ] `google_drive_sync_with_token.py` presente
- [ ] `atualizar_status_processado.py` atualizado
- [ ] Teste rápido bem-sucedido
- [ ] `auto_pipeline.py` rodando
- [ ] Logs sendo gerados
- [ ] Uploads aparecendo no Google Drive

