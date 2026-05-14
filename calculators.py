"""
Funções de cálculo do sistema de INSS

Este módulo contém todas as funções de cálculo:
- Busca em tabelas condicionais
- Cálculo de áreas individuais
- Cálculo completo de INSS da obra
"""

from typing import List, Tuple
from datetime import datetime
from models import AreaConstrucao, CalculoArea, ResultadoSimulacao
from constants import (
    TABELA_PMO, TABELA_FATOR_SOCIAL, TABELA_EQUIVALENCIA,
    TABELA_FATOR_AJUSTE, TABELA_PERCENTUAL_CATEGORIA,
    FATOR_REDUCAO_COMPLEMENTAR_COBERTA, FATOR_REDUCAO_COMPLEMENTAR_DESCOBERTA,
    ALIQUOTA_INSS_ORIGINAL
)
from utils import validar_tipo, validar_categoria, validar_material, arredondar


def obter_pmo(tipo: str, material: str) -> float:
    """
    Obtém o Percentual de Mão de Obra (PMO) da tabela

    Args:
        tipo: Tipo da construção
        material: Material predominante

    Returns:
        Percentual de mão de obra (ex: 0.20 para 20%)

    Raises:
        ValueError: Se a combinação não existir na tabela
    """
    tipo = validar_tipo(tipo)
    material = validar_material(material)

    chave = (tipo, material)
    if chave not in TABELA_PMO:
        raise ValueError(
            f"Combinação tipo='{tipo}' e material='{material}' "
            f"não encontrada na tabela PMO"
        )

    return TABELA_PMO[chave]


def obter_fator_social(area_total: float) -> float:
    """
    Obtém o Fator Social baseado na área total do projeto

    Args:
        area_total: Área total em m²

    Returns:
        Fator social (ex: 0.40 para área entre 100-200 m²)

    Raises:
        ValueError: Se a área for inválida ou não encontrada
    """
    if area_total <= 0:
        raise ValueError(f"Área total deve ser positiva: {area_total}")

    # Formato v1: (area_maxima, fator)
    # A área é comparada com area_maxima, retorna o fator da primeira faixa que a área cabe
    for area_max, fator in TABELA_FATOR_SOCIAL:
        if area_total <= area_max:
            return fator

    raise ValueError(f"Área total {area_total} fora dos limites da tabela")


def obter_percentual_equivalencia(tipo: str, area_m2: float) -> float:
    """
    Obtém o percentual de equivalência baseado no tipo e área

    Args:
        tipo: Tipo da construção
        area_m2: Área em m²

    Returns:
        Percentual de equivalência (ex: 0.89 para 89%)

    Raises:
        ValueError: Se tipo não existir na tabela
    """
    tipo = validar_tipo(tipo)

    if tipo not in TABELA_EQUIVALENCIA:
        raise ValueError(f"Tipo '{tipo}' não encontrado na tabela de equivalência")

    # Formato v1: [(area_maxima, percentual), ...]
    # A área é comparada com area_maxima, retorna o percentual da primeira faixa que a área cabe
    faixas = TABELA_EQUIVALENCIA[tipo]
    for area_max, percentual in faixas:
        if area_m2 <= area_max:
            return percentual

    raise ValueError(
        f"Área {area_m2} m² fora dos limites da tabela para tipo '{tipo}'"
    )


def obter_fator_ajuste(area_total: float) -> float:
    """
    Obtém o Fator de Ajuste baseado na área total do projeto

    Args:
        area_total: Área total em m²

    Returns:
        Fator de ajuste (ex: 0.50 para área <= 350 m²)

    Raises:
        ValueError: Se a área for inválida ou não encontrada
    """
    if area_total <= 0:
        return 0.50  # Mínimo

    # Formato v1: (area_maxima, fator)
    # A área é comparada com area_maxima, retorna o fator da primeira faixa que a área cabe
    for area_max, fator in TABELA_FATOR_AJUSTE:
        if area_total <= area_max:
            return fator

    raise ValueError(f"Área total {area_total} fora dos limites da tabela")


def obter_percentual_categoria(categoria: str) -> float:
    """
    Obtém o percentual da categoria de obra

    Args:
        categoria: Categoria da obra

    Returns:
        Percentual da categoria (ex: 1.00 para obra_nova, 0.35 para reforma)

    Raises:
        ValueError: Se categoria não existir
    """
    categoria = validar_categoria(categoria)

    if categoria not in TABELA_PERCENTUAL_CATEGORIA:
        raise ValueError(
            f"Categoria '{categoria}' não encontrada na tabela de percentuais"
        )

    return TABELA_PERCENTUAL_CATEGORIA[categoria]


def carregar_percentuais_usinados() -> dict:
    """
    Carrega percentuais de usinados do CSV

    Returns:
        Dicionário com (UF, tipo) -> percentual
        Exemplo: ('CE', 'unifamiliar') -> 0.0572

    Raises:
        FileNotFoundError: Se arquivo não encontrado
    """
    import csv
    import os

    # Mapeia nomes das colunas para tipos internos
    MAPA_COLUNAS = {
        'Residencial unifamiliar': 'unifamiliar',
        'Residencial multifamiliar': 'multifamiliar',
        'Projeto de interesse social': 'casa_popular',
        'Comercial salas e lojas': 'comercial',
        'Galpão industrial': 'galpao'
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_csv = os.path.join(base_dir, 'usinados.csv')

    percentuais = {}

    with open(arquivo_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uf = row['UF'].strip()
            for col_excel, tipo_interno in MAPA_COLUNAS.items():
                if col_excel in row:
                    val_str = row[col_excel].strip().replace('%', '').replace(',', '.')
                    if val_str:
                        percentuais[(uf, tipo_interno)] = float(val_str) / 100

    return percentuais


def obter_vau(estado: str, tipo: str, vau_dict: dict, usado_concreto_usinado: bool = False) -> float:
    """
    Obtém o Valor de Aferição Unitária (VAU) para o estado e tipo

    Args:
        estado: Sigla do estado (UF)
        tipo: Tipo da construção
        vau_dict: Dicionário de VAU carregado
        usado_concreto_usinado: Se foi usado concreto usinado

    Returns:
        VAU em R$/m²

    Raises:
        ValueError: Se estado/tipo não encontrado
    """
    tipo = validar_tipo(tipo)
    chave = (estado, tipo)

    if chave not in vau_dict:
        raise ValueError(
            f"VAU não encontrado para estado='{estado}' e tipo='{tipo}'\n"
            f"Verifique se o arquivo vau.csv está atualizado."
        )

    vau_base = vau_dict[chave]

    # Nota: Concreto usinado NÃO altera o VAU
    # O ajuste de concreto usinado é aplicado no PMO (redução de 10%)

    return vau_base


def calcular_area(
    area: AreaConstrucao,
    vau: float,
    area_total_categoria: float,
    area_total_sem_existente: float
) -> CalculoArea:
    """
    Calcula os valores para uma área específica da construção

    Args:
        area: Dados da área
        vau: Valor de Aferição Unitária
        area_total_categoria: Área total da categoria (para fator social)
        area_total_sem_existente: Área total exceto existente (para fator de ajuste)

    Returns:
        Cálculo completo da área

    Raises:
        ValueError: Se dados forem inválidos
    """
    # Validações
    tipo = validar_tipo(area.tipo)
    categoria = validar_categoria(area.categoria)
    material = validar_material(area.material)

    if area.area_m2 <= 0:
        raise ValueError(f"Área deve ser positiva: {area.area_m2}")

    # 1. Percentual de equivalência
    # Para áreas principais: usa tabela por tipo e área
    # Para áreas complementares: usa percentuais fixos (50% coberta, 25% descoberta)
    fator_reducao_complementar = 1.0

    if area.is_principal:
        # Área principal: usa tabela de equivalência
        percentual_equiv = obter_percentual_equivalencia(tipo, area.area_m2)
    else:
        # Área complementar: percentual fixo baseado em cobertura
        if area.coberta is None:
            raise ValueError("Área complementar deve especificar se é coberta ou não")

        if area.coberta:
            # Complementar coberta: 50%
            percentual_equiv = FATOR_REDUCAO_COMPLEMENTAR_COBERTA
            fator_reducao_complementar = FATOR_REDUCAO_COMPLEMENTAR_COBERTA
        else:
            # Complementar descoberta: 25%
            percentual_equiv = FATOR_REDUCAO_COMPLEMENTAR_DESCOBERTA
            fator_reducao_complementar = FATOR_REDUCAO_COMPLEMENTAR_DESCOBERTA

    # 2. Área equivalente
    area_equiv = area.area_m2 * percentual_equiv

    # 4. Custo estimado
    custo_estimado = area_equiv * vau

    # Se categoria for 'existente', custo = 0 (não soma no custo total)
    if categoria == 'existente':
        custo_estimado = 0.0

    # 5. PMO (Percentual de Mão de Obra)
    pmo = obter_pmo(tipo, material)

    # 6. Percentual da categoria
    percentual_categoria = obter_percentual_categoria(categoria)

    # 7. Fator Social (usa área da categoria)
    fator_social = obter_fator_social(area_total_categoria)

    # 8. RMT Base
    rmt_base = custo_estimado * pmo * percentual_categoria * fator_social

    # 8.1. Desconto pré-fabricado (se >=40% das notas são pré-fabricadas)
    if area.prefabricado:
        rmt_base = rmt_base * 0.3  # Mantém 30% do valor (70% de desconto)

    # 9. Fator de Ajuste (usa área total sem existente)
    fator_ajuste = obter_fator_ajuste(area_total_sem_existente)

    # 10. RMT Otimizado - PLACEHOLDER
    # O RMT Otimizado real será calculado em distribution.py após aplicação da decadência
    # (RMT Total é primeiro dividido em Decadente/Não Decadente, depois otimizado)
    rmt_otimizado = rmt_base

    return CalculoArea(
        area=area,
        percentual_equivalencia=percentual_equiv,
        area_equivalente=arredondar(area_equiv, 2),
        vau=vau,
        custo_estimado=arredondar(custo_estimado, 2),
        pmo=pmo,
        percentual_categoria=percentual_categoria,
        fator_social=fator_social,
        rmt_base=arredondar(rmt_base, 2),
        fator_ajuste=fator_ajuste,
        rmt_otimizado=arredondar(rmt_otimizado, 2),
        fator_reducao_complementar=fator_reducao_complementar
    )


def calcular_inss_obra(
    areas: List[AreaConstrucao],
    estado: str,
    data_inicio: datetime,
    data_fim: datetime,
    vau_dict: dict,
    usado_concreto_usinado: bool = False,
    obra_finalizada: bool = False,
    data_analise: datetime = None
) -> ResultadoSimulacao:
    """
    Calcula o INSS completo de uma obra com múltiplas áreas

    Args:
        areas: Lista de áreas da construção
        estado: Estado (UF) da obra
        data_inicio: Data de início da obra
        data_fim: Data de término da obra
        vau_dict: Dicionário de VAU carregado
        usado_concreto_usinado: Se foi usado concreto usinado
        obra_finalizada: Se True, todos os meses têm multa/juros/MAED
        data_analise: Data de análise (default: data atual)

    Returns:
        Resultado completo da simulação

    Raises:
        ValueError: Se dados forem inválidos
    """
    from collections import defaultdict

    if not areas:
        raise ValueError("Lista de áreas não pode estar vazia")

    if data_inicio >= data_fim:
        raise ValueError("Data de início deve ser anterior à data de término")

    if data_analise is None:
        data_analise = datetime.now()

    # 1. Calcular área total do projeto (excluindo existente para fator de ajuste)
    area_total_sem_existente = sum(a.area_m2 for a in areas if a.categoria != 'existente')

    # 2. Agrupar áreas por categoria
    areas_por_categoria = defaultdict(list)
    for area in areas:
        areas_por_categoria[area.categoria].append(area)

    # 2.1. Calcular área total existente (para somar no fator social de outras categorias)
    area_total_existente = sum(a.area_m2 for a in areas_por_categoria['existente'])

    # 3. Calcular cada área individualmente
    calculos_areas = []
    for area in areas:
        # Obter VAU específico para o tipo da área
        vau = obter_vau(estado, area.tipo, vau_dict, usado_concreto_usinado)

        # Calcular área total da mesma categoria (para fator social)
        area_total_categoria = sum(a.area_m2 for a in areas_por_categoria[area.categoria])

        # Calcular área
        calculo = calcular_area(area, vau, area_total_categoria, area_total_sem_existente)
        calculos_areas.append(calculo)

    # 4. Totalizar resultados
    custo_total = sum(c.custo_estimado for c in calculos_areas)
    rmt_total = sum(c.rmt_base for c in calculos_areas)
    rmt_otimizado_total = sum(c.rmt_otimizado for c in calculos_areas)

    # 4.1. Calcular RMT Total ORIGINAL (sem desconto pré-fabricado) para cálculo de usinados
    # Precisamos recalcular o RMT de cada área SEM o desconto pré-fabricado
    rmt_total_original = 0.0
    for calculo in calculos_areas:
        rmt_base_original = calculo.rmt_base
        # Se a área tem prefabricado, o rmt_base já está reduzido a 30% do original
        # Precisamos reverter: rmt_base / 0.3 = rmt_original
        if calculo.area.prefabricado:
            rmt_base_original = calculo.rmt_base / 0.3
        rmt_total_original += rmt_base_original

    # 5. Calcular RMT após Usinados (Cenário Intermediário)
    # A base de cálculo do cenário 2 deve ser (RMT Original - Desconto Usinado) * Fator Prefab
    rmt_apos_usinados = 0.0
    percentuais_usinados = {}
    if usado_concreto_usinado:
        try:
            percentuais_usinados = carregar_percentuais_usinados()
        except FileNotFoundError:
            pass

    for calculo in calculos_areas:
        area = calculo.area
        vau_atual = vau_dict.get((estado, area.tipo), 0.0)
        
        # 1. RMT Original da área (sem nenhum desconto)
        rmt_original_area = calculo.area_equivalente * vau_atual * calculo.pmo * calculo.percentual_categoria * calculo.fator_social
        
        # 2. Desconto Usinado (sempre baseado no VAU atual)
        desconto_area = 0.0
        if usado_concreto_usinado and area.categoria != 'existente':
            chave = (estado, area.tipo)
            if chave in percentuais_usinados:
                percentual_usinado = percentuais_usinados[chave]
                # Desconto = 5% × % usinado × custo estimado × % categoria
                desconto_area = 0.05 * percentual_usinado * calculo.custo_estimado * calculo.percentual_categoria
        
        # 3. RMT Intermediário = (Original - Usinado) * Fator Prefab
        fator_prefab = 0.3 if area.prefabricado else 1.0
        rmt_area_inter = (rmt_original_area - desconto_area) * fator_prefab
        rmt_apos_usinados += rmt_area_inter

    # 5.2. Calcular INSS sem otimização (36.8% do RMT após Usinados)
    inss_original_calculado = rmt_apos_usinados * ALIQUOTA_INSS_ORIGINAL

    # 6. Nota: Distribuição mensal e cálculo de INSS otimizado
    # será feito pelo módulo distribution.py
    # Por enquanto, retornamos valores placeholder
    calculos_mensais = []  # Será preenchido por distribution.py

    return ResultadoSimulacao(
        calculos_areas=calculos_areas,
        custo_total=arredondar(custo_total, 2),
        rmt_total=arredondar(rmt_total, 2),
        rmt_otimizado_total=arredondar(rmt_otimizado_total, 2),
        rmt_otimizado_final=arredondar(rmt_otimizado_total, 2),  # Placeholder
        inss_original=arredondar(inss_original_calculado, 2),
        inss_pouca_otimizacao=0.0,  # Placeholder (será calculado em distribution.py)
        inss_otimizado=0.0,  # Placeholder
        economia=0.0,  # Placeholder
        percentual_economia=0.0,  # Placeholder
        calculos_mensais=calculos_mensais,
        rmt_apos_usinados=arredondar(rmt_apos_usinados, 2),
        rmt_apos_usinados_nao_decadente=0.0, # Placeholder
        usado_concreto_usinado=usado_concreto_usinado,
        estado=estado,
        data_inicio=data_inicio,
        data_fim=data_fim,
        data_analise=data_analise,
        obra_finalizada=obra_finalizada
    )
