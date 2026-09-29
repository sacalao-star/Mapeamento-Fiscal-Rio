# ============================================================
# PRISMA RIO · PLATAFORMA ENTERPRISE DE INTELIGÊNCIA URBANA
# ============================================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# Importando a base de dados e o motor fiscal do nosso arquivo modular
from imoveis_db import BANCO_IMOVEIS, simular_cenario_fiscal

st.set_page_config(
    page_title="PRISMA RIO · Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .main-title { color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0; }
    .sub-title { color: #E2E8F0; font-size: 13.5px; margin-top: 4px; }
    
    .metric-card {
        background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 16px; text-align: center;
    }
    .metric-val { font-size: 22px; font-weight: 800; }
    .metric-lbl { color: #475569; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

df_imoveis = pd.DataFrame(BANCO_IMOVEIS)

def fmt_moeda(val): return f"R$ {round(val):,.0f}".replace(",", ".")
def fmt_num(val): return f"{round(val):,.0f}".replace(",", ".")

if "selected_id" not in st.session_state:
    st.session_state.selected_id = df_imoveis.iloc[0]["id"]

st.markdown("""
<div class="gov-badge">
    <div class="gov-header-top">Arquitetura Modular Enterprise v2.0</div>
    <div class="main-title">PRISMA RIO</div>
    <div class="sub-title">Plataforma Preditiva de Reconversão Imobiliária e Impacto Fiscal</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🎯 Governança de Ativos")
    bairro_sel = st.selectbox("Filtrar por Bairro:", ["Todos os Bairros"] + list(df_imoveis["bairro"].unique()))
    
    df_filt = df_imoveis if bairro_sel == "Todos os Bairros" else df_imoveis[df_imoveis["bairro"] == bairro_sel]
    idx_atual = list(df_filt["id"].values).index(st.session_state.selected_id) if st.session_state.selected_id in df_filt["id"].values else 0
    
    end_escolhido = st.selectbox("Selecionar Endereço:", df_filt["endereco"].tolist(), index=idx_atual)
    ativo = df_filt[df_filt["endereco"] == end_escolhido].iloc[0]
    st.session_state.selected_id = ativo["id"]
    
    st.markdown("---")
    st.markdown("### ⚙️ Parâmetros Macro")
    tx_inflacao = st.slider("IPCA Projetado (% a.a.)", 2.0, 12.0, 4.5, 0.5)
    tx_desconto = st.slider("WACC / Taxa Desconto (%)", 4.0, 18.0, 10.0, 0.5)
    ano_itbi = st.slider("Ano Venda Residencial (ITBI)", 1, 12, 3) if ativo["trilha"] == "Habitação" else 1

sim_resultado = simular_cenario_fiscal(ativo, tx_inflacao, tx_desconto, ano_itbi)
df_f = sim_resultado["fluxo"]

col_mapa, col_ficha = st.columns([1.5, 1])

with col_mapa:
    st.subheader("📍 Malha Geoespacial")
    m = folium.Map(location=[ativo["lat"], ativo["lon"]], zoom_start=14, tiles="OpenStreetMap")
    
    for _, row in df_imoveis.iterrows():
        is_Ativo = (row["id"] == ativo["id"])
        color = "blue" if is_Ativo else "red"
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"<b>{row['endereco']}</b><br>{row['status']}",
            tooltip=row["id"],
            icon=folium.Icon(color=color, icon="star" if is_Ativo else "info-sign")
        ).add_to(m)
        
    map_out = st_folium(m, width="100%", height=420, key="mapa_v2")
    
    if map_out and (map_out.get("last_object_clicked") or map_out.get("last_clicked")):
        click = map_out.get("last_object_clicked") or map_out.get("last_clicked")
        c_lat, c_lon = click.get("lat"), click.get("lng") or click.get("lon")
        if c_lat and c_lon:
            df_imoveis["dist"] = (df_imoveis["lat"] - c_lat)**2 + (df_imoveis["lon"] - c_lon)**2
            closest = df_imoveis.loc[df_imoveis["dist"].idxmin()]
            if closest["dist"] < 0.001 and closest["id"] != st.session_state.selected_id:
                st.session_state.selected_id = closest["id"]
                st.rerun()

with col_ficha:
    st.subheader("📑 Ficha do Ativo")
    st.markdown(f"""
    <div style="background-color: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 16px;">
        <p style="margin: 0; font-size: 11px; color: #475569; font-weight: bold;">SQL: {ativo['id']} | {ativo['bairro']}</p>
        <p style="margin: 4px 0 8px 0; font-size: 17px; font-weight: 800; color: #0F172A;">{ativo['endereco']}</p>
        <p style="margin: 0; font-size: 13px; color: #334155;"><b>Diagnóstico:</b> {ativo['detalhes']}</p>
        <p style="margin: 8px 0 0 0; font-size: 13px;"><b>Vocação (Trilha):</b> <b>{ativo['trilha']}</b></p>
        <hr style="margin: 10px 0; border-color: #CBD5E1;">
        <span style="background-color: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">⚠ {ativo['status']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.markdown(f"""
    <div style="background-color: #F1F5F9; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 14px; text-align: center;">
        <div style="font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;">Valor Venal Estimado</div>
        <div style="font-size: 24px; font-weight: 800; color: #D97706; margin-top: 4px;">{fmt_moeda(ativo['valor_aproximado'])}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.subheader("📊 Indicadores de Impacto (VPL & Macroeconomia)")
k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#059669;">{fmt_moeda(sim_resultado["vpl_projetado"])}</div><div class="metric-lbl">VPL Municipal (13 Anos)</div></div>', unsafe_allow_html=True)
with k2: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#2563EB;">{fmt_num(sim_resultado["empregos"])}</div><div class="metric-lbl">Empregos Diretos</div></div>', unsafe_allow_html=True)
with k3: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#D97706;">{fmt_moeda(sim_resultado["fat_medio_futuro"])}</div><div class="metric-lbl">Faturamento Setorial (Ano 5)</div></div>', unsafe_allow_html=True)
with k4: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#0F172A;">{ativo["area_m2"]:,} m²</div><div class="metric-lbl">Área do Imóvel</div></div>', unsafe_allow_html=True)

st.markdown("---")
st.subheader("📈 Projeção do Balanço Fiscal Consolidado")
fig = go.Figure()
fig.add_trace(go.Bar(x=df_f["Ano"], y=df_f["IPTU"], name='IPTU Recorrente', marker_color='#D97706'))

if ativo["trilha"] == "Habitação":
    fig.add_trace(go.Bar(x=df_f["Ano"], y=df_f["ITBI"], name='ITBI (Transação)', marker_color='#059669'))
else:
    fig.add_trace(go.Bar(x=df_f["Ano"], y=df_f["ISS"], name='ISSQN (Serviços)', marker_color='#2563EB'))
    fig.add_trace(go.Bar(x=df_f["Ano"], y=df_f["ICMS"], name='Repasse ICMS', marker_color='#10B981'))

fig.update_layout(
    barmode='stack', plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    margin=dict(l=0, r=0, t=10, b=10), height=380,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    xaxis=dict(tickfont=dict(color="#0F172A")), yaxis=dict(tickprefix="R$ ", tickfont=dict(color="#0F172A"))
)
st.plotly_chart(fig, use_container_width=True)
