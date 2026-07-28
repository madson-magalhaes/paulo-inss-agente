-- ============================================================================
-- GRANT DE PERMISSÕES — schema por cliente (multi-tenant)
-- Rodar no SQL Editor do Supabase, DEPOIS de criar_schema_cliente.sql e
-- DEPOIS de adicionar o schema em Settings > API > Extra search path
-- (ou Exposed schemas, dependendo da versão da UI).
--
-- Por que precisa: diferente do schema "public", um schema novo no Postgres
-- NÃO recebe GRANT automático para as roles que a API REST do Supabase usa
-- (anon, authenticated, service_role). Sem este passo, toda chamada via API
-- (supabase-py, PostgREST) retorna "permission denied for schema" (42501),
-- mesmo com o schema corretamente exposto/no search path.
--
-- Este script só concede permissões — não cria, altera nem apaga dados.
-- ============================================================================

DO $MAIN$
DECLARE
  v_schema TEXT := 'paulo_robson';  -- mesmo nome usado em criar_schema_cliente.sql
BEGIN

  -- Permissão de "entrar" no schema (obrigatória antes de qualquer outra)
  EXECUTE format('GRANT USAGE ON SCHEMA %I TO anon, authenticated, service_role', v_schema);

  -- Permissões nas tabelas já existentes no schema
  EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO anon, authenticated, service_role', v_schema);

  -- Permissões em sequences (necessário para colunas GENERATED/IDENTITY funcionarem via API)
  EXECUTE format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO anon, authenticated, service_role', v_schema);

  -- Permissão de executar a função salvar_orcamento (RPC via API, se vier a ser chamada assim)
  EXECUTE format('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA %I TO anon, authenticated, service_role', v_schema);

  -- Garante que TABELAS/SEQUENCES/FUNÇÕES criadas no futuro NESTE schema também
  -- recebam as mesmas permissões automaticamente (sem precisar rodar este script de novo)
  EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon, authenticated, service_role', v_schema);
  EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT USAGE, SELECT ON SEQUENCES TO anon, authenticated, service_role', v_schema);
  EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT EXECUTE ON FUNCTIONS TO anon, authenticated, service_role', v_schema);

  RAISE NOTICE 'Permissões concedidas no schema % para anon, authenticated, service_role.', v_schema;

END;
$MAIN$ LANGUAGE plpgsql;
