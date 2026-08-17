import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gestão de Bloco Cirúrgico", layout="wide")
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        div[data-testid="stMetricValue"] {font-size: 20px;}
    </style>
""", unsafe_allow_html=True)

# 1. Carregamento e Cálculos de Tempo Completos
@st.cache_data
def carregar_dados():
    df = pd.read_excel("dados.xlsx", skiprows=3, header=None)
    
    # Selecionando colunas de identificação e todas as etapas de data/hora relevantes
    # 9,10 (Entrada Sala) | 11,12 (Início Anestesia) | 17,18 (Fim Anestesia) | 19,20 (Saída Sala)
    # 21,22 (Início Limpeza) | 23,24 (Fim Limpeza) | 27,28 (UTI/Enfermaria)
    cols = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 17, 18, 19, 20, 21, 22, 23, 24, 27, 28]
    df_sub = df.iloc[:, cols].dropna(subset=[0]).copy()
    
    df_sub.columns = [
        'ID', 'IDADE', 'SEXO', 'PORTE', 'ESPECIALIDADE', 'SALA', 'CID',
        'D_ENT_SALA', 'H_ENT_SALA', 'D_INI_ANEST', 'H_INI_ANEST',
        'D_FIM_ANEST', 'H_FIM_ANEST', 'D_SAIDA_SALA', 'H_SAIDA_SALA',
        'D_INI_LIM', 'H_INI_LIM', 'D_FIM_LIM', 'H_FIM_LIM',
        'D_UTI', 'H_UTI'
    ]
    
    for col in ['SEXO', 'PORTE', 'ESPECIALIDADE', 'SALA', 'CID']:
        df_sub[col] = df_sub[col].astype(str).str.strip()
        
    df_sub['IDADE'] = pd.to_numeric(df_sub['IDADE'], errors='coerce')

    # Combinando Datas e Horas de forma segura
    def combine_dt(d_col, h_col):
        return pd.to_datetime(df_sub[d_col].astype(str).str[:10] + ' ' + df_sub[h_col].astype(str), errors='coerce')

    df_sub['Entrada_Sala'] = combine_dt('D_ENT_SALA', 'H_ENT_SALA')
    df_sub['Inicio_Anestesia'] = combine_dt('D_INI_ANEST', 'H_INI_ANEST')
    df_sub['Fim_Anestesia'] = combine_dt('D_FIM_ANEST', 'H_FIM_ANEST')
    df_sub['Saida_Sala'] = combine_dt('D_SAIDA_SALA', 'H_SAIDA_SALA')
    df_sub['Inicio_Limpeza'] = combine_dt('D_INI_LIM', 'H_INI_LIM')
    df_sub['Fim_Limpeza'] = combine_dt('D_FIM_LIM', 'H_FIM_LIM')
    df_sub['UTI_Enfermaria'] = combine_dt('D_UTI', 'H_UTI')

    # Cálculo dos Tempos em Minutos
    df_sub['Tempo_Cirurgia_Min'] = (df_sub['Fim_Limpeza'] - df_sub['Inicio_Limpeza']).dt.total_seconds() / 60 # ajuste caso use fim cirurgia
    df_sub['Tempo_Anestesia_Min'] = (df_sub['Fim_Anestesia'] - df_sub['Inicio_Anestesia']).dt.total_seconds() / 60
    df_sub['Tempo_Sala_Min'] = (df_sub['Saida_Sala'] - df_sub['Entrada_Sala']).dt.total_seconds() / 60
    df_sub['Tempo_Limpeza_Min'] = (df_sub['Fim_Limpeza'] - df_sub['Inicio_Limpeza']).dt.total_seconds() / 60
    df_sub['Tempo_Saida_UTI_Horas'] = (df_sub['UTI_Enfermaria'] - df_sub['Saida_Sala']).dt.total_seconds() / 3600

    return df_sub

df = carregar_dados()

# 2. Barra Lateral (Filtros)
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

# 3. Páginas (Abas)
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

# ================= ABA 2: TEMPOS E MOVIMENTOS =================
with aba2:
    st.markdown("### ⏱️ Indicadores de Desempenho e Tempos Operacionais")
    
    # Calculando estatísticas
    m_anes = df_filtrado['Tempo_Anestesia_Min'].mean()
    med_anes = df_filtrado['Tempo_Anestesia_Min'].median()
    
    m_sala = df_filtrado['Tempo_Sala_Min'].mean()
    med_sala = df_filtrado['Tempo_Sala_Min'].median()
    
    # Filtro para evitar inconsistências temporais negativas na admissão UTI
    df_uti_valido = df_filtrado[df_filtrado['Tempo_Saida_UTI_Horas'] >= 0]
    m_uti = df_uti_valido['Tempo_Saida_UTI_Horas'].mean()
    med_uti = df_uti_valido['Tempo_Saida_UTI_Horas'].median()

    # Linha 1 de Métricas (Anestesia e Permanência em Sala)
    st.markdown("#### 💉 Anestesia & 🚪 Permanência em Sala")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Média Anestesia", f"{m_anes:.0f} min" if pd.notna(m_anes) else "N/A")
    t2.metric("Mediana Anestesia", f"{med_anes:.0f} min" if pd.notna(med_anes) else "N/A")
    t3.metric("Média Entrada ➔ Saída", f"{m_sala:.0f} min" if pd.notna(m_sala) else "N/A")
    t4.metric("Mediana Entrada ➔ Saída", f"{med_sala:.0f} min" if pd.notna(med_sala) else "N/A")
    
    st.markdown("---")
    
    # Linha 2 de Métricas (Saída da Sala vs Admissão UTI/Enfermaria)
    st.markdown("#### 🛏️ Intervalo: Saída de Sala ➔ Admissão UTI/Enfermaria")
    u1, u2 = st.columns(2)
    u1.metric("Tempo Médio (Saída ➔ UTI)", f"{m_uti:.1f} horas" if pd.notna(m_uti) else "N/A")
    u2.metric("Tempo Mediano (Saída ➔ UTI)", f"{med_uti:.1f} horas" if pd.notna(med_uti) else "N/A")
    
    st.divider()
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("🧹 Média de Limpeza por Sala (Minutos)")
        if not df_filtrado.empty:
            limpeza_sala = df_filtrado.groupby('SALA')['Tempo_Limpeza_Min'].mean()
            st.bar_chart(limpeza_sala, color="#ff7f0e")
            
    with col_g2:
        st.subheader("⏳ Média de Permanência em Sala por Especialidade")
        if not df_filtrado.empty:
            sala_esp = df_filtrado.groupby('ESPECIALIDADE')['Tempo_Sala_Min'].mean()
            st.bar_chart(sala_esp, color="#2ca02c")

# ================= ABA 3: BASE DE DADOS =================
with aba3:
    st.markdown("### Extração de Dados")
    st.write("Visualize ou exporte a tabela abaixo com os filtros aplicados.")
    st.dataframe(df_filtrado[['ID', 'IDADE', 'SEXO', 'ESPECIALIDADE', 'SALA', 'CID', 'Tempo_Anestesia_Min', 'Tempo_Sala_Min']], use_container_width=True)