# ATUALIZAR AGENTE — SDR Paulo Robson (Lia)
> Documento de trabalho para Claude Code · Julho 2026
> Objetivo: eliminar duplicação de `numero_orcamento`, garantir chamada da tool `salvar_dados_obra` e mover toda lógica determinística do LLM para o Postgres.

---

## 1. CONTEXTO DO SISTEMA

**Stack:** n8n (workflow `SDR - Paulo Robson`, 86 nodes) + Supabase (Postgres) + Evolution API (WhatsApp) + Grok 4.3 via OpenRouter.

**Fluxo de negócio:** agente SDR "Lia" coleta dados técnicos de obra via WhatsApp (10 etapas), salva no Supabase (`paulo_orcamentos`), um código externo é disparado quando a tabela é alimentada e calcula o diagnóstico de INSS de obra. Depois um Agente de Fechamento (webhook do Supabase) apresenta os valores ao lead.

**3 agentes no workflow:**
| Agente | Papel | Tools |
|---|---|---|
| `AI Agent` | SDR Lia (produção) | `salvar_dados_obra`, `verificar_orcamento`, `Base_Conhecimento` |
| `AI Agent2` | Agente de Fechamento (trigger: `Webhook-Supabase`) | nenhuma (só memória) |
| `AI Agent3` | Agente de testes do Paulo (extrator direto, branch `Paulo_teste`) | `salvar_dados_obra1`, `verificar_orcamento1` |

**Fluxo principal:** `Webhook → Check_JID → Config → Paulo_teste → Skip_Own → Get_User → Rota_Midia (texto/áudio/imagem/PDF) → Merge_Msgs → Save_Conv → Wait_Limit (debounce) → Get_Msg_DB → Validar → AI Agent → Format_Msg1 → Split/Loop → Send_Msg (Evolution API)`

**Regra de negócio central do orçamento:**
- Cada orçamento = 1 número único (`numero_orcamento`)
- Um orçamento pode ter **N linhas** na tabela (área principal + piscina/garagem), todas com o **mesmo número** — o código externo soma as linhas pelo número
- Clientes diferentes = números diferentes, sempre
- **Mesmo telefone pode gerar múltiplos orçamentos** (engenheiro simula vários clientes dele pelo mesmo WhatsApp) — cada simulação = número novo
- `status_orcamento` default `'aberto'`; o código externo processa e (deve) alterar o status

---

## 2. AUDITORIA — PROBLEMAS ENCONTRADOS NO JSON ATUAL

### 🔴 CRÍTICO 1 — Conflito de formato do `numero_orcamento`
- System prompt (v4.7): formato `AAMMDD` + seq → dia 08/05/2026 = `26050801`
- Descrição `$fromAI` do node `salvar_dados_obra`: formato `DDMMYY` + seq → mesmo dia = `08052601`
- **Formatos invertidos.** O Grok segue ora um, ora outro. Registros salvos no formato "errado" não batem com o filtro de data que o agente aplica ao ler `verificar_orcamento` → ele acha que o dia está vazio → gera sequência `01` de novo → **números duplicados entre clientes**. Causa principal das colisões, somada à race condition (execuções paralelas lendo a mesma "maior sequência").

### 🔴 CRÍTICO 2 — `telefone` via `$fromAI`
O modelo digita o telefone no payload. O prompt manda usar `TELEFONE_LEAD` exato, mas o mecanismo permite alucinação de dígito. Deve ser injetado deterministicamente, fora do alcance do modelo.

### 🔴 CRÍTICO 3 — `verificar_orcamento` = `SELECT` com `returnAll: true`, sem filtro/limite
A tabela inteira entra no contexto a cada fechamento. Cresce sem limite → contexto inchado → Grok "desiste" da cadeia de tools e alucina a mensagem de encerramento sem chamar `salvar_dados_obra` (**o problema original**). Também infla custo por token.

### 🔴 CRÍTICO 4 — Contradição: 1 linha por chamada vs "chame exatamente uma vez"
O node insere **uma linha por chamada** (cada `$fromAI` = um valor escalar). Obra com áreas complementares exige 2-3 chamadas, mas o prompt proíbe mais de uma. E nada garante o mesmo número entre chamadas — o modelo regenera os parâmetros a cada call.

### 🟡 Menores
- Nenhuma tool tem `toolDescription` explícita (sinal fraco de "quando usar" → contribui pro skip)
- `AI Agent` sem `maxIterations`, sem "Return Intermediate Steps"; `salvar_dados_obra` sem `retryOnFail`
- Formato do `meses_paralisados` (`MM/AAAA` separados por vírgula, ex: `10/2025,11/2025` — cada mês enumerado, NÃO intervalo) vem só da descrição `$fromAI`, nunca foi especificado no prompt — funciona por inferência, é frágil
- `AI Agent3` (testes) duplica as tools → risco de drift de manutenção

---

## 3. DESIGN ALVO

**Princípio:** o LLM só conversa e monta um payload JSON único. Todo o determinístico (número, dedup, expansão de áreas em linhas, expansão de meses paralisados) vai para uma função plpgsql no Supabase, chamada por um node **Execute Query**.

**Ganhos:**
1. 1 tool call por conversa (a regra do prompt vira verdadeira) — piscina + principal = 1 call, N linhas, mesmo número
2. Zero colisão entre clientes (atomicidade `INSERT ... ON CONFLICT`)
3. Mesmo telefone, obra nova = número novo (fora da janela de dedup)
4. `verificar_orcamento` **deixa de existir** — cadeia cai de 2 tools + parse CSV + aritmética para 1 call simples (ataca diretamente o skip do Grok)
5. Expansão de meses sai do modelo (sem erro de virada de ano)
6. `telefone` hardcoded — modelo nem vê o campo

### ✅ DECISÕES RESOLVIDAS (Madson, 04/07/2026)
- [x] **Regra de borda dos meses paralisados:** o contrato aceita DUAS formas por intervalo, e o modelo nunca faz aritmética: `{"inicio","fim"}` com `fim` = último mês parado (INCLUSIVO — mês único parado: `inicio` = `fim`); ou `{"inicio","retomada"}` com `retomada` = mês em que a obra voltou (EXCLUSIVO, mês de retomada é ativo). *Lição do 1º teste real (04/07/2026): o modelo codificou meses soltos como `inicio = fim`, e com `fim` exclusivo a expansão gerava série vazia → `meses_paralisados` em branco. Por isso `fim` passou a ser inclusivo, com `retomada` como forma alternativa.*
- [x] **Janela de dedup:** 10 minutos + **mesmo `nome`**. A Lia sempre coleta o nome do cliente antes de salvar; quando um engenheiro simula outro cliente pelo mesmo WhatsApp, o nome é diferente → número novo. Se telefone + nome (normalizado) + janela de 10 min coincidirem (= mesma conversa), a função atualiza o MESMO orçamento respeitando o ciclo do pipeline: regrava linhas `'aberto'`, preserva linhas `'processando'` (só acrescenta as novas), e gera número NOVO se algo já foi `'processado'` ou se o payload contradiz linha em processamento — **detalhe completo na seção 4.3**. *Lição do 2º teste real (04/07/2026): lead acrescentou demolição + piscina após o salvamento; o prompt antigo proibia rechamar a tool e o agente "prometeu repassar ao time" (dado perdido). Agora o prompt manda rechamar com o payload completo e a função atualiza o mesmo orçamento.*
- [x] **Ciclo do `status_orcamento`:** confirmado na tabela de produção — o código externo (pipeline v6_agente_ia, `atualizar_status_processado.py`) altera para `'processado'` após processar. A dedup por `'aberto'` não vaza entre orçamentos legítimos.
- [x] **Demolição/reforma: principal ou complementar** (professor, 04/07/2026): um orçamento PODE ter **mais de uma linha principal** (ex: demolição da casa velha + construção nova = 2 principais, cada uma na tabela de equivalência). Quando o lead menciona demolição/reforma junto com outra obra, o agente pergunta onde foi: construção inteira → principal (caso mais comum); estrutura menor/anexa → complementar com `coberta` inferida (casa/edícula/garagem → sim; muro/piscina/quadra → nao; **sem como inferir → `nao`/descoberta por padrão**), exibida no resumo da Etapa 10 para o lead corrigir. O cálculo (`calculators.py:261`) decide por linha — múltiplas principais passam sem mudança de código. A função valida: linha `is_principal=nao` sem `coberta` → erro `DADOS INCOMPLETOS` que instrui o agente a perguntar e rechamar (evita o loop de falha no pipeline — 3º teste real).

### ⚠️ REGRA ADICIONAL — linhas heterogêneas por orçamento
Um orçamento pode ter linhas com `tipo`/`categoria`/`material` **diferentes** (ex: reforma + demolição). O código de cálculo (`io_handlers.py`) lê `tipo`, `categoria`, `material` e `prefabricado` **por linha**; só `estado`, datas, `concreto_usinado` e `paralisacao` vêm da primeira linha. Portanto esses 4 campos ficam **dentro de cada item** do array `areas` no contrato — não no nível do orçamento.

---

## 4. FASE 1 — SUPABASE (via API/MCP, ambiente de teste)

Criar estrutura **paralela** para testar sem tocar na produção. Sufixo `_v2`.

### 4.1 Tabela de teste (espelho da atual + melhorias)

```sql
CREATE TABLE IF NOT EXISTS paulo_orcamentos_v2 (
  id                BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  nome              VARCHAR,
  telefone          VARCHAR NOT NULL,
  numero_orcamento  VARCHAR NOT NULL,
  estado            VARCHAR,
  tipo              VARCHAR,
  categoria         VARCHAR,
  material          VARCHAR,
  area_m2           VARCHAR,          -- espelho exato da produção (tabela será renomeada na migração)
  is_principal      VARCHAR,
  coberta           VARCHAR,
  data_inicio       VARCHAR,
  data_fim          VARCHAR,
  concreto_usinado  VARCHAR DEFAULT 'nao',
  paralisacao       VARCHAR,
  prefabricado      VARCHAR DEFAULT 'nao',
  status_orcamento  TEXT DEFAULT 'aberto',
  meses_paralisados TEXT
);

CREATE INDEX IF NOT EXISTS idx_orc_v2_tel_status
  ON paulo_orcamentos_v2 (telefone, status_orcamento, created_at DESC);
```

> Nota: `area_m2` como `NUMERIC` é melhoria opcional. Se o código externo espera string, manter `VARCHAR` para não quebrar o parser — decidir na migração final.

### 4.2 Tabela de sequência diária (compartilhada entre teste e produção depois)

```sql
CREATE TABLE IF NOT EXISTS orcamento_seq (
  dia DATE PRIMARY KEY,
  seq INT NOT NULL DEFAULT 0
);
```

### 4.3 Função principal — `salvar_orcamento_v2`

> 📄 **Fonte da verdade: `supabase_v2_setup.sql`** (mantido em sincronia com
> `migracao_producao.sql`, que é idêntico apontando para `paulo_orcamentos`).
> O SQL não é mais duplicado aqui para evitar drift entre as cópias.

Comportamento (respeitando o ciclo do pipeline Python `aberto → processando → processado`):

1. **Expande meses paralisados** — `{inicio, fim}` (fim = último mês parado, INCLUSIVO) ou `{inicio, retomada}` (retomada EXCLUSIVA). O modelo nunca faz aritmética.
2. **Dedup** (mesmo telefone + MESMO nome normalizado, janela 10 min):
   - linhas todas `'aberto'` → apaga e **regrava tudo do payload com o MESMO número** (payload = fonte da verdade; cobre chamada duplicada, acréscimo e correção)
   - tem linha `'processando'` → linhas em processamento ficam **intactas**; só as áreas novas entram como `'aberto'` no mesmo número — o `validar_aguardando_ciclo.py` detecta o novo `'aberto'`, reinicia o aguardo e processa tudo junto UMA vez. Se o payload **contradiz** uma linha processando (correção de valor/dados gerais) → número NOVO com payload completo
   - tem linha `'processado'` → linha finalizada nunca volta ao ciclo nem recebe append (a coleta ignoraria as linhas antigas e o cálculo sairia sem a principal) → número NOVO com payload completo
3. **Número atômico**: `AAMMDD` + sequência de 2 dígitos via `orcamento_seq` (data local America/Fortaleza).
4. **Uma linha por área**, campos `tipo/categoria/material/prefabricado` por linha; área já existente como linha `'processando'` é pulada (nunca duplica no ciclo).

### 4.4 Contrato do payload JSON (o que o agente monta)

```json
{
  "nome": "João da Silva",
  "telefone": "5588999999999",
  "estado": "CE",
  "data_inicio": "01/01/2023",
  "data_fim": "31/08/2023",
  "concreto_usinado": "nao",
  "paralisacao": "sim",
  "paralisacoes": [
    { "inicio": "03/2025", "fim": "04/2025" },
    { "inicio": "10/2025", "retomada": "01/2026" }
  ],
  "areas": [
    { "tipo": "unifamiliar", "categoria": "obra_nova", "material": "alvenaria", "area_m2": "190",   "is_principal": "sim", "coberta": "",    "prefabricado": "nao" },
    { "tipo": "unifamiliar", "categoria": "obra_nova", "material": "alvenaria", "area_m2": "32.50", "is_principal": "nao", "coberta": "nao", "prefabricado": "nao" }
  ]
}
```

Regras do contrato:
- **Nível do orçamento** (igual em todas as linhas): `nome`, `telefone`, `estado`, `data_inicio`, `data_fim`, `concreto_usinado`, `paralisacao`, `paralisacoes`.
- **Nível da linha** (dentro de cada item de `areas`): `tipo`, `categoria`, `material`, `area_m2`, `is_principal`, `coberta`, `prefabricado`. Isso permite orçamentos heterogêneos — ex: reforma + demolição = 2 itens com `categoria` diferente, mesmo número.
- `paralisacoes`: um item por período parado, vazio `[]` quando `paralisacao = "nao"`. Duas formas: `{"inicio","fim"}` (`fim` = último mês parado, inclusivo; mês único: `inicio` = `fim`) ou `{"inicio","retomada"}` (`retomada` = mês em que voltou, exclusivo). O modelo NUNCA enumera meses nem faz contas — só passa os intervalos como o lead informou.
- `areas`: sempre pelo menos 1 item (principal). `coberta` = `""` para principal, `sim`/`nao` para complementares.
- `telefone`: será **sobrescrito deterministicamente** no n8n antes da query (ver Fase 2) — o valor do modelo é ignorado.
- `nome`: participa da dedup (telefone + nome + 10 min) — é o que separa dois clientes diferentes do mesmo engenheiro.

---

## 5. FASE 2 — n8n (mudanças no workflow)

### 5.1 Substituir o node `salvar_dados_obra` (postgresTool insert → postgresTool executeQuery)

Configuração alvo:
- **Operation:** Execute Query
- **Query** (payload embutido na query com escape de `'` — o campo "Query Parameters" do n8n divide valores em vírgulas e quebraria o JSON):
```sql
SELECT salvar_orcamento_v2(
  jsonb_set(
    '{{ $fromAI('payload_json', '...', 'string').replace(/'/g, "''") }}'::jsonb,
    '{telefone}',
    to_jsonb('{{ $('Config').first().json.USER_ID }}'::text)
  )
) AS numero_orcamento;
```
- A descrição do `$fromAI('payload_json', ...)` enumera o contrato: nome, telefone, estado, data_inicio, data_fim, concreto_usinado, paralisacao, paralisacoes (array de intervalos inicio/fim em MM/AAAA), areas (array de itens com tipo, categoria, material, area_m2, is_principal, coberta, prefabricado — um item por área/linha)
- **toolDescription (explícita):** "Salva TODOS os dados coletados da obra no banco e gera o número do orçamento. Chamar EXATAMENTE UMA VEZ por conversa, somente após a confirmação do resumo (Etapa 10) e coleta do nome. Recebe um único parâmetro payload_json com todas as áreas e paralisações juntas. Retorna o numero_orcamento gerado."
- **Node settings:** `retryOnFail: true`, `maxTries: 2`

> O `jsonb_set` do telefone garante que mesmo que o modelo alucine o número, o valor gravado é sempre o `USER_ID` do Config. Testar se `$('Config').first()` resolve dentro do tool node nesta versão do n8n — se não resolver, alternativa: passar o telefone via segundo query parameter fixo.

### 5.2 Remover `verificar_orcamento`
- Desconectar `verificar_orcamento --[ai_tool]--> AI Agent` e deletar o node.
- Mesmo para `verificar_orcamento1` / `AI Agent3`.

### 5.3 Replicar em `salvar_dados_obra1` (agente de testes do Paulo)
Mesma configuração do 5.1, apontando para a mesma função. Manter os dois nodes idênticos (copiar/colar) para evitar drift.

### 5.4 `AI Agent` — settings
- `maxIterations`: definir (ex: 10)
- Ativar "Return Intermediate Steps" (habilita guardrail futuro de verificação pós-resposta: se a resposta contém padrão de encerramento mas a tool não aparece nos steps → bloquear e reinjetar)

### 5.5 Guardrail opcional (fase posterior, se skip persistir)
IF node após o `AI Agent`: regex de encerramento na resposta (`time técnico já recebeu`) E ausência de `salvar_dados_obra` nos intermediate steps → não enviar; reinjetar no agente: `[SISTEMA: você afirmou envio sem executar salvar_dados_obra. Execute a tool agora antes de responder.]`

---

## 6. FASE 3 — SYSTEM PROMPT v4.8 (mudanças na v4.7)

### 6.1 REMOVER
- Toda a seção "Geração do `numero_orcamento`" (os 5 passos com `verificar_orcamento`)
- `numero_orcamento` da tabela de payload
- Linhas do checklist sobre `verificar_orcamento` ("Chamar verificar_orcamento antes de salvar_dados_obra" / "Inventar ou calcular numero_orcamento sem consultar a tool")
- Menções a `verificar_orcamento` na seção de Segurança (lista de tools)

### 6.2 SUBSTITUIR a Transição Final por:

```markdown
## TRANSIÇÃO FINAL — ENCAMINHAMENTO

> 🔒 REGRA ABSOLUTA DE VERACIDADE: Você está PROIBIDA de dizer ao lead que
> os dados foram enviados, registrados ou encaminhados ao time técnico antes
> de ter recebido a resposta de SUCESSO da tool `salvar_dados_obra` no seu
> contexto. Afirmar envio sem a tool ter executado é uma FALHA GRAVE: o
> orçamento NUNCA será gerado e o lead será perdido.

### Sequência obrigatória (nesta ordem exata):

1. Lead confirma o resumo da Etapa 10 + nome coletado.
2. CHAMAR a tool `salvar_dados_obra` com o payload JSON completo
   (todas as áreas e paralisações em uma única chamada). Não escreva
   nada ao lead ainda.
3. SOMENTE APÓS ver o retorno de sucesso da tool no contexto, enviar
   a mensagem de encerramento.

### Checkpoint interno antes de QUALQUER mensagem de encerramento:

"Existe no contexto desta conversa um resultado de execução da tool
`salvar_dados_obra`?"
- NÃO existe → você ainda não pode encerrar. Chame a tool AGORA.
- Existe com sucesso → envie a mensagem de encerramento.
- Existe com erro → informe instabilidade e que o time entrará em contato.
```

### 6.3 SUBSTITUIR a tabela "FORMATO DE SAÍDA" pelo contrato JSON

```markdown
## FORMATO DE SAÍDA — PAYLOAD DA TOOL `salvar_dados_obra`

A tool recebe UM ÚNICO parâmetro `payload_json` com TODOS os dados da
conversa. Chame a tool UMA ÚNICA VEZ, com todas as áreas juntas.

### Campos no nível do orçamento (uma vez no payload):

| Campo | Tipo | Regra |
|---|---|---|
| `nome` | string | Nome completo coletado na pré-transição. Quando um engenheiro/despachante pede orçamento para um cliente dele, é o nome DO CLIENTE. |
| `estado` | string | Sigla UF maiúscula |
| `data_inicio` | string | `DD/MM/AAAA` |
| `data_fim` | string | `DD/MM/AAAA`, posterior ao início |
| `concreto_usinado` | string | `sim` / `nao` — padrão `nao` |
| `paralisacao` | string | `sim` / `nao` |
| `paralisacoes` | array | Um item por período parado. Duas formas: `{"inicio": "MM/AAAA", "fim": "MM/AAAA"}` (`fim` = ÚLTIMO mês parado, inclusivo — mês único: `inicio` = `fim`) OU `{"inicio": "MM/AAAA", "retomada": "MM/AAAA"}` (lead informou o mês em que VOLTOU; o sistema exclui a retomada). Vazia `[]` se `paralisacao = nao`. NUNCA enumere meses fora dos intervalos nem faça contas. |
| `telefone` | string | Preencher com TELEFONE_LEAD (o sistema valida e corrige automaticamente) |

### Campos DENTRO de cada item do array `areas` (um item por área/linha):

| Campo | Tipo | Regra |
|---|---|---|
| `tipo` | string | `unifamiliar` / `multifamiliar` / `comercial` / `galpao` / `casa_popular` / `conjunto_habitacional` / `edificio_garagem` |
| `categoria` | string | `obra_nova` / `acrescimo` / `reforma` / `demolicao` |
| `material` | string | `alvenaria` / `madeira` / `mista` / `concreto` |
| `area_m2` | string | Decimal com ponto: `"190"`, `"127.40"` — nunca vírgula |
| `is_principal` | string | `sim` (área principal) / `nao` (complementar) |
| `coberta` | string | `""` para principal, `sim`/`nao` para complementares |
| `prefabricado` | string | `sim` / `nao` |

Exemplos de composição do array `areas`:
- Casa simples → 1 item (principal)
- Casa + piscina → 2 itens, mesmo `tipo`/`categoria`/`material`
- Reforma + demolição → 2 itens com `categoria` DIFERENTE (`reforma` e `demolicao`), no MESMO payload/orçamento

O campo `numero_orcamento` NÃO existe mais no payload — é gerado
automaticamente pelo sistema. A tool retorna o número gerado.
```

### 6.4 Ajustar Etapa 9 (uma linha após a validação cronológica)
> Após validar, armazene cada período no array `paralisacoes`: se o lead informou quando a obra VOLTOU, use `{"inicio": "MM/AAAA", "retomada": "MM/AAAA"}`; se informou o último mês parado ou um mês único parado, use `{"inicio": "MM/AAAA", "fim": "MM/AAAA"}` (inclusivo). Não enumere meses fora dos intervalos nem faça contas — o sistema expande.

### 6.5 Adicionar ao checklist Pode/Não Pode
| ✅ | ❌ |
|---|---|
| Chamar `salvar_dados_obra` uma única vez com todas as áreas no payload | Afirmar que dados foram enviados sem ter o resultado da tool no contexto |
| Passar paralisações como intervalos início/fim | Enumerar meses paralisados individualmente |

---

## 7. FASE 4 — PROTOCOLO DE TESTES (tabela `_v2`, antes de trocar produção)

Executar via API do Supabase (chamadas diretas à função) ANTES de plugar no n8n:

```sql
-- T1: obra simples, sem paralisação, 1 área
SELECT salvar_orcamento_v2('{"nome":"Teste Um","telefone":"5588000000001","estado":"CE","data_inicio":"01/01/2023","data_fim":"31/08/2023","concreto_usinado":"nao","paralisacao":"nao","paralisacoes":[],"areas":[{"tipo":"unifamiliar","categoria":"obra_nova","material":"alvenaria","area_m2":"190","is_principal":"sim","coberta":"","prefabricado":"nao"}]}'::jsonb);
-- Esperado: 1 linha, numero = AAMMDD01 (se primeiro do dia)

-- T2: obra com piscina (2 áreas) → 2 linhas, MESMO numero
SELECT salvar_orcamento_v2('{"nome":"Teste Dois","telefone":"5588000000002",...,"areas":[{"tipo":"unifamiliar","categoria":"obra_nova","material":"alvenaria","area_m2":"250","is_principal":"sim","coberta":"","prefabricado":"nao"},{"tipo":"unifamiliar","categoria":"obra_nova","material":"alvenaria","area_m2":"32","is_principal":"nao","coberta":"nao","prefabricado":"nao"}]}'::jsonb);

-- T3: paralisação com virada de ano — forma "retomada" {inicio:10/2025, retomada:03/2026}
-- Esperado meses: 10/2025,11/2025,12/2025,01/2026,02/2026 (mês de retomada fora)

-- T3b: forma "fim" inclusiva com mês único {inicio:03/2025, fim:03/2025}
-- Esperado meses: 03/2025 (caso real do 1º teste que falhou com a versão exclusiva)

-- T4: DEDUP — repetir T1 imediatamente (mesmo telefone, MESMO nome)
-- Esperado: retorna o MESMO numero, NÃO insere linhas novas

-- T5: mesmo telefone, NOME DIFERENTE, imediatamente (engenheiro simulando outro cliente)
-- Esperado: numero NOVO, linhas novas (dedup exige telefone + nome iguais)

-- T6: CONCORRÊNCIA — dois clientes simultâneos
-- Rodar T1-like com telefones diferentes em duas conexões ao mesmo tempo
-- Esperado: numeros DIFERENTES, sem colisão

-- T7: múltiplas paralisações no array
-- Esperado: meses concatenados em ordem cronológica

-- T8: REFORMA + DEMOLIÇÃO — 2 itens em areas com categoria diferente
-- Esperado: 2 linhas, MESMO numero, categorias 'reforma' e 'demolicao' preservadas por linha

-- T9: mesmo telefone + mesmo nome, mas fora da janela (simular created_at -15 min no T1)
-- Esperado: numero NOVO (dedup só atua dentro de 10 min)

-- T10: rechamada com área acrescentada, linhas ainda 'aberto'
-- Salvar 1 área → rechamar com 3 áreas (principal + demolição + piscina)
-- Esperado: MESMO numero, 3 linhas (regravadas), nada duplicado

-- T11: rechamada com orçamento em 'processando' (simular UPDATE status)
-- Esperado: MESMO numero; linhas processando intactas; só as áreas novas
-- entram como 'aberto' (validar_aguardando_ciclo reinicia o aguardo)

-- T12: rechamada com orçamento já 'processado' (simular UPDATE status)
-- Esperado: numero NOVO com payload completo (linha processada nunca volta ao ciclo)
```

Depois, testes end-to-end pelo n8n (workflow paralelo `SDR - Paulo Robson v2`, tudo apontando pra `_v2`):
- [ ] Conversa completa texto → tool chamada 1x → linhas corretas
- [ ] Conversa com imagem de alvará → dados extraídos → payload correto
- [ ] Lead que despeja tudo na primeira mensagem
- [ ] Reforma + demolição na mesma conversa → 2 linhas, categorias distintas, mesmo número
- [ ] Engenheiro emenda 2 clientes (nomes diferentes) em < 10 min → 2 números diferentes
- [ ] 20 conversas seguidas: taxa de chamada da tool = 100% (era o bug original)

⚠️ Caveats operacionais durante os testes:
- O workflow v2 usa os **mesmos webhook paths** do v1 → n8n não permite os dois ATIVOS simultaneamente. Desativar o v1 durante a janela de teste (ou testar em instância n8n separada).
- O pipeline externo (v6_agente_ia) lê `paulo_orcamentos` (produção) → linhas da `_v2` ficam `'aberto'` para sempre durante os testes. Isso não atrapalha a dedup (janela de 10 min expira), mas para testar o ciclo completo é preciso apontar `coletar.py` temporariamente para `_v2`.
- O Database Webhook do Supabase (dispara o Agente de Fechamento) está na tabela de produção → o fechamento não dispara nos testes com `_v2`, a menos que se crie um webhook de teste na `_v2`.

## 8. FASE 5 — MIGRAÇÃO (após testes aprovados)

> Estratégia escolhida (Madson): estrutura paralela completa — workflow `SDR - Paulo Robson v2.json` + tabela `paulo_orcamentos_v2`. Testes na estrutura nova; depois a troca é feita **manualmente renomeando** (workflow e/ou tabela). Produção intocada durante os testes.

1. Backup da `paulo_orcamentos` atual (export CSV via Supabase)
2. **Inicializar a sequência do dia**: antes de ativar a v2 em produção, setar `orcamento_seq.seq` do dia atual com a maior sequência já usada em `paulo_orcamentos` naquele dia (a produção antiga gera número via LLM e a `orcamento_seq` não conhece esses números) →
```sql
INSERT INTO orcamento_seq (dia, seq)
SELECT (now() AT TIME ZONE 'America/Fortaleza')::date,
       coalesce(max(right(numero_orcamento, 2)::int), 0)
FROM paulo_orcamentos
WHERE left(numero_orcamento, 6) = to_char((now() AT TIME ZONE 'America/Fortaleza')::date, 'YYMMDD')
ON CONFLICT (dia) DO UPDATE SET seq = greatest(orcamento_seq.seq, excluded.seq);
```
3. Trocar a tabela-alvo: ou renomear `paulo_orcamentos_v2` → `paulo_orcamentos` (com backup/rename da antiga), ou alterar a função para apontar para `paulo_orcamentos` — decidir no dia
4. Adicionar índice `(telefone, status_orcamento, created_at DESC)` na tabela de produção
5. Ativar o workflow v2 (desativando o v1) — mesmos webhooks paths, então **nunca os dois ativos ao mesmo tempo**
6. Reconfigurar o Database Webhook do Supabase (trigger do Agente de Fechamento) para a tabela final, se necessário
7. Monitorar 48h: query diária de sanidade →
```sql
-- Colisões: mesmo numero, telefones diferentes (deve retornar 0)
SELECT numero_orcamento, count(DISTINCT telefone)
FROM paulo_orcamentos
GROUP BY 1 HAVING count(DISTINCT telefone) > 1;
```

---

## 9. ARQUIVOS DE REFERÊNCIA
- `SDR - Paulo Robson.json` — workflow n8n atual (v4.7) — NÃO ALTERAR (produção)
- `SDR - Paulo Robson v2.json` — workflow novo para importar e testar (gerado por este plano)
- `supabase_v2_setup.sql` — DDL + função `salvar_orcamento_v2` (rodar no SQL Editor do Supabase se a API não permitir DDL)
- System prompt v4.7 — dentro do node `AI Agent` (`options.systemMessage`, 56.904 chars)
- Tabela atual: `public.paulo_orcamentos` (colunas: id, created_at, nome, telefone, numero_orcamento, estado, tipo, categoria, material, area_m2 [varchar], is_principal, coberta, data_inicio, data_fim, concreto_usinado, paralisacao, prefabricado, status_orcamento [default 'aberto'], meses_paralisados)
- Formato real de `meses_paralisados` em produção: `10/2025,11/2025` (enumeração, não intervalo)