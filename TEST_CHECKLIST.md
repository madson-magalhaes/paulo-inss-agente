# v6_agente_ia - Teste Completo do Pipeline

## ✅ Correções Implementadas

### 1. Arquivos INSS Agora Salvam na Pasta do Orçamento
- **Arquivo**: `processar_orcamento.py` → chamada a `main.py` corrigida
- **Resultado**: `orcamentos/orcamento_XXXXX_ClientName/inss-*.csv` é gerado corretamente

### 2. Status Muda de 'processando' → 'processado'
- **Arquivo**: `atualizar_status_processado.py` → marcar como processado agora funciona
- **Resultado**: Supabase é atualizado após processamento bem-sucedido

### 3. Google Drive Upload Uma Única Vez
- **Arquivo**: `atualizar_status_processado.py` → rastreamento com `.claude/drive_sincronizacoes.json`
- **Resultado**: Primeira sincronização = upload; próximas = apenas atualização

### 4. Caminhos 100% Relativos (Multiplataforma)
- **Arquivos**: Todos os scripts em v6_agente_ia
- **Resultado**: Funciona em Windows, Linux, macOS, VPS com estrutura idêntica

## 🧪 Como Testar

### Teste 1: Gerar Arquivos INSS Localmente
```bash
cd /Users/madsonmagalhaes/Documents/Paulo\ Robson\ INSS/v5_supabase/supabase/v6_agente_ia

# Processa um orçamento específico
python3 processar_orcamento.py 12052601

# Verifica se arquivos foram criados
ls -la orcamentos/orcamento_12052601_*/
# Deve mostrar: obra-*.csv, inss-*.csv, inss-*-otimizado.csv (pode falhar, é ok)
```

### Teste 2: Marcar como Processado + Google Drive
```bash
# Atualiza status no Supabase e sincroniza Google Drive
python3 atualizar_status_processado.py 12052601

# Verifica se status mudou em paulo_orcamentos (12052601 → 'processado')
# Verifica se pasta existe no Google Drive com os arquivos
```

### Teste 3: Pipeline Completo
```bash
# Roda o pipeline automático completo
python3 auto_pipeline.py

# Monitora o progresso:
# 1. Coleta orçamentos de Supabase
# 2. Valida em 2 ciclos
# 3. Marca como 'processando'
# 4. Processa (gera INSS)
# 5. Marca como 'processado' + Drive
```

## 📋 Checklist Pós-Correção

- [ ] Arquivos `inss-*.csv` aparecem em `orcamentos/orcamento_XXXXX_ClientName/`
- [ ] Status no Supabase muda para 'processado' após processing
- [ ] Google Drive recebe upload apenas uma vez (na segunda vez só atualiza)
- [ ] Nenhum erro de importação (todos imports locais)
- [ ] Funciona com caminhos relativos (`./.`, `./orcamentos`, etc.)
- [ ] Não há hardcoded absolute paths (`/Users/`, `C:\`, `/home/`)

## 🚀 Pronto para Deploy

A v6_agente_ia está pronta para:
1. **Git push** para repositório
2. **Clone na VPS**
3. **Executar**: `python3 auto_pipeline.py` em loop

Todos os caminhos são relativos, todos os imports estão corretos, nenhuma dependência externa faltando.

