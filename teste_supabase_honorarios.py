#!/usr/bin/env python3
"""
Script de teste para validar as novas colunas no Supabase
Simula a inserção de dados com as colunas inss_com_honorarios e percentual_inss_com_honorarios
"""

import json
from datetime import datetime

# Exemplo com dados do exemplo-CE.csv
exemplo_ce = {
    'nome': 'Estrutural Engenharia',
    'telefone': '(85) 3199-8855',
    'numero_orcamento': 12052601,
    'inss_sem_reducao': 132256.19,           # Cenário 1 (Padrão)
    'inss_otimizado': 59303.06,              # Cenário 3 (Otimizado)
    'percentual_economia': 55.16,            # (132256.19 - 59303.06) / 132256.19 × 100
    'honorarios': 21885.94,
    # NOVOS CAMPOS
    'inss_com_honorarios': 59303.06 + 21885.94,  # = 81189.00
    'percentual_inss_com_honorarios': ((132256.19 - 81189.00) / 132256.19) * 100,  # = 38.61%
}

print("\n" + "=" * 80)
print("TESTE: NOVAS COLUNAS SUPABASE - EXEMPLO-CE")
print("=" * 80)

print("\n📊 Dados a Inserir em paulo_inss:")
print("-" * 80)

for chave, valor in exemplo_ce.items():
    if isinstance(valor, float):
        if 'percentual' in chave:
            print(f"{chave:.<40} {valor:.2f}%")
        else:
            print(f"{chave:.<40} R$ {valor:,.2f}")
    else:
        print(f"{chave:.<40} {valor}")

print("\n" + "=" * 80)
print("ANÁLISE DOS DADOS")
print("=" * 80)

inss_sem = exemplo_ce['inss_sem_reducao']
inss_otim = exemplo_ce['inss_otimizado']
honorarios = exemplo_ce['honorarios']
inss_com_hon = exemplo_ce['inss_com_honorarios']
perc_economia = exemplo_ce['percentual_economia']
perc_com_hon = exemplo_ce['percentual_inss_com_honorarios']

print(f"\n💰 Valores Monetários:")
print(f"   INSS sem otimização:     R$ {inss_sem:>12,.2f}  (100%)")
print(f"   INSS otimizado:          R$ {inss_otim:>12,.2f}   ({perc_economia:.2f}%)")
print(f"   Honorários:              R$ {honorarios:>12,.2f}   ({(honorarios/inss_sem)*100:.2f}%)")
print(f"   ─────────────────────────────────────────────────")
print(f"   INSS com Honorários:     R$ {inss_com_hon:>12,.2f}   ({perc_com_hon:.2f}%)")

print(f"\n📈 Análise de Economias:")
print(f"   Economia pura INSS:      R$ {inss_sem - inss_otim:>12,.2f}   ({perc_economia:.2f}%)")
print(f"   Custo com honorários:    R$ {honorarios:>12,.2f}")
print(f"   Economia líquida:        R$ {inss_sem - inss_com_hon:>12,.2f}   ({100 - perc_com_hon:.2f}%)")

print(f"\n🔍 Percentuais Explicados:")
print(f"   {perc_economia:.2f}% = Economia de INSS (desconto puro)")
print(f"   {perc_com_hon:.2f}% = Custo total em relação ao INSS original")
print(f"   Diferença = {perc_com_hon - perc_economia:.2f}% (percentual dos honorários)")

print("\n" + "=" * 80)
print("JSON PARA INSERIR NO SUPABASE")
print("=" * 80)
print(json.dumps(exemplo_ce, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("✅ VALIDAÇÕES")
print("=" * 80)

validacoes = {
    "inss_com_honorarios = inss_otimizado + honorarios": abs(inss_com_hon - (inss_otim + honorarios)) < 0.01,
    "percentual_com_honorarios = (sem_reducao - com_honorarios) / sem_reducao × 100": abs(perc_com_hon - ((inss_sem - inss_com_hon) / inss_sem * 100)) < 0.01,
    "percentual_com_honorarios < percentual_economia": perc_com_hon < perc_economia,
    "percentual_com_honorarios > 0%": perc_com_hon > 0,
    "INSS com honorários > INSS otimizado": inss_com_hon > inss_otim,
}

for validacao, resultado in validacoes.items():
    status = "✅" if resultado else "❌"
    print(f"{status} {validacao}")

print("\n" + "=" * 80)
print("SQL PARA EXECUTAR NO SUPABASE")
print("=" * 80)

sql = f"""
-- Adicionar colunas (se ainda não existirem)
ALTER TABLE paulo_inss ADD COLUMN IF NOT EXISTS inss_com_honorarios NUMERIC;
ALTER TABLE paulo_inss ADD COLUMN IF NOT EXISTS percentual_inss_com_honorarios NUMERIC;

-- Inserir dados de teste
INSERT INTO paulo_inss (
    nome,
    telefone,
    numero_orcamento,
    inss_sem_reducao,
    inss_otimizado,
    percentual_economia,
    honorarios,
    inss_com_honorarios,
    percentual_inss_com_honorarios
) VALUES (
    '{exemplo_ce['nome']}',
    '{exemplo_ce['telefone']}',
    {exemplo_ce['numero_orcamento']},
    {inss_sem},
    {inss_otim},
    {perc_economia},
    {honorarios},
    {inss_com_hon},
    {perc_com_hon}
);
"""

print(sql)

print("\n" + "=" * 80)
print("✅ TESTE CONCLUÍDO")
print("=" * 80)
print("\nPróximos passos:")
print("1. Executar SQL no Supabase para criar colunas")
print("2. Executar atualizar_status_processado.py com exemplo-CE")
print("3. Verificar dados inseridos no Supabase")
print()
