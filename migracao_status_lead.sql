-- ============================================================================
-- Migração: bloqueio de agente por operador (frase-gatilho)
-- Adiciona coluna 'status' em paulo_conversas_leads para controlar se o AI
-- Agent deve ou não responder ao lead, controlado pelo operador via WhatsApp:
--   - "transferindo para o especialista" -> status = 'bloqueado'
--   - "retomando conversa"               -> status = 'ativo'
-- Enquanto bloqueado, o workflow continua salvando as mensagens do lead
-- (buffer em paulo_conversas_leads e histórico em paulo_chat_histories),
-- só a chamada ao AI Agent é suprimida.
-- ============================================================================

ALTER TABLE paulo_conversas_leads
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'ativo';

-- Garantir que linhas existentes fiquem com o agente ativo por padrão
UPDATE paulo_conversas_leads SET status = 'ativo' WHERE status IS NULL;

-- ============================================================================
-- Migração: reaquecimento de leads inativos (1h/4h/1d/3d/7d/15d)
-- last_message_at: timestamp da última mensagem do LEAD (gravado por Save_Conv1
-- a cada mensagem recebida). Fonte de verdade separada de 'timeout' (debounce).
-- enviado_1h..enviado_15d: flags do que já foi disparado para o marco atual;
-- Save_Conv1 zera todas elas (junto com last_message_at) a cada nova mensagem
-- do lead, reiniciando o ciclo de reaquecimento do zero.
-- ============================================================================

ALTER TABLE paulo_conversas_leads
  ADD COLUMN IF NOT EXISTS last_message_at timestamptz,
  ADD COLUMN IF NOT EXISTS enviado_1h  boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS enviado_4h  boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS enviado_1d  boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS enviado_3d  boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS enviado_7d  boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS enviado_15d boolean NOT NULL DEFAULT false;

UPDATE paulo_conversas_leads SET last_message_at = created_at WHERE last_message_at IS NULL;
