import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gestão de Bloco Cirúrgico", layout="wide")
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        div[data-testid="stMetricValue"] {font-size: 24px;}
    </style>
""", unsafe_allow_html=True)

# 1. Carregamento e Cálculos de Tempo
@st.cache_data
def carregar_dados():
    df = pd.read_excel("dados.xlsx", skiprows=3, header=None)
    
    # Pegando as colunas principais e também as de datas e horas de Cirurgia e Limpeza
    # 13,14 (Início Cirurgia) | 15,16 (Fim Cirurgia) | 21,22 (Início Limpeza) | 23,24 (Fim Limpeza)
    cols = [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 21, 22, 23, 24]
    df_sub = df.iloc[:, cols].dropna(subset=[0]).copy()
    
    df_sub.columns = [
        'ID', 'IDADE', 'SEXO', 'PORTE', 'ESPECIALIDADE', 'SALA', 'CID',
        'D_INI_CIR', 'H_INI_CIR', 'D_FIM_CIR', 'H_FIM_CIR',
        'D_INI_LIM', 'H_INI_LIM', 'D_FIM_LIM', 'H_FIM_LIM'
    ]
    
    # Limpando espaços de texto
    for col in ['SEXO', 'PORTE', 'ESPECIALIDADE', 'SALA', 'CID']:
        df_sub[col] = df_sub[col].astype(str).str.strip()
        
    df_sub['IDADE'] = pd.to_numeric(df_sub['IDADE'], errors='coerce')

    # TRUQUE DE MESTRE: Juntando Data e Hora para calcular os minutos exatos!
    df_sub['Inicio_Cirurgia'] = pd.to_datetime(df_sub['D_INI_CIR'].astype(str).str[:10] + ' ' + df_sub['H_INI_CIR'].astype(str), errors='coerce')
    df_sub['Fim_Cirurgia'] = pd.to_datetime(df_sub['D_FIM_CIR'].astype(str).str[:10] + ' ' + df_sub['H_FIM_CIR'].astype(str), errors='coerce')
    df_sub['Inicio_Limpeza'] = pd.to_datetime(df_sub['D_INI_LIM'].astype(str).str[:10] + ' ' + df_sub['H_INI_LIM'].astype(str), errors='coerce')
    df_sub['Fim_Limpeza'] = pd.to_datetime(df_sub['D_FIM_LIM'].astype(str).str[:10] + ' ' + df_sub['H_FIM_LIM'].astype(str), errors='coerce')

    # Calculando a duração em minutos
    df_sub['Tempo_Cirurgia_Min'] = (df_sub['Fim_Cirurgia'] - df_sub['Inicio_Cirurgia']).dt.total_seconds() / 60
    df_sub['Tempo_Limpeza_Min'] = (df_sub['Fim_Limpeza'] - df_sub['Inicio_Limpeza']).dt.total_seconds() / 60

    return df_sub

df = carregar_dados()

# 2. Barra Lateral (Os Filtros que afetam TODAS as páginas)
st.sidebar.header("🔍 Filtros Operacionais")

df_filtrado = df.copy()

especialidades = ["Todas"] + sorted(list(df['ESPECIALIDADE'].unique()))
esp_selecionada = st.sidebar.selectbox("Especialidade:", especialidades)
if esp_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['ESPECIALIDADE'] == esp_selecionada]

salas = ["Todas"] + sorted(list(df_filtrado['SALA'].unique()))
sala_selecionada = st.sidebar.selectbox("Número da Sala:", salas)
if sala_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['SALA'] == sala_selecionada]

cids = ["Todos"] + sorted(list(df_filtrado['CID'].unique()))
cid_selecionado = st.sidebar.selectbox("CID Principal:", cids)
if cid_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['CID'] == cid_selecionado]

# 3. Criando as Páginas (Abas)
st.title("🏥 Gestão Estratégica - Bloco Cirúrgico")

aba1, aba2, aba3 = st.tabs(["📊 Visão Geral", "⏱️ Tempos e Movimentos", "📋 Base de Dados"])

# ================= ABA 1: VISÃO GERAL =================
with aba1:
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Cirurgias", len(df_filtrado))
    kpi2.metric("Média Idade", f"{int(df_filtrado['IDADE'].mean()) if not df_filtrado['IDADE'].dropna().empty else 0} anos")
    kpi3.metric("Salas Ativas", df_filtrado['SALA'].nunique())
    kpi4.metric("Top CID", df_filtrado['CID'].mode()[0] if not df_filtrado.empty else "N/A")
    kpi5.metric("Top Especialidade", df_filtrado['ESPECIALIDADE'].mode()[0] if not df_filtrado.empty else "N/A")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Volume por Especialidade")
        st.line_chart(df_filtrado['ESPECIALIDADE'].value_counts())
    with col2:
        st.subheader("📈 Volume por Sala")
        st.line_chart(df_filtrado['SALA'].value_counts())

    st.subheader("📋 CIDs Mais Frequentes")
    st.bar_chart(df_filtrado['CID'].value_counts().head(10), horizontal=True)

# ================= ABA 2: TEMPOS (GIRO DE SALA) =================
with aba2:
    st.markdown("### Eficiência do Bloco")
    
    # Calculando médias gerais de tempo para os KPIs
    media_cir = df_filtrado['Tempo_Cirurgia_Min'].mean()
    media_limp = df_filtrado['Tempo_Limpeza_Min'].mean()
    
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Tempo Médio de Cirurgia", f"{media_cir:.0f} min" if pd.notna(media_cir) else "N/A")
    col_t2.metric("Tempo Médio de Limpeza", f"{media_limp:.0f} min" if pd.notna(media_limp) else "N/A")
    col_t3.metric("Tempo Total de Giro Médio", f"{(media_cir + media_limp):.0f} min" if pd.notna(media_cir) else "N/A")
    
    st.divider()
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("🧹 Média de Limpeza por Sala (Minutos)")
        # Agrupa o tempo médio de limpeza por sala
        if not df_filtrado.empty:
            limpeza_sala = df_filtrado.groupby('SALA')['Tempo_Limpeza_Min'].mean()
            st.bar_chart(limpeza_sala, color="#ff7f0e")
            
    with col_g2:
        st.subheader("✂️ Média de Cirurgia por Especialidade (Minutos)")
        if not df_filtrado.empty:
            cirurgia_esp = df_filtrado.groupby('ESPECIALIDADE')['Tempo_Cirurgia_Min'].mean()
            st.bar_chart(cirurgia_esp, color="#2ca02c")

# ================= ABA 3: BASE DE DADOS =================
with aba3:
    st.markdown("### Extração de Dados")
    st.write("Visualize ou exporte a tabela abaixo com os filtros aplicados.")
    st.dataframe(df_filtrado[['ID', 'IDADE', 'SEXO', 'ESPECIALIDADE', 'SALA', 'CID', 'Tempo_Cirurgia_Min', 'Tempo_Limpeza_Min']], use_container_width=True)