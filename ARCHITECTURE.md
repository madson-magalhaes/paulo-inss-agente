# v6_agente_ia - Pipeline Architecture

## Overview

The automated pipeline consists of 6 integrated stages that run continuously every 60 seconds. Each stage is a discrete, reusable component.

```
auto_pipeline.py (every 60s)
    ↓
executar_pipeline.py (orchestrator)
    ├─ STAGE 1: coletar.py
    ├─ STAGE 2: validador_orcamentos_v2.py
    ├─ STAGE 2.5: marcar_processando.py
    ├─ STAGE 2.6: validar_aguardando_ciclo.py
    ├─ STAGE 3: processar_orcamento.py (for each ready orçamento)
    └─ STAGE 4: atualizar_status_processado.py (for each processed orçamento)
```

## Stage Details

### STAGE 1: COLETA (Collection) - `coletar.py`

**Purpose**: Fetch orçamentos from Supabase and prepare for processing

**Input**: 
- Supabase table `paulo_orcamentos` with status_orcamento='aberto' or 'processando'

**Process**:
1. Connects to Supabase via SUPABASE_URL + SUPABASE_KEY
2. Queries for active orçamentos (status: aberto, processando)
3. For each orçamento:
   - Creates folder: `orcamentos/orcamento_XXXXX_ClientName/`
   - Exports data to: `orcamentos/orcamento_XXXXX_ClientName/obra-XXXXX.csv`
   - If paralisação exists: `orcamentos/orcamento_XXXXX_ClientName/paralisacao_obra-XXXXX.csv`

**Output**:
- Dict mapping numero_orcamento → orçamento data (name, etc.)
- Folders created in `./orcamentos/`
- CSV files in respective folders

**Key Points**:
- ❌ NO intermediate `dados_supabase/` folder
- ✅ Direct export to final location
- ✅ Client name included in folder name
- ✅ Cross-platform paths using pathlib

---

### STAGE 2: VALIDAÇÃO (Validation) - `validador_orcamentos_v2.py`

**Purpose**: Enforce two-cycle validation to prevent partial processing

**Input**: 
- Orçamentos from STAGE 1
- Control file: `.claude/orcamentos_validacao_v2.json`

**Process**:
1. For each orçamento, track:
   - First cycle: Register count of open/processed lines
   - Second cycle: Verify no changes (60-second wait)
   - If count decreased: Alert (partial processing detected)
   - If count stable: Mark as ready

2. Only allow processing after CICLOS_VALIDACAO cycles pass

**Output**:
- Dict of ready orçamentos (passed both cycles)
- Dict of waiting orçamentos (still in validation)
- Control file updated

**Key Points**:
- ✅ Prevents duplicate processing
- ✅ Detects partial processing
- ✅ Configurable: INTERVALO_SEGURANCA, CICLOS_VALIDACAO (in .env)

---

### STAGE 2.5: MARCAÇÃO (Marking) - `marcar_processando.py`

**Purpose**: Transition status from 'aberto' to 'processando'

**Process**:
1. For orçamentos with status='aberto'
2. Update Supabase: status_orcamento → 'processando'

**Output**:
- Supabase record updated

**Key Points**:
- ⚠️ This is a checkpoint - once marked, must complete or mark 'processado'

---

### STAGE 2.6: AGUARDO (Cycle Wait) - `validar_aguardando_ciclo.py`

**Purpose**: Final validation before processing

**Process**:
1. Count how many 'processando' orçamentos are ready
2. Filter out those still in first cycle
3. Return only orçamentos ready for processing

**Output**:
- Dict of orçamentos ready for STAGE 3 processing

---

### STAGE 3: PROCESSAMENTO (Processing) - `processar_orcamento.py`

**Purpose**: Calculate INSS values and generate output files

**Process** (for each ready orçamento):
1. Find folder: `./orcamentos/orcamento_XXXXX_ClientName/`
2. Locate input files: `obra-XXXXX.csv`, `paralisacao_obra-XXXXX.csv`
3. Prepare paralisacao.csv for main.py (temporary)
4. Execute main.py to calculate INSS
5. Save output files:
   - `inss-XXXXX.csv` (normal calculation)
   - `inss-XXXXX-otimizado.csv` (optimized variant)

**Output Files** (saved in `./orcamentos/orcamento_XXXXX_ClientName/`):
```
orcamentos/orcamento_12052603_Luis Augusto/
├── obra-12052603.csv              [input - preserved]
├── paralisacao_obra-12052603.csv  [input - if exists]
├── inss-12052603.csv              [output - generated]
└── inss-12052603-otimizado.csv    [output - generated]
```

**Key Points**:
- ✅ Input files preserved for audit trail
- ✅ Output files permanently stored (not deleted)
- ✅ Ready for next processing cycle or review

---

### STAGE 4: FINALIZAÇÃO (Finalization) - `atualizar_status_processado.py`

**Purpose**: Transition to 'processado' and sync with Google Drive

**Process** (for each successfully processed orçamento):
1. Validate that INSS files exist
2. Update Supabase: status_orcamento → 'processado'
3. Sync folder with Google Drive:
   - Check if folder exists in Drive
   - If exists: Update files (no duplicates)
   - If not exists: Create folder and upload files
4. Report completion

**Google Drive Behavior**:
- **First run**: Creates new folder, uploads all files
- **Subsequent runs**: Updates files in existing folder
- **Result**: No duplicate files, atomic updates

**Key Points**:
- ✅ Executes ONLY after successful processing
- ✅ Google Drive upload deduplicates
- ✅ Status marked only after validation AND Drive sync

---

## Data Flow Example

```
Orçamento 12052603 - Luis Augusto

STAGE 1 (COLETA):
  Supabase: {"numero": 12052603, "status": "aberto", ...}
            ↓
  ./orcamentos/orcamento_12052603_Luis Augusto/
  ├── obra-12052603.csv

STAGE 2 (VALIDAÇÃO):
  First cycle: Count = 1 open, 0 processed
  [Wait 60s]
  Second cycle: Count = 1 open, 0 processed → PASS
  Ready: {12052603: {...}}

STAGE 2.5 (MARCAÇÃO):
  Supabase: status → "processando"

STAGE 2.6 (AGUARDO):
  Check: Is in processando for > 60s? YES → Ready to process

STAGE 3 (PROCESSAMENTO):
  Input: ./orcamentos/orcamento_12052603_Luis Augusto/obra-12052603.csv
  Process: Calculate INSS
  Output: 
    ├── inss-12052603.csv
    └── inss-12052603-otimizado.csv

STAGE 4 (FINALIZAÇÃO):
  Validate: Files exist? YES
  Database: Update status → "processado"
  Drive: Upload/sync folder
  Result: ✅ Complete
```

---

## Error Handling

| Stage | Error | Action |
|-------|-------|--------|
| 1 | Supabase connection fails | Retry next cycle |
| 2 | Validation fails | Wait for next cycle |
| 2.5 | Mark fails | Warning, continue (may retry next cycle) |
| 3 | Processing fails | Log error, don't advance to STAGE 4 |
| 4 | Drive sync fails | Warning, but mark 'processado' (files are safe locally) |

---

## Configuration

**Environment Variables** (in `.env`):

```bash
# Supabase
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Google Drive
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=<folder-id>
GOOGLE_OAUTH_CREDENTIALS_FILE=.credentials/oauth_credentials.json
GOOGLE_OAUTH_TOKEN_PATH=.credentials/google_token.json

# Validation
INTERVALO_SEGURANCA_ORCAMENTOS=60        # seconds between cycles
CICLOS_VALIDACAO_ORCAMENTOS=2             # cycles required to process
```

---

## File Locations

```
v6_agente_ia/
├── auto_pipeline.py                    # Run every 60s
├── executar_pipeline.py                # Orchestrator
├── coletar.py                          # STAGE 1
├── validador_orcamentos_v2.py          # STAGE 2
├── marcar_processando.py               # STAGE 2.5
├── validar_aguardando_ciclo.py         # STAGE 2.6
├── processar_orcamento.py              # STAGE 3
├── atualizar_status_processado.py      # STAGE 4 ← NEW
├── google_drive_sync.py                # Drive integration
│
├── .env                                # Credentials (local)
├── .env.example                        # Template (for VPS)
├── .gitignore                          # Protect secrets
│
├── .credentials/                       # OAuth tokens
│   ├── oauth_credentials.json
│   └── google_token.json
│
├── orcamentos/                         # Runtime: Per-orçamento folders
│   └── orcamento_XXXXX_ClientName/
│       ├── obra-XXXXX.csv              [input]
│       ├── paralisacao_obra-XXXXX.csv  [input, if exists]
│       ├── inss-XXXXX.csv              [output]
│       └── inss-XXXXX-otimizado.csv    [output]
│
└── .claude/                            # Runtime: Control files
    ├── orcamentos_validacao_v2.json
    └── [other control files]
```

---

## Performance Notes

- **Collection**: ~100ms per orçamento (depends on Supabase latency)
- **Validation**: ~50ms per orçamento + network
- **Processing**: ~5-30 seconds per orçamento (INSS calculation)
- **Drive Sync**: ~2-5 seconds (depends on file sizes + network)

**Total per cycle**: 2-3 minutes for 5 orçamentos (most time in STAGE 3)

---

## Scalability

- **Local**: Tested with 2-5 concurrent orçamentos
- **VPS**: Can handle 10+ orçamentos per cycle
- **Bottleneck**: INSS calculation (STAGE 3), not I/O
- **Optimization**: Parallel processing possible for STAGE 3 (future)

