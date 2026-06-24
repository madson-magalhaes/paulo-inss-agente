"""
Módulo de Otimização de Distribuição de Recibos

Este módulo lê o CSV de saída do main.py e otimiza a distribuição de recibos
para minimizar o número de colaboradores e reduzir juros/multa.
"""

import csv
import os
import math
import copy
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LimiteRemuneracao:
    """Limite de remuneração mensal para autônomos"""
    mes: int
    ano: int
    valor_maximo: float

    def __repr__(self):
        return f"{self.mes:02d}/{self.ano} - R$ {self.valor_maximo:,.2f}"


@dataclass
class MesDistribuicao:
    """Dados de um mês da distribuição"""
    mes: int
    ano: int
    mes_ano_str: str
    remuneracao_corrigida: float
    selic: float
    recibo_original: float
    inss_original: float
    multa_original: float
    juros_original: float
    maed_original: float
    total_original: float
    prazo: str
    creditos: str

    # Campos calculados pela otimização
    recibo_otimizado: float = 0.0
    remuneracao_corrigida_otimizada: float = 0.0
    qtd_autonomos: int = 0
    qtd_mei: int = 0
    inss_otimizado: float = 0.0
    multa_otimizada: float = 0.0
    juros_otimizado: float = 0.0
    maed_otimizado: float = 0.0
    total_otimizado: float = 0.0

    def __repr__(self):
        return f"{self.mes_ano_str}: Recibo R$ {self.recibo_otimizado:,.2f}"


# Constantes
RECIBO_MINIMO = 300.00
LIMITE_ANUAL_MEI = 81000.00
ALIQUOTA_CPP = 0.20
ALIQUOTA_MULTA = 0.20
VALOR_MAED = 100.00
DIA_LIMITE_JUROS = 15


def carregar_tabela_remuneracao(arquivo_csv: str = 'tabela-remuneracao.csv') -> List[LimiteRemuneracao]:
    from utils import parse_mes_ano

    limites = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(base_dir, arquivo_csv) if not os.path.isabs(arquivo_csv) else arquivo_csv
    with open(caminho, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mes_ano_str = row['Mês/Ano'].strip()
            try:
                mes, ano = parse_mes_ano(mes_ano_str)
            except ValueError as e:
                print(f"⚠ Aviso: Não foi possível normalizar mês '{mes_ano_str}': {str(e)}")
                continue

            valor = float(row['Remuneração Máxima'].strip().replace(',', ''))
            limites.append(LimiteRemuneracao(mes, ano, valor))
    limites.sort(key=lambda x: (x.ano, x.mes))
    return limites


def obter_limite_remuneracao(mes: int, ano: int, tabela_limites: List[LimiteRemuneracao]) -> float:
    limite_aplicavel = tabela_limites[0]
    for limite in tabela_limites:
        if (ano > limite.ano) or (ano == limite.ano and mes >= limite.mes):
            limite_aplicavel = limite
        else: break
    return limite_aplicavel.valor_maximo


def calcular_qtd_autonomos_ideal(meses: List[MesDistribuicao], tabela_limites: List[LimiteRemuneracao], data_analise: datetime) -> int:
    """
    Calcula a quantidade fixa de autônomos para a obra usando o máximo necessário em qualquer período.

    Estratégia (validada pelo Professor, otimizada):
    1. Calcula recibo hipotético único: recibo_hip = RMT_total / soma((1+selic/100) de todos os meses).
    2. Para cada mês, calcula qtd_teste = ceil(recibo_hip / limite_remuneracao_do_período).
    3. Retorna max(qtds) — usa a quantidade máxima necessária em qualquer período.
       Justificativa: se precisa de N autônomos em algum mês, usa N em toda a obra para maximizar economia.
    """
    mv = [m for m in meses if m.remuneracao_corrigida > 0]
    if not mv: return 1

    s_rmt = sum(m.remuneracao_corrigida for m in mv)
    s_f = sum((1 + m.selic / 100.0) for m in mv)

    # Recibo hipotético único (linear) pra teste
    recibo_hip = s_rmt / s_f if s_f > 0 else 0

    # Calcula quantidade por mês nesse cenário hipotético
    qtds_teste = []
    for m in mv:
        limite_mes = obter_limite_remuneracao(m.mes, m.ano, tabela_limites)
        qtd_mes = math.ceil(recibo_hip / limite_mes) if limite_mes > 0 else 1
        qtds_teste.append(qtd_mes)

    # Usa o máximo necessário em qualquer período — nunca reduz capacidade
    return max(1, max(qtds_teste) if qtds_teste else 1)


def parse_mes_ano(mes_ano_str: str) -> Tuple[int, int]:
    partes = mes_ano_str.split('/')
    mes, ano = int(partes[0]), int(partes[1])
    if ano < 100: ano = 2000 + ano if ano < 50 else 1900 + ano
    return mes, ano


def converter_valor_csv(v: str) -> float:
    if not v or not v.strip(): return 0.0
    v = v.replace('R$', '').replace('%', '').strip()
    if ',' in v and '.' in v: return float(v.replace('.', '').replace(',', '.'))
    if ',' in v: return float(v.replace(',', '.'))
    try: return float(v)
    except: return 0.0


def carregar_distribuicao_csv(arquivo_csv: str) -> Tuple[List[MesDistribuicao], Dict]:
    meses = []
    with open(arquivo_csv, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    idx_dist = next((i for i, l in enumerate(lines) if 'DISTRIBUIÇÃO MENSAL' in l), -1)
    if idx_dist == -1: raise ValueError("Seção 'DISTRIBUIÇÃO MENSAL' não encontrada")
    idx_header = idx_dist + 1
    while idx_header < len(lines) and not lines[idx_header].strip(): idx_header += 1
    headers = [h.strip() for h in lines[idx_header].strip().split(',')]
    for i in range(idx_header + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.lower().startswith('total') or '...' in line: break
        valores = [v.strip() for v in line.split(',')]
        if len(valores) < len(headers): continue
        row = dict(zip(headers, valores))
        m_a = row.get('Mês/Ano', row.get('Mês', '')).strip()
        if not m_a: continue
        mes, ano = parse_mes_ano(m_a)
        meses.append(MesDistribuicao(
            mes=mes, ano=ano, mes_ano_str=m_a,
            remuneracao_corrigida=converter_valor_csv(row.get('Remuneração Corrigida', '0')),
            selic=converter_valor_csv(row.get('ICM %', row.get('Selic', '0'))),
            recibo_original=converter_valor_csv(row.get('Recibo (Base)', row.get('Recibo (R$)', '0'))),
            inss_original=converter_valor_csv(row.get('CPP (20%)', row.get('INSS 20% (R$)', '0'))),
            multa_original=converter_valor_csv(row.get('Multa (20%)', row.get('Multa INSS 20% (R$)', '0'))),
            juros_original=converter_valor_csv(row.get('Mora (Selic)', row.get('Juros Selic (R$)', '0'))),
            maed_original=converter_valor_csv(row.get('MAED', row.get('MAED (R$)', '0'))),
            total_original=converter_valor_csv(row.get('Total INSS', row.get('Total (R$)', '0'))),
            prazo=row.get('Prazo', 'Não').strip(), creditos=row.get('Créditos', 'Lançar').strip()
        ))
    return meses, {}


def otimizar_distribuicao(meses: List[MesDistribuicao], tabela_limites: List[LimiteRemuneracao], data_analise: datetime, modo: str = 'autonomo', qtd_fixo: Optional[int] = None) -> List[MesDistribuicao]:
    mv = [m for m in meses if m.remuneracao_corrigida > 0]
    if not mv: return meses

    s_rmt = sum(m.remuneracao_corrigida for m in mv)
    s_f = sum((1 + m.selic / 100.0) for m in mv)
    # Partição passado/futuro: um mês é vencido se a data de vencimento (dia 20 do mês seguinte) passou
    m_at, a_at, d_at = data_analise.month, data_analise.year, data_analise.day

    mp, mf = [], []
    for m in mv:
        # Data de vencimento do mês: dia 20 do mês seguinte
        mes_venc = m.mes + 1
        ano_venc = m.ano
        if mes_venc > 12:
            mes_venc = 1
            ano_venc += 1
        data_vencimento = datetime(ano_venc, mes_venc, 20)

        # Mês é passado se a data de vencimento já passou
        if data_analise >= data_vencimento:
            mp.append(m)
        else:
            mf.append(m)

    # Calcula a quantidade ideal de autônomos se não foi informada manualmente
    if qtd_fixo is None:
        lim_trabalho = calcular_qtd_autonomos_ideal(meses, tabela_limites, data_analise)
    else:
        lim_trabalho = qtd_fixo

    # CENÁRIO 1: Obra 100% futura (sem meses passados) — distribuição linear igual
    if not mp and mf:
        recibo_fixo = s_rmt / s_f
        for m in mv:
            m.recibo_otimizado = recibo_fixo

    # CENÁRIO 2: Obra 100% passada (nenhum mês futuro/atual) — distribuição linear entre vencidos
    elif mp and not mf:
        recibo_fixo = s_rmt / s_f
        for m in mv:
            m.recibo_otimizado = recibo_fixo

    # CENÁRIO 3: Obra em andamento (mistura de passado + futuro)
    # Recibo fixo nos futuros = qtd_fixa × limite_vigente; nos passados, resíduo de RMT distribuído uniformemente
    else:
        # Atribui recibo aos meses futuros: recibo_futuro = lim_trabalho × limite_vigente
        for m in mf:
            limite_futuro = obter_limite_remuneracao(m.mes, m.ano, tabela_limites)
            m.recibo_otimizado = lim_trabalho * limite_futuro

        # Calcula quanto de RMT foi alocado aos futuros
        soma_rmt_futuros = sum(m.recibo_otimizado * (1 + m.selic / 100.0) for m in mf)

        # Calcula recibo único para meses passados (engenharia reversa)
        if mp and soma_rmt_futuros < s_rmt:
            soma_fator_passado = sum((1 + m.selic / 100.0) for m in mp)
            if soma_fator_passado > 0:
                recibo_passado = (s_rmt - soma_rmt_futuros) / soma_fator_passado
                recibo_passado = max(RECIBO_MINIMO, recibo_passado)
                for m in mp:
                    m.recibo_otimizado = recibo_passado
        elif mp:
            # Fallback: se RMT dos futuros já exceder total (edge case raro), usar mínimo
            for m in mp:
                m.recibo_otimizado = RECIBO_MINIMO
            
    for m in mv:
        m.remuneracao_corrigida_otimizada = round(m.recibo_otimizado * (1 + m.selic/100.0), 2)
        cpp = m.recibo_otimizado * ALIQUOTA_CPP
        m.inss_otimizado = round(cpp, 2)
        mvenc, avenc = m.mes + 1, m.ano
        if mvenc > 12: mvenc = 1; avenc += 1
        dvj, dvm = datetime(avenc, mvenc, 15), datetime(avenc, mvenc, 20)
        if data_analise >= dvm:
            m.multa_otimizada, m.juros_otimizado, m.maed_otimizado = round(cpp*0.2, 2), round(cpp*m.selic/100, 2), VALOR_MAED
        elif data_analise >= dvj:
            m.multa_otimizada, m.juros_otimizado, m.maed_otimizado = round(cpp*0.2, 2), round(cpp*m.selic/100, 2), 0.0
        else: m.multa_otimizada = m.juros_otimizado = m.maed_otimizado = 0.0
        m.total_otimizado = round(m.inss_otimizado + m.multa_otimizada + m.juros_otimizado + m.maed_otimizado, 2)
        m.qtd_autonomos = math.ceil(m.recibo_otimizado / obter_limite_remuneracao(m.mes, m.ano, tabela_limites))
    return meses


def otimizar_com_autonomos_fixos(meses: List[MesDistribuicao], tabela_limites: List[LimiteRemuneracao], data_analise: datetime, qtd_fixo: int) -> List[MesDistribuicao]:
    return otimizar_distribuicao(meses, tabela_limites, data_analise, qtd_fixo=qtd_fixo)


def coletar_avisos_otimizacao(meses: List[MesDistribuicao], rmt_exp: float, qtd_solicitada: Optional[int] = None) -> List[str]:
    avisos = []
    s_rc = sum(m.remuneracao_corrigida_otimizada for m in meses)
    if abs(s_rc - rmt_exp) > 1.0: 
        avisos.append(f"Diferença RMT: Exp R$ {rmt_exp:,.2f}, Obt R$ {s_rc:,.2f}")
    if qtd_solicitada:
        max_u = max((m.qtd_autonomos for m in meses), default=0)
        if max_u > qtd_solicitada:
            avisos.append(f"ALERTA: {qtd_solicitada} autônomo(s) é INSUFICIENTE para o RMT alvo. "
                         f"Sistema utilizou automaticamente {max_u} autônomos para garantir conformidade.")
    return avisos


@dataclass
class InformacoesReceitaFederal:
    darfs_atrasadas: float = 0.0
    darf_mes_atual: float = 0.0
    darfs_futuras_media: float = 0.0
    darfs_futuras_total: float = 0.0
    qtd_meses_futuros: int = 0
    primeira_darf_futura: str = ""
    ultima_darf_futura: str = ""
    soma_maed_atrasadas: float = 0.0
    multa_parcelamento: float = 0.0
    pagamento_vista: float = 0.0
    pagamento_parcelado_total: float = 0.0
    qtd_parcelas_sugerida: int = 0
    valor_parcela: float = 0.0


def calcular_informacoes_receita_federal(meses: List[MesDistribuicao], data_atual: datetime) -> InformacoesReceitaFederal:
    info = InformacoesReceitaFederal()
    a_at, m_at, d_at = data_atual.year, data_atual.month, data_atual.day
    if d_at < 20:
        m_df, a_df = m_at - 1, a_at
        if m_df < 1: m_df = 12; a_df -= 1
    else: m_df, a_df = m_at, a_at
    matr, matu, mfut = [], None, []
    for m in meses:
        if m.total_otimizado <= 0: continue
        if (m.ano < a_df) or (m.ano == a_df and m.mes < m_df): matr.append(m)
        elif m.ano == a_df and m.mes == m_df: matu = m
        else: mfut.append(m)
    info.darfs_atrasadas = sum(m.total_otimizado for m in matr)
    info.soma_maed_atrasadas = sum(m.maed_otimizado for m in matr)
    if matu: info.darf_mes_atual = matu.total_otimizado
    if mfut:
        info.darfs_futuras_total = sum(m.total_otimizado for m in mfut)
        info.qtd_meses_futuros = len(mfut)
        info.darfs_futuras_media = info.darfs_futuras_total / len(mfut)
        pm, um = mfut[0], mfut[-1]
        mp, ap = pm.mes+1, pm.ano
        if mp > 12: mp=1; ap+=1
        info.primeira_darf_futura = f"{mp:02d}/{str(ap)[-2:]}"
        mu, au = um.mes+1, um.ano
        if mu > 12: mu=1; au+=1
        info.ultima_darf_futura = f"{mu:02d}/{str(au)[-2:]}"
    info.multa_parcelamento = info.soma_maed_atrasadas * 0.20
    info.pagamento_vista = info.darfs_atrasadas
    info.pagamento_parcelado_total = info.darfs_atrasadas + info.multa_parcelamento
    if info.pagamento_parcelado_total > 0:
        qtd = min(60, max(1, int(info.pagamento_parcelado_total / 200.0)))
        val = info.pagamento_parcelado_total / qtd
        while val < 200.0 and qtd > 1: qtd -= 1; val = info.pagamento_parcelado_total / qtd
        info.qtd_parcelas_sugerida, info.valor_parcela = qtd, val
    return info


def exportar_csv_otimizado(meses: List[MesDistribuicao], arquivo_saida: str, modo: str = 'autonomo', arquivo_base_csv: Optional[str] = None, avisos: Optional[List[str]] = None, inss_original: Optional[float] = None, data_atual: Optional[datetime] = None):
    if data_atual is None: data_atual = datetime.now()
    info_otim = calcular_informacoes_receita_federal(meses, data_atual)
    inss_otim = sum(m.total_otimizado for m in meses)
    s_recibo = sum(m.recibo_otimizado for m in meses)
    
    # Importa funções para calcular honorários baseado na metragem
    try:
        from io_handlers import carregar_honorarios_csv, obter_percentual_honorario
        honorarios_dict = carregar_honorarios_csv()
    except:
        honorarios_dict = {
            'area_minima': [0.0],
            'area_maxima': [999999.0],
            'percentual': [30.0]
        }

    with open(arquivo_saida, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if arquivo_base_csv and os.path.exists(arquivo_base_csv):
            with open(arquivo_base_csv, 'r', encoding='utf-8-sig') as fb:
                all_rows = list(csv.reader(fb))
            inss_puro = inss_original if inss_original and inss_original > 0 else 0.0
            if inss_puro == 0:
                for r in all_rows:
                    if r and '1. Padrão (Pior)' in r[0]: inss_puro = converter_valor_csv(r[4])
            economia = inss_puro - inss_otim

            # Extrai área total do arquivo base para calcular percentual correto
            area_total = 0.0
            for r in all_rows:
                if r and len(r) > 8 and r[0] and 'Área' in r[0] and 'Equiv' in str(r[8]):
                    try:
                        area_total = float(str(r[8]).replace(',', '.'))
                    except:
                        pass

            perc_honorario = obter_percentual_honorario(area_total, honorarios_dict)
            honorarios = economia * (perc_honorario / 100.0)
            idx_dist = next((i for i, r in enumerate(all_rows) if r and 'DISTRIBUIÇÃO MENSAL' in r[0]), -1)
            if idx_dist >= 0:
                in_rf = False
                for i in range(idx_dist):
                    row = all_rows[i]
                    if not row or not any(row): writer.writerow([]); continue
                    if len(row) > 1 and 'Cenário' in row[0] and 'Estratégia' in row[1]:
                        writer.writerow(['Cenário', 'Estratégia Aplicada', 'RMT (VAU Atual)', 'RMT (VAU Previsto)', 'INSS Final'])
                        continue
                    if 'INFORMAÇÕES PARA RECEITA FEDERAL' in row[0]:
                        in_rf = True; writer.writerow(['[INFORMAÇÕES PARA RECEITA FEDERAL]']); continue
                    if in_rf:
                        if 'DETALHAMENTO' in row[0]: in_rf = False
                        else:
                            if 'DARFs Atrasadas' in row[0]: writer.writerow(['DARFs Atrasadas', f'{info_otim.darfs_atrasadas:.2f}'])
                            elif 'DARF do Mês Atual' in row[0]: writer.writerow(['DARF do Mês Atual', f'{info_otim.darf_mes_atual:.2f}'])
                            elif 'DARFs Futuras (Média)' in row[0]: writer.writerow(['DARFs Futuras (Média)', f'{info_otim.darfs_futuras_media:.2f}'])
                            elif 'DARFs Futuras (Total)' in row[0]: writer.writerow(['DARFs Futuras (Total)', f'{info_otim.darfs_futuras_total:.2f}'])
                            elif 'Quantidade de Meses Futuros' in row[0]: writer.writerow(['Quantidade de Meses Futuros', str(info_otim.qtd_meses_futuros)])
                            elif 'Primeira DARF Futura' in row[0]: writer.writerow(['Primeira DARF Futura', info_otim.primeira_darf_futura])
                            elif 'Última DARF Futura' in row[0]: writer.writerow(['Última DARF Futura', info_otim.ultima_darf_futura])
                            elif 'Soma das MAEDs Atrasadas' in row[0]: writer.writerow(['Soma das MAEDs Atrasadas', f'{info_otim.soma_maed_atrasadas:.2f}'])
                            elif 'Multa de Parcelamento' in row[0]: writer.writerow(['Multa de Parcelamento (20% das MAEDs)', f'{info_otim.multa_parcelamento:.2f}'])
                            elif 'Opção 1: Pagamento à Vista' in row[0]: writer.writerow(['Opção 1: Pagamento à Vista', f'{info_otim.pagamento_vista:.2f}'])
                            elif 'Opção 2: Pagamento Parcelado' in row[0]: writer.writerow(['Opção 2: Pagamento Parcelado', f'{info_otim.pagamento_parcelado_total:.2f}'])
                            elif 'Sugestão Parcelas' in row[0]: writer.writerow(['Sugestão Parcelas', f"{info_otim.qtd_parcelas_sugerida}x {info_otim.valor_parcela:.2f}"])
                            continue
                    if '1. Padrão (Pior)' in row[0]: writer.writerow(['1. Padrão (Pior)', row[1], row[2], row[2], row[4]])
                    elif '2. Intermediário' in row[0]: writer.writerow(['2. Intermediário', row[1], row[2], row[3], row[4]])
                    elif '3. Otimizado (Nosso)' in row[0]:
                        writer.writerow(['3. Otimizado (Nosso)', row[1], row[2], f'{s_recibo:.2f}', f'{inss_otim:.2f}'])
                    elif 'NOTA:' in row[0] and 'VAU' in row[0]: writer.writerow(row)
                    elif 'ECONOMIA REAL GERADA' in row[0]: writer.writerow(['ECONOMIA REAL GERADA', '', '', '', f'{economia:.2f}'])
                    elif 'PERCENTUAL ECONOMIA' in row[0]: writer.writerow(['PERCENTUAL ECONOMIA', '', '', '', f'{(economia/inss_puro*100):.2f}%' if inss_puro > 0 else '0.00%'])
                    elif 'Honorários Estimados' in row[0]: writer.writerow(['Honorários Estimados', f'{honorarios:.2f}'])
                    else: writer.writerow(row)
                writer.writerow([])
        if avisos:
            writer.writerow(['[AVISOS E ALERTAS]']); [writer.writerow([f'{i}. {a}']) for i, a in enumerate(avisos, 1)]; writer.writerow([])
        writer.writerow(['[DISTRIBUIÇÃO MENSAL]'])
        writer.writerow(['Mês', 'Remuneração Corrigida', 'Selic', 'Recibo Original', 'Recibo Otimizado', 'Qtd Autônomos', 'Qtd MEI', 'INSS 20%', 'Multa 20%', 'Juros Selic', 'MAED', 'Total INSS'])
        for m in meses:
            is_f = (m.ano > data_atual.year) or (m.ano == data_atual.year and m.mes >= data_atual.month)
            writer.writerow([m.mes_ano_str, f"{m.remuneracao_corrigida_otimizada:.2f}", f"{m.selic:.2f}", f"{m.recibo_original:.2f}", f"{m.recibo_otimizado:.2f}", str(m.qtd_autonomos) if m.qtd_autonomos > 0 else '', str(m.qtd_mei) if m.qtd_mei > 0 else ('N/A' if not is_f else ''), f"{m.inss_otimizado:.2f}", f"{m.multa_otimizada:.2f}", f"{m.juros_otimizado:.2f}", f"{m.maed_otimizado:.2f}", f"{m.total_otimizado:.2f}"])
        writer.writerow([]); writer.writerow(['TOTAIS'])
        max_a, max_m = max((m.qtd_autonomos for m in meses), default=0), max((m.qtd_mei for m in meses), default=0)
        writer.writerow(['Total', f"{sum(m.remuneracao_corrigida_otimizada for m in meses):.2f}", '', f"{sum(m.recibo_original for m in meses):.2f}", f"{sum(m.recibo_otimizado for m in meses):.2f}", f"Máx: {max_a}" if max_a > 0 else '', f"Máx: {max_m}" if max_m > 0 else '', f"{sum(m.inss_otimizado for m in meses):.2f}", f"{sum(m.multa_otimizada for m in meses):.2f}", f"{sum(m.juros_otimizado for m in meses):.2f}", f"{sum(m.maed_otimizado for m in meses):.2f}", f"{sum(m.total_otimizado for m in meses):.2f}"])


def main():
    import sys
    if len(sys.argv) < 2: return
    arquivo_entrada, modo = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'autonomo')
    tabela_limites = carregar_tabela_remuneracao()
    meses, _ = carregar_distribuicao_csv(arquivo_entrada)
    meses_otimizados = otimizar_distribuicao(meses, tabela_limites, datetime.now(), modo)
    inss_orig = 0.0
    rmt_exp = 0.0
    with open(arquivo_entrada, 'r', encoding='utf-8-sig') as f:
        fb_rows = list(csv.reader(f))
        for r in fb_rows:
            if r:
                if '1. Padrão (Pior)' in r[0]: inss_orig = converter_valor_csv(r[4])
                if '3. Otimizado (Nosso)' in r[0]: rmt_exp = converter_valor_csv(r[3])
    nome_base = os.path.splitext(os.path.basename(arquivo_entrada))[0]
    exportar_csv_otimizado(meses_otimizados, f"{nome_base}-otimizado.csv", modo, arquivo_entrada, coletar_avisos_otimizacao(meses_otimizados, rmt_exp), inss_orig)
    max_a = max((m.qtd_autonomos for m in meses_otimizados), default=0)
    print(f"\nDeseja alterar o número de autônomos (atualmente: {max_a})? (s/n): ")
    import sys as sys_module
    if not sys_module.stdin.isatty():
        resp = sys_module.stdin.read().split()
        if resp and resp[0] == 's':
            qtd = int(resp[1])
            meses_fixo = otimizar_com_autonomos_fixos(copy.deepcopy(meses), tabela_limites, datetime.now(), qtd)
            exportar_csv_otimizado(meses_fixo, f"{nome_base}-otimizado-{qtd}autonomos.csv", modo, arquivo_entrada, coletar_avisos_otimizacao(meses_fixo, rmt_exp, qtd), inss_orig)
    else:
        try:
            resp = input().strip().lower()
            if resp == 's':
                qtd = int(input("Quantos autônomos você tem disponível? (mínimo: 1): ").strip())
                meses_fixo = otimizar_com_autonomos_fixos(copy.deepcopy(meses), tabela_limites, datetime.now(), qtd)
                exportar_csv_otimizado(meses_fixo, f"{nome_base}-otimizado-{qtd}autonomos.csv", modo, arquivo_entrada, coletar_avisos_otimizacao(meses_fixo, rmt_exp, qtd), inss_orig)
        except EOFError: pass

if __name__ == '__main__':
    main()
