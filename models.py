"""
Modelos de dados para o sistema de cálculo de INSS

Este módulo contém todas as classes de dados (dataclasses) usadas no sistema.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class AreaConstrucao:
    """
    Representa uma área específica da construção

    Attributes:
        tipo: Tipo da construção (unifamiliar, multifamiliar, comercial, etc.)
        categoria: Categoria da obra (obra_nova, reforma, demolicao, acrescimo, existente)
        material: Material predominante (alvenaria, madeira, mista, concreto, metalico)
        area_m2: Área em metros quadrados
        is_principal: Se é a área principal da construção
        coberta: Para áreas complementares, se é coberta ou descoberta
        prefabricado: Se a área utiliza material pré-fabricado (>= 40% das NFs)
    """
    tipo: str
    categoria: str
    material: str
    area_m2: float
    is_principal: bool = True
    coberta: Optional[bool] = None
    prefabricado: bool = False


@dataclass
class CalculoArea:
    """
    Resultado do cálculo para uma área específica
    """
    area: AreaConstrucao
    percentual_equivalencia: float
    area_equivalente: float
    vau: float
    custo_estimado: float
    pmo: float
    percentual_categoria: float
    fator_social: float
    rmt_base: float
    fator_ajuste: float
    rmt_otimizado: float
    fator_reducao_complementar: float = 1.0


@dataclass
class CalculoMensal:
    """
    Resultado do cálculo para um mês específico
    """
    mes: int
    ano: int
    icm_percentual: float
    remuneracao: float
    remuneracao_corrigida: float
    cpp: float
    multa: float
    mora: float
    maed: float
    inss_total: float


@dataclass
class InformacoesReceitaFederal:
    """Informações sobre pagamentos à Receita Federal"""
    # DARFs
    darfs_atrasadas: float = 0.0
    darf_mes_atual: float = 0.0
    darfs_futuras_media: float = 0.0
    darfs_futuras_total: float = 0.0
    qtd_meses_futuros: int = 0
    primeira_darf_futura: str = ""  # Formato: MM/AA
    ultima_darf_futura: str = ""  # Formato: MM/AA

    # Composição das atrasadas
    soma_maed_atrasadas: float = 0.0
    multa_parcelamento: float = 0.0  # 20% das MAEDs atrasadas

    # Condições de pagamento
    pagamento_vista: float = 0.0  # Só DARFs atrasadas
    pagamento_parcelado_total: float = 0.0  # DARFs atrasadas + multa 20%
    qtd_parcelas_sugerida: int = 0
    valor_parcela: float = 0.0


@dataclass
class ResultadoSimulacao:
    """
    Resultado completo da simulação de INSS

    Attributes:
        calculos_areas: Lista de cálculos por área
        custo_total: Custo total estimado da obra
        rmt_total: RMT total (soma de todas as áreas)
        rmt_total_decadente: RMT correspondente a meses decadentes (até Dez/2020)
        rmt_total_nao_decadente: RMT efetivo após desconto de decadência
        rmt_apos_usinados: RMT após desconto de concreto usinado (se aplicável)
        rmt_otimizado_total: RMT otimizado total (sem ajuste de VAU previsto)
        rmt_otimizado_final: RMT otimizado final (com ajuste de VAU previsto)
        usado_concreto_usinado: Se foi usado concreto usinado
        inss_original: INSS sem otimização
        inss_otimizado: INSS com otimização
        economia: Economia gerada
        percentual_economia: Percentual de economia
        calculos_mensais: Lista de cálculos mensais
        estado: Estado (UF) da obra
        data_inicio: Data de início da obra
        data_fim: Data de término da obra
        data_analise: Data de análise para cálculo de multas/juros
        obra_finalizada: Se a obra está finalizada
        info_rf: Informações para a Receita Federal
    """
    calculos_areas: List[CalculoArea]
    custo_total: float
    rmt_total: float
    rmt_otimizado_total: float
    rmt_otimizado_final: float
    inss_original: float
    inss_pouca_otimizacao: float
    inss_otimizado: float
    economia: float
    percentual_economia: float
    calculos_mensais: List[CalculoMensal]
    rmt_total_decadente: float = 0.0
    rmt_total_nao_decadente: float = 0.0
    rmt_apos_usinados: float = 0.0
    rmt_apos_usinados_nao_decadente: float = 0.0
    usado_concreto_usinado: bool = False
    estado: str = ''
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    data_analise: Optional[datetime] = None
    obra_finalizada: bool = False
    info_rf: Optional[InformacoesReceitaFederal] = None
    nome_contato: str = ''
    telefone_contato: str = ''
