"""
Constantes e tabelas de referência para cálculo de INSS

Este módulo centraliza todas as constantes, alíquotas e tabelas condicionais
utilizadas nos cálculos.
"""

# ============================================================================
# ALÍQUOTAS E VALORES FIXOS
# ============================================================================

ALIQUOTA_INSS_ORIGINAL = 0.368  # 36.8% - INSS sem otimização
ALIQUOTA_CPP = 0.20  # 20% - Contribuição Previdenciária Patronal
ALIQUOTA_MULTA = 0.20  # 20% - Multa sobre atraso
MAED_FIXO = 100.00  # R$ 100,00 - Multa Administrativa fixa por mês

# ============================================================================
# TABELA PMO - PERCENTUAL DE MÃO DE OBRA
# ============================================================================
#
# Formato: (tipo, material): percentual
# Determina o percentual de mão de obra baseado no tipo de construção e material
#
TABELA_PMO = {
    # Residencial unifamiliar, multifamiliar, comercial, edifícios de garagens, galpão industrial
    ('unifamiliar', 'alvenaria'): 0.20,
    ('multifamiliar', 'alvenaria'): 0.20,
    ('comercial', 'alvenaria'): 0.20,
    ('edificio_garagem', 'alvenaria'): 0.20,
    ('galpao', 'alvenaria'): 0.20,

    ('unifamiliar', 'madeira'): 0.15,
    ('multifamiliar', 'madeira'): 0.15,
    ('comercial', 'madeira'): 0.15,
    ('edificio_garagem', 'madeira'): 0.15,
    ('galpao', 'madeira'): 0.15,

    ('unifamiliar', 'mista'): 0.15,
    ('multifamiliar', 'mista'): 0.15,
    ('comercial', 'mista'): 0.15,
    ('edificio_garagem', 'mista'): 0.15,
    ('galpao', 'mista'): 0.15,

    # Concreto (estruturas de concreto armado/protendido)
    ('unifamiliar', 'concreto'): 0.20,
    ('multifamiliar', 'concreto'): 0.20,
    ('comercial', 'concreto'): 0.20,
    ('edificio_garagem', 'concreto'): 0.20,
    ('galpao', 'concreto'): 0.20,

    # Metálico (estruturas metálicas)
    ('unifamiliar', 'metalico'): 0.15,
    ('multifamiliar', 'metalico'): 0.15,
    ('comercial', 'metalico'): 0.15,
    ('edificio_garagem', 'metalico'): 0.15,
    ('galpao', 'metalico'): 0.15,

    # Casa popular e conjunto habitacional popular
    ('casa_popular', 'alvenaria'): 0.12,
    ('conjunto_habitacional', 'alvenaria'): 0.12,
    ('casa_popular', 'madeira'): 0.07,
    ('conjunto_habitacional', 'madeira'): 0.07,
    ('casa_popular', 'mista'): 0.07,
    ('conjunto_habitacional', 'mista'): 0.07,
    ('casa_popular', 'concreto'): 0.12,
    ('conjunto_habitacional', 'concreto'): 0.12,
    ('casa_popular', 'metalico'): 0.07,
    ('conjunto_habitacional', 'metalico'): 0.07,
}

# ============================================================================
# TABELA FATOR SOCIAL
# ============================================================================
#
# Tabela de Fator Social baseada na área total da construção
# Formato: (area_maxima, fator)
# 0 - 100 m²: 20%
# 100.01 - 200 m²: 40%
# 200.01 - 300 m²: 55%
# 300.01 - 400 m²: 70%
# 400.01 ou maior: 90%
#
TABELA_FATOR_SOCIAL = [
    (100.00, 0.20),
    (200.00, 0.40),
    (300.00, 0.55),
    (400.00, 0.70),
    (float('inf'), 0.90),
]

# ============================================================================
# TABELA EQUIVALÊNCIA
# ============================================================================
#
# Tabela de Percentuais de Equivalência baseada no tipo de imóvel e área total
# Nova lógica simplificada conforme documento de atualizações
# Formato: tipo_construcao: [(area_maxima, percentual), ...]
#
TABELA_EQUIVALENCIA = {
    'unifamiliar': [
        (1000.00, 0.89),      # 0 - 1000 m²: 89%
        (float('inf'), 0.85)  # 1000.01 m² ou maior: 85%
    ],
    'multifamiliar': [
        (1000.00, 0.90),      # 0 - 1000 m²: 90%
        (float('inf'), 0.86)  # 1000.01 m² ou maior: 86%
    ],
    'comercial': [
        (3000.00, 0.86),      # 0 - 3000 m²: 86%
        (float('inf'), 0.83)  # 3000.01 m² ou maior: 83%
    ],
    'edificio_garagem': [
        (3000.00, 0.86),      # 0 - 3000 m²: 86%
        (float('inf'), 0.83)  # 3000.01 m² ou maior: 83%
    ],
    'casa_popular': [
        (float('inf'), 0.98)  # Qualquer área: 98%
    ],
    'galpao': [
        (float('inf'), 0.95)  # Qualquer área: 95%
    ],
    'conjunto_habitacional': [
        (float('inf'), 0.98)  # Qualquer área: 98%
    ]
}

# ============================================================================
# TABELA FATOR DE AJUSTE
# ============================================================================
#
# Tabela de Fator de Ajuste baseada na área total do projeto
# Formato: (area_maxima, fator)
# 0 - 350 m²: 50%
# 350.01 m² ou maior: 70%
#
TABELA_FATOR_AJUSTE = [
    (350.00, 0.50),      # 0 - 350 m²: 50%
    (float('inf'), 0.70) # 350.01 m² ou maior: 70%
]

# ============================================================================
# TABELA PERCENTUAL CATEGORIA
# ============================================================================
#
# Tabela de Percentual de Categoria baseada no tipo de obra
# Formato: {categoria: percentual}
#
TABELA_PERCENTUAL_CATEGORIA = {
    'obra_nova': 1.00,         # Obra Nova: 100%
    'reforma': 0.35,           # Reforma: 35%
    'demolicao': 0.00,         # Demolição: 0%
    'acrescimo': 1.00,         # Acréscimo: 100%
    'existente': 0.00,         # Construção Existente (apenas para constar): 0%
}

# ============================================================================
# TIPOS VÁLIDOS
# ============================================================================

TIPOS_VALIDOS = {
    'unifamiliar',
    'multifamiliar',
    'comercial',
    'edificio_garagem',
    'galpao',
    'casa_popular',
    'conjunto_habitacional',
}

CATEGORIAS_VALIDAS = {
    'obra_nova',
    'reforma',
    'demolicao',
    'acrescimo',
    'existente',
}

MATERIAIS_VALIDOS = {
    'alvenaria',
    'madeira',
    'mista',
    'concreto',
    'metalico',
}

# ============================================================================
# MAPEAMENTO DE NOMES ALTERNATIVOS
# ============================================================================
#
# Permite usar nomes em inglês ou alternativos para as categorias
#
MAPEAMENTO_CATEGORIAS = {
    'new_construction': 'obra_nova',
    'renovation': 'reforma',
    'demolition': 'demolicao',
    'expansion': 'acrescimo',
    'existing': 'existente',
}

# ============================================================================
# FATORES DE REDUÇÃO PARA ÁREAS COMPLEMENTARES
# ============================================================================
#
# Para áreas complementares, NÃO usa a tabela de equivalência
# Usa percentuais fixos que substituem a % de equivalência:
# Coberta: 50% (área equivalente = área × 0.50)
# Descoberta: 25% (área equivalente = área × 0.25)
#
FATOR_REDUCAO_COMPLEMENTAR_COBERTA = 0.50   # Área complementar coberta: 50%
FATOR_REDUCAO_COMPLEMENTAR_DESCOBERTA = 0.25  # Área complementar descoberta: 25%

# ============================================================================
# REGRAS DE PARALISAÇÃO E DECADÊNCIA
# ============================================================================

# Data limite para meses decadentes (até Dez/2020 inclusive)
# Meses decadentes são descontados do RMT Total (benefício fiscal)
from datetime import datetime
DATA_LIMITE_DECADENCIA = datetime(2020, 12, 31)

# Meses que NUNCA recebem recibos (Jan/21 a Set/21)
# Mesmo que não paralisados, estes meses não têm distribuição de recibos
# Os valores destes meses são redistribuídos nos meses válidos
MESES_SEM_RECIBOS = [
    (1, 2021), (2, 2021), (3, 2021), (4, 2021), (5, 2021),
    (6, 2021), (7, 2021), (8, 2021), (9, 2021)
]
