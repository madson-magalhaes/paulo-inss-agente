-- ============================================================================
-- Migração: textos de reaquecimento (follow-up) editáveis por etapa e marco
-- Tabela consultada pelo workflow "Reaquecimento de Leads" (Schedule Trigger).
-- Para alterar o texto enviado num marco/etapa, edite a coluna 'texto' direto
-- pelo Supabase (Table Editor ou SQL) — não precisa mexer no workflow n8n.
--
-- etapa: identifica onde o lead parou na conversa (classificado por um LLM
-- auxiliar lendo paulo_chat_histories no momento do reaquecimento). Valores:
--   'titularidade'      -> Etapa 1 (nem informou se é PF/PJ)
--   'localizacao'       -> Etapa 2 (falta estado)
--   'categoria'         -> Etapa 3 (falta categoria da obra)
--   'destinacao'        -> Etapa 4 (falta destinação)
--   'tipo_construtivo'  -> Etapa 5 (falta tipo construtivo)
--   'area'              -> Etapa 6 (falta área construída/complementares)
--   'datas'             -> Etapas 7/8 (falta início/término da obra)
--   'paralisacao'       -> Etapa 9 (falta info de paralisação)
--   'confirmacao'       -> Etapa 10 (resumo apresentado, aguardando confirmação)
--   'nome'              -> aguardando nome completo
--   'orcamento_gerado'  -> já passou pela Transição Final (numero_orcamento existe)
--
-- marco: '1h' | '4h' | '1d' | '3d' | '7d' | '15d'
-- ============================================================================

CREATE TABLE IF NOT EXISTS paulo_reengajamento_textos (
  etapa  text NOT NULL,
  marco  text NOT NULL,
  texto  text NOT NULL,
  PRIMARY KEY (etapa, marco)
);

-- Textos padrão (edite livremente depois pelo Supabase).
INSERT INTO paulo_reengajamento_textos (etapa, marco, texto) VALUES
  ('titularidade',     '1h',  'Oi! Vi que paramos por aqui 🙂 Sua obra é em nome de pessoa física ou empresa?'),
  ('titularidade',     '4h',  'Continuando por aqui: sua obra está no CPF ou no CNPJ?'),
  ('titularidade',     '1d',  'Olá! Ainda podemos continuar sua simulação de regularização da obra. É pessoa física ou jurídica?'),
  ('titularidade',     '3d',  'Passando para retomar sua simulação — é rapidinho! A obra é pessoa física ou jurídica?'),
  ('titularidade',     '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('titularidade',     '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('localizacao',      '1h',  'Oi! Faltou só o estado (UF) da sua obra para continuarmos 🙂'),
  ('localizacao',      '4h',  'Em qual estado fica a obra? Assim consigo continuar sua simulação.'),
  ('localizacao',      '1d',  'Olá! Podemos retomar? Só preciso saber o estado onde é a obra.'),
  ('localizacao',      '3d',  'Passando para retomar: qual o estado (UF) da obra?'),
  ('localizacao',      '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('localizacao',      '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('categoria',        '1h',  'Oi! Faltou saber se a obra é construção nova, reforma, ampliação ou demolição.'),
  ('categoria',        '4h',  'Sua obra é construção nova, reforma, ampliação ou demolição?'),
  ('categoria',        '1d',  'Olá! Para continuarmos: sua obra é construção nova, reforma, ampliação ou demolição?'),
  ('categoria',        '3d',  'Retomando por aqui: sua obra é construção nova, reforma, ampliação ou demolição?'),
  ('categoria',        '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('categoria',        '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('destinacao',       '1h',  'Oi! Faltou saber a destinação da obra: residencial (uma ou mais casas), comercial ou galpão?'),
  ('destinacao',       '4h',  'Sua obra é residencial, comercial ou um galpão?'),
  ('destinacao',       '1d',  'Olá! Para continuar: a obra é residencial, comercial ou galpão?'),
  ('destinacao',       '3d',  'Retomando: sua obra tem destinação residencial, comercial ou é um galpão?'),
  ('destinacao',       '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('destinacao',       '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('tipo_construtivo', '1h',  'Oi! Faltou saber o tipo construtivo: alvenaria, madeira, mista ou concreto?'),
  ('tipo_construtivo', '4h',  'Sua obra é em alvenaria, madeira, mista ou concreto?'),
  ('tipo_construtivo', '1d',  'Olá! Para continuar: qual o tipo construtivo da obra (alvenaria, madeira, mista ou concreto)?'),
  ('tipo_construtivo', '3d',  'Retomando: alvenaria, madeira, mista ou concreto — qual o tipo construtivo?'),
  ('tipo_construtivo', '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('tipo_construtivo', '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('area',             '1h',  'Oi! Faltou só a área construída (em m²) para eu continuar sua simulação.'),
  ('area',             '4h',  'Qual a área construída da obra, em m²?'),
  ('area',             '1d',  'Olá! Para continuar, preciso da área construída (m²) da obra.'),
  ('area',             '3d',  'Retomando por aqui: qual a metragem (m²) da área construída?'),
  ('area',             '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('area',             '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('datas',            '1h',  'Oi! Faltou saber quando a obra começou e terminou (ou previsão de término).'),
  ('datas',            '4h',  'Quando a obra começou, e qual o término (ou previsão)?'),
  ('datas',            '1d',  'Olá! Para continuar: qual foi o início da obra e o término (ou previsão)?'),
  ('datas',            '3d',  'Retomando: preciso saber a data de início e término (ou previsão) da obra.'),
  ('datas',            '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('datas',            '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('paralisacao',      '1h',  'Oi! Só falta saber: a obra teve algum período parado?'),
  ('paralisacao',      '4h',  'A obra chegou a ficar paralisada em algum período?'),
  ('paralisacao',      '1d',  'Olá! Para fechar sua simulação: a obra teve paralisação em algum momento?'),
  ('paralisacao',      '3d',  'Retomando: houve paralisação da obra em algum período?'),
  ('paralisacao',      '7d',  'Ainda dá tempo de continuar sua simulação gratuita. Deseja continuar?'),
  ('paralisacao',      '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('confirmacao',      '1h',  'Oi! Só falta você confirmar o resumo que te enviei para eu finalizar sua simulação 🙂'),
  ('confirmacao',      '4h',  'Podemos confirmar os dados da sua obra para eu concluir a simulação?'),
  ('confirmacao',      '1d',  'Olá! Sua simulação está quase pronta, só falta a confirmação dos dados. Pode confirmar?'),
  ('confirmacao',      '3d',  'Retomando: falta só confirmar os dados para eu concluir sua simulação.'),
  ('confirmacao',      '7d',  'Ainda dá tempo de concluir sua simulação gratuita. Deseja continuar?'),
  ('confirmacao',      '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('nome',             '1h',  'Oi! Só falta seu nome completo para eu concluir sua simulação.'),
  ('nome',             '4h',  'Pode me confirmar seu nome completo para finalizar?'),
  ('nome',             '1d',  'Olá! Só falta seu nome completo para fechar sua simulação.'),
  ('nome',             '3d',  'Retomando: qual seu nome completo, para eu concluir?'),
  ('nome',             '7d',  'Ainda dá tempo de concluir sua simulação gratuita. Deseja continuar?'),
  ('nome',             '15d', 'Última tentativa de contato: se ainda tiver interesse na simulação, é só responder aqui.'),

  ('orcamento_gerado', '1h',  'Oi! Sua simulação já foi encaminhada ao nosso time técnico. Ficou com alguma dúvida?'),
  ('orcamento_gerado', '4h',  'Passando para saber se ficou alguma dúvida sobre sua simulação já encaminhada ao time técnico.'),
  ('orcamento_gerado', '1d',  'Olá! Nosso time técnico já recebeu sua simulação. Posso ajudar em algo enquanto isso?'),
  ('orcamento_gerado', '3d',  'Retomando contato: ficou alguma dúvida sobre sua simulação, já encaminhada ao time técnico?'),
  ('orcamento_gerado', '7d',  'Ainda estamos à disposição para qualquer dúvida sobre sua simulação.'),
  ('orcamento_gerado', '15d', 'Última tentativa de contato: se precisar de algo sobre sua simulação, é só responder aqui.')
ON CONFLICT (etapa, marco) DO NOTHING;
