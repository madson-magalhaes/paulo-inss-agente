-- ============================================================================
-- RECRIAR TABELA orcamento_seq (deletada por engano)
-- Rodar no SQL Editor do Supabase, TUDO DE UMA VEZ.
-- Esta tabela só guarda o contador diário usado por salvar_orcamento_v2()
-- para montar numero_orcamento (AAMMDD + seq de 2 dígitos). Não tem dados
-- de negócio, então é seguro recriar do zero e reidratar a partir do que
-- já existe em paulo_orcamentos.
-- ============================================================================

CREATE TABLE IF NOT EXISTS orcamento_seq (
  dia DATE PRIMARY KEY,
  seq INT NOT NULL DEFAULT 0
);

-- Reidratar a sequência de HOJE com a maior seq já usada em numero_orcamento
-- (evita colisão/duplicação de número no próximo orçamento salvo hoje)
INSERT INTO orcamento_seq (dia, seq)
SELECT (now() AT TIME ZONE 'America/Fortaleza')::date,
       coalesce(max(right(numero_orcamento, 2)::int), 0)
FROM paulo_orcamentos
WHERE left(numero_orcamento, 6) = to_char((now() AT TIME ZONE 'America/Fortaleza')::date, 'YYMMDD')
ON CONFLICT (dia) DO UPDATE SET seq = greatest(orcamento_seq.seq, excluded.seq);

-- Opcional: reidratar também dias anteriores, se quiser manter o histórico
-- de contadores consistente (não é necessário para o funcionamento —
-- a função só usa o dia atual — mas evita confusão em auditorias futuras).
INSERT INTO orcamento_seq (dia, seq)
SELECT to_date(left(numero_orcamento, 6), 'YYMMDD') AS dia,
       max(right(numero_orcamento, 2)::int) AS seq
FROM paulo_orcamentos
GROUP BY left(numero_orcamento, 6)
ON CONFLICT (dia) DO UPDATE SET seq = greatest(orcamento_seq.seq, excluded.seq);

-- Conferir o resultado:
-- SELECT * FROM orcamento_seq ORDER BY dia DESC;
