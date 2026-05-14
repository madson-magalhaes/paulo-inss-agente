"""
Funções utilitárias e auxiliares

Este módulo contém funções helper para formatação, validação,
arredondamento e outras operações auxiliares.
"""

import re
from datetime import datetime
from typing import Tuple
from constants import (
    TIPOS_VALIDOS, CATEGORIAS_VALIDAS, MATERIAIS_VALIDOS,
    MAPEAMENTO_CATEGORIAS
)


def arredondar(valor: float, casas: int = 2) -> float:
    """
    Arredonda um valor para o número especificado de casas decimais

    Args:
        valor: Valor a ser arredondado
        casas: Número de casas decimais (padrão: 2)

    Returns:
        Valor arredondado
    """
    return round(valor, casas)


def limpar_valor_numerico(valor_str: str) -> float:
    """
    Converte uma string com formatação para float

    Remove separadores de milhar e converte vírgula decimal para ponto.
    Suporta formatos como: 1.234,56 ou 1'234.56 ou 1234.56

    Args:
        valor_str: String com valor formatado

    Returns:
        Valor como float

    Examples:
        >>> limpar_valor_numerico("1.234,56")
        1234.56
        >>> limpar_valor_numerico("1'234.56")
        1234.56
    """
    # Remove espaços
    valor_str = valor_str.strip()

    # Remove apóstrofos (separador de milhar usado pela Receita)
    valor_str = valor_str.replace("'", "")

    # Detecta se usa vírgula como decimal (padrão brasileiro)
    if ',' in valor_str:
        # Remove pontos (separador de milhar) e troca vírgula por ponto
        valor_str = valor_str.replace('.', '').replace(',', '.')
    # Se não tem vírgula, assume ponto como decimal e remove vírgulas (se houver)
    else:
        # Remove vírgulas que podem ser separadores de milhar
        valor_str = valor_str.replace(',', '')

    return float(valor_str)


def formatar_valor(valor: float) -> str:
    """
    Formata um valor monetário para exibição

    Args:
        valor: Valor numérico

    Returns:
        String formatada como "R$ 1.234,56"
    """
    if valor == 0:
        return "R$ 0,00"

    # Formata com separador de milhar e vírgula decimal
    valor_str = f"{valor:,.2f}"

    # Troca vírgula por ponto (milhar) e ponto por vírgula (decimal)
    valor_str = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')

    return f"R$ {valor_str}"


def formatar_valor_export(valor: float) -> str:
    """
    Formata um valor monetário para exportação (padrão internacional)

    Args:
        valor: Valor numérico

    Returns:
        String formatada como "1234.56" (sem separador de milhar, ponto decimal)

    Examples:
        >>> formatar_valor_export(1234.56)
        '1234.56'
        >>> formatar_valor_export(1234567.89)
        '1234567.89'
    """
    return f"{valor:.2f}"


def formatar_percentual(valor: float, casas: int = 1) -> str:
    """
    Formata um percentual para exibição

    Args:
        valor: Valor percentual (ex: 23.5 para 23.5%)
        casas: Casas decimais (padrão: 1)

    Returns:
        String formatada como "23.5%"
    """
    return f"{valor:.{casas}f}%"


def formatar_percentual_export(valor: float, casas: int = 2) -> str:
    """
    Formata um percentual para exportação (padrão internacional)

    Args:
        valor: Valor percentual (ex: 23.5 para 23.5%)
        casas: Casas decimais (padrão: 2)

    Returns:
        String formatada como "23.50" (sem símbolo %, ponto decimal)

    Examples:
        >>> formatar_percentual_export(23.5)
        '23.50'
        >>> formatar_percentual_export(0.89, 4)
        '0.8900'
    """
    return f"{valor:.{casas}f}"


def validar_tipo(tipo: str) -> str:
    """
    Valida e normaliza um tipo de construção

    Args:
        tipo: Tipo a ser validado

    Returns:
        Tipo normalizado (minúsculas)

    Raises:
        ValueError: Se o tipo for inválido
    """
    tipo_lower = tipo.lower()

    if tipo_lower not in TIPOS_VALIDOS:
        tipos_str = ', '.join(sorted(TIPOS_VALIDOS))
        raise ValueError(
            f"Tipo '{tipo}' não reconhecido. "
            f"Tipos válidos: {tipos_str}"
        )

    return tipo_lower


def validar_categoria(categoria: str) -> str:
    """
    Valida e normaliza uma categoria de obra

    Args:
        categoria: Categoria a ser validada

    Returns:
        Categoria normalizada

    Raises:
        ValueError: Se a categoria for inválida
    """
    categoria_lower = categoria.lower()

    # Verifica mapeamento de nomes alternativos
    if categoria_lower in MAPEAMENTO_CATEGORIAS:
        categoria_lower = MAPEAMENTO_CATEGORIAS[categoria_lower]

    if categoria_lower not in CATEGORIAS_VALIDAS:
        categorias_str = ', '.join(sorted(CATEGORIAS_VALIDAS))
        raise ValueError(
            f"Categoria '{categoria}' não reconhecida. "
            f"Categorias válidas: {categorias_str}"
        )

    return categoria_lower


def validar_material(material: str) -> str:
    """
    Valida e normaliza um material de construção

    Args:
        material: Material a ser validado

    Returns:
        Material normalizado (minúsculas)

    Raises:
        ValueError: Se o material for inválido
    """
    material_lower = material.lower()

    if material_lower not in MATERIAIS_VALIDOS:
        materiais_str = ', '.join(sorted(MATERIAIS_VALIDOS))
        raise ValueError(
            f"Material '{material}' não reconhecido. "
            f"Materiais válidos: {materiais_str}"
        )

    return material_lower


def calcular_meses_entre_datas(data_inicio: datetime, data_fim: datetime) -> int:
    """
    Calcula o número de meses entre duas datas (inclusivo)

    Args:
        data_inicio: Data inicial
        data_fim: Data final

    Returns:
        Número de meses (mínimo 1)
    """
    meses = (data_fim.year - data_inicio.year) * 12 + (data_fim.month - data_inicio.month) + 1
    return max(1, meses)


def mes_ano_is_decadente(mes: int, ano: int) -> bool:
    """
    Verifica se um mês/ano é considerado decadente

    Meses decadentes são aqueles até e incluindo Dezembro/2020.
    Estes meses não recebem recibos e são descontados do RMT Total
    como benefício fiscal.

    Args:
        mes: Mês (1-12)
        ano: Ano (ex: 2020, 2021)

    Returns:
        True se o mês é decadente (antes ou igual a Dez/2020), False caso contrário

    Examples:
        >>> mes_ano_is_decadente(12, 2020)
        True
        >>> mes_ano_is_decadente(1, 2021)
        False
        >>> mes_ano_is_decadente(6, 2019)
        True
    """
    from constants import DATA_LIMITE_DECADENCIA

    # Cria data do primeiro dia do mês
    data_mes = datetime(ano, mes, 1)

    # Verifica se é antes ou igual ao limite de decadência
    return data_mes <= DATA_LIMITE_DECADENCIA


def parse_mes_ano(mes_ano_str: str) -> Tuple[int, int]:
    """
    Converte string "Mês/Ano" para tupla (mês, ano)

    Aceita múltiplos formatos:
    - Inglês: "Jan/24", "May/2026"
    - Português: "Mai/24", "Maio/26", "Jan/24"
    - Numérico: "01/24", "5/2026", "05/26"

    Args:
        mes_ano_str: String no formato "Mês/Ano"

    Returns:
        Tupla (mês, ano)

    Examples:
        >>> parse_mes_ano("Jan/24")
        (1, 2024)
        >>> parse_mes_ano("12/2024")
        (12, 2024)
        >>> parse_mes_ano("mai/26")
        (5, 2026)
        >>> parse_mes_ano("05/26")
        (5, 2026)
    """
    meses_nomes = {
        'jan': 1, 'janeiro': 1,
        'feb': 2, 'fev': 2, 'fevereiro': 2,
        'mar': 3, 'março': 3, 'marco': 3,
        'apr': 4, 'abr': 4, 'abril': 4,
        'may': 5, 'mai': 5, 'maio': 5,
        'jun': 6, 'junho': 6,
        'jul': 7, 'julho': 7,
        'aug': 8, 'ago': 8, 'agosto': 8,
        'sep': 9, 'set': 9, 'setembro': 9,
        'oct': 10, 'out': 10, 'outubro': 10,
        'nov': 11, 'novembro': 11,
        'dec': 12, 'dez': 12, 'dezembro': 12
    }

    partes = mes_ano_str.strip().split('/')
    if len(partes) != 2:
        raise ValueError(f"Formato inválido: {mes_ano_str}. Use 'Mês/Ano'")

    mes_str = partes[0].strip()
    ano_str = partes[1].strip()

    # Tenta converter o primeiro elemento como número
    try:
        mes = int(mes_str)
        if not (1 <= mes <= 12):
            raise ValueError(f"Mês fora do intervalo 1-12: {mes}")
    except ValueError:
        # Se não for número, tenta como nome de mês
        mes_lower = mes_str.lower()
        mes = meses_nomes.get(mes_lower)
        if mes is None:
            raise ValueError(f"Mês não reconhecido: {mes_str}")

    # Converte ano (completa se for formato curto)
    try:
        ano = int(ano_str)
        if ano < 100:
            ano += 2000
    except ValueError:
        raise ValueError(f"Ano inválido: {ano_str}")

    return (mes, ano)


def parse_data_ddmmyyyy(data_str: str) -> datetime:
    """
    Converte string DD/MM/YYYY ou DD/MM/YY para datetime

    Args:
        data_str: String no formato "01/03/2024" ou "01/03/24"

    Returns:
        Objeto datetime

    Raises:
        ValueError: Se a data for inválida
    """
    try:
        # Tenta formato completo primeiro
        return datetime.strptime(data_str, '%d/%m/%Y')
    except ValueError:
        try:
            # Tenta formato curto (ano com 2 dígitos)
            return datetime.strptime(data_str, '%d/%m/%y')
        except ValueError:
            raise ValueError(f"Data inválida: {data_str}. Use o formato DD/MM/YYYY ou DD/MM/YY")


def parse_boolean(valor: str) -> bool:
    """
    Converte string para boolean

    Args:
        valor: String como "sim", "yes", "true", "1", etc.

    Returns:
        Boolean correspondente

    Examples:
        >>> parse_boolean("sim")
        True
        >>> parse_boolean("no")
        False
    """
    valor_lower = valor.lower().strip()

    if valor_lower in ('sim', 'yes', 'true', '1', 's', 'y'):
        return True
    elif valor_lower in ('não', 'nao', 'no', 'false', '0', 'n'):
        return False
    else:
        raise ValueError(f"Valor booleano inválido: {valor}")


def normalizar_mes_ano(mes_ano_str: str) -> str:
    """
    Normaliza diferentes formatos de mês/ano para formato padrão "Mmm/YY"

    Aceita múltiplos formatos:
    - Inglês: "May/26", "May/2026"
    - Português: "Mai/26", "Maio/26"
    - Numérico: "05/26", "5/26", "05/2026"

    Retorna sempre no formato: "Mmm/YY" (ex: "May/26", "Jan/24")

    Args:
        mes_ano_str: String com mês/ano em qualquer formato aceito

    Returns:
        String normalizada no formato "Mmm/YY"

    Raises:
        ValueError: Se o formato for inválido

    Examples:
        >>> normalizar_mes_ano("May/26")
        'May/26'
        >>> normalizar_mes_ano("mai/26")
        'May/26'
        >>> normalizar_mes_ano("05/26")
        'May/26'
        >>> normalizar_mes_ano("5/2026")
        'May/26'
    """
    meses_pt_en = {
        'jan': 'Jan', 'janeiro': 'Jan',
        'feb': 'Feb', 'fev': 'Feb', 'fevereiro': 'Feb',
        'mar': 'Mar', 'março': 'Mar', 'marco': 'Mar',
        'apr': 'Apr', 'abr': 'Apr', 'abril': 'Apr',
        'may': 'May', 'mai': 'May', 'maio': 'May',
        'jun': 'Jun', 'junho': 'Jun',
        'jul': 'Jul', 'julho': 'Jul',
        'aug': 'Aug', 'ago': 'Aug', 'agosto': 'Aug',
        'sep': 'Sep', 'set': 'Sep', 'setembro': 'Sep',
        'oct': 'Oct', 'out': 'Oct', 'outubro': 'Oct',
        'nov': 'Nov', 'novembro': 'Nov',
        'dec': 'Dec', 'dez': 'Dec', 'dezembro': 'Dec'
    }

    try:
        partes = mes_ano_str.strip().split('/')
        if len(partes) != 2:
            raise ValueError("Formato inválido")

        mes_str = partes[0].strip()
        ano_str = partes[1].strip()

        # Tenta converter mês como número
        try:
            mes_num = int(mes_str)
            if not (1 <= mes_num <= 12):
                raise ValueError("Mês fora do intervalo 1-12")
            mes_abrev = list(meses_pt_en.keys())[mes_num - 1:mes_num]
            mes_resultado = meses_pt_en[mes_abrev[0]] if mes_abrev else None
            if not mes_resultado:
                raise ValueError("Mês inválido")
        except ValueError:
            # Se não é número, trata como nome de mês
            mes_lower = mes_str.lower()
            mes_resultado = meses_pt_en.get(mes_lower)
            if not mes_resultado:
                raise ValueError(f"Mês não reconhecido: {mes_str}")

        # Normaliza ano (sempre retorna 2 dígitos)
        ano_num = int(ano_str)
        if ano_num > 100:
            ano_num = ano_num % 100
        ano_resultado = f"{ano_num:02d}"

        return f"{mes_resultado}/{ano_resultado}"

    except Exception as e:
        raise ValueError(f"Erro ao normalizar mês/ano '{mes_ano_str}': {str(e)}")
