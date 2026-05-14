# v6_agente_ia - Quick Start Guide

## 🚀 Local Setup (60 seconds)

```bash
# 1. Install dependencies
pip install supabase pandas python-dotenv google-auth-oauthlib google-auth-httplib2 google-api-python-client

# 2. Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials and Google Drive folder ID

# 3. OAuth setup (first time only)
python3 google_drive_sync.py <numero_orcamento>
# Follow browser prompts to authorize - token is saved automatically

# 4. Run pipeline
python3 auto_pipeline.py
```

## 📋 What Happens

The pipeline runs **every 60 seconds** automatically:

1. **COLETA** (Collection) - Fetches data from Supabase
   - Creates `orcamentos/orcamento_XXXXX_ClientName/` folders
   - Exports `obra-XXXXX.csv` directly into each folder
   - No intermediate `dados_supabase/` folder

2. **VALIDAÇÃO** (Validation) - Two-cycle validation
   - First run: Registers the orçamento
   - Waits 60 seconds
   - Second run: Validates completeness before processing

3. **MARCAÇÃO** (Marking) - Updates Supabase status
   - Changes status from 'aberto' to 'processando'

4. **AGUARDO** (Cycle Wait) - Enforces validation requirement
   - Prevents processing until both cycles pass

5. **PROCESSAMENTO** (Processing) - INSS calculation
   - Generates `inss-*.csv` and `inss-*-otimizado.csv`
   - Files saved in `orcamentos/orcamento_XXXXX_ClientName/` (permanent)

6. **FINALIZAÇÃO** (Finalization) - Status update + Google Drive sync
   - Marks status 'processando' → 'processado' in Supabase
   - Uploads/syncs folder to Google Drive (no duplicates)
   - Detects existing folders and updates files atomically

## 🖥️ VPS Deployment

### From Local:
```bash
# Copy OAuth token to VPS (pre-authenticated, no re-auth needed)
scp .credentials/google_token.json user@vps:/path/to/v6_agente_ia/.credentials/

# Copy .env with Supabase credentials
scp .env user@vps:/path/to/v6_agente_ia/
```

### On VPS:
```bash
cd /path/to/v6_agente_ia

# Install dependencies
pip install supabase pandas python-dotenv google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Run
python3 auto_pipeline.py

# It will run continuously, updating Supabase and Google Drive every 60 seconds
```

## 📊 Monitor Execution

```bash
# Watch pipeline output
tail -f /path/to/auto_pipeline.log

# Check Supabase status
python3 -c "from coletar import coletar_orcamentos; coletar_orcamentos()"

# Check folder structure
ls -la orcamentos/
ls -la dados_supabase/
```

## 🔐 Security Notes

- **Never commit**: `.env` (contains secrets)
- **Never commit**: `.credentials/oauth_credentials.json` (Client ID/Secret)
- **Never commit**: `.credentials/google_token.json` (Auth token)
- **Safe to copy**: `.credentials/google_token.json` to VPS (reusable token)
- **Gitignore**: Already configured to protect secrets

## 📁 Key Files

- `auto_pipeline.py` - Main automation (runs every 60s)
- `coletar.py` - Supabase data collection
- `google_drive_sync.py` - Google Drive OAuth sync
- `calculators.py` - INSS calculation logic
- `icm.csv` - ICM reference rates (May/26)
- `vau.csv` - VAU reference values (May/26)

## 🆘 Troubleshooting

**Pipeline not collecting data?**
- Check `.env` has valid `SUPABASE_URL` and `SUPABASE_KEY`
- Verify Supabase table `paulo_orcamentos` has status_orcamento='aberto' records

**Google Drive sync failing?**
- Check `.env` has valid `GOOGLE_DRIVE_FOLDER_ID`
- Run `python3 google_drive_sync.py <numero_orcamento>` to re-authenticate
- Token is saved to `.credentials/google_token.json`

**Folders not being created?**
- Ensure write permissions on `./orcamentos/` directory
- Check disk space is available

## 📖 Full Documentation

- `README.md` - Overview and features
- `INSTALLATION.md` - Detailed setup instructions
- `SETUP_OAUTH.md` - OAuth configuration walkthrough
- `DEPLOYMENT_CHECKLIST.md` - Pre-deployment validation
- `FINAL_VALIDATION.md` - Test results and verification

---

**Status**: ✅ Ready for production  
**Last Updated**: 2026-05-14  
**Compatible**: Windows, Linux, macOS
