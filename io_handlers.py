"""
Módulo de manipulação de entrada e saída de dados

Este módulo contém funções para carregar arquivos CSV de entrada e exportar
resultados em diversos formatos (CSV, JSON, Texto).
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Tuple, Dict
try:
    from models import AreaConstrucao, CalculoArea, CalculoMensal, ResultadoSimulacao, InformacoesReceitaFederal
except ImportError:
    from models import AreaConstrucao, CalculoArea, CalculoMensal, ResultadoSimulacao, InformacoesReceitaFederal


def _buscar_contato_supabase(numero_orcamento: str) -> Tuple[str, str]:
    """
    Busca informações de contato no Supabase baseado no número do orçamento
    Retorna (nome, telefone)
    """
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        import os as os_module

        # Carrega variáveis de ambiente do .env (compatível com Windows, Linux, macOS)
        from pathlib import Path
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(str(env_path))
        else:
            load_dotenv()

        url = os_module.getenv('SUPABASE_URL')
        key = os_module.getenv('SUPABASE_KEY')

        if not url or not key:
            return "", ""

        client = create_client(url, key)
        response = client.table('paulo_orcamentos').select('nome, telefone').eq('numero_orcamento', numero_orcamento).limit(1).execute()

        if response.data and len(response.data) > 0:
            row = response.data[0]
            nome = row.get('nome', '')
            telefone = row.get('telefone', '')
            return nome, telefone
        return "", ""

    except Exception as e:
        raise Exception(f"Erro ao buscar contato no Supabase: {str(e)}")


def formatar_valor(valor: float) -> str:
    """Formata valor monetário para exibição no terminal"""
    if valor is None: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_valor_export(valor: float) -> str:
    """Formata valor monetário para exportação CSV (sem R$)"""
    if valor is None: return "0.00"
    return f"{valor:.2f}"


def formatar_percentual_export(valor: float) -> str:
    """Formata percentual para exportação CSV com símbolo %"""
    if valor is None: return "0.00%"
    return f"{valor:.2f}%"


def parse_boolean(valor: str) -> bool:
    """Converte strings como 'sim', 'nao', 'true', 'false' para boolean"""
    if not valor:
        return False
    v = valor.strip().lower()
    return v in ('sim', 's', 'true', 't', '1', 'yes', 'y')


def carregar_vau_csv(arquivo_csv: str = 'vau.csv') -> Tuple[Dict[tuple, float], str]:
    """
    Carrega os valores de VAU e o mês de referência

    Aceita múltiplos formatos de mês/ano: "May/26", "Mai/26", "05/26", etc.
    """
    from utils import normalizar_mes_ano

    vau_dict = {}
    mes_ref = ""
    MAPA_TIPOS = {
        'Casa popular': 'casa_popular',
        'Comercial salas e lojas': 'comercial',
        'Conjunto habitacional popular': 'conjunto_habitacional',
        'Edifício de Garagens': 'edificio_garagem',
        'Galpão industrial': 'galpao',
        'Residencial multifamiliar': 'multifamiliar',
        'Residencial unifamiliar': 'unifamiliar'
    }

    try:
        with open(arquivo_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not mes_ref and 'Mês/Ano' in row:
                    mes_raw = row['Mês/Ano'].strip()
                    try:
                        mes_ref = normalizar_mes_ano(mes_raw)
                    except ValueError as e:
                        print(f"⚠ Aviso: Não foi possível normalizar mês '{mes_raw}': {str(e)}")
                        mes_ref = mes_raw

                uf = row['UF'].strip().upper()
                for col_csv, tipo_interno in MAPA_TIPOS.items():
                    if col_csv in row:
                        valor_str = row[col_csv].strip().replace("'", "").replace(',', '.')
                        try:
                            vau_dict[(uf, tipo_interno)] = float(valor_str)
                        except ValueError:
                            continue
    except Exception as e:
        raise ValueError(f"Erro ao ler arquivo VAU: {str(e)}")

    return vau_dict, mes_ref


def carregar_obra_de_csv(caminho_csv: str) -> Tuple[ResultadoSimulacao, set, str]:
    """
    Lê um arquivo CSV de obra e executa todo o processo de cálculo e distribuição
    Tenta puxar nome_contato e telefone do CSV primeiro, depois do Supabase se não encontrar
    """
    from calculators import calcular_inss_obra
    from distribution import distribuir_mensal, carregar_icm_csv
    from utils import parse_data_ddmmyyyy

    areas = []
    estado = ""
    data_inicio = None
    data_fim = None
    concreto_usinado = False
    tem_paralisacao = False
    nome_contato = ""
    telefone_contato = ""

    with open(caminho_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not estado:
                estado = row['estado'].strip().upper()
                data_inicio = parse_data_ddmmyyyy(row['data_inicio'].strip())
                data_fim = parse_data_ddmmyyyy(row['data_fim'].strip())

                concreto_str = row.get('concreto_usinado', 'nao').strip()
                concreto_usinado = parse_boolean(concreto_str)

                paralisacao_str = row.get('paralisacao', 'nao').strip()
                tem_paralisacao = parse_boolean(paralisacao_str)

                nome_contato = row.get('nome', '').strip()
                telefone_contato = row.get('telefone', '').strip()

            # Prefabricado é opcional
            prefabricado = parse_boolean(row.get('prefabricado', 'nao'))

            areas.append(AreaConstrucao(
                tipo=row['tipo'].strip().lower(),
                categoria=row['categoria'].strip().lower(),
                material=row['material'].strip().lower(),
                area_m2=float(row['area_m2'].replace(',', '.')),
                is_principal=parse_boolean(row['is_principal']),
                coberta=parse_boolean(row['coberta']) if row.get('coberta') else None,
                prefabricado=prefabricado
            ))

    # Determina se obra está finalizada
    data_atual = datetime.now()
    obra_finalizada = data_fim < data_atual

    # Carrega VAU e ICM (diretório local)
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vau_path = os.path.join(base_dir, 'vau.csv')
    icm_path = os.path.join(base_dir, 'icm.csv')

    vau_dict, mes_vau = carregar_vau_csv(vau_path)

    # Calcula INSS da obra
    resultado = calcular_inss_obra(
        areas=areas,
        estado=estado,
        data_inicio=data_inicio,
        data_fim=data_fim,
        vau_dict=vau_dict,
        usado_concreto_usinado=concreto_usinado,
        obra_finalizada=obra_finalizada,
        data_analise=data_atual
    )

    # Carrega ICM
    icm_dict = carregar_icm_csv(icm_path)

    # Carrega paralisação CONDICIONALMENTE (apenas se indicado no CSV)
    paralisacao_set = None

    if tem_paralisacao:
        paralisacao_path = os.path.join(base_dir, 'paralisacao.csv')
        try:
            from distribution import carregar_paralisacao_csv
            paralisacao_set = carregar_paralisacao_csv(paralisacao_path)
            print(f"✓ Loaded {len(paralisacao_set)} paralyzed months from paralisacao.csv")
        except FileNotFoundError:
            print(f"⚠ WARNING: Column 'paralisacao' is 'sim' but paralisacao.csv not found at {paralisacao_path}")
            print(f"⚠ Continuing without paralyzed months...")
            paralisacao_set = None
        except Exception as e:
            print(f"⚠ Warning loading paralisacao.csv: {str(e)}")
            paralisacao_set = None
    else:
        print("ℹ No paralyzed months (paralisacao='nao')")

    # Distribui mensalmente
    resultado = distribuir_mensal(resultado, icm_dict, paralisacao_set)

    # Exibe resultado
    exibir_resultado_completo(resultado, mes_vau)

    # Se não encontrou informações de contato no CSV, busca no Supabase
    if not nome_contato or not telefone_contato:
        import re
        nome_arquivo = os.path.basename(caminho_csv)
        match = re.search(r'(\d+)', nome_arquivo)
        if match:
            numero_orcamento = match.group(1)
            try:
                nome_sb, telefone_sb = _buscar_contato_supabase(numero_orcamento)
                if not nome_contato:
                    nome_contato = nome_sb
                if not telefone_contato:
                    telefone_contato = telefone_sb
            except Exception as e:
                pass

    # Inclui informações de contato no resultado para serem exportadas
    resultado.nome_contato = nome_contato
    resultado.telefone_contato = telefone_contato

    return resultado, paralisacao_set, mes_vau


def exportar_csv_resumo(resultado: ResultadoSimulacao, arquivo_saida: str, diretorio_base: str = None, paralisacao_set: set = None, mes_vau: str = ""):
    """
    Exporta resultado para CSV com formato organizado e modular
    """
    import os
    from constants import ALIQUOTA_INSS_ORIGINAL

    if diretorio_base and not os.path.dirname(arquivo_saida):
        arquivo_saida = os.path.join(diretorio_base, arquivo_saida)

    with open(arquivo_saida, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)

        # BLOCO 1: DADOS DO PROJETO
        writer.writerow(['[DADOS DO PROJETO]'])
        writer.writerow(['Nome do Contato', resultado.nome_contato])
        writer.writerow(['Telefone do Contato', resultado.telefone_contato])
        writer.writerow(['Estado', resultado.estado])
        writer.writerow(['Data Início', resultado.data_inicio.strftime('%d/%m/%Y')])
        writer.writerow(['Data Fim', resultado.data_fim.strftime('%d/%m/%Y')])
        writer.writerow(['Status', 'OBRA FINALIZADA' if resultado.obra_finalizada else 'OBRA EM ANDAMENTO'])
        writer.writerow(['Custo Total da Obra', formatar_valor_export(resultado.custo_total)])
        writer.writerow([])

        # BLOCO 2: ANÁLISE TEMPORAL
        writer.writerow(['[ANÁLISE TEMPORAL]'])
        meses_totais = len(resultado.calculos_mensais)
        meses_paralisados = len(paralisacao_set) if paralisacao_set else 0
        writer.writerow(['Meses Totais', meses_totais])
        writer.writerow(['Meses de Paralisação', meses_paralisados])
        if paralisacao_set:
            meses_formatados = ', '.join([f"{m[0]:02d}/{m[1]}" for m in sorted(list(paralisacao_set))])
            writer.writerow(['Detalhamento Paralisações', meses_formatados])
        
        perc_decadencia = (resultado.rmt_total_decadente / resultado.rmt_total * 100) if resultado.rmt_total > 0 else 0
        writer.writerow(['RMT Decadente', formatar_valor_export(resultado.rmt_total_decadente)])
        writer.writerow(['Percentual Decadência', formatar_percentual_export(perc_decadencia)])
        writer.writerow([])

        # BLOCO 3: MATRIZ DE COMPARAÇÃO TRIBUTÁRIA
        inss_puro = resultado.rmt_total * ALIQUOTA_INSS_ORIGINAL
        economia_real = inss_puro - resultado.inss_otimizado
        perc_real = (economia_real / inss_puro * 100) if inss_puro > 0 else 0

        writer.writerow(['[MATRIZ DE COMPARAÇÃO TRIBUTÁRIA]'])
        writer.writerow(['Cenário', 'Estratégia Aplicada', 'RMT (VAU Atual)', 'RMT (VAU Previsto)', 'INSS Final'])
        
        # Padrão
        writer.writerow(['1. Padrão (Pior)', 'Aferição Direta Receita', formatar_valor_export(resultado.rmt_total), formatar_valor_export(resultado.rmt_total), formatar_valor_export(inss_puro)])
        
        # Intermediário
        label_inter = "Decadência + Usinado" if resultado.usado_concreto_usinado else "Decadência"
        writer.writerow(['2. Intermediário', label_inter, formatar_valor_export(resultado.rmt_apos_usinados), formatar_valor_export(resultado.rmt_apos_usinados_nao_decadente), formatar_valor_export(resultado.inss_pouca_otimizacao)])
        
        # Otimizado
        writer.writerow(['3. Otimizado (Nosso)', 'Estratégia de Folha (CPP)', formatar_valor_export(resultado.rmt_apos_usinados), formatar_valor_export(resultado.rmt_otimizado_final), formatar_valor_export(resultado.inss_otimizado)])
        
        if mes_vau:
            writer.writerow([f'NOTA: Cenários 1 e 2 usam VAU ({mes_vau}). Cenário 3 usa VAU PREVISTO.'])

        writer.writerow(['ECONOMIA REAL GERADA', '', '', '', formatar_valor_export(economia_real)])
        writer.writerow(['PERCENTUAL ECONOMIA', '', '', '', formatar_percentual_export(perc_real)])
        writer.writerow([])

        # BLOCO 4: PARÂMETROS E OPERAÇÃO
        writer.writerow(['[PARÂMETROS E OPERAÇÃO]'])
        # Calcula honorário baseado na metragem
        honorarios = carregar_honorarios_csv()
        area_total = sum(area.area_equivalente for area in resultado.calculos_areas) if resultado.calculos_areas else 0
        perc_honorario = obter_percentual_honorario(area_total, honorarios)
        valor_honorarios = economia_real * (perc_honorario / 100.0)
        writer.writerow(['Honorários Estimados', formatar_valor_export(valor_honorarios)])
        writer.writerow(['Percentual Honorários', formatar_percentual_export(perc_honorario)])
        writer.writerow([])

        # BLOCO 5: INFORMAÇÕES PARA RECEITA FEDERAL
        if resultado.info_rf:
            info_rf = resultado.info_rf
            writer.writerow(['[INFORMAÇÕES PARA RECEITA FEDERAL]'])
            writer.writerow(['Item', 'Valor'])
            writer.writerow(['DARFs Atrasadas', formatar_valor_export(info_rf.darfs_atrasadas)])
            writer.writerow(['DARF do Mês Atual', formatar_valor_export(info_rf.darf_mes_atual)])
            writer.writerow(['DARFs Futuras (Média)', formatar_valor_export(info_rf.darfs_futuras_media)])
            writer.writerow(['DARFs Futuras (Total)', formatar_valor_export(info_rf.darfs_futuras_total)])
            writer.writerow(['Quantidade de Meses Futuros', str(info_rf.qtd_meses_futuros)])

            if info_rf.primeira_darf_futura:
                writer.writerow(['Primeira DARF Futura', info_rf.primeira_darf_futura])
                writer.writerow(['Última DARF Futura', info_rf.ultima_darf_futura])

            writer.writerow(['Soma das MAEDs Atrasadas', formatar_valor_export(info_rf.soma_maed_atrasadas)])
            writer.writerow(['Multa de Parcelamento (20% das MAEDs)', formatar_valor_export(info_rf.multa_parcelamento)])
            writer.writerow(['Opção 1: Pagamento à Vista', formatar_valor_export(info_rf.pagamento_vista)])
            writer.writerow(['Opção 2: Pagamento Parcelado', formatar_valor_export(info_rf.pagamento_parcelado_total)])
            writer.writerow(['Sugestão Parcelas', f"{info_rf.qtd_parcelas_sugerida}x {formatar_valor_export(info_rf.valor_parcela)}"])
            writer.writerow([])

        # DETALHAMENTO POR ÁREA
        writer.writerow(['DETALHAMENTO POR ÁREA'])
        header_areas = [
            'Área', 'Tipo', 'Categoria', 'Material', 'Área m²', 'Principal',
            'Coberta', 'Prefabr.', '% Equiv.', 'Área Equiv.', 'VAU', 'Custo Estimado',
            'PMO', '% Cat.', 'Fator Social', 'RMT Base', 'RMT Otimizado'
        ]
        writer.writerow(header_areas)

        for i, calc in enumerate(resultado.calculos_areas, 1):
            area = calc.area
            writer.writerow([
                f'Área {i}',
                area.tipo,
                area.categoria,
                area.material,
                formatar_valor_export(area.area_m2),
                'Sim' if area.is_principal else 'Não',
                'Sim' if area.coberta else ('Não' if area.coberta is False else 'N/A'),
                'Sim' if area.prefabricado else 'Não',
                formatar_percentual_export(calc.percentual_equivalencia * 100),
                formatar_valor_export(calc.area_equivalente),
                formatar_valor_export(calc.vau),
                formatar_valor_export(calc.custo_estimado),
                formatar_percentual_export(calc.pmo * 100),
                formatar_percentual_export(calc.percentual_categoria * 100),
                formatar_percentual_export(calc.fator_social * 100),
                formatar_valor_export(calc.rmt_base),
                formatar_valor_export(calc.rmt_otimizado)
            ])
        writer.writerow([])

        # DISTRIBUIÇÃO MENSAL
        writer.writerow(['DISTRIBUIÇÃO MENSAL'])
        header_mensal = [
            'Mês/Ano', 'Remuneração Corrigida', 'ICM %', 'Paralisado',
            'Observação', 'Recibo (Base)', 'CPP (20%)', 'Multa (20%)',
            'Mora (Selic)', 'MAED', 'Total INSS'
        ]
        writer.writerow(header_mensal)

        for calc in resultado.calculos_mensais:
            from utils import mes_ano_is_decadente
            from constants import MESES_SEM_RECIBOS
            is_decadente = mes_ano_is_decadente(calc.mes, calc.ano)
            is_paralisado = (calc.mes, calc.ano) in (paralisacao_set if paralisacao_set else set())
            is_sem_recibos = (calc.mes, calc.ano) in MESES_SEM_RECIBOS

            obs = []
            if is_decadente: obs.append('Decadente')
            if is_paralisado: obs.append('Paralisação')
            if is_sem_recibos: obs.append('Sem recibos (Jan-Set/21)')

            writer.writerow([
                f'{calc.mes:02d}/{calc.ano}',
                formatar_valor_export(calc.remuneracao_corrigida),
                formatar_percentual_export(calc.icm_percentual),
                'Sim' if is_paralisado else 'Não',
                ' / '.join(obs),
                formatar_valor_export(calc.remuneracao),
                formatar_valor_export(calc.cpp),
                formatar_valor_export(calc.multa),
                formatar_valor_export(calc.mora),
                formatar_valor_export(calc.maed),
                formatar_valor_export(calc.inss_total)
            ])

        # Totais da distribuição
        rmt_final = sum(c.remuneracao_corrigida for c in resultado.calculos_mensais)
        inss_final = sum(c.inss_total for c in resultado.calculos_mensais)
        cpp_final = sum(c.cpp for c in resultado.calculos_mensais)
        multa_final = sum(c.multa for c in resultado.calculos_mensais)
        mora_final = sum(c.mora for c in resultado.calculos_mensais)
        maed_final = sum(c.maed for c in resultado.calculos_mensais)
        
        writer.writerow([])
        writer.writerow([
            formatar_valor_export(rmt_final), '', '', 'RMT atingido', '',
            '', formatar_valor_export(cpp_final), formatar_valor_export(multa_final),
            formatar_valor_export(mora_final), formatar_valor_export(maed_final),
            formatar_valor_export(inss_final)
        ])


def exportar_json(resultado: ResultadoSimulacao, arquivo_saida: str, diretorio_base: str = None):
    """
    Exporta resultado para JSON
    """
    import os

    if diretorio_base and not os.path.dirname(arquivo_saida):
        arquivo_saida = os.path.join(diretorio_base, arquivo_saida)

    dados = {
        'resumo': {
            'estado': resultado.estado,
            'custo_total': resultado.custo_total,
            'rmt_total': resultado.rmt_total,
            'rmt_total_decadente': resultado.rmt_total_decadente,
            'rmt_total_nao_decadente': resultado.rmt_total_nao_decadente,
            'rmt_otimizado': resultado.rmt_otimizado_total,
            'rmt_otimizado_final': resultado.rmt_otimizado_final,
            'inss_original': resultado.inss_original,
            'inss_pouca_otimizacao': resultado.inss_pouca_otimizacao,
            'inss_otimizado': resultado.inss_otimizado,
            'economia': resultado.economia,
            'percentual_economia': resultado.percentual_economia
        },
        'areas': [],
        'distribuicao_mensal': []
    }

    for calc in resultado.calculos_areas:
        area = calc.area
        dados['areas'].append({
            'tipo': area.tipo,
            'categoria': area.categoria,
            'material': area.material,
            'area_m2': area.area_m2,
            'is_principal': area.is_principal,
            'coberta': area.coberta,
            'prefabricado': area.prefabricado,
            'rmt_base': calc.rmt_base,
            'rmt_otimizado': calc.rmt_otimizado
        })

    for calc in resultado.calculos_mensais:
        dados['distribuicao_mensal'].append({
            'mes': calc.mes,
            'ano': calc.ano,
            'remuneracao': calc.remuneracao,
            'remuneracao_corrigida': calc.remuneracao_corrigida,
            'inss_total': calc.inss_total
        })

    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def exibir_resultado_completo(resultado: ResultadoSimulacao, mes_vau: str = ""):
    """
    Exibe relatório completo no terminal formatado de forma modular e organizada
    """
    from constants import ALIQUOTA_INSS_ORIGINAL
    
    print("\n" + "=" * 110)
    print("RELATÓRIO DE CÁLCULO DE INSS - ESTRATÉGIA OTIMIZADA")
    print("=" * 110)

    # BLOCO 1: DADOS DO PROJETO
    print("\n[DADOS DO PROJETO]")
    status_obra = 'OBRA FINALIZADA' if resultado.obra_finalizada else 'OBRA EM ANDAMENTO'
    print(f"Estado: {resultado.estado} | Período: {resultado.data_inicio.strftime('%m/%Y')} a {resultado.data_fim.strftime('%m/%Y')}")
    print(f"Status: {status_obra} | Custo Total Estimado: {formatar_valor(resultado.custo_total)}")

    # BLOCO 2: ANÁLISE TEMPORAL
    meses_totais = len(resultado.calculos_mensais)
    perc_decadencia = (resultado.rmt_total_decadente / resultado.rmt_total * 100) if resultado.rmt_total > 0 else 0

    print("\n[ANÁLISE TEMPORAL]")
    print(f"• Meses Totais: {meses_totais}")
    print(f"• Decadência Aplicada: {formatar_valor(resultado.rmt_total_decadente)} ({perc_decadencia:.2f}% do projeto)")
    
    # BLOCO 3: MATRIZ DE COMPARAÇÃO TRIBUTÁRIA
    inss_puro = resultado.rmt_total * ALIQUOTA_INSS_ORIGINAL
    
    print("\n[MATRIZ DE COMPARAÇÃO TRIBUTÁRIA]")
    print("-" * 110)
    print(f"{'Cenário':<20} | {'Estratégia Aplicada':<25} | {'RMT (VAU Atual)':<16} | {'RMT (VAU Prev.)':<16} | {'INSS Final'}")
    print("-" * 110)
    
    # Cenário 1: Padrão
    print(f"{'1. Padrão (Pior)':<20} | {'Aferição Direta Receita':<25} | {formatar_valor(resultado.rmt_total):>16} | {'-':>16} | {formatar_valor(inss_puro)}")
    
    # Cenário 2: Intermediário
    label_inter = "Decadência + Usinado" if resultado.usado_concreto_usinado else "Decadência"
    print(f"{'2. Intermediário':<20} | {label_inter:<25} | {formatar_valor(resultado.rmt_apos_usinados):>16} | {formatar_valor(resultado.rmt_apos_usinados_nao_decadente):>16} | {formatar_valor(resultado.inss_pouca_otimizacao)}")
    
    # Cenário 3: Otimizado
    print(f"{'3. Otimizado (Nosso)':<20} | {'Estratégia de Folha (CPP)':<25} | {formatar_valor(resultado.rmt_apos_usinados):>16} | {formatar_valor(resultado.rmt_otimizado_final):>16} | {formatar_valor(resultado.inss_otimizado)}")
    print("-" * 110)
    if mes_vau:
        print(f"NOTA: Cenários 1 e 2 utilizam VAU ({mes_vau}). Cenário 3 utiliza VAU PREVISTO (Desoneração).")
    
    # Resumo de Economia
    economia_real = inss_puro - resultado.inss_otimizado
    perc_real = (economia_real / inss_puro * 100) if inss_puro > 0 else 0
    print(f"ECONOMIA REAL GERADA: {formatar_valor(economia_real)} ({perc_real:.2f}%)")

    # BLOCO 4: PARÂMETROS E OPERAÇÃO
    honorarios = economia_real * 0.30
    print("\n[PARÂMETROS E OPERAÇÃO]")
    # Calcula honorário baseado na metragem
    honorarios_dict = carregar_honorarios_csv()
    area_total = sum(area.area_equivalente for area in resultado.calculos_areas) if resultado.calculos_areas else 0
    perc_honorario = obter_percentual_honorario(area_total, honorarios_dict)
    honorarios = economia_real * (perc_honorario / 100.0)
    print(f"• Honorários Estimados ({perc_honorario:.0f}%): {formatar_valor(honorarios)}")
    
    if resultado.info_rf:
        info = resultado.info_rf
        print(f"\n[INFORMAÇÕES PARA RECEITA FEDERAL]")
        print(f"• À Vista (DARFs Atrasadas): {formatar_valor(info.pagamento_vista)}")
        print(f"• Parcelado (Total Sugerido): {formatar_valor(info.pagamento_parcelado_total)} ({info.qtd_parcelas_sugerida}x {formatar_valor(info.valor_parcela)})")
        if info.primeira_darf_futura:
            print(f"• Primeira DARF Futura: {info.primeira_darf_futura}")
            print(f"• Última DARF Futura: {info.ultima_darf_futura}")

    print("\n" + "=" * 110)


def carregar_honorarios_csv(arquivo_csv: str = 'honorarios.csv') -> Dict[str, float]:
    """
    Carrega a tabela de honorários por faixa de metragem de um CSV.

    Retorna um dicionário com a estrutura:
    {
        'area_minima': [valores],
        'area_maxima': [valores],
        'percentual': [valores]
    }
    """
    honorarios = {
        'area_minima': [],
        'area_maxima': [],
        'percentual': []
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_path = os.path.join(script_dir, arquivo_csv)

    try:
        with open(arquivo_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                honorarios['area_minima'].append(float(row['area_minima']))
                honorarios['area_maxima'].append(float(row['area_maxima']))
                honorarios['percentual'].append(float(row['percentual']))
        return honorarios
    except FileNotFoundError:
        print(f"⚠️ Aviso: Arquivo {arquivo_csv} não encontrado. Usando honorário padrão de 30%")
        return {
            'area_minima': [0.0],
            'area_maxima': [999999.0],
            'percentual': [30.0]
        }


def obter_percentual_honorario(area_total: float, honorarios: Dict[str, float]) -> float:
    """
    Retorna o percentual de honorário baseado na metragem total da obra.

    Args:
        area_total: Metragem total da obra em m²
        honorarios: Dicionário com tabela de honorários

    Returns:
        Percentual de honorário (ex: 30.0 para 30%)
    """
    for i, (area_min, area_max) in enumerate(zip(honorarios['area_minima'], honorarios['area_maxima'])):
        if area_min <= area_total <= area_max:
            return honorarios['percentual'][i]

    # Fallback para última faixa
    return honorarios['percentual'][-1]
