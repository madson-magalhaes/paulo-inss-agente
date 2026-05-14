# ✅ Checklist Pré-Deployment

Use este checklist para garantir que tudo está pronto antes de fazer push para GitHub.

## 📋 Verificação Local

### Código e Estrutura
- [ ] Todos os scripts Python funcionando (`*.py`)
- [ ] Pipeline automático testado (`auto_pipeline.py`)
- [ ] Google Drive sync funcionando
- [ ] Supabase conexão OK

### Arquivos de Configuração
- [ ] `.gitignore` contém `.env`
- [ ] `.gitignore` contém `.credentials/`
- [ ] `.env.example` criado (SEM valores sensíveis)
- [ ] `requirements.txt` atualizado com todas as dependências

### Documentação
- [ ] `README.md` criado
- [ ] `DEPLOYMENT_GITHUB.md` completo e detalhado
- [ ] `PUSH_GITHUB.sh` executável

### Credenciais Seguras
- [ ] `.env` está no `.gitignore`
- [ ] `.credentials/` está no `.gitignore`
- [ ] `orcamentos/` está no `.gitignore`
- [ ] `.claude/` está no `.gitignore`

## 🔐 Verificação de Segurança

- [ ] Nenhuma credencial real em arquivos que serão commitados
- [ ] OAuth token está apenas em `.env` (não commitado)
- [ ] Google Cloud credentials não estão nos scripts
- [ ] Supabase keys apenas em `.env`
- [ ] Repositório GitHub será PRIVATE

## 🚀 Pré-Push

- [ ] Rodou `python3 auto_pipeline.py` com sucesso
- [ ] Processou pelo menos 1 orçamento completo
- [ ] Google Drive upload funcionou
- [ ] Supabase inserção funcionou
- [ ] Sem erros nos logs

## 📦 GitHub

- [ ] Conta GitHub criada
- [ ] Repositório criado (PRIVATE)
- [ ] SSH ou Personal Access Token configurado
- [ ] `git` instalado na máquina

## 🖥️ VPS (Preparação)

- [ ] VPS disponível com SSH
- [ ] Python 3.9+ instalado na VPS
- [ ] `pip` instalado na VPS
- [ ] Acesso de leitura/escrita ao diretório

## 📋 Dados Supabase

- [ ] Projeto Supabase criado
- [ ] Tabela `paulo_orcamentos` criada
- [ ] Tabela `paulo_inss` criada
- [ ] URL e chaves copiadas para local `.env`

## 🔑 Google Drive OAuth

- [ ] Projeto Google Cloud criado
- [ ] Google Drive API ativada
- [ ] OAuth 2.0 credenciais criadas
- [ ] Redirect URIs configuradas (localhost:8080)
- [ ] Token OAuth gerado e salvo em `.env`
- [ ] Google Drive folder ID obtido

---

## ✨ Quando Tudo Estiver Pronto:

```bash
# 1. Na máquina local
cd "/Users/madsonmagalhaes/Documents/Paulo Robson INSS/v6_agente_ia"
bash PUSH_GITHUB.sh

# 2. Na VPS
git clone https://github.com/SEU_USUARIO/paulo-inss-agente.git
cd paulo-inss-agente
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env com suas credenciais
python3 auto_pipeline.py
```

---

**Status**: Checklist criado em Maio 2026
