import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import math

# 1. Configuração Inicial
st.set_page_config(page_title="PRISMA RIO", layout="wide", initial_sidebar_state="collapsed")

# 2. Reset de CSS Seguro para Celular (Evitando bugs de Dark Mode)
st.markdown("""
<style>
    /* Forçando as cores para não sumirem no modo claro/escuro do celular */
    .stApp { background-color: #F8FAFC !important; }
    h1, h2, h3, p, div, span, label { color: #0F172A !important; }
    
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border-bottom: 3px solid #D97706;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .hero-banner h1 { color: #FFFFFF !important; font-size: 24px; margin: 0; font-weight: 800;}
    .hero-banner p { color: #CBD5E1 !important; font-size: 14px; margin-top: 5px; }
    
    .kpi-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        border-top: 4px solid #2563EB;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-title { color: #64748B !important; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    .kpi-value { color: #0F172A !important; font-size: 22px; font-weight: 800; margin-top: 4px; }
    
    .asset-card { background: #FFFFFF !important; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    .asset-address { font-size: 18px; font-weight: 800; color: #0F172A !important; margin-top: 4px;}
    .asset-sql { color: #64748B !important; font-size: 12px; font-weight: bold;}
    
    .tag-status { 
        display: inline-block; 
        background: #FEE2E2 !important; 
        color: #991B1B !important; 
        padding: 6px 12px; 
        border-radius: 6px; 
        font-size: 12px; 
        font-weight: bold; 
        margin-top: 12px;
        border: 1px solid #FCA5A5;
    }
    
    .data-grid { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 20px; }
    .data-item { background: #F1F5F9 !important; padding: 16px; border-radius: 8px; border: 1px solid #E2E8F0;}
    .data-label { font-size: 11px; color: #64748B !important; text-transform: uppercase; font-weight: 700;}
    .data-val { font-size: 16px; font-weight: 800; color: #0F172A !important; margin-top: 4px;}
</style>
""", unsafe_allow_html=True)

# 3. Formatadores
def fmt_moeda(val):
    if val is None or math.isnan(val): return "R$ 0"
    return f"R$ {val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_num(val):
    if val is None or math.isnan(val): return "0"
    return f"{val:,.0f}".replace(",", ".")

# 4. Dados
df_imoveis = pd.DataFrame([
    {"id": "SQL-101.002-9", "endereco": "Av. Pres. Vargas, 1200", "bairro": "Centro", "area_m2": 8500, "v_venal": 25500000, "status": "Dívida Ativa Crítica", "trilha": "Varejo e Logística", "lat": -22.9035, "lon": -43.1812, "score_risco": 8.5, "desc": "Antigo edifício comercial vazio há 6 anos."},
    {"id": "SQL-204.015-1", "endereco": "Rua do Lavradio, 85", "bairro": "Lapa", "area_m2": 3200, "v_venal": 9600000, "status": "Subutilizado", "trilha": "Saúde", "lat": -22.9103, "lon": -43.1818, "score_risco": 4.2, "desc": "Sobrado histórico com pavimento superior abandonado."},
    {"id": "SQL-309.882-4", "endereco": "Av. Rodrigues Alves, 315", "bairro": "Saúde (Porto)", "area_m2": 15000, "v_venal": 52500000, "status": "Abandonado", "trilha": "Habitação", "lat": -22.8955, "lon": -43.1850, "score_risco": 9.1, "desc": "Galpão obsoleto no coração do Porto Maravilha."},
    {"id": "SQL-412.330-7", "endereco": "Rua Riachuelo, 210", "bairro": "Fátima", "area_m2": 5000, "v_venal": 14000000, "status": "Notificado", "trilha": "Educação", "lat": -22.9150, "lon": -43.1880, "score_risco": 6.8, "desc": "Edificação escolar desativada. Foco de notificação fiscal."}
])

if "selected_id" not in st.session_state: st.session_state.selected_id = df_imoveis.iloc[0]["id"]

# 5. Lógica Preditiva
def simular_cenario(dados, tx_inflacao_aa, tx_desconto_wacc, ano_venda_itbi):
    area, vv, trilha = dados["area_m2"], dados["v_venal"], dados["trilha"]
    
    if trilha == "Varejo e Logística":
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 6000, 25, 0.02, 0.03, 0.0
        escada = [(6, 0), (8, 25), (10, 50), (999, 100)]
    elif trilha == "Saúde":
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 8000, 20, 0.04, 0.01, 0.0
        escada = [(8, 0), (9, 25), (10, 50), (999, 100)]
    elif trilha == "Educação":
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 3500, 45, 0.045, 0.005, 0.0
        escada = [(6, 0), (8, 25), (10, 50), (999, 70)]
    else: 
        f_m2, emp_m2, iss_p, icms_p, itbi_p = 0, 200, 0.0, 0.0, 0.03
        escada = [(6, 0), (8, 25), (10, 50), (999, 100)]

    fat_ano0 = area * f_m2
    empregos = int(area / emp_m2)
    fluxo, vpl_total = [], 0
    
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
        
        iptu_pago = (vv_atual * 0.025) * (pct_pgto / 100)
        iss_pago = fat_atual * iss_p
        icms_pago = fat_atual * icms_p
        itbi_pago = (vv_atual * itbi_p) if (ano == ano_venda_itbi and trilha == "Habitação") else 0
        
        rec_total = iptu_pago + iss_pago + icms_pago + itbi_pago
        vpl_total += (rec_total / f_desconto)
        fluxo.append({"Ano": f"Ano {ano}", "Faturamento": fat_atual, "IPTU": iptu_pago, "ISS": iss_pago, "ICMS": icms_pago, "ITBI": itbi_pago})
        
    return {"fluxo": pd.DataFrame(fluxo), "empregos": empregos, "vpl_projetado": vpl_total, "fat_medio": fat_ano0 * ((1 + (tx_inflacao_aa / 100)) ** 5)}

# 6. Hero Banner
st.markdown("""
<div class="hero-banner">
    <h1>PRISMA RIO</h1>
    <p>Plataforma Preditiva de Reconversão Imobiliária e Impacto Fiscal</p>
</div>
""", unsafe_allow_html=True)

# 7. Sidebar e Controles
with st.sidebar:
    st.markdown("### 🔍 Governança de Ativos")
    idx_atual = list(df_imoveis["id"].values).index(st.session_state.selected_id) if st.session_state.selected_id in df_imoveis["id"].values else 0
    end_escolhido = st.selectbox("Selecione o Imóvel:", df_imoveis["endereco"].tolist(), index=idx_atual)
    ativo = df_imoveis[df_imoveis["endereco"] == end_escolhido].iloc[0]
    st.session_state.selected_id = ativo["id"]
    
    st.markdown("---")
    st.markdown("### ⚙️ Parâmetros Macroeconômicos")
    tx_inflacao = st.slider("IPCA Projetado (% a.a.)", 2.0, 12.0, 4.5)
    tx_desconto = st.slider("WACC / Taxa Desconto (%)", 4.0, 18.0, 10.0)
    ano_itbi = st.slider("Ano Venda (ITBI)", 1, 12, 3) if ativo["trilha"] == "Habitação" else 1

sim = simular_cenario(ativo, tx_inflacao, tx_desconto, ano_itbi)
df_f = sim["fluxo"]

# 8. KPIs (Ajustado para Celular - 2 colunas)
col1, col2 = st.columns(2)
with col1:
    st.markdown(f'<div class="kpi-card" style="border-top-color: #059669;"><div class="kpi-title">VPL Municipal (13 Anos)</div><div class="kpi-value">{fmt_moeda(sim["vpl_projetado"])}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-card" style="border-top-color: #2563EB;"><div class="kpi-title">Faturamento Setorial</div><div class="kpi-value">{fmt_moeda(sim["fat_medio"])}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card" style="border-top-color: #D97706;"><div class="kpi-title">Empregos Diretos</div><div class="kpi-value">{fmt_num(sim["empregos"])}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-card" style="border-top-color: #DC2626;"><div class="kpi-title">Score de Risco Urbano</div><div class="kpi-value">{ativo["score_risco"]}/10</div></div>', unsafe_allow_html=True)

st.markdown("---")

# 9. Mapa e Ficha (Ajustado para mobile vertical)
st.markdown("### 📍 Auditoria Geoespacial (Clique nos pinos)")
m = folium.Map(location=[ativo["lat"], ativo["lon"]], zoom_start=15, tiles="OpenStreetMap")
for idx, row in df_imoveis.iterrows():
    is_active = (row["id"] == ativo["id"])
    color = "blue" if is_active else "red"
    if is_active:
        folium.CircleMarker(location=[row["lat"], row["lon"]], radius=30, color="#2563EB", fill=True, fill_opacity=0.2).add_to(m)
    folium.Marker(location=[row["lat"], row["lon"]], tooltip=row["endereco"], icon=folium.Icon(color=color, icon="star" if is_active else "info-sign")).add_to(m)

map_out = st_folium(m, width="100%", height=350, key="mapa_final")

if map_out and map_out.get("last_object_clicked"):
    c_lat, c_lon = map_out["last_object_clicked"]["lat"], map_out["last_object_clicked"]["lng"]
    df_imoveis["dist"] = (df_imoveis["lat"] - c_lat)**2 + (df_imoveis["lon"] - c_lon)**2
    closest = df_imoveis.loc[df_imoveis["dist"].idxmin()]
    if closest["dist"] < 0.001 and closest["id"] != st.session_state.selected_id:
        st.session_state.selected_id = closest["id"]
        st.rerun()

st.markdown(f"""
<div class="asset-card">
    <div class="asset-sql">{ativo['id']} | {ativo['bairro']}</div>
    <div class="asset-address">{ativo['endereco']}</div>
    <div class="tag-status">⚠️ {ativo['status']}</div>
    <p style="margin-top: 16px; font-size: 14px; color: #475569; line-height: 1.5;"><b>Parecer de Campo:</b> {ativo['desc']}</p>
    
    <div class="data-grid">
        <div class="data-item">
            <div class="data-label">Vocação Setorial (Trilha)</div>
            <div class="data-val">{ativo['trilha']}</div>
        </div>
        <div class="data-item">
            <div class="data-label">Valor Patrimonial Base Estimado</div>
            <div class="data-val" style="color: #D97706;">{fmt_moeda(ativo['v_venal'])}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 10. Gráfico (Design Limpo e Empilhado)
st.markdown("### 📊 Balanço Projetado de Fluxo de Caixa")
fig = go.Figure()
fig.add_trace(go.Bar(x=df_f["Ano"], y=df_f["IPTU"], name='IPTU Recorrente', marker_color='#D97706'))

if ativo["trilha"] == "Habitação":
    fig.add_trace(go.Bar(x=df_f["Ano"], y=df_f["ITBI"], name='ITBI (Transação)', marker_color='#059669'))
else:
    fig.add_trace(go.Bar(x=df_f["Ano"], y=df_f["ISS"], name='ISSQN (Serviços)', marker_color='#2563EB'))

fig.update_layout(
    barmode='stack',
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=0, r=0, t=10, b=10),
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color="#0F172A")),
    xaxis=dict(tickfont=dict(color="#64748B")),
    yaxis=dict(tickfont=dict(color="#64748B"), tickprefix="R$ ")
)
st.plotly_chart(fig, use_container_width=True)
