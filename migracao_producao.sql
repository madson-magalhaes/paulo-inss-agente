-- ============================================================================
-- MIGRAÇÃO PARA PRODUÇÃO — SDR Paulo Robson v2
-- Rodar no SQL Editor do Supabase, TUDO DE UMA VEZ, com o workflow v1 DESATIVADO.
-- O workflow n8n v2 NÃO precisa de nenhuma alteração: os nodes chamam a função
-- salvar_orcamento_v2(), e o nome da tabela só existe dentro da função (passo 3).
-- ============================================================================

-- 1. Limpar eventuais linhas de teste que sobraram na _v2
--    (confira antes com: SELECT * FROM paulo_orcamentos_v2;)
DELETE FROM paulo_orcamentos_v2 WHERE nome LIKE 'TESTE_%';

-- 2. Troca de nomes: produção antiga vira arquivo, _v2 assume o nome oficial
--    (o pipeline Python lê 'paulo_orcamentos' — passa a ler a tabela nova)
ALTER TABLE paulo_orcamentos    RENAME TO paulo_orcamentos_old;
ALTER TABLE paulo_orcamentos_v2 RENAME TO paulo_orcamentos;

-- 3. Reapontar a função para o nome novo (mantém o nome salvar_orcamento_v2,
--    então o workflow n8n fica intacto)
--
-- Convivência com o ciclo do pipeline Python (aberto → processando → processado):
--   • coletar.py coleta linhas 'aberto' + 'processando' juntas
--   • validar_aguardando_ciclo.py reinicia o aguardo se surge linha 'aberto'
--     nova num orçamento 'processando' → tudo é processado junto, UMA vez
--   • linha 'processado' fica FORA da próxima coleta → nunca pode voltar
--     ao ciclo nem receber "append" (o cálculo sairia sem a área principal)
--
-- Comportamento da dedup (mesmo telefone + nome, janela de 10 min):
--   • linhas todas 'aberto'   → regrava tudo do payload, MESMO número
--   • tem linha 'processando' → mantém as que processam, insere SÓ as áreas
--                               novas ('aberto') no MESMO número; se o payload
--                               CONTRADIZ uma linha processando (correção de
--                               valor) → orçamento NOVO completo
--   • tem linha 'processado'  → orçamento NOVO completo (número novo)
CREATE OR REPLACE FUNCTION salvar_orcamento_v2(p JSONB)
RETURNS TEXT AS $$
DECLARE
  v_num   TEXT;
  v_seq   INT;
  v_dia   DATE := (now() AT TIME ZONE 'America/Fortaleza')::date;  -- data local, não UTC
  v_area  JSONB;
  v_par   JSONB;
  v_meses TEXT := NULL;
  v_chunk TEXT;
  v_ini   DATE;
  v_fim   DATE;
BEGIN
  -- 0. VALIDAÇÃO: toda linha não-principal precisa de coberta sim/nao
  --    (o cálculo usa: coberta=50%, descoberta=25% — vale até para demolição).
  --    Falhar AQUI permite ao agente perguntar ao lead e rechamar; se passasse,
  --    o pipeline Python travaria em loop de erro no 'processando'.
  IF EXISTS (
    SELECT 1 FROM jsonb_array_elements(p->'areas') a
    WHERE a->>'is_principal' = 'nao'
      AND coalesce(a->>'coberta', '') NOT IN ('sim', 'nao')
  ) THEN
    RAISE EXCEPTION 'DADOS INCOMPLETOS: toda area com is_principal=nao (piscina, garagem, demolicao etc) exige coberta=sim ou nao. Pergunte ao lead se a area/estrutura e coberta e chame a tool novamente com o payload completo corrigido.';
  END IF;

  -- 1. Expansão de meses paralisados (antes da dedup, que compara meses):
  --      {"inicio","fim"}      → fim = ÚLTIMO mês parado (INCLUSIVO)
  --      {"inicio","retomada"} → retomada = mês em que voltou (EXCLUSIVO)
  FOR v_par IN
    SELECT * FROM jsonb_array_elements(coalesce(p->'paralisacoes', '[]'::jsonb))
  LOOP
    v_ini := to_date(v_par->>'inicio', 'MM/YYYY');

    IF v_par ? 'retomada' AND coalesce(v_par->>'retomada', '') <> '' THEN
      v_fim := to_date(v_par->>'retomada', 'MM/YYYY') - interval '1 month';
    ELSIF coalesce(v_par->>'fim', '') <> '' THEN
      v_fim := to_date(v_par->>'fim', 'MM/YYYY');
    ELSE
      CONTINUE;  -- intervalo sem fim/retomada: ignora
    END IF;

    SELECT string_agg(to_char(d, 'MM/YYYY'), ',' ORDER BY d)
      INTO v_chunk
    FROM generate_series(v_ini, v_fim, interval '1 month') d;

    IF v_chunk IS NOT NULL THEN
      v_meses := CASE WHEN v_meses IS NULL THEN v_chunk
                      ELSE v_meses || ',' || v_chunk END;
    END IF;
  END LOOP;

  -- 2. DEDUP: mesma conversa? (mesmo telefone + MESMO NOME, últimos 10 min)
  --    Nome diferente = engenheiro simulando outro cliente → número novo
  SELECT numero_orcamento INTO v_num
  FROM paulo_orcamentos
  WHERE telefone = p->>'telefone'
    AND lower(trim(nome)) = lower(trim(p->>'nome'))
    AND created_at > now() - interval '10 minutes'
  ORDER BY created_at DESC
  LIMIT 1;

  IF v_num IS NOT NULL THEN
    -- 2a. Linha já finalizada ('processado' ou além)? Não pode voltar ao ciclo
    --     nem receber append → orçamento NOVO com o payload completo
    IF EXISTS (
      SELECT 1 FROM paulo_orcamentos
      WHERE numero_orcamento = v_num
        AND status_orcamento NOT IN ('aberto', 'processando')
    ) THEN
      v_num := NULL;

    -- 2b. Linha 'processando' que o payload NÃO contém identicamente (correção
    --     de valor ou dados gerais mudaram)? Não dá pra corrigir linha no ciclo
    --     → orçamento NOVO completo. (Acréscimo puro passa: payload ⊇ linhas.)
    ELSIF EXISTS (
      SELECT 1 FROM paulo_orcamentos t
      WHERE t.numero_orcamento = v_num
        AND t.status_orcamento = 'processando'
        AND NOT (
          t.estado = p->>'estado'
          AND t.data_inicio = p->>'data_inicio'
          AND t.data_fim = p->>'data_fim'
          AND t.concreto_usinado = coalesce(p->>'concreto_usinado', 'nao')
          AND t.paralisacao = coalesce(p->>'paralisacao', 'nao')
          AND t.meses_paralisados = coalesce(v_meses, '')
          AND EXISTS (
            SELECT 1 FROM jsonb_array_elements(p->'areas') a
            WHERE a->>'tipo' = t.tipo
              AND a->>'categoria' = t.categoria
              AND a->>'material' = t.material
              AND (a->>'area_m2')::numeric = t.area_m2::numeric
              AND a->>'is_principal' = t.is_principal
              AND coalesce(a->>'coberta', '') = coalesce(t.coberta, '')
              AND coalesce(a->>'prefabricado', 'nao') = coalesce(t.prefabricado, 'nao')
          )
        )
    ) THEN
      v_num := NULL;
    END IF;
  END IF;

  IF v_num IS NOT NULL THEN
    -- Mesma conversa, nada finalizado: linhas ainda 'aberto' são regravadas
    -- pelo payload (fonte da verdade); linhas 'processando' ficam INTACTAS
    DELETE FROM paulo_orcamentos
    WHERE numero_orcamento = v_num
      AND status_orcamento = 'aberto';
  ELSE
    -- 3. Conversa/orçamento novo: número atômico AAMMDD + seq de 2 dígitos
    INSERT INTO orcamento_seq (dia, seq)
    VALUES (v_dia, 1)
    ON CONFLICT (dia) DO UPDATE SET seq = orcamento_seq.seq + 1
    RETURNING seq INTO v_seq;

    v_num := to_char(v_dia, 'YYMMDD') || lpad(v_seq::text, 2, '0');
  END IF;

  -- 4. Inserir uma linha por área — todas com o mesmo número.
  --    tipo/categoria/material/prefabricado são POR LINHA (reforma + demolição).
  --    Área que já existe como linha 'processando' deste número é PULADA
  --    (segue no ciclo; nunca duplica).
  FOR v_area IN SELECT * FROM jsonb_array_elements(p->'areas')
  LOOP
    IF EXISTS (
      SELECT 1 FROM paulo_orcamentos t
      WHERE t.numero_orcamento = v_num
        AND t.status_orcamento = 'processando'
        AND t.tipo = v_area->>'tipo'
        AND t.categoria = v_area->>'categoria'
        AND t.material = v_area->>'material'
        AND t.area_m2::numeric = (v_area->>'area_m2')::numeric
        AND t.is_principal = v_area->>'is_principal'
        AND coalesce(t.coberta, '') = coalesce(v_area->>'coberta', '')
        AND coalesce(t.prefabricado, 'nao') = coalesce(v_area->>'prefabricado', 'nao')
    ) THEN
      CONTINUE;
    END IF;

    INSERT INTO paulo_orcamentos
      (numero_orcamento, nome, telefone, estado, tipo, categoria, material,
       area_m2, is_principal, coberta, data_inicio, data_fim,
       concreto_usinado, paralisacao, prefabricado, meses_paralisados)
    VALUES
      (v_num,
       p->>'nome',
       p->>'telefone',
       p->>'estado',
       v_area->>'tipo',
       v_area->>'categoria',
       v_area->>'material',
       v_area->>'area_m2',
       v_area->>'is_principal',
       coalesce(v_area->>'coberta', ''),
       p->>'data_inicio',
       p->>'data_fim',
       coalesce(p->>'concreto_usinado', 'nao'),
       coalesce(p->>'paralisacao', 'nao'),
       coalesce(v_area->>'prefabricado', 'nao'),
       coalesce(v_meses, ''));
  END LOOP;

  RETURN v_num;
END;
$$ LANGUAGE plpgsql;

-- 4. Migrar o histórico da tabela antiga (opcional mas recomendado — o pipeline
--    Python só processa status 'aberto', então não haverá reprocessamento)
INSERT INTO paulo_orcamentos
  (created_at, nome, telefone, numero_orcamento, estado, tipo, categoria,
   material, area_m2, is_principal, coberta, data_inicio, data_fim,
   concreto_usinado, paralisacao, prefabricado, status_orcamento, meses_paralisados)
SELECT
   created_at, nome, telefone, numero_orcamento, estado, tipo, categoria,
   material, area_m2, is_principal, coberta, data_inicio, data_fim,
   concreto_usinado, paralisacao, prefabricado, status_orcamento, meses_paralisados
FROM paulo_orcamentos_old;

-- 5. Inicializar a sequência do dia com a maior sequência já usada hoje
--    (evita colisão com números gerados pela produção antiga no mesmo dia)
INSERT INTO orcamento_seq (dia, seq)
SELECT (now() AT TIME ZONE 'America/Fortaleza')::date,
       coalesce(max(right(numero_orcamento, 2)::int), 0)
FROM paulo_orcamentos
WHERE left(numero_orcamento, 6) = to_char((now() AT TIME ZONE 'America/Fortaleza')::date, 'YYMMDD')
ON CONFLICT (dia) DO UPDATE SET seq = greatest(orcamento_seq.seq, excluded.seq);

-- ============================================================================
-- Depois de rodar: ativar o workflow 'SDR - Paulo Robson v2' no n8n
-- (e manter o v1 desativado — mesmos webhook paths).
-- A tabela paulo_orcamentos_old fica como backup; apagar só quando tiver certeza.
-- ============================================================================
