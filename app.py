import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import time

# ============================================================
# CONFIGURAÇÕES DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="GIS-Gov | Simulador de Mapeamento Fiscal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores
NAVY = "#1B3A5C"
GOLD = "#B8892F"
VERMELHO = "#B42318"
VERDE = "#15803D"
AZUL_ROYAL = "#2563EB"
TXT_DARK = "#0F172A"

# Estilos CSS Personalizados
st.markdown("""
<style>
    .metric-card { background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 10px; }
    .metric-val { font-size: 20px; font-weight: 800; }
    .metric-lbl { color: #475569; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-top: 4px; }
    .stApp { background-color: #FFFFFF; color: #0F172A; }
    div[data-testid="stSidebar"] { background-color: #F1F5F9; border-right: 1.5px solid #CBD5E1; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNÇÕES UTILITÁRIAS E APIs (Gratuitas)
# ============================================================
def fmt_moeda(val):
    return f"R$ {val:,.0f}".replace(",", ".")

def fmt_num(val):
    return f"{val:,.0f}".replace(",", ".")

@st.cache_data(ttl=3600)
def geocode_endereco(endereco):
    """API Gratuita do OpenStreetMap (Nominatim) para converter endereço em Lat/Lon."""
    url = f"https://nominatim.openstreetmap.org/search?q={endereco}&format=json&limit=1"
    headers = {"User-Agent": "GISGovSimulador/1.0"}
    try:
        time.sleep(1) # Respeitar política de uso da API
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()[0]
            return float(data['lat']), float(data['lon'])
    except Exception as e:
        pass
    return None, None

@st.cache_data(ttl=3600)
def consultar_cnpj(cnpj_puro):
    """API Gratuita (BrasilAPI) para dados empresariais."""
    cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj_puro)))
    if len(cnpj_limpo) != 14:
        return None
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


# ============================================================
# BASE DE DADOS SIMULADA (Ativos Ociosos / Dívida Ativa)
# ============================================================
# Base estruturada interna (Dívida Ativa real possui sigilo fiscal).
dados_iniciais = [
    {"id": "SQL-001", "endereco": "Av. Presidente Vargas, Centro, Rio de Janeiro", "cnpj": "00000000000191", "area_m2": 8500, "v_venal": 25000000, "status": "Dívida Ativa Crítica", "trilha_sugerida": "Varejo, Indústria e Logística", "lat": -22.9035, "lon": -43.1812},
    {"id": "SQL-002", "endereco": "Rua do Lavradio, Lapa, Rio de Janeiro", "cnpj": "33683111000107", "area_m2": 3200, "v_venal": 8000000, "status": "Subutilizado", "trilha_sugerida": "Saúde", "lat": -22.9103, "lon": -43.1818},
    {"id": "SQL-003", "endereco": "Av. Rodrigues Alves, Saúde, Rio de Janeiro", "cnpj": "12345678000195", "area_m2": 15000, "v_venal": 45000000, "status": "Abandonado", "trilha_sugerida": "Habitação", "lat": -22.8955, "lon": -43.1850},
    {"id": "SQL-004", "endereco": "Rua Riachuelo, Bairro de Fátima, Rio de Janeiro", "cnpj": "11222333000181", "area_m2": 5000, "v_venal": 12500000, "status": "Notificado (IPTU Prog.)", "trilha_sugerida": "Educação", "lat": -22.9150, "lon": -43.1880},
]

if "df_imoveis" not in st.session_state:
    st.session_state.df_imoveis = pd.DataFrame(dados_iniciais)


# ============================================================
# CÁLCULOS DO MOTOR FISCAL
# ============================================================
ALIQUOTA_IPTU = 0.025 # 2.5%

def simular_balanco_fiscal(area, v_venal, trilha):
    iptu_cheio = v_venal * ALIQUOTA_IPTU
    
    if trilha == "Varejo, Indústria e Logística":
        faturamento_m2 = 6000
        emprego_m2 = 25
        escada = [(6, 0), (8, 25), (10, 50), (13, 100)]
        aliquota_iss, aliquota_icms = 0.02, 0.03
    elif trilha == "Saúde":
        faturamento_m2 = 8000
        emprego_m2 = 20
        escada = [(8, 0), (9, 25), (10, 50), (13, 100)]
        aliquota_iss, aliquota_icms = 0.04, 0.01
    elif trilha == "Educação":
        faturamento_m2 = 3500
        emprego_m2 = 45
        escada = [(6, 0), (8, 25), (10, 50), (13, 70)] 
        aliquota_iss, aliquota_icms = 0.045, 0.005
    else: # Habitação
        faturamento_m2 = 0
        emprego_m2 = 200
        escada = [(6, 0), (8, 25), (10, 50), (13, 100)]
        aliquota_iss, aliquota_icms = 0, 0
        
    faturamento_anual = area * faturamento_m2
    empregos = area / emprego_m2
    iss_anual = faturamento_anual * aliquota_iss
    icms_anual = faturamento_anual * aliquota_icms
    itbi_inicial = v_venal * 0.03 if trilha == "Habitação" else 0
    
    iptu_pago = []
    for ano in range(1, 14):
        pct = 100
        for ano_max, pct_escada in escada:
            if ano <= ano_max:
                pct = pct_escada
                break
        iptu_pago.append(iptu_cheio * (pct / 100))
        
    return {
        "empregos": empregos,
        "faturamento": faturamento_anual,
        "iss": iss_anual,
        "icms": icms_anual,
        "itbi": itbi_inicial,
        "iptu_anual_pago": iptu_pago,
        "iptu_cheio": iptu_cheio
    }


# ============================================================
# INTERFACE PRINCIPAL
# ============================================================
st.title("🗺️ GIS-Gov | Inteligência Geográfica e Mapeamento Fiscal")
st.markdown("Sistema de localização de ativos ociosos em Dívida Ativa com cálculo de viabilidade fiscal e impacto socioeconômico de reconversão.")

# ----------------- BARRA LATERAL (FILTROS E BUSCA) -----------------
with st.sidebar:
    st.header("🔍 Busca e Parametrização")
    
    modo_busca = st.radio("Método de Seleção:", ["Catálogo Interno", "Busca por API (CNPJ)", "Busca por API (Endereço)"])
    
    imovel_sel_idx = 0
    novo_lat, novo_lon = None, None
    novo_dados = None
    
    if modo_busca == "Catálogo Interno":
        lista_opcoes = [f"{row['id']} - {row['endereco'].split(',')[0]}" for idx, row in st.session_state.df_imoveis.iterrows()]
        selecao = st.selectbox("Ativos Mapeados:", lista_opcoes)
        idx_sel = lista_opcoes.index(selecao)
        dados_imovel = st.session_state.df_imoveis.iloc[idx_sel]
        novo_lat, novo_lon = dados_imovel['lat'], dados_imovel['lon']
        
    elif modo_busca == "Busca por API (CNPJ)":
        st.caption("Usa BrasilAPI para puxar dados da empresa e vincular ao mapa.")
        input_cnpj = st.text_input("Digite o CNPJ (Ex: 00.000.000/0001-91):")
        if st.button("Consultar CNPJ") and input_cnpj:
            with st.spinner("Consultando Receita..."):
                res_cnpj = consultar_cnpj(input_cnpj)
                if res_cnpj:
                    st.success(f"Razão Social: {res_cnpj.get('razao_social')}")
                    endereco_fmt = f"{res_cnpj.get('logradouro')}, {res_cnpj.get('municipio')}, {res_cnpj.get('uf')}"
                    st.info(f"Localizando: {endereco_fmt}")
                    n_lat, n_lon = geocode_endereco(endereco_fmt)
                    if n_lat and n_lon:
                        novo_dados = {"id": "NOVO-API", "endereco": endereco_fmt, "cnpj": input_cnpj, "area_m2": 4000, "v_venal": 10000000, "status": "Simulação Customizada", "trilha_sugerida": "Varejo, Indústria e Logística", "lat": n_lat, "lon": n_lon}
                    else:
                        st.error("Não foi possível geocodificar o endereço na API do mapa.")
                else:
                    st.error("CNPJ Inválido ou API indisponível.")
                    
    elif modo_busca == "Busca por API (Endereço)":
        st.caption("Usa OpenStreetMap Nominatim para plotar pontos arbitrários.")
        input_end = st.text_input("Digite o Endereço Completo no Rio de Janeiro:")
        if st.button("Localizar no Mapa") and input_end:
            with st.spinner("Geocodificando..."):
                n_lat, n_lon = geocode_endereco(input_end)
                if n_lat and n_lon:
                    novo_dados = {"id": "NOVO-GEO", "endereco": input_end, "cnpj": "-", "area_m2": 3500, "v_venal": 8000000, "status": "Simulação Customizada", "trilha_sugerida": "Varejo, Indústria e Logística", "lat": n_lat, "lon": n_lon}
                else:
                    st.error("Local não encontrado.")

    if novo_dados:
        dados_imovel = pd.Series(novo_dados)
        novo_lat, novo_lon = dados_imovel['lat'], dados_imovel['lon']

# ----------------- MAPA PRINCIPAL E DETALHES -----------------
col_mapa, col_info = st.columns([1.8, 1])

with col_mapa:
    st.subheader("📍 Visualização Geoespacial")
    
    # Prepara o DataFrame do mapa
    df_plot = st.session_state.df_imoveis.copy()
    if novo_dados:
        df_plot = pd.concat([df_plot, pd.DataFrame([novo_dados])], ignore_index=True)
    
    # Criar mapa interativo 100% Gratuito (Plotly OpenStreetMap)
    fig_mapa = px.scatter_mapbox(
        df_plot,
        lat="lat",
        lon="lon",
        hover_name="endereco",
        hover_data=["id", "status", "area_m2"],
        color="status",
        color_discrete_map={
            "Dívida Ativa Crítica": VERMELHO,
            "Abandonado": "#991B1B",
            "Subutilizado": GOLD,
            "Notificado (IPTU Prog.)": "#EA580C",
            "Simulação Customizada": AZUL_ROYAL
        },
        zoom=13 if not novo_lat else 16,
        center={"lat": novo_lat or -22.9068, "lon": novo_lon or -43.1729},
        height=500
    )
    
    fig_mapa.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.8)"),
    )
    
    st.plotly_chart(fig_mapa, use_container_width=True)

with col_info:
    st.subheader("📊 Ficha do Ativo Selecionado")
    
    if 'dados_imovel' in locals():
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 15px;">
            <p style="margin: 0; font-size: 13px; color: #475569;"><b>ID / SQL:</b> {dados_imovel['id']}</p>
            <p style="margin: 3px 0; font-size: 15px; font-weight: 700; color: #1B3A5C;">{dados_imovel['endereco']}</p>
            <p style="margin: 0; font-size: 13px; color: #475569;"><b>CNPJ Vinculado:</b> {dados_imovel['cnpj']}</p>
            <hr style="margin: 10px 0; border-color: #CBD5E1;">
            <p style="margin: 0; font-size: 14px; color: {VERMELHO}; font-weight: bold;">⚠️ {dados_imovel['status']}</p>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #0F172A;"><b>Área do Lote:</b> {fmt_num(dados_imovel['area_m2'])} m²</p>
            <p style="margin: 0; font-size: 14px; color: #0F172A;"><b>Valor Venal Est.:</b> {fmt_moeda(dados_imovel['v_venal'])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        # Configurações para o motor
        trilha_dinamica = st.selectbox("Selecione a Trilha de Reconversão:", 
                                       ["Varejo, Indústria e Logística", "Saúde", "Educação", "Habitação"],
                                       index=["Varejo, Indústria e Logística", "Saúde", "Educação", "Habitação"].index(dados_imovel['trilha_sugerida']))
        
        sim_dados = simular_balanco_fiscal(dados_imovel['area_m2'], dados_imovel['v_venal'], trilha_dinamica)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:{NAVY};">{fmt_num(sim_dados["empregos"])}</div><div class="metric-lbl">Empregos (Est.)</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:{VERDE};">{fmt_moeda(sim_dados["iss"] + sim_dados["icms"] + sim_dados["itbi"])}</div><div class="metric-lbl">Imp. Indiretos (Ano 1)</div></div>', unsafe_allow_html=True)


# ----------------- MOTOR FISCAL / GRÁFICO PROJEÇÃO -----------------
if 'sim_dados' in locals():
    st.markdown("---")
    st.subheader("📈 Projeção do Balanço Fiscal (IPTU vs. Tributos Indiretos)")
    
    anos_eixo = [f"Ano {a}" for a in range(0, 14)]
    
    iptu_linha = [0] + sim_dados['iptu_anual_pago']
    iss_linha = [0] + [sim_dados['iss']] * 13
    icms_linha = [0] + [sim_dados['icms']] * 13
    
    fig_proj = go.Figure()
    
    # IPTU (Dourado)
    fig_proj.add_trace(go.Scatter(x=anos_eixo, y=iptu_linha, mode='lines+markers', name='IPTU Arrecadado (c/ Isenção)', line=dict(color=GOLD, width=4, shape="spline"), marker=dict(size=8)))
    
    if trilha_dinamica == "Habitação":
        itbi_linha = [0, sim_dados['itbi']] + [0] * 12
        fig_proj.add_trace(go.Scatter(x=anos_eixo, y=itbi_linha, mode='lines+markers', name='ITBI (Venda Inicial)', line=dict(color=VERDE, width=4, shape="spline"), marker=dict(size=8)))
    else:
        fig_proj.add_trace(go.Scatter(x=anos_eixo, y=iss_linha, mode='lines+markers', name='ISS Anual (Operação)', line=dict(color=AZUL_ROYAL, width=4, shape="spline"), marker=dict(size=8)))
        fig_proj.add_trace(go.Scatter(x=anos_eixo, y=icms_linha, mode='lines+markers', name='ICMS / VAF Anual', line=dict(color=VERDE, width=4, shape="spline"), marker=dict(size=8)))
        
    fig_proj.update_layout(
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=TXT_DARK)),
        margin=dict(l=10, r=10, t=10, b=10), height=380,
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#E2E8F0", tickprefix="R$ ")
    )
    
    st.plotly_chart(fig_proj, use_container_width=True)
