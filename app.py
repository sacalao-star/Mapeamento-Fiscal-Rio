import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="GIS-Gov Rio | Mapeamento e Projeção Fiscal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores Institucionais
NAVY = "#1B3A5C"
GOLD = "#B8892F"
VERMELHO = "#B42318"
VERDE = "#15803D"
AZUL_ROYAL = "#2563EB"
TXT_DARK = "#0F172A"

st.markdown("""
<style>
    .metric-card { background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 14px; text-align: center; margin-bottom: 10px; }
    .metric-val { font-size: 22px; font-weight: 800; }
    .metric-lbl { color: #475569; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-top: 4px; }
    .stApp { background-color: #FFFFFF; color: #0F172A; }
    div[data-testid="stSidebar"] { background-color: #F1F5F9; border-right: 1.5px solid #CBD5E1; }
</style>
""", unsafe_allow_html=True)

def fmt_moeda(val):
    if val is None: return "R$ 0"
    return f"R$ {round(val):,.0f}".replace(",", ".")

def fmt_num(val):
    if val is None: return "0"
    return f"{round(val):,.0f}".replace(",", ".")

# ============================================================
# 2. BASE DE DADOS DOS IMÓVEIS (MAPEAMENTO GEOGRÁFICO)
# ============================================================
# Imóveis estratégicos ociosos ou em Dívida Ativa no Centro e Zona Portuária do Rio
df_imoveis = pd.DataFrame([
    {
        "id": "SQL-101.002-9", 
        "endereco": "Av. Presidente Vargas, 1200 — Centro", 
        "bairro": "Centro",
        "area_m2": 8500, 
        "valor_aproximado": 25500000, 
        "status": "Dívida Ativa Crítica", 
        "trilha_padrao": "Varejo, Indústria e Logística", 
        "lat": -22.9035, 
        "lon": -43.1812,
        "detalhes": "Antigo edifício comercial vazio há 6 anos. Possui passivo acumulado de IPTU e taxas."
    },
    {
        "id": "SQL-204.015-1", 
        "endereco": "Rua do Lavradio, 85 — Lapa", 
        "bairro": "Lapa",
        "area_m2": 3200, 
        "valor_aproximado": 9600000, 
        "status": "Subutilizado", 
        "trilha_padrao": "Saúde", 
        "lat": -22.9103, 
        "lon": -43.1818,
        "detalhes": "Sobrado de grande porte com pavimento superior abandonado. Ideal para clínica ou centro médico de atendimento."
    },
    {
        "id": "SQL-309.882-4", 
        "endereco": "Av. Rodrigues Alves, 315 — Saúde (Porto)", 
        "bairro": "Saúde",
        "area_m2": 15000, 
        "valor_aproximado": 52500000, 
        "status": "Abandonado (Porto Maravilha)", 
        "trilha_padrao": "Habitação", 
        "lat": -22.8955, 
        "lon": -43.1850,
        "detalhes": "Galpão logístico obsoleto na Zona Portuária. Potencial para retrofit residencial (Reviver Centro)."
    },
    {
        "id": "SQL-412.330-7", 
        "endereco": "Rua Riachuelo, 210 — Bairro de Fátima", 
        "bairro": "Fátima",
        "area_m2": 5000, 
        "valor_aproximado": 14000000, 
        "status": "Notificado (IPTU Progressivo)", 
        "trilha_padrao": "Educação", 
        "lat": -22.9150, 
        "lon": -43.1880,
        "detalhes": "Terreno com edificação escolar desativada. Alvo de notificação para cumprimento da função social da propriedade."
    },
    {
        "id": "SQL-501.991-2", 
        "endereco": "Rua da Carioca, 42 — Centro", 
        "bairro": "Centro",
        "area_m2": 2100, 
        "valor_aproximado": 7350000, 
        "status": "Dívida Ativa", 
        "trilha_padrao": "Varejo, Indústria e Logística", 
        "lat": -22.9078, 
        "lon": -43.1802,
        "detalhes": "Prédio comercial multistore com andares superiores ociosos no calçadão histórico."
    }
])

# ============================================================
# 3. MOTOR DE CÁLCULO FISCAL E ECONÔMICO
# ============================================================
ALIQUOTA_IPTU = 0.025 # 2.5% a.a.

def calcular_simulacao(area, valor_venal, trilha):
    iptu_cheio = valor_venal * ALIQUOTA_IPTU
    
    if trilha == "Varejo, Indústria e Logística":
        faturamento_m2 = 6000
        emprego_m2 = 25
        escada = [(6, 0), (8, 25), (10, 50), (999, 100)]
        iss_pct, icms_pct, itbi_ pct = 0.02, 0.03, 0.0
    elif trilha == "Saúde":
        faturamento_m2 = 8000
        emprego_m2 = 20
        escada = [(8, 0), (9, 25), (10, 50), (999, 100)]
        iss_pct, icms_pct, itbi_pct = 0.04, 0.01, 0.0
    elif trilha == "Educação":
        faturamento_m2 = 3500
        emprego_m2 = 45
        escada = [(6, 0), (8, 25), (10, 50), (999, 70)]
        iss_pct, icms_pct, itbi_pct = 0.045, 0.005, 0.0
    else: # Habitação
        faturamento_m2 = 0
        emprego_m2 = 200
        escada = [(6, 0), (8, 25), (10, 50), (999, 100)]
        iss_pct, icms_pct, itbi_pct = 0.0, 0.0, 0.03

    faturamento_anual = area * faturamento_m2
    empregos = area / emprego_m2
    iss_anual = faturamento_anual * iss_pct
    icms_anual = faturamento_anual * icms_pct
    itbi_comercial = valor_venal * itbi_pct

    pagos = []
    for ano in range(1, 14):
        pct = 100
        for ano_max, p in escada:
            if ano <= ano_max:
                pct = p
                break
        pagos.append(iptu_cheio * (pct / 100))

    return {
        "empregos": empregos,
        "faturamento": faturamento_anual,
        "iss": iss_anual,
        "icms": icms_anual,
        "itbi": itbi_comercial,
        "iptu_pago": pagos,
        "iptu_cheio": iptu_cheio
    }

# ============================================================
# 4. INTERFACE DO APLICATIVO
# ============================================================
st.title("🗺️ GIS-Gov Rio | Mapeamento de Ativos e Projeção Fiscal")
st.markdown("Navegue pelo mapa interativo do município, explore os imóveis mapeados em **dívida ativa / ociosos** (pontos vermelhos) e clique para simular o potencial de arrecadação e empregos.")

# Sidebar de Seleção Rápida ou Filtro por Bairro
with st.sidebar:
    st.header("🎯 Seleção de Imóveis")
    bairro_filtro = st.selectbox("Filtrar por Bairro:", ["Todos"] + list(df_imoveis["bairro"].unique()))
    
    if bairro_filtro != "Todos":
        df_filtrado = df_imoveis[df_imoveis["bairro"] == bairro_filtro]
    else:
        df_filtrado = df_imoveis
        
    imovel_escolhido_str = st.selectbox(
        "Escolha o Imóvel:",
        options=df_filtrado["endereco"].tolist()
    )
    
    # Obter dados do imóvel selecionado
    dados_loc = df_imoveis[df_imoveis["endereco"] == imovel_escolhido_str].iloc[0]
    
    st.markdown("---")
    st.markdown("### ⚙️ Parâmetro de Trilha")
    trilha_sel = st.selectbox(
        "Trilha Setorial de Reconversão:",
        ["Varejo, Indústria e Logística", "Saúde", "Educação", "Habitação"],
        index=["Varejo, Indústria e Logística", "Saúde", "Educação", "Habitação"].index(dados_loc["trilha_padrao"])
    )

# ============================================================
# 5. MAPA INTERATIVO (ESTILO GOOGLE MAPS)
# ============================================================
st.subheader("📍 Mapa de Ociosidade e Dívida Ativa")
st.caption("💡 Dica: Dê zoom no mapa, navegue pelas regiões do Rio e clique nos marcadores para identificar os locais.")

# Criar o mapa com Plotly OpenStreetMap (Gratuito e sem token)
fig_mapa = px.scatter_mapbox(
    df_imoveis,
    lat="lat",
    lon="lon",
    hover_name="endereco",
    hover_data=["id", "status", "valor_aproximado"],
    color_discrete_sequence=[VERMELHO],
    zoom=13,
    center={"lat": dados_loc["lat"], "lon": dados_loc["lon"]},
    height=420
)

fig_mapa.update_traces(marker=dict(size=14, symbol="circle"))
fig_mapa.update_layout(
    mapbox_style="open-street-map",
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="#FFFFFF",
)

st.plotly_chart(fig_mapa, use_container_width=True)

# ============================================================
# 6. PAINEL DE DADOS DO IMÓVEL SELECIONADO
# ============================================================
st.markdown("---")
st.subheader(f"🏢 Ficha do Imóvel Selecionado: {dados_loc['bairro']}")

col_f1, col_f2 = st.columns([1.5, 1])

with col_f1:
    st.markdown(f"""
    <div style="background-color: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 18px;">
        <p style="margin: 0; font-size: 12px; color: #475569; font-weight: bold;">INSCRIÇÃO IMOBILIÁRIA (SQL): {dados_loc['id']}</p>
        <p style="margin: 4px 0 10px 0; font-size: 17px; font-weight: 800; color: #1B3A5C;">{dados_loc['endereco']}</p>
        <p style="margin: 0; font-size: 13.5px; color: #0F172A; line-height: 1.5;"><b>Contexto Urbano:</b> {dados_loc['detalhes']}</p>
        <hr style="margin: 12px 0; border-color: #CBD5E1;">
        <span style="background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;">⚠️ {dados_loc['status']}</span>
    </div>
    """, unsafe_allow_html=True)

with col_f2:
    st.markdown(f"""
    <div style="background-color: #F1F5F9; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 18px; text-align: center;">
        <div style="font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase;">Valor Aproximado do Imóvel (Venal / Mercado)</div>
        <div style="font-size: 26px; font-weight: 800; color: #B8892F; margin-top: 6px;">{fmt_moeda(dados_loc['valor_aproximado'])}</div>
        <div style="font-size: 12px; color: #0F172A; margin-top: 4px;">Área Construída / Lote: <b>{fmt_num(dados_loc['area_m2'])} m²</b></div>
    </div>
    """, unsafe_allow_html=True)

# Executar simulação com os dados do local escolhido
sim = calcular_simulacao(dados_loc["area_m2"], dados_loc["valor_aproximado"], trilha_sel)

# ============================================================
# 7. PROJEÇÃO MATEMÁTICA E ECONÔMICA (LÁ EM BAIXO)
# ============================================================
st.markdown("---")
st.subheader("📈 Projeção Matemática e Retorno Econômico (13 Anos)")
st.caption("Resultados estimados de impacto socioeconômico e arrecadação tributária com base na reconversão funcional do ativo selecionado.")

m1, m2, m3 = st.columns(3)
with m1:
    render_card(fmt_num(sim["empregos"]), "Empregos Diretos Estimados", NAVY)
with m2:
    render_card(fmt_moeda(sim["faturamento"]), "Faturamento Anual Estimado", NAVY)
with m3:
    tot_indireto_ano1 = sim["iss"] + sim["icms"] + sim["itbi"]
    render_card(fmt_moeda(tot_indireto_ano1), "Tributos Indiretos (Ano 1)", VERDE)

st.write("")
st.subheader("📊 Gráfico de Evolução Fiscal por Imposto (Do Ano 0 ao Ano 11)")

anos_eixo = [f"Ano {a}" for a in range(0, 12)]
iptu_linha = [0] + sim["iptu_pago"][:11]

fig_proj = go.Figure()

# IPTU (Dourado)
fig_proj.add_trace(go.Scatter(
    x=anos_eixo, y=iptu_linha, mode="lines+markers",
    name="IPTU Pago (com Isenção)",
    line=dict(color=GOLD, width=4, shape="spline"), marker=dict(size=8)
))

if trilha_sel == "Habitação":
    itbi_linha = [0, sim["itbi"]] + [0] * 10
    fig_proj.add_trace(go.Scatter(
        x=anos_eixo, y=itbi_linha, mode="lines+markers",
        name="ITBI (Comercialização)",
        line=dict(color=VERDE, width=4, shape="spline"), marker=dict(size=8)
    ))
else:
    iss_linha = [0] + [sim["iss"]] * 11
    icms_linha = [0] + [sim["icms"]] * 11
    fig_proj.add_trace(go.Scatter(
        x=anos_eixo, y=iss_linha, mode="lines+markers",
        name="ISS (Imposto Sobre Serviços)",
        line=dict(color=AZUL_ROYAL, width=4, shape="spline"), marker=dict(size=8)
    ))
    fig_proj.add_trace(go.Scatter(
        x=anos_eixo, y=icms_linha, mode="lines+markers",
        name="ICMS / VAF",
        line=dict(color=VERDE, width=4, shape="spline"), marker=dict(size=8)
    ))

fig_proj.update_layout(
    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=TXT_DARK)),
    margin=dict(l=5, r=5, t=10, b=10), height=380,
    xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(color=TXT_DARK)),
    yaxis=dict(gridcolor="#E2E8F0", tickprefix="R$ ", tickfont=dict(color=TXT_DARK))
)

st.plotly_chart(fig_proj, use_container_width=True)
st.caption("💡 **Análise de Balanço Fiscal:** No **Ano 0** (fase de obras), os impostos iniciam em R$ 0. A partir do **Ano 1** (operação), os tributos indiretos entram em regime contínuo, superando amplamente o IPTU enquanto durar o incentivo de reconversão.")
