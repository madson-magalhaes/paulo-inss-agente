# Multi-tenant: schema por cliente

Setup de teste para o padrão de um schema Postgres dedicado por cliente, em vez de tudo dentro de `public` com tabelas prefixadas (`paulo_*`), que é como a produção real funciona hoje.

**Nada aqui afeta produção.** Os workflows deste diretório são cópias; os arquivos originais na raiz do projeto continuam servindo produção normalmente, apontando para `public`.

## Estrutura

- `criar_schema_cliente.sql` — script único de onboarding por cliente. Cria o schema, as tabelas de negócio, a função `salvar_orcamento`, os GRANTs, e a tabela de histórico de chat (ver exceção abaixo).
- `grant_permissoes_schema.sql` — script de GRANT isolado, mantido por retrocompatibilidade (já incorporado em `criar_schema_cliente.sql`).
- `SDR - Paulo Robson v3.3 Z-API. -- testes.json` — cópia do workflow principal, apontando para o schema `paulo_robson`.
- `SDR - Reaquecimento Leads. v.1 -- testes.json` — cópia do workflow de reaquecimento, mesmo schema.
- `SDR - Reaquecimento Leads. TESTE TEMPOS CURTOS.json` — variante só para teste rápido: intervalos de tempo em minutos em vez de horas/dias. **Não usar em produção.**

## Como criar um cliente novo

1. Abra `criar_schema_cliente.sql` e troque `v_schema := 'paulo_robson'` pelo nome do novo schema (única linha a editar).
2. Rode o arquivo inteiro, de uma vez, no SQL Editor do Supabase.
3. No painel do Supabase, vá em **Settings → API → Exposed schemas** (não confundir com o campo "Extra search path", que é outra coisa e não resolve o acesso via API REST) e adicione o schema novo à lista.
4. Configure os workflows n8n do cliente: campo `schema` de cada node Postgres → nome do novo schema; tabelas sem prefixo (`orcamentos`, `inss`, `conversas_leads`, `reengajamento_textos`, `orcamento_seq`).
5. Nos 2 nodes de memória (`Postgres Chat Memory...`) e em qualquer `SELECT`/`INSERT` que toque `chat_histories`, aponte para `public.<schema>_chat_histories` — ver exceção abaixo.
6. No Python, defina `SUPABASE_SCHEMA=<nome_do_schema>` no `.env` do cliente (usa o mesmo `supabase_client.py` da raiz do projeto).

## Exceção: `chat_histories` fica em `public`

Todas as tabelas de negócio vivem dentro do schema do cliente. **A única exceção é `chat_histories`**, que fica em `public`, com nome prefixado pelo cliente (ex: `public.paulo_robson_chat_histories`).

Motivo: o node `@n8n/n8n-nodes-langchain.memoryPostgresChat` (memória conversacional do AI Agent) não tem parâmetro de schema — só "Table Name" (string livre). Não existe workaround via parâmetro do node nem via credencial Postgres padrão do n8n (não expõe `search_path`). O isolamento entre clientes, para essa tabela específica, vem do **nome** da tabela, não do schema Postgres.

Isso significa: **todo node que referencia `chat_histories`, incluindo queries SQL cruas (`SELECT`/`INSERT` manuais), precisa apontar explicitamente para `public.<schema>_chat_histories`** — não para `<schema>.chat_histories`. Esquecer esse detalhe num único node quebra o fluxo silenciosamente (o n8n para a execução com "No output data returned" quando uma query não encontra a tabela/retorna vazio), sem erro óbvio — foi a causa raiz de um bug real nesta implementação (`Get_Historico_Lead` do reaquecimento).

## Padrão de timestamp

Todo `created_at`/comparação de tempo no Postgres usa `now()` puro (sem `AT TIME ZONE`). `TIMESTAMPTZ` já armazena o instante absoluto corretamente, independente de qual timezone é usado para exibir ou gravar o valor — não precisa (e não deve) converter timezone antes de comparar duas colunas `TIMESTAMPTZ`. A única exceção é `v_dia` dentro da função `salvar_orcamento`, que usa `America/Sao_Paulo` explicitamente porque precisa do **dia calendário local** (não um instante), para compor o `numero_orcamento`.

## Checklist ao adicionar cliente novo (evitar bugs já vistos)

- [ ] Rodar `criar_schema_cliente.sql` completo (schema + tabelas + função + GRANTs).
- [ ] Expor o schema em Settings → API → Exposed schemas (não é feito pelo SQL).
- [ ] Criar/conferir `public.<schema>_chat_histories` e apontar TODOS os nodes de memória/histórico para lá, com o nome certo — inclusive queries SQL cruas fora dos nodes Postgres estruturados.
- [ ] Conferir que nenhum node ficou apontando para `<schema>.chat_histories` (schema errado) por engano.
- [ ] `SUPABASE_SCHEMA` no `.env` do cliente, se for usar os scripts Python.

## Status (25/07/2026)

Testado ponta a ponta com sucesso, tudo local: mensagem via WhatsApp → agente → `paulo_robson.conversas_leads`/`public.paulo_robson_chat_histories` → `paulo_robson.orcamentos` (via função `salvar_orcamento`) → `auto_pipeline.py` (rodando localmente, `SUPABASE_SCHEMA=paulo_robson` no `.env`) → cálculo de INSS → `paulo_robson.inss` → sincronização com Google Drive. Nenhum commit feito ainda — tudo em working tree local.

## Roadmap: próxima sessão (deploy em VPS)

Plano confirmado: (1) commit + push desta migração para o GitHub, (2) clonar o repo numa VPS, (3) configurar o **Database Webhook do Supabase** (que dispara o Agente de Fechamento) apontando para **`paulo_robson.inss`**, não `public.paulo_inss` — o teste na VPS já é o cenário multi-tenant. Detalhes técnicos (URL do webhook, credenciais do n8n na instância nova, etc.) na memória de projeto `roadmap-deploy-vps-webhook-supabase` (fora deste repo, no sistema de memória do Claude Code).
