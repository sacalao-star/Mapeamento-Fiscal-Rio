# ============================================================
# BASE DE DADOS GEOESPACIAL E MOTOR MATEMÁTICO - PRISMA RIO
# ============================================================
import pandas as pd

# 1. BANCO DE DADOS DE ATIVOS (Incluindo Bonsucesso e grandes eixos)
BANCO_IMOVEIS = [
    {
        "id": "SQL-998.112-2",
        "endereco": "Rua da Regeneração, Bonsucesso",
        "bairro": "Bonsucesso",
        "area_m2": 4500,
        "valor_aproximado": 8500000,
        "status": "Dívida Ativa / Leilão PGM",
        "trilha": "Varejo e Logística",
        "lat": -22.8641,
        "lon": -43.2502,
        "detalhes": "Galpão industrial autuado por abandono fiscal e passivo crônico de IPTU mapeado em edital."
    },
    {
        "id": "SQL-101.002-9",
        "endereco": "Av. Presidente Vargas, 1200",
        "bairro": "Centro",
        "area_m2": 8500,
        "valor_aproximado": 25500000,
        "status": "Dívida Ativa Crítica",
        "trilha": "Varejo e Logística",
        "lat": -22.9035,
        "lon": -43.1812,
        "detalhes": "Antigo edifício comercial vazio há 6 anos. Passivo acumulado de taxas municipais."
    },
    {
        "id": "SQL-309.882-4",
        "endereco": "Av. Rodrigues Alves, 315",
        "bairro": "Saúde (Porto)",
        "area_m2": 15000,
        "valor_aproximado": 52500000,
        "status": "Abandonado (Porto Maravilha)",
        "trilha": "Habitação",
        "lat": -22.8955,
        "lon": -43.1850,
        "detalhes": "Galpão obsoleto na Zona Portuária. Potencial estratégico para retrofit residencial."
    },
    {
        "id": "SQL-204.015-1",
        "endereco": "Rua do Lavradio, 85",
        "bairro": "Lapa",
        "area_m2": 3200,
        "valor_aproximado": 9600000,
        "status": "Subutilizado",
        "trilha": "Saúde",
        "lat": -22.9103,
        "lon": -43.1818,
        "detalhes": "Sobrado de grande porte com pavimento superior abandonado. Alta demanda para clínica."
    },
    {
        "id": "SQL-502.329-0",
        "endereco": "Campo de São Cristóvão, 250",
        "bairro": "São Cristóvão",
        "area_m2": 14000,
        "valor_aproximado": 35000000,
        "status": "Abandonado",
        "trilha": "Varejo e Logística",
        "lat": -22.9010,
        "lon": -43.2200,
        "detalhes": "Galpão industrial obsoleto próximo às principais vias de escoamento logístico norte."
    }
]

# 2. MOTOR MATEMÁTICO E FISCAL (VPL, WACC, IPCA)
ALIQUOTA_IPTU = 0.025 # 2.5% a.a.

def simular_cenario_fiscal(dados, tx_inflacao_aa, tx_desconto_wacc, ano_venda_itbi):
    area = dados["area_m2"]
    vv = dados["valor_aproximado"]
    trilha = dados["trilha"]
    
    if trilha == "Varejo e Logística":
        f_m2, emp_m2 = 6000, 25
        iss_p, icms_p, itbi_p = 0.02, 0.03, 0.0
        escada = [(6, 0), (8, 25), (10, 50), (999, 100)]
    elif trilha == "Saúde":
        f_m2, emp_m2 = 8000, 20
        iss_p, icms_p, itbi_p = 0.04, 0.01, 0.0
        escada = [(8, 0), (9, 25), (10, 50), (999, 100)]
    elif trilha == "Educação":
        f_m2, emp_m2 = 3500, 45
        iss_p, icms_p, itbi_p = 0.045, 0.005, 0.0
        escada = [(6, 0), (8, 25), (10, 50), (999, 70)]
    else: # Habitação
        f_m2, emp_m2 = 0, 200
        iss_p, icms_p, itbi_p = 0.0, 0.0, 0.03
        escada = [(6, 0), (8, 25), (10, 50), (999, 100)]

    fat_ano0 = area * f_m2
    empregos = int(area / emp_m2)
    
    fluxo = []
    vpl_total = 0
    
    for ano in range(0, 13):
        f_inflacao = (1 + (tx_inflacao_aa / 100)) ** ano
        f_desconto = (1 + (tx_desconto_wacc / 100)) ** ano
        
        fat_atual = 0 if ano == 0 else fat_ano0 * f_inflacao
        vv_atual = vv * f_inflacao
        
        pct_pgto = 100
        for ano_limite, pct_tabela in escada:
            if ano <= ano_limite:
                pct_pgto = pct_tabela
                break
        
        iptu_pago = (vv_atual * ALIQUOTA_IPTU) * (pct_pgto / 100)
        iss_pago = fat_atual * iss_p
        icms_pago = fat_atual * icms_p
        itbi_pago = (vv_atual * itbi_p) if (ano == ano_venda_itbi and trilha == "Habitação") else 0
        
        rec_total = iptu_pago + iss_pago + icms_pago + itbi_pago
        vpl_total += (rec_total / f_desconto)
        
        fluxo.append({
            "Ano": f"Ano {ano}",
            "Faturamento Estimado": fat_atual,
            "IPTU": iptu_pago,
            "ISS": iss_pago,
            "ICMS": icms_pago,
            "ITBI": itbi_pago,
            "Receita Total": rec_total
        })
        
    return {
        "fluxo": pd.DataFrame(fluxo),
        "empregos": empregos,
        "vpl_projetado": vpl_total,
        "fat_medio_futuro": fat_ano0 * ((1 + (tx_inflacao_aa / 100)) ** 5)
    }
