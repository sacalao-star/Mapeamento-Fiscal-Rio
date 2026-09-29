import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS
# ============================================================
st.set_page_config(
    page_title="PRISMA RIO · Inteligência Territorial e Balanço Fiscal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS limpa e moderna
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF !important; color: #0F172A !important; }
    div[data-testid="stSidebar"] { background-color: #F1F5F9 !important; border-right: 1.5px solid #CBD5E1; }
    
    .gov-badge {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1.5px solid #D97706;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: left;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .gov-header-top { color: #FBBF24; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }
    .main-title { color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0; letter-spacing: 0.5px; }
    .sub-title { color: #E2E8F0; font-size: 13.5px; margin-top: 4px; }
    
    .metric-card {
        background: #F8FAFC;
        border: 1.5px solid #CBD5E1;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-val { font-size: 22px; font-weight: 800; }
    .metric-lbl { color: #475569; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

def fmt_moeda(val):
    if val is None: return "R$ 0"
    return f"R$ {round(val):,.0f}".replace(",", ".")

def fmt_num(val):
    if val is None: return "0"
    return f"{round(val):,.0f}".replace(",", ".")

def render_card(valor, legenda, cor="#0F172A"):
    html = f'<div class="metric-card"><div class="metric-val" style="color:{cor};">{valor}</div><div class="metric-lbl">{legenda}</div></div>'
    st.markdown(html, unsafe_allow_html=True)

# ============================================================
# 2. BASE DE DADOS COMPLETA DE IMÓVEIS (RIO DE JANEIRO)
# ============================================================
df_imoveis = pd.DataFrame([
    # Centro e Zona Portuária
    {
        "id": "SQL-101.002-9", 
        "endereco": "Av. Presidente Vargas, 1200 — Centro", 
        "bairro": "Centro",
        "area_m2": 8500, 
        "valor_aproximado": 25500000, 
        "status": "Dívida Ativa Crítica", 
        "trilha": "Varejo, Indústria e Logística", 
        "lat": -22.9035, 
        "lon": -43.1812,
        "detalhes": "Antigo edifício comercial vazio há 6 anos. Passivo acumulado de IPTU e taxas municipais."
    },
    {
        "id": "SQL-204.015-1", 
        "endereco": "Rua do Lavradio, 85 — Lapa", 
        "bairro": "Lapa",
        "area_m2": 3200, 
        "valor_aproximado": 9600000, 
        "status": "Subutilizado", 
        "trilha": "Saúde", 
        "lat": -22.9103, 
        "lon": -43.1818,
        "detalhes": "Sobrado de grande porte com pavimento superior abandonado. Alta demanda para clínica médica."
    },
    {
        "id": "SQL-309.882-4", 
        "endereco": "Av. Rodrigues Alves, 315 — Saúde", 
        "bairro": "Saúde (Porto)",
        "area_m2": 15000, 
        "valor_aproximado": 52500000, 
        "status": "Abandonado (Porto Maravilha)", 
        "trilha": "Habitação", 
        "lat": -22.8955, 
        "lon": -43.1850,
        "detalhes": "Galpão obsoleto na Zona Portuária. Potencial estratégico para retrofit residencial (Reviver Centro)."
    },
    {
        "id": "SQL-412.330-7", 
        "endereco": "Rua Riachuelo, 210 — Fátima", 
        "bairro": "Bairro de Fátima",
        "area_m2": 5000, 
        "valor_aproximado": 14000000, 
        "status": "Notificado (IPTU Progressivo)", 
        "trilha": "Educação", 
        "lat": -22.9150, 
        "lon": -43.1880,
        "detalhes": "Terreno com edificação escolar desativada. Alvo de notificação por descumprimento de função social."
    },
    {
        "id": "SQL-501.991-2", 
        "endereco": "Rua da Carioca, 42 — Centro", 
        "bairro": "Centro",
        "area_m2": 2100, 
        "valor_aproximado": 7350000, 
        "status": "Dívida Ativa", 
        "trilha": "Varejo, Indústria e Logística", 
        "lat": -22.9078, 
        "lon": -43.1802,
        "detalhes": "Prédio comercial multistore com andares superiores ociosos no calçadão histórico."
    },
    {
        "id": "SQL-602.114-8", 
        "endereco": "Av. Rio Branco, 156 — Centro", 
        "bairro": "Centro",
        "area_m2": 12000, 
        "valor_aproximado": 48000000, 
        "status": "Subutilizado", 
        "trilha": "Varejo, Indústria e Logística", 
        "lat": -22.9050, 
        "lon": -43.1775,
        "detalhes": "Edifício corporativo tradicional com baixa taxa de ocupação nos andares intermediários."
    },
    {
        "id": "SQL-703.441-3", 
        "endereco": "Rua Senador Pompeu, 180 — Santo Cristo", 
        "bairro": "Santo Cristo",
        "area_m2": 18500, 
        "valor_aproximado": 45000000, 
        "status": "Dívida Ativa Crítica", 
        "trilha": "Habitação", 
        "lat": -22.8930, 
        "lon": -43.1900,
        "detalhes": "Antigo complexo de armazéns ferroviários e portuários degradados."
    },
    {
        "id": "SQL-804.552-0", 
        "endereco": "Praça Tiradentes, 40 — Centro", 
        "bairro": "Centro",
        "area_m2": 4500, 
        "valor_aproximado": 16000000, 
        "status": "Abandonado", 
        "trilha": "Educação", 
        "lat": -22.9070, 
        "lon": -43.1850,
        "detalhes": "Edificação de relevância histórica com andares superiores fechados."
    },
    {
        "id": "SQL-905.663-1", 
        "endereco": "Rua do Ouvidor, 75 — Centro", 
        "bairro": "Centro",
        "area_m2": 1800, 
        "valor_aproximado": 6500000, 
        "status": "Subutilizado", 
        "trilha": "Varejo, Indústria e Logística", 
        "lat": -22.9020, 
        "lon": -43.1760,
        "detalhes": "Sobrado comercial multifamiliar ocioso no coração comercial."
    },
    # Zona Sul
    {
        "id": "SQL-112.774-2", 
        "endereco": "Rua Visconde de Pirajá, 350 — Ipanema", 
        "bairro": "Ipanema",
        "area_m2": 2800, 
        "valor_aproximado": 28000000, 
        "status": "Subutilizado", 
        "trilha": "Varejo, Indústria e Logística", 
        "lat": -22.9830, 
        "lon": -43.2040,
        "detalhes": "Laje corporativa e pavimentos comerciais com longo período de desocupação."
    },
    {
        "id": "SQL-123.885-6", 
        "endereco": "Praia de Botafogo, 228 — Botafogo", 
        "bairro": "Botafogo",
        "area_m2": 6200, 
        "valor_aproximado": 31000000, 
        "status": "Dívida Ativa", 
        "trilha": "Saúde", 
        "lat": -22.9430, 
        "lon": -43.1820,
        "detalhes": "Antiga sede empresarial com excelente infraestrutura ociosa na Enseada de Botafogo."
    },
    {
        "id": "SQL-134.996-7", 
        "endereco": "Rua do Catete, 190 — Catete", 
        "bairro": "Catete",
        "area_m2": 3500, 
        "valor_aproximado": 12500000, 
        "status": "Abandonado", 
        "trilha": "Habitação", 
        "lat": -22.9250, 
        "lon": -43.1780,
        "detalhes": "Solar histórico desocupado com grande potencial de retrofit para moradia."
    },
    {
        "id": "SQL-145.107-8", 
        "endereco": "Av. Nossa Senhora de Copacabana, 750 — Copacabana", 
        "bairro": "Copacabana",
        "area_m2": 2400, 
        "valor_aproximado": 15000000, 
        "status": "Subutilizado", 
        "trilha": "Saúde", 
        "lat": -22.9670, 
        "lon": -43.1850,
        "detalhes": "Galeria comercial com térreo e sobreloja desativados."
    },
    # Zona Norte e Grande Tijuca
    {
        "id": "SQL-156.218-9", 
        "endereco": "Av. Maracanã, 450 — Tijuca", 
        "bairro": "Tijuca",
        "area_m2": 7000, 
        "valor_aproximado": 22000000, 
        "status": "Dívida Ativa Crítica", 
        "trilha": "Varejo, Indústria e Logística", 
        "lat": -22.9210, 
        "lon": -43.2350,
        "detalhes": "Antigo showroom automotivo e estacionamento de grande porte ocioso."
    },
    {
        "id": "SQL-167.329-0", 
        "endereco": "Campo de São Cristóvão, 250 — São Cristóvão", 
        "bairro": "São Cristóvão",
        "area_m2": 14000, 
        "valor_aproximado": 35000000, 
        "status": "Abandonado", 
        "trilha": "Varejo, Indústria e Logística", 
        "lat": -22.9010, 
        "lon": -43.2200,
        "detalhes": "Galpão industrial obsoleto próximo às vias de escoamento logístico."
    },
    {
        "id": "SQL-178.430-1", 
        "endereco": "Rua Itapiru, 900 — Rio Comprido", 
        "bairro": "Rio Comprido",
        "area_m2": 11000, 
        "valor_aproximado": 24000000, 
        "status": "Notificado (IPTU Progressivo)", 
        "trilha": "Educação", 
        "lat": -22.9200, 
        "lon": -43.2050,
        "detalhes": "Complexo fabril desativado aguardando reconversão de zoneamento."
    }
])

if "selected_id" not in st.session_state:
    st.session_state.selected_id = df_imoveis.iloc[0]["id"]

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
        iss_pct, icms_pct, itbi_pct = 0.02, 0.03, 0.0
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
# 4. CABEÇALHO PROFISSIONAL INDEPENDENTE
# ============================================================
st.markdown("""
<div class="gov-badge">
    <div class="gov-header-top">Núcleo de Estudos de Inteligência Territorial e Urbana</div>
    <div class="main-title">PRISMA RIO</div>
    <div class="sub-title">Plataforma Independente de Reconversão Imobiliária e Simulação de Impacto Fiscal</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 5. BARRA LATERAL (SELEÇÃO)
# ============================================================
with st.sidebar:
    st.header("🎯 Filtros e Ativos")
    bairro_filtro = st.selectbox("Filtrar por Região:", ["Todos os Bairros"] + list(df_imoveis["bairro"].unique()))
    
    df_filtrado = df_imoveis if bairro_filtro == "Todos os Bairros" else df_imoveis[df_imoveis["bairro"] == bairro_filtro]
    
    current_idx = 0
    if st.session_state.selected_id in df_filtrado["id"].values:
        current_idx = list(df_filtrado["id"].values).index(st.session_state.selected_id)

    imovel_escolhido = st.selectbox(
        "Selecione o Endereço:",
        options=df_filtrado["endereco"].tolist(),
        index=current_idx
    )
    
    row_selecionada = df_filtrado[df_filtrado["endereco"] == imovel_escolhido].iloc[0]
    st.session_state.selected_id = row_selecionada["id"]
    
    st.markdown("---")
    st.markdown("### ℹ️ Navegação no Mapa")
    st.caption("Alterne o imóvel pelo menu acima ou **clique diretamente nos marcadores do mapa** para mudar a operação instantaneamente.")

dados_loc = df_imoveis[df_imoveis["id"] == st.session_state.selected_id].iloc[0]

# ============================================================
# 6. MAPA INTERATIVO COM CAPTURA DE CLIQUE EM MARCADORES
# ============================================================
st.subheader("📍 Mapa Interativo de Ativos")
st.caption(f"Ativo selecionado: **{dados_loc['endereco']}** ({len(df_imoveis)} imóveis mapeados na base)")

m = folium.Map(location=[dados_loc["lat"], dados_loc["lon"]], zoom_start=13, tiles="OpenStreetMap")

for idx, r in df_imoveis.iterrows():
    is_active = (r["id"] == dados_loc["id"])
    color = "blue" if is_active else "red"
    icon_glyph = "star" if is_active else "info-sign"
    
    folium.Marker(
        location=[r["lat"], r["lon"]],
        popup=f"<b>{r['endereco']}</b><br>Status: {r['status']}<br>Área: {r['area_m2']} m²",
        tooltip=f"{r['id']} - {r['bairro']}",
        icon=folium.Icon(color=color, icon=icon_glyph)
    ).add_to(m)

# Captura de cliques no mapa / marcadores
map_output = st_folium(m, width="100%", height=450, key="mapa_interativo")

clicked_coords = None
if map_output:
    if map_output.get("last_object_clicked"):
        clicked_coords = map_output["last_object_clicked"]
    elif map_output.get("last_clicked"):
        clicked_coords = map_output["last_clicked"]

if clicked_coords:
    clicked_lat = clicked_coords.get("lat")
    clicked_lon = clicked_coords.get("lng") or clicked_coords.get("lon")
    if clicked_lat and clicked_lon:
        df_imoveis["dist"] = (df_imoveis["lat"] - clicked_lat)**2 + (df_imoveis["lon"] - clicked_lon)**2
        closest = df_imoveis.loc[df_imoveis["dist"].idxmin()]
        
        if closest["dist"] < 0.001 and closest["id"] != st.session_state.selected_id:
            st.session_state.selected_id = closest["id"]
            st.rerun()

# ============================================================
# 7. FICHA TÉCNICA DO ATIVO SELECIONADO
# ============================================================
st.markdown("---")
col_f1, col_f2 = st.columns([1.5, 1])

with col_f1:
    st.markdown(f"""
    <div style="background-color: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 18px;">
        <p style="margin: 0; font-size: 12px; color: #475569; font-weight: bold;">INSCRIÇÃO IMOBILIÁRIA (SQL): {dados_loc['id']}</p>
        <p style="margin: 4px 0 10px 0; font-size: 18px; font-weight: 800; color: #0F172A;">{dados_loc['endereco']}</p>
        <p style="margin: 0; font-size: 13.5px; color: #334155; line-height: 1.5;"><b>Diagnóstico Urbano:</b> {dados_loc['detalhes']}</p>
        <p style="margin: 10px 0 0 0; font-size: 13.5px; color: #0F172A;"><b>Vocação Setorial (Trilha):</b> <b>{dados_loc['trilha']}</b></p>
        <hr style="margin: 12px 0; border-color: #CBD5E1;">
        <span style="background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;">⚠️ {dados_loc['status']}</span>
    </div>
    """, unsafe_allow_html=True)

with col_f2:
    st.markdown(f"""
    <div style="background-color: #F1F5F9; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 18px; text-align: center;">
        <div style="font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase;">Valor de Mercado / Venal Estimado</div>
        <div style="font-size: 28px; font-weight: 800; color: #D97706; margin-top: 6px;">{fmt_moeda(dados_loc['valor_aproximado'])}</div>
        <div style="font-size: 13px; color: #334155; margin-top: 6px;">Área Útil / Terreno: <b>{fmt_num(dados_loc['area_m2'])} m²</b></div>
    </div>
    """, unsafe_allow_html=True)

sim = calcular_simulacao(dados_loc["area_m2"], dados_loc["valor_aproximado"], dados_loc["trilha"])

# ============================================================
# 8. PROJEÇÃO MATEMÁTICA E GRÁFICO EXECUTIVO DE BARRAS
# ============================================================
st.markdown("---")
st.subheader("📈 Projeção Matemática e Balanço Fiscal (13 Anos)")
st.caption("Simulação comparativa do fluxo de arrecadação tributária ao longo dos anos.")

m1, m2, m3 = st.columns(3)
with m1:
    render_card(fmt_num(sim["empregos"]), "Empregos Diretos Gerados", "#0F172A")
with m2:
    render_card(fmt_moeda(sim["faturamento"]), "Faturamento Setorial Anual", "#2563EB")
with m3:
    tot_indireto_ano1 = sim["iss"] + sim["icms"] + sim["itbi"]
    render_card(fmt_moeda(tot_indireto_ano1), "Tributos Indiretos (Ano 1)", "#059669")

st.write("")
st.subheader("📊 Gráfico Comparativo Anual de Arrecadação")

anos_eixo = [f"Ano {a}" for a in range(0, 12)]
iptu_barras = [0] + sim["iptu_pago"][:11]

fig_proj = go.Figure()

fig_proj.add_trace(go.Bar(
    x=anos_eixo, y=iptu_barras,
    name="IPTU Arrecadado",
    marker_color="#D97706"
))

if dados_loc["trilha"] == "Habitação":
    itbi_barras = [0, sim["itbi"]] + [0] * 10
    fig_proj.add_trace(go.Bar(
        x=anos_eixo, y=itbi_barras,
        name="ITBI (Operação)",
        marker_color="#059669"
    ))
else:
    iss_barras = [0] + [sim["iss"]] * 11
    icms_barras = [0] + [sim["icms"]] * 11
    
    fig_proj.add_trace(go.Bar(
        x=anos_eixo, y=iss_barras,
        name="ISS (Serviços)",
        marker_color="#2563EB"
    ))
    fig_proj.add_trace(go.Bar(
        x=anos_eixo, y=icms_barras,
        name="ICMS / VAF",
        marker_color="#059669"
    ))

fig_proj.update_layout(
    barmode="group",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color="#0F172A", size=12)),
    margin=dict(l=10, r=10, t=20, b=10),
    height=400,
    xaxis=dict(showgrid=False, tickfont=dict(color="#0F172A")),
    yaxis=dict(gridcolor="#E2E8F0", tickprefix="R$ ", tickfont=dict(color="#0F172A"))
)

st.plotly_chart(fig_proj, use_container_width=True)
st.markdown("""
<div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #334155; margin-top: 10px;">
    💡 <b>Nota Analítica:</b> O modelo demonstra o salto na arrecadação municipal com a conversão de ativos ociosos, equilibrando a transição fiscal de curto e longo prazo.
</div>
""", unsafe_allow_html=True)
