import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import math

# ============================================================
# 1. CONFIGURAÇÃO GERAL E INJEÇÃO DE UI/UX (Enterprise Level)
# ============================================================
st.set_page_config(
    page_title="PRISMA RIO | Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS para aniquilar a "cara de Streamlit" e simular React/Next.js
st.markdown("""
<style>
    /* Reset e Variáveis globais */
    :root {
        --primary: #0F172A;
        --accent: #2563EB;
        --gold: #D97706;
        --success: #059669;
        --danger: #DC2626;
        --bg-main: #F8FAFC;
        --card-bg: #FFFFFF;
        --border: #E2E8F0;
        --text-main: #1E293B;
        --text-muted: #64748B;
    }
    
    /* Ocultar elementos nativos do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp { background-color: var(--bg-main) !important; color: var(--text-main) !important; font-family: 'Inter', sans-serif; }
    
    /* Customização da Sidebar */
    div[data-testid="stSidebar"] {
        background-color: var(--card-bg) !important;
        border-right: 1px solid var(--border);
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }
    
    /* Cabeçalho Corporativo Avançado */
    .hero-banner {
        background: linear-gradient(135deg, var(--primary) 0%, #1E293B 100%);
        border-bottom: 3px solid var(--gold);
        border-radius: 0 0 16px 16px;
        padding: 28px 32px;
        margin: -48px -1rem 24px -1rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-content h1 { color: #FFFFFF; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .hero-content p { color: #94A3B8; font-size: 14px; margin: 6px 0 0 0; font-weight: 500; }
    .hero-badge { background: rgba(217, 119, 6, 0.2); color: #FBBF24; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid rgba(217, 119, 6, 0.5); text-transform: uppercase; letter-spacing: 1px; }

    /* Cards de Métrica (Glassmorphism) */
    .kpi-container { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
    .kpi-card {
        flex: 1; min-width: 200px; background: var(--card-bg); border: 1px solid var(--border);
        border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-top: 4px solid var(--accent); transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-title { color: var(--text-muted); font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { color: var(--primary); font-size: 26px; font-weight: 800; line-height: 1.2; }
    
    /* Ficha do Imóvel */
    .asset-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .asset-header { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 16px; }
    .asset-sql { color: var(--text-muted); font-size: 12px; font-weight: bold; letter-spacing: 1px; }
    .asset-address { font-size: 20px; font-weight: 800; color: var(--primary); margin-top: 4px; }
    .tag-critical { background: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    .tag-warning { background: #FEF3C7; color: #B45309; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    
    .data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .data-item { background: var(--bg-main); padding: 12px; border-radius: 8px; border: 1px solid var(--border); }
    .data-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; margin-bottom: 4px;}
    .data-val { font-size: 16px; font-weight: 700; color: var(--primary); }

    /* Customizar Abas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; border-radius: 4px 4px 0px 0px; padding: 10px 0; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid var(--accent) !important; color: var(--accent) !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. FUNÇÕES ÚTEIS
# ============================================================
def fmt_moeda(val):
    if val is None or math.isnan(val): return "R$ 0"
    return f"R$ {val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_num(val):
    if val is None or math.isnan(val): return "0"
    return f"{val:,.0f}".replace(",", ".")

def create_kpi_card(title, value, color_hex="#2563EB"):
    return f'<div class="kpi-card" style="border-top-color: {color_hex};"><div class="kpi-title">{title}</div><div class="kpi-value">{value}</div></div>'

# ============================================================
# 3. BASE DE DADOS (SCORE DE RISCO INCLUSO)
# ============================================================
df_imoveis = pd.DataFrame([
    {"id": "SQL-101.002-9", "endereco": "Av. Presidente Vargas, 1200", "bairro": "Centro", "area_m2": 8500, "v_venal": 25500000, "status": "Dívida Ativa Crítica", "trilha": "Varejo, Ind. e Logística", "lat": -22.9035, "lon": -43.1812, "score_risco": 8.5, "desc": "Antigo edifício comercial vazio há 6 anos. Alto risco de degradação estrutural e invasão."},
    {"id": "SQL-204.015-1", "endereco": "Rua do Lavradio, 85", "bairro": "Lapa", "area_m2": 3200, "v_venal": 9600000, "status": "Subutilizado", "trilha": "Saúde", "lat": -22.9103, "lon": -43.1818, "score_risco": 4.2, "desc": "Sobrado de grande porte com pavimento superior abandonado. Entorno gentrificado."},
    {"id": "SQL-309.882-4", "endereco": "Av. Rodrigues Alves, 315", "bairro": "Saúde (Porto)", "area_m2": 15000, "v_venal": 52500000, "status": "Abandonado", "trilha": "Habitação", "lat": -22.8955, "lon": -43.1850, "score_risco": 9.1, "desc": "Galpão obsoleto no coração do Porto Maravilha. Foco estratégico do programa Reviver Centro."},
    {"id": "SQL-412.330-7", "endereco": "Rua Riachuelo, 210", "bairro": "Fátima", "area_m2": 5000, "v_venal": 14000000, "status": "Notificado (IPTU)", "trilha": "Educação", "lat": -22.9150, "lon": -43.1880, "score_risco": 6.8, "desc": "Terreno com edificação escolar desativada. Notificado para cumprimento da função social."},
    {"id": "SQL-156.218-9", "endereco": "Av. Maracanã, 450", "bairro": "Tijuca", "area_m2": 7000, "v_venal": 22000000, "status": "Dívida Ativa", "trilha": "Varejo, Ind. e Logística", "lat": -22.9210, "lon": -43.2350, "score_risco": 7.5, "desc": "Antigo showroom automotivo e estacionamento. Excelente viabilidade logística e fluxo."}
])

if "selected_id" not in st.session_state: st.session_state.selected_id = df_imoveis.iloc[0]["id"]

# ============================================================
# 4. MOTOR FINANCEIRO AVANÇADO (INFLAÇÃO + VPL)
# ============================================================
def simular_cenario(dados, tx_inflacao_aa, tx_desconto_wacc, ano_venda_itbi):
    area, vv, trilha = dados["area_m2"], dados["v_venal"], dados["trilha"]
    aliq_iptu = 0.025
    
    if trilha == "Varejo, Ind. e Logística":
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 6000, 25, 0.02, 0.03, 0.0
        escada = [(6, 0), (8, 25), (10, 50), (999, 100)]
    elif trilha == "Saúde":
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 8000, 20, 0.04, 0.01, 0.0
        escada = [(8, 0), (9, 25), (10, 50), (999, 100)]
    elif trilha == "Educação":
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 3500, 45, 0.045, 0.005, 0.0
        escada = [(6, 0), (8, 25), (10, 50), (999, 70)]
    else: # Habitação
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 0, 200, 0.0, 0.0, 0.03
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
        
        iptu_pago = (vv_atual * aliq_iptu) * (pct_pgto / 100)
        iss_pago = fat_atual * iss_p
        icms_pago = fat_atual * icms_p
        itbi_pago = (vv_atual * itbi_p) if (ano == ano_venda_itbi and trilha == "Habitação") else 0
        
        rec_total = iptu_pago + iss_pago + icms_pago + itbi_pago
        vpl_total += (rec_total / f_desconto)
        
        fluxo.append({"Ano": f"Ano {ano}", "Faturamento Estimado": fat_atual, "IPTU": iptu_pago, "ISS": iss_pago, "ICMS": icms_pago, "ITBI": itbi_pago, "Receita Total": rec_total})
        
    return {"fluxo": pd.DataFrame(fluxo), "empregos": empregos, "vpl_projetado": vpl_total, "fat_medio_futuro": fat_ano0 * ((1 + (tx_inflacao_aa / 100)) ** 5)}

# ============================================================
# 5. HERO BANNER PRINCIPAL
# ============================================================
st.markdown("""
<div class="hero-banner">
    <div class="hero-content">
        <div class="hero-badge">Acesso Master / Nível Executivo</div>
        <h1>PRISMA RIO</h1>
        <p>Plataforma Preditiva de Reconversão Imobiliária, Auditoria Espacial e Impacto Fiscal</p>
    </div>
    <div style="text-align: right; display: none;"></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 6. SIDEBAR (MOTOR MACROECONÔMICO E FILTROS)
# ============================================================
with st.sidebar:
    st.markdown('<div style="font-size: 14px; font-weight: 800; color: #0F172A; margin-bottom: 16px;">🔍 GOVERNANÇA DE ATIVOS</div>', unsafe_allow_html=True)
    bairro_sel = st.selectbox("Filtro Regional:", ["Rio de Janeiro (Todos)"] + list(df_imoveis["bairro"].unique()))
    df_filt = df_imoveis if bairro_sel == "Rio de Janeiro (Todos)" else df_imoveis[df_imoveis["bairro"] == bairro_sel]
    
    idx_atual = list(df_filt["id"].values).index(st.session_state.selected_id) if st.session_state.selected_id in df_filt["id"].values else 0
    end_escolhido = st.selectbox("Selecionar Inscrição Imobiliária:", df_filt["endereco"].tolist(), index=idx_atual)
    ativo_selecionado = df_filt[df_filt["endereco"] == end_escolhido].iloc[0]
    st.session_state.selected_id = ativo_selecionado["id"]
    
    st.markdown("---")
    st.markdown('<div style="font-size: 14px; font-weight: 800; color: #0F172A; margin-bottom: 16px;">⚙️ PAINEL MACROECONÔMICO (IA)</div>', unsafe_allow_html=True)
    tx_inflacao = st.slider("Projeção IPCA (% a.a.)", 2.0, 12.0, 4.5, 0.1)
    tx_desconto = st.slider("WACC / Taxa Desconto (%)", 4.0, 18.0, 10.0, 0.5)
    ano_itbi = st.slider("Ano de Venda Residencial (ITBI)", 1, 12, 3) if ativo_selecionado["trilha"] == "Habitação" else 1

resultado_sim = simular_cenario(ativo_selecionado, tx_inflacao, tx_desconto, ano_itbi)
df_fluxo = resultado_sim["fluxo"]

# ============================================================
# 7. DASHBOARD E ABAS
# ============================================================
st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(create_kpi_card("VPL Municipal (13 Anos)", fmt_moeda(resultado_sim["vpl_projetado"]), "#059669"), unsafe_allow_html=True)
with c2: st.markdown(create_kpi_card("Empregos Gerados", fmt_num(resultado_sim["empregos"]), "#2563EB"), unsafe_allow_html=True)
with c3: st.markdown(create_kpi_card("Faturamento Médio", fmt_moeda(resultado_sim["fat_medio_futuro"]), "#6366F1"), unsafe_allow_html=True)
with c4: st.markdown(create_kpi_card("Score de Risco Urbano", f"{ativo_selecionado['score_risco']}/10", "#DC2626"), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

tab_mapa, tab_fiscal, tab_tabela = st.tabs(["🗺️ Auditoria Geoespacial", "📊 Inteligência Fiscal", "📑 Matriz de Dados"])

with tab_mapa:
    col_mapa, col_ficha = st.columns([1.6, 1])
    with col_mapa:
        st.markdown('<div style="font-weight: 800; font-size: 16px; margin-bottom: 12px; color: #0F172A;">Nó Central de Monitoramento</div>', unsafe_allow_html=True)
        m = folium.Map(location=[ativo_selecionado["lat"], ativo_selecionado["lon"]], zoom_start=15, tiles="CartoDB positron")
        for idx, row in df_imoveis.iterrows():
            if row["id"] == ativo_selecionado["id"]:
                folium.CircleMarker(location=[row["lat"], row["lon"]], radius=35, color="#2563EB", fill=True, fill_color="#2563EB", fill_opacity=0.2, weight=2).add_to(m)
                folium.Marker(location=[row["lat"], row["lon"]], icon=folium.Icon(color="blue", icon="star")).add_to(m)
            else:
                folium.Marker(location=[row["lat"], row["lon"]], tooltip=row["endereco"], icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
        
        map_out = st_folium(m, width="100%", height=450, key="map_principal")
        if map_out and map_out.get("last_object_clicked"):
            c_lat, c_lon = map_out["last_object_clicked"]["lat"], map_out["last_object_clicked"]["lng"]
            df_imoveis["dist"] = (df_imoveis["lat"] - c_lat)**2 + (df_imoveis["lon"] - c_lon)**2
            closest = df_imoveis.loc[df_imoveis["dist"].idxmin()]
            if closest["dist"] < 0.001 and closest["id"] != st.session_state.selected_id:
                st.session_state.selected_id = closest["id"]
                st.rerun()
                
    with col_ficha:
        st.markdown(f"""
        <div class="asset-card">
            <div class="asset-header">
                <div><div class="asset-sql">{ativo_selecionado['id']} | {ativo_selecionado['bairro']}</div><div class="asset-address">{ativo_selecionado['endereco']}</div></div>
                <div><span class="{'tag-critical' if 'Dívida' in ativo_selecionado['status'] else 'tag-warning'}">{ativo_selecionado['status']}</span></div>
            </div>
            <p style="font-size: 13.5px; color: #475569; margin-bottom: 24px;"><b>Parecer IA:</b> {ativo_selecionado['desc']}</p>
            <div class="data-grid">
                <div class="data-item"><div class="data-label">Vocação Setorial</div><div class="data-val">{ativo_selecionado['trilha']}</div></div>
                <div class="data-item"><div class="data-label">Valor Patrimonial Base</div><div class="data-val" style="color: #D97706;">{fmt_moeda(ativo_selecionado['v_venal'])}</div></div>
                <div class="data-item"><div class="data-label">Metragem Auditada</div><div class="data-val">{fmt_num(ativo_selecionado['area_m2'])} m²</div></div>
                <div class="data-item"><div class="data-label">Coordenadas</div><div class="data-val" style="font-size: 13px;">{ativo_selecionado['lat']:.4f}, {ativo_selecionado['lon']:.4f}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab_fiscal:
    st.markdown('<div style="font-weight: 800; font-size: 16px; margin-bottom: 16px;">Balanço Projetado de Fluxo de Caixa Municipal</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_fluxo["Ano"], y=df_fluxo["IPTU"], mode='lines', name='IPTU', line=dict(width=3, color='#D97706', shape='spline'), stackgroup='one'))
    
    if ativo_selecionado["trilha"] == "Habitação":
        fig.add_trace(go.Scatter(x=df_fluxo["Ano"], y=df_fluxo["ITBI"], mode='lines', name='ITBI', line=dict(width=3, color='#059669', shape='spline'), stackgroup='one'))
    else:
        fig.add_trace(go.Scatter(x=df_fluxo["Ano"], y=df_fluxo["ISS"], mode='lines', name='ISSQN', line=dict(width=3, color='#2563EB', shape='spline'), stackgroup='one'))
        fig.add_trace(go.Scatter(x=df_fluxo["Ano"], y=df_fluxo["ICMS"], mode='lines', name='ICMS', line=dict(width=3, color='#10B981', shape='spline'), stackgroup='one'))

    fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), margin=dict(l=10, r=10, t=10, b=10), height=400, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab_tabela:
    st.markdown('<div style="font-weight: 800; font-size: 16px; margin-bottom: 16px;">Matriz de Exportação de Dados</div>', unsafe_allow_html=True)
    df_exibicao = df_fluxo.copy()
    for c in ["Faturamento Estimado", "IPTU", "ISS", "ICMS", "ITBI", "Receita Total"]:
        df_exibicao[c] = df_exibicao[c].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
