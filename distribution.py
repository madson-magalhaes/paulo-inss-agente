"""
Funções de distribuição mensal do INSS

Este módulo contém a lógica de distribuição mensal dos valores de INSS,
incluindo cálculo de ICM, CPP, multa, mora e MAED para obras finalizadas
e obras em andamento.
"""

from typing import List, Dict, Set
from datetime import datetime
from models import CalculoMensal, ResultadoSimulacao, InformacoesReceitaFederal
from constants import ALIQUOTA_CPP, ALIQUOTA_MULTA, MAED_FIXO, ALIQUOTA_INSS_ORIGINAL
from utils import calcular_meses_entre_datas, arredondar


def calcular_resumo_receita_federal(
    calculos_mensais: List[CalculoMensal],
    data_atual: datetime
) -> InformacoesReceitaFederal:
    """
    Calcula informações sobre pagamentos à Receita Federal para o resumo geral

    Regra do dia 20:
    - Temos até dia 20 do mês seguinte para pagar o INSS do mês anterior
    - Se hoje é ANTES do dia 20: Mês atual para DARF = mês ANTERIOR
    - Se hoje é dia 20 ou DEPOIS: Mês atual para DARF = mês ATUAL

    Args:
        calculos_mensais: Lista de meses da distribuição
        data_atual: Data atual para determinar atrasos

    Returns:
        InformacoesReceitaFederal com as informações calculadas
    """
    info = InformacoesReceitaFederal()

    ano_atual = data_atual.year
    mes_atual = data_atual.month
    dia_atual = data_atual.day

    # Determinar qual é o mês atual para fins de DARF
    if dia_atual < 20:
        mes_darf_atual = mes_atual - 1
        ano_darf_atual = ano_atual
        if mes_darf_atual < 1:
            mes_darf_atual = 12
            ano_darf_atual -= 1
    else:
        mes_darf_atual = mes_atual
        ano_darf_atual = ano_atual

    meses_atrasados = []
    mes_darf_atual_obj = None
    meses_futuros = []

    for m in calculos_mensais:
        # Pula meses com total zerado
        if m.inss_total <= 0:
            continue

        # Classificar comparando (ano, mes) com (ano_darf_atual, mes_darf_atual)
        if (m.ano < ano_darf_atual) or (m.ano == ano_darf_atual and m.mes < mes_darf_atual):
            # Atrasado
            meses_atrasados.append(m)
        elif m.ano == ano_darf_atual and m.mes == mes_darf_atual:
            # Mês atual
            mes_darf_atual_obj = m
        else:
            # Futuro
            meses_futuros.append(m)

    # Calcula DARFs atrasadas
    info.darfs_atrasadas = sum(m.inss_total for m in meses_atrasados)
    info.soma_maed_atrasadas = sum(m.maed for m in meses_atrasados)

    # Calcula DARF do mês atual
    if mes_darf_atual_obj:
        info.darf_mes_atual = mes_darf_atual_obj.inss_total

    # Calcula DARFs futuras
    if len(meses_futuros) > 0:
        info.darfs_futuras_total = sum(m.inss_total for m in meses_futuros)
        info.qtd_meses_futuros = len(meses_futuros)
        info.darfs_futuras_media = info.darfs_futuras_total / len(meses_futuros)

        # Primeira e última DARF futura (paga no mês seguinte ao mês da obra)
        p_mes = meses_futuros[0]
        u_mes = meses_futuros[-1]

        # Primeira
        m_p = p_mes.mes + 1
        a_p = p_mes.ano
        if m_p > 12:
            m_p = 1
            a_p += 1
        info.primeira_darf_futura = f"{m_p:02d}/{str(a_p)[-2:]}"

        # Última
        m_u = u_mes.mes + 1
        a_u = u_mes.ano
        if m_u > 12:
            m_u = 1
            a_u += 1
        info.ultima_darf_futura = f"{m_u:02d}/{str(a_u)[-2:]}"

    # Multa parcelamento (20% das MAEDs atrasadas)
    info.multa_parcelamento = info.soma_maed_atrasadas * 0.20

    # Condições de pagamento
    info.pagamento_vista = info.darfs_atrasadas
    info.pagamento_parcelado_total = info.darfs_atrasadas + info.multa_parcelamento

    # Parcelas (mínimo R$ 200, máximo 60 meses)
    P_MIN = 200.0
    P_MAX = 60
    if info.pagamento_parcelado_total > 0:
        qtd = int(info.pagamento_parcelado_total / P_MIN)
        if qtd < 1: qtd = 1
        if qtd > P_MAX: qtd = P_MAX
        val = info.pagamento_parcelado_total / qtd
        while val < P_MIN and qtd > 1:
            qtd -= 1
            val = info.pagamento_parcelado_total / qtd
        info.qtd_parcelas_sugerida = qtd
        info.valor_parcela = val

    return info


def carregar_icm_csv(arquivo_csv: str = 'icm.csv') -> Dict[tuple, float]:
    """
    Carrega os índices ICM do arquivo CSV

    Args:
        arquivo_csv: Caminho para o arquivo ICM

    Returns:
        Dicionário com (mes, ano) -> ICM percentual

    Raises:
        FileNotFoundError: Se arquivo não existir
        ValueError: Se formato for inválido
    """
    import csv
    from utils import parse_mes_ano, limpar_valor_numerico

    icm_dict = {}

    try:
        with open(arquivo_csv, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
            reader = csv.DictReader(f)

            for row in reader:
                mes_ano_str = row['Mês/Ano'].strip()
                percentual_str = row['%'].strip()

                # Parse mês/ano
                mes, ano = parse_mes_ano(mes_ano_str)

                # Remove o símbolo de % e converte para float
                percentual_str = percentual_str.replace('%', '').strip()
                icm_percentual = limpar_valor_numerico(percentual_str) / 100

                icm_dict[(mes, ano)] = icm_percentual

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Arquivo ICM não encontrado: {arquivo_csv}\n"
            f"Certifique-se de que o arquivo existe no diretório correto."
        )
    except Exception as e:
        raise ValueError(f"Erro ao ler arquivo ICM: {str(e)}")

    return icm_dict


def obter_icm(mes: int, ano: int, icm_dict: Dict[tuple, float]) -> float:
    """
    Obtém o ICM para um mês/ano específico

    Args:
        mes: Mês (1-12)
        ano: Ano (ex: 2024)
        icm_dict: Dicionário de ICM carregado

    Returns:
        ICM como percentual (ex: 0.2352 para 23.52%)

    Raises:
        ValueError: Se mês/ano não encontrado
    """
    chave = (mes, ano)

    if chave not in icm_dict:
        # Se for mês atual ou futuro, ICM é zero (não há juros/multa ainda)
        agora = datetime.now()
        if (ano > agora.year) or (ano == agora.year and mes >= agora.month):
            return 0.0

        raise ValueError(
            f"ICM não encontrado para {mes:02d}/{ano}\n"
            f"Verifique se o arquivo icm.csv está atualizado."
        )

    return icm_dict[chave]


def carregar_paralisacao_csv(arquivo_csv: str = 'paralisacao.csv') -> Set[tuple]:
    """
    Carrega meses paralisados do arquivo CSV

    O arquivo deve conter uma coluna "Mês/Ano" com cada mês paralisado.
    Meses paralisados não recebem recibos e não contam para distribuição.

    Args:
        arquivo_csv: Caminho para o arquivo de paralisação

    Returns:
        Set de tuplas (mes, ano) com meses paralisados
    """
    import csv
    from utils import parse_mes_ano

    paralisados = set()

    try:
        with open(arquivo_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                mes_ano_str = row['Mês/Ano'].strip()

                # Parse mês/ano
                mes, ano = parse_mes_ano(mes_ano_str)

                # Adiciona ao set
                paralisados.add((mes, ano))

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Arquivo de paralisação não encontrado: {arquivo_csv}\n"
            f"Certifique-se de que o arquivo existe no diretório correto."
        )
    except Exception as e:
        raise ValueError(f"Erro ao ler arquivo de paralisação: {str(e)}")

    return paralisados


def calcular_mora(cpp: float, icm_percentual: float) -> float:
    """
    Calcula juros de mora (Selic)

    Args:
        cpp: Valor da CPP
        icm_percentual: ICM em percentual (ex: 0.2352 para 23.52%)

    Returns:
        Valor dos juros
    """
    return cpp * icm_percentual


def ajustar_vau_por_data(
    vau_base: float,
    data_analise: datetime,
    data_fim: datetime,
    obra_finalizada: bool
) -> float:
    """
    Ajusta o VAU baseado na data de análise

    Para obra em andamento:
        - Sempre adiciona R$20 por mês futuro (do mês atual até o último)
        - MAIS R$20 adicional se dia > 20
    Para obra finalizada:
        - Adiciona R$20 se dia > 20

    Args:
        vau_base: VAU original
        data_analise: Data de análise
        data_fim: Data de término da obra
        obra_finalizada: Se a obra está finalizada

    Returns:
        VAU ajustado
    """
    if obra_finalizada:
        # Obra finalizada: ajuste baseado no dia da análise
        if data_analise.day > 20:
            return vau_base + 20.00
        return vau_base
    else:
        # Obra em andamento: dois acréscimos
        # 1. Acréscimo por meses restantes (sempre aplica)
        meses_restantes = calcular_meses_entre_datas(data_analise, data_fim)
        meses_futuros = max(0, meses_restantes)
        acrescimo_meses = 20.00 * meses_futuros

        # 2. Acréscimo adicional se dia > 20
        acrescimo_dia = 20.00 if data_analise.day > 20 else 0.00

        return vau_base + acrescimo_meses + acrescimo_dia


def distribuir_mensal(
    resultado: ResultadoSimulacao,
    icm_dict: Dict[tuple, float],
    paralisacao_set: Set[tuple] = None
) -> ResultadoSimulacao:
    """
    Distribui o RMT otimizado ao longo dos meses da obra

    Considera meses paralisados, decadentes e a regra Jan/21-Set/21
    para determinar quais meses recebem recibos.

    Args:
        resultado: Resultado com RMT otimizado calculado
        icm_dict: Dicionário de ICM carregado
        paralisacao_set: Set de tuplas (mes, ano) com meses paralisados (opcional)

    Returns:
        Resultado com calculos_mensais preenchido e inss_otimizado calculado

    Raises:
        ValueError: Se dados forem inválidos
    """
    if resultado.data_inicio is None or resultado.data_fim is None:
        raise ValueError("Datas de início e fim são obrigatórias")

    if resultado.data_analise is None:
        resultado.data_analise = datetime.now()

    # Determina se obra está finalizada
    data_atual = datetime.now()
    obra_finalizada = resultado.data_fim < data_atual

    # Calcula total de meses
    total_meses = calcular_meses_entre_datas(resultado.data_inicio, resultado.data_fim)

    # NOTA: RMT Otimizado Final será calculado APÓS decadência e recálculo de RMT Otimizado
    # (movido para depois do cálculo de decadência)

    # ============================================================================
    # CONTAGEM DE MESES DECADENTES E CÁLCULO DE RMT NÃO DECADENTE
    # ============================================================================
    # Importa constantes e funções necessárias
    from constants import MESES_SEM_RECIBOS
    from utils import mes_ano_is_decadente

    # Inicializa set vazio se paralisacao_set for None
    if paralisacao_set is None:
        paralisacao_set = set()

    # Contadores
    total_meses_decadentes = 0
    total_meses_validos = 0  # Meses não paralisados

    # Percorre todos os meses da obra para contar
    mes_temp = resultado.data_inicio.month
    ano_temp = resultado.data_inicio.year

    for _ in range(total_meses):
        # Verifica se é paralisado
        is_paralisado = (mes_temp, ano_temp) in paralisacao_set

        # Verifica se é decadente
        is_decadente = mes_ano_is_decadente(mes_temp, ano_temp)

        # Conta meses válidos (não paralisados)
        if not is_paralisado:
            total_meses_validos += 1

        # Conta meses decadentes (apenas os não paralisados)
        # Paralisação em decadente: não conta no numerador, mas desconta no denominador
        # Isso aumenta o % decadente e reduz mais o imposto (benefício fiscal)
        if is_decadente and not is_paralisado:
            total_meses_decadentes += 1

        # Avança mês
        mes_temp += 1
        if mes_temp > 12:
            mes_temp = 1
            ano_temp += 1

    # Calcula percentual de decadência
    # % Decadência = Meses Decadentes / Total de Meses Válidos
    percentual_decadencia = total_meses_decadentes / total_meses_validos if total_meses_validos > 0 else 0

    # Calcula RMT Total Decadente e Não Decadente
    # IMPORTANTE: Usa RMT TOTAL (antes de qualquer otimização)
    # Decadência é benefício fiscal: desconta meses até Dez/2020 do cálculo
    rmt_total_decadente = resultado.rmt_total * percentual_decadencia
    rmt_total_nao_decadente = resultado.rmt_total * (1 - percentual_decadencia)

    # Atualiza resultado
    resultado.rmt_total_decadente = arredondar(rmt_total_decadente, 2)
    resultado.rmt_total_nao_decadente = arredondar(rmt_total_nao_decadente, 2)

    # ============================================================================
    # CÁLCULO DE POUCA OTIMIZAÇÃO (Decadência + Usinado)
    # ============================================================================
    # Aplica o percentual de não decadência sobre o RMT após Usinados
    # Isso representa o cenário onde o cliente usa usinado e decadência, mas NÃO usa nossa otimização CPP
    percentual_nao_decadencia = (1 - percentual_decadencia)
    rmt_pos_usinado_nao_decadente = resultado.rmt_apos_usinados * percentual_nao_decadencia
    resultado.rmt_apos_usinados_nao_decadente = arredondar(rmt_pos_usinado_nao_decadente, 2)
    resultado.inss_pouca_otimizacao = arredondar(resultado.rmt_apos_usinados_nao_decadente * ALIQUOTA_INSS_ORIGINAL, 2)

    # ============================================================================
    # RECALCULAR RMT OTIMIZADO (APÓS DECADÊNCIA)
    # ============================================================================
    # Agora que sabemos o RMT Não Decadente, aplicamos fator de ajuste
    # Fator de ajuste é baseado em área total (mesmo para todas as áreas)

    if resultado.calculos_areas:
        # Obtém fator de ajuste do primeiro cálculo (é o mesmo para todos)
        fator_ajuste_global = resultado.calculos_areas[0].fator_ajuste

        # Recalcula RMT Otimizado para cada área proporcionalmente
        proporcao_nao_decadente = (1 - percentual_decadencia)

        for calculo_area in resultado.calculos_areas:
            # RMT Otimizado = RMT Base × (1 - % Decadência) × Fator de Ajuste
            rmt_otimizado_corrigido = calculo_area.rmt_base * proporcao_nao_decadente * fator_ajuste_global
            calculo_area.rmt_otimizado = arredondar(rmt_otimizado_corrigido, 2)

        # Recalcula total otimizado
        rmt_otimizado_total_corrigido = sum(c.rmt_otimizado for c in resultado.calculos_areas)
        resultado.rmt_otimizado_total = arredondar(rmt_otimizado_total_corrigido, 2)

    # ============================================================================
    # AJUSTE DE VAU PREVISTO (RMT OTIMIZADO FINAL)
    # ============================================================================
    # Agora que temos RMT Otimizado (após decadência e fator ajuste), aplicamos VAU previsto
    rmt_otimizado_final_ajustado = 0.0

    for calculo_area in resultado.calculos_areas:
        # VAU original usado no cálculo
        vau_original = calculo_area.vau

        # VAU ajustado pela data (VAU previsto)
        vau_ajustado = ajustar_vau_por_data(
            vau_original,
            resultado.data_analise,
            resultado.data_fim,
            obra_finalizada
        )

        # Fator de ajuste VAU para esta área
        fator_ajuste_vau = vau_ajustado / vau_original if vau_original > 0 else 1.0

        # RMT Otimizado Final = RMT Otimizado × fator ajuste VAU
        rmt_otimizado_final_area = calculo_area.rmt_otimizado * fator_ajuste_vau

        # Soma ao total
        rmt_otimizado_final_ajustado += rmt_otimizado_final_area

    # RMT Otimizado Final = soma dos RMT ajustados por VAU
    resultado.rmt_otimizado_final = arredondar(rmt_otimizado_final_ajustado, 2)

    # ============================================================================
    # DISTRIBUIÇÃO DE RECIBOS (USA RMT OTIMIZADO FINAL COMO BASE)
    # ============================================================================

    # MUDANÇA: Agora o RECIBO é fixo e a REMUNERAÇÃO CORRIGIDA varia com ICM
    # Primeiro, precisamos calcular o recibo fixo que resulta no RMT alvo
    # IMPORTANTE: Usa RMT Otimizado Final (já com decadência, fator ajuste e VAU previsto)
    rmt_alvo = resultado.rmt_otimizado_final

    # Soma total dos fatores (1 + ICM) APENAS de meses válidos
    # Meses válidos = não-decadentes, não-paralisados, não jan-sep/21
    soma_fatores_icm = 0.0
    icms_por_mes = []  # Lista para guardar ICM de cada mês (inclui todos, válidos ou não)

    # Pré-calcula ICMs de todos os meses
    mes_temp = resultado.data_inicio.month
    ano_temp = resultado.data_inicio.year

    for _ in range(total_meses):
        # Verifica se é mês válido para recibo
        is_decadente = mes_ano_is_decadente(mes_temp, ano_temp)
        is_paralisado = (mes_temp, ano_temp) in paralisacao_set
        is_jan_sep_21 = (mes_temp, ano_temp) in MESES_SEM_RECIBOS

        # Obtém ICM (mesmo para meses não válidos, para manter índice correto)
        icm_percentual = obter_icm(mes_temp, ano_temp, icm_dict)
        icms_por_mes.append(icm_percentual)

        if not (is_decadente or is_paralisado or is_jan_sep_21):
            # Acumula (1 + ICM)
            soma_fatores_icm += (1.0 + icm_percentual)

        # Avança para o próximo mês
        mes_temp += 1
        if mes_temp > 12:
            mes_temp = 1
            ano_temp += 1

    # Recibo fixo = RMT Alvo / Soma(1 + ICM)
    recibo_fixo = rmt_alvo / soma_fatores_icm if soma_fatores_icm > 0 else 0.0

    # Agora gera os cálculos mensais
    calculos = []
    mes_corrente = resultado.data_inicio.month
    ano_corrente = resultado.data_inicio.year

    for mes_index in range(total_meses):
        # Verifica condições do mês
        is_decadente = mes_ano_is_decadente(mes_corrente, ano_corrente)
        is_paralisado = (mes_corrente, ano_corrente) in paralisacao_set
        is_jan_sep_21 = (mes_corrente, ano_corrente) in MESES_SEM_RECIBOS

        if is_decadente or is_paralisado or is_jan_sep_21:
            # Obtém ICM (para exibição)
            icm_percentual = icms_por_mes[mes_index]

            # TODOS os valores são ZERO
            recibo_base = 0.0
            remuneracao_corrigida = 0.0
            cpp = 0.0
            multa = 0.0
            mora = 0.0
            maed = 0.0

        else:
            # ========================================================================
            # CÁLCULO DO MÊS (apenas para meses válidos)
            # ========================================================================

            # Obtém ICM
            icm_percentual = icms_por_mes[mes_index]

            # MUDANÇA: Recibo FIXO
            recibo_base = recibo_fixo

            # Remuneração Corrigida = Recibo × (1 + ICM)
            remuneracao_corrigida = recibo_base * (1.0 + icm_percentual)

            # CPP = 20% do Recibo (Base)
            cpp = recibo_base * ALIQUOTA_CPP

            # Determina se o mês já venceu em relação à data de análise
            # Regra: Vencimento no dia 20 do mês seguinte
            mes_vencimento = mes_corrente + 1
            ano_vencimento = ano_corrente
            if mes_vencimento > 12:
                mes_vencimento = 1
                ano_vencimento += 1
            
            data_vencimento = datetime(ano_vencimento, mes_vencimento, 20)
            is_vencido = resultado.data_analise >= data_vencimento

            # Multa = 20% da CPP (apenas se vencido e não decadente)
            multa = (cpp * ALIQUOTA_MULTA) if (is_vencido and not is_decadente) else 0.0

            # Mora = CPP × ICM (apenas se vencido e não decadente)
            mora = calcular_mora(cpp, icm_percentual) if (is_vencido and not is_decadente) else 0.0

            # MAED Fixa (apenas se vencido e houver CPP)
            maed = MAED_FIXO if (is_vencido and cpp > 0) else 0.0

        # Total INSS do mês
        inss_total = cpp + multa + mora + maed

        # Cria objeto de cálculo mensal
        calculo_mensal = CalculoMensal(
            mes=mes_corrente,
            ano=ano_corrente,
            icm_percentual=arredondar(icm_percentual * 100, 2),
            remuneracao=arredondar(recibo_base, 2),
            remuneracao_corrigida=arredondar(remuneracao_corrigida, 2),
            cpp=arredondar(cpp, 2),
            multa=arredondar(multa, 2),
            mora=arredondar(mora, 2),
            maed=arredondar(maed, 2),
            inss_total=arredondar(inss_total, 2)
        )

        calculos.append(calculo_mensal)

        # Avança para o próximo mês
        mes_corrente += 1
        if mes_corrente > 12:
            mes_corrente = 1
            ano_corrente += 1

    # Atualiza resultado
    resultado.calculos_mensais = calculos
    resultado.obra_finalizada = obra_finalizada

    # Calcula INSS otimizado total
    inss_otimizado_total = sum(c.inss_total for c in calculos)
    resultado.inss_otimizado = arredondar(inss_otimizado_total, 2)

    # NOTA: RMT Otimizado Final já foi calculado no início da função (antes da distribuição)
    # para ser usado na distribuição mensal

    # Recalcula economia
    resultado.economia = arredondar(resultado.inss_original - resultado.inss_otimizado, 2)
    resultado.percentual_economia = arredondar(
        (resultado.economia / resultado.inss_original * 100) if resultado.inss_original > 0 else 0,
        2
    )

    # Calcula resumo para Receita Federal (Sessão 8)
    data_analise = resultado.data_analise if resultado.data_analise else datetime.now()
    resultado.info_rf = calcular_resumo_receita_federal(calculos, data_analise)

    return resultado
