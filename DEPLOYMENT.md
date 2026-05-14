# 🚀 Guia de Deployment na VPS

## Pré-requisitos
- Acesso SSH à VPS
- Git instalado
- Python 3.8+ instalado
- `.env` com as variáveis sensíveis

## Passo 1: Clone do Repositório

```bash
ssh seu_usuario@seu_vps.com
cd /var/www

# Clone o repositório
git clone seu_repo_aqui
cd v6_agente_ia
```

## Passo 2: Configurar Variáveis de Ambiente

### Opção A: Copiar arquivo `.env` manualmente (SEGURO)

Na sua máquina local:
```bash
# Copie o .env para a VPS via SCP (Seguro!)
scp .env seu_usuario@seu_vps.com:/var/www/v6_agente_ia/.env
```

Na VPS:
```bash
# Verifique que o arquivo foi copiado
ls -la .env

# Defina permissões (somente leitura para o proprietário)
chmod 600 .env
```

### Opção B: Usar Variáveis de Ambiente do Sistema

Se preferir não ter arquivo `.env`, defina as variáveis no sistemaa:

**Na VPS, edite o arquivo de inicialização:**

Para systemd service (`/etc/systemd/system/agente-ia.service`):
```ini
[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/var/www/v6_agente_ia
Environment="SUPABASE_URL=https://pyagqbqzyksbiutkeyzk.supabase.co"
Environment="SUPABASE_KEY=sb_publishable_YKMHWGCC6E0K3QPX3KIDrQ_vgCOXGEc"
Environment="GOOGLE_DRIVE_ENABLED=true"
Environment="GOOGLE_DRIVE_FOLDER_ID=1hh8APinmIZ9CNT98yZ2DJP2H-q0gk1Ou"
Environment="GOOGLE_SERVICE_ACCOUNT_TYPE=service_account"
Environment="GOOGLE_SERVICE_ACCOUNT_PROJECT_ID=gdrive-inss-agentes-ia"
# ... e assim por diante
ExecStart=/usr/bin/python3 seu_script.py
Restart=always
```

### Opção C: Usar `.env` com `.env.local` (Recomendado Híbrido)

```bash
# Na VPS
cp .env.example .env.local

# Edite apenas .env.local com as variáveis sensíveis
nano .env.local

# O script carregará ambos: .env.example (versionado) + .env.local (ignorado pelo git)
```

## Passo 3: Instalar Dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Passo 4: Testar Conexão com Google Drive

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Teste o script
python3 google_drive_sync.py 12052601
```

## Passo 5: Configurar Cron (Automação)

Para executar sincronização em horários específicos:

```bash
# Edite o crontab
crontab -e

# Adicione (exemplo: toda madrugada às 2:00 AM)
0 2 * * * cd /var/www/v6_agente_ia && source venv/bin/activate && python3 google_drive_sync.py >> /var/log/agente-ia.log 2>&1
```

## 🔒 Segurança

### ✅ Boas Práticas

1. **Nunca commite `.env`**
   ```bash
   # Verifique .gitignore
   cat .gitignore
   ```

2. **Proteça o arquivo `.env`**
   ```bash
   chmod 600 .env          # Apenas proprietário pode ler
   chmod 640 .env.local    # Apenas proprietário e seu grupo
   ```

3. **Rotação de Credenciais**
   - Regenre chaves no Google Cloud Console periodicamente
   - Atualize `.env` com as novas credenciais

4. **Monitoramento**
   ```bash
   # Ver últimas linhas do log
   tail -f /var/log/agente-ia.log
   ```

## 📋 Checklist de Deploy

- [ ] Clone do repositório concluído
- [ ] Arquivo `.env` copiado e protegido (`chmod 600`)
- [ ] Dependências instaladas
- [ ] Conexão com Google Drive testada
- [ ] Cron configurado (se necessário)
- [ ] Logs configurados
- [ ] Backup de credenciais em local seguro

## ⚠️ Troubleshooting

**Erro: "Arquivo de credenciais não encontrado"**
```bash
# Verifique se .env existe
test -f .env && echo "✓ .env existe" || echo "✗ .env não encontrado"

# Verifique se as variáveis estão carregadas
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_SERVICE_ACCOUNT_PROJECT_ID'))"
```

**Erro: "Permissão negada ao acessar Google Drive"**
```bash
# Verifique se a Service Account tem acesso à pasta
# Compartilhe a pasta no Google Drive com o email da Service Account:
# google-drive-agente-inss@gdrive-inss-agentes-ia.iam.gserviceaccount.com
```

