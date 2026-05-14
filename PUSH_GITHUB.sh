#!/bin/bash

# ============================================================================
# SCRIPT: Fazer Push para GitHub
# ============================================================================
# Use este script para fazer o push do projeto para GitHub

echo "============================================================================"
echo "CONFIGURAR E FAZER PUSH PARA GITHUB"
echo "============================================================================"
echo ""

# Pedir informações
read -p "Digite seu username do GitHub: " GITHUB_USER
read -p "Digite seu email (para git config): " EMAIL
read -p "Digite seu nome completo (para git config): " FULLNAME

REPO_NAME="paulo-inss-agente"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo ""
echo "📋 Configuração:"
echo "  • GitHub User: $GITHUB_USER"
echo "  • Repositório: $REPO_URL"
echo "  • Email: $EMAIL"
echo ""

# 1. Inicializar git
echo "1️⃣  Inicializando git..."
git init
git config user.email "$EMAIL"
git config user.name "$FULLNAME"
echo "   ✅ Git inicializado"
echo ""

# 2. Adicionar arquivos
echo "2️⃣  Adicionando arquivos..."
git add .
echo "   ✅ Arquivos adicionados"
echo ""

# 3. Verificar status
echo "3️⃣  Verificando status..."
echo ""
git status
echo ""
read -p "Os arquivos acima estão corretos? (S/n): " CONFIRM
if [ "$CONFIRM" != "n" ]; then
  echo "   ✅ Confirmado!"
else
  echo "   ❌ Abortado. Verifique os arquivos."
  exit 1
fi
echo ""

# 4. Fazer commit
echo "4️⃣  Fazendo commit..."
git commit -m "chore: initial commit - production ready INSS automation system

- Complete OAuth 2.0 Google Drive integration (VPS-ready)
- Supabase database integration
- Automated INSS calculation pipeline
- Multi-platform compatible (Windows, Linux, macOS, VPS)
- Deployment guide and documentation"

echo "   ✅ Commit criado"
echo ""

# 5. Adicionar remote
echo "5️⃣  Adicionando remote origin..."
git branch -M main
git remote add origin "$REPO_URL"
echo "   ✅ Remote adicionado: $REPO_URL"
echo ""

# 6. Fazer push
echo "6️⃣  Fazendo push para GitHub..."
echo "   (pode pedir autenticação - use seu GitHub token ou SSH)"
echo ""
git push -u origin main

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ SUCESSO!"
  echo ""
  echo "Seu repositório está em:"
  echo "  🔗 $REPO_URL"
  echo ""
  echo "Próximas ações:"
  echo "  1. Clonar na VPS: git clone $REPO_URL"
  echo "  2. Configurar .env: cp .env.example .env"
  echo "  3. Instalar dependências: pip install -r requirements.txt"
  echo "  4. Rodar: python3 auto_pipeline.py"
  echo ""
  echo "Veja DEPLOYMENT_GITHUB.md para guia completo."
else
  echo ""
  echo "❌ Erro ao fazer push!"
  echo "   Verifique sua autenticação do GitHub (token ou SSH)"
fi
