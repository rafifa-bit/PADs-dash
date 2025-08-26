import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard PAD - Processos Administrativos Disciplinares",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("⚖️ Dashboard PAD - Processos Administrativos Disciplinares")
st.markdown("---")
st.write("Bem-vindo ao Dashboard de Análise de Processos Administrativos Disciplinares (PADs).")
st.write("Por favor, faça o upload do arquivo Excel para iniciar a análise.")

# Widget de upload de arquivo
uploaded_file = st.file_uploader("Escolha um arquivo Excel", type="xlsx")

# Verifica se um arquivo foi enviado antes de prosseguir
if uploaded_file is None:
    st.info("Aguardando o upload do arquivo.")
    st.stop()

# Cache para carregar dados
@st.cache_data
def load_data(file):
    """Carrega e processa os dados do arquivo Excel a partir de um arquivo carregado"""
    try:
        # Lê o arquivo do objeto de upload
        # CORREÇÃO CRÍTICA: Use a variável 'file' que é o objeto do arquivo carregado
        # NÃO use um caminho de arquivo local fixo como 'C:\\Users\\...'
        df = pd.read_excel(file, sheet_name="PAD")

        # Processamento de datas
        df['DATA E HORA DE ENTRADA'] = pd.to_datetime(df['DATA E HORA DE ENTRADA'], errors='coerce')
        df['DATA DE ENTRADA'] = pd.to_datetime(df['DATA DE ENTRADA'], errors='coerce')
        
        # Extrair ano e mês para análises temporais
        df['ANO'] = df['DATA E HORA DE ENTRADA'].dt.year
        df['MES'] = df['DATA E HORA DE ENTRADA'].dt.month
        df['MES_ANO'] = df['DATA E HORA DE ENTRADA'].dt.to_period('M')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregar dados usando o arquivo carregado
df = load_data(uploaded_file)

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique a planilha ou o formato do arquivo.")
    st.stop()

# Sidebar com filtros
st.sidebar.header("🔍 Filtros")

# Filtro por ano
anos_disponiveis = sorted(df['ANO'].dropna().astype(int).unique())
if anos_disponiveis:
    ano_selecionado = st.sidebar.selectbox(
        "Selecione o Ano:",
        options=['Todos'] + list(anos_disponiveis),
        index=0
    )
else:
    ano_selecionado = 'Todos'

# Filtro por tipo
tipos_disponiveis = df['TIPO'].dropna().unique()
tipo_selecionado = st.sidebar.multiselect(
    "Selecione o Tipo:",
    options=tipos_disponiveis,
    default=list(tipos_disponiveis)
)

# Filtro por espécie
especies_disponiveis = df['ESPÉCIE'].dropna().unique()
especie_selecionada = st.sidebar.multiselect(
    "Selecione a Espécie:",
    options=especies_disponiveis,
    default=list(especies_disponiveis)
)

# Filtro por assunto
assuntos_disponiveis = df['ASSUNTO'].dropna().unique()
assunto_selecionado = st.sidebar.multiselect(
    "Selecione o Assunto:",
    options=assuntos_disponiveis,
    default=list(assuntos_disponiveis)
)

# Aplicar filtros
df_filtrado = df.copy()

if ano_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['ANO'] == ano_selecionado]

if tipo_selecionado:
    df_filtrado = df_filtrado[df_filtrado['TIPO'].isin(tipo_selecionado)]

if especie_selecionada:
    df_filtrado = df_filtrado[df_filtrado['ESPÉCIE'].isin(especie_selecionada)]

if assunto_selecionado:
    df_filtrado = df_filtrado[df_filtrado['ASSUNTO'].isin(assunto_selecionado)]

# Métricas principais
st.markdown("---")
st.subheader("📊 Resumo das Métricas")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_processos = len(df_filtrado)
    st.metric("Total de Processos", total_processos)

with col2:
    processos_pendentes = len(df_filtrado[df_filtrado['STATUS'] == 'Pendente'])
    st.metric("Processos Pendentes", processos_pendentes)

with col3:
    processos_com_decisao = len(df_filtrado[df_filtrado['DECISAO'].notna()])
    st.metric("Processos com Decisão", processos_com_decisao)

with col4:
    taxa_conclusao = (processos_com_decisao / total_processos * 100) if total_processos > 0 else 0
    st.metric("Taxa de Conclusão (%)", f"{taxa_conclusao:.1f}%")

st.markdown("---")

# Layout em duas colunas para os gráficos
col_left, col_right = st.columns(2)

with col_left:
    # Gráfico de distribuição por tipo
    st.subheader("📊 Distribuição por Tipo")
    if not df_filtrado['TIPO'].dropna().empty:
        tipo_counts = df_filtrado['TIPO'].value_counts()
        fig_tipo = px.pie(
            values=tipo_counts.values,
            names=tipo_counts.index,
            title="Distribuição de Processos por Tipo"
        )
        fig_tipo.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_tipo, use_container_width=True)
    else:
        st.info("Nenhum dado de tipo disponível para os filtros selecionados.")

    # Gráfico de distribuição por espécie
    st.subheader("📋 Distribuição por Espécie")
    if not df_filtrado['ESPÉCIE'].dropna().empty:
        especie_counts = df_filtrado['ESPÉCIE'].value_counts().head(10)
        fig_especie = px.bar(
            x=especie_counts.values,
            y=especie_counts.index,
            orientation='h',
            title="Top 10 Espécies de Documentos",
            labels={'x': 'Quantidade', 'y': 'Espécie'}
        )
        fig_especie.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_especie, use_container_width=True)
    else:
        st.info("Nenhum dado de espécie disponível para os filtros selecionados.")

with col_right:
    # Gráfico de distribuição por assunto
    st.subheader("🎯 Distribuição por Assunto")
    if not df_filtrado['ASSUNTO'].dropna().empty:
        assunto_counts = df_filtrado['ASSUNTO'].value_counts().head(10)
        fig_assunto = px.bar(
            x=assunto_counts.values,
            y=assunto_counts.index,
            orientation='h',
            title="Top 10 Assuntos",
            labels={'x': 'Quantidade', 'y': 'Assunto'}
        )
        fig_assunto.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_assunto, use_container_width=True)
    else:
        st.info("Nenhum dado de assunto disponível para os filtros selecionados.")

    # Gráfico de decisões
    st.subheader("⚖️ Distribuição de Decisões")
    if not df_filtrado['DECISAO'].dropna().empty:
        decisao_counts = df_filtrado['DECISAO'].value_counts()
        fig_decisao = px.pie(
            values=decisao_counts.values,
            names=decisao_counts.index,
            title="Distribuição de Decisões dos PADs"
        )
        fig_decisao.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_decisao, use_container_width=True)
    else:
        st.info("Nenhum dado de decisão disponível para os filtros selecionados.")

# Análise temporal
st.markdown("---")
st.subheader("📈 Análise Temporal")

if not df_filtrado['DATA E HORA DE ENTRADA'].dropna().empty:
    # Gráfico de linha temporal
    df_temporal = df_filtrado.groupby(df_filtrado['DATA E HORA DE ENTRADA'].dt.date).size().reset_index()
    df_temporal.columns = ['Data', 'Quantidade']
    
    fig_temporal = px.line(
        df_temporal,
        x='Data',
        y='Quantidade',
        title="Evolução Temporal dos Processos PAD",
        labels={'Data': 'Data de Entrada', 'Quantidade': 'Número de Processos'}
    )
    fig_temporal.update_layout(xaxis_title="Data de Entrada", yaxis_title="Número de Processos")
    st.plotly_chart(fig_temporal, use_container_width=True)
    
    # Análise por mês/ano
    col_temp1, col_temp2 = st.columns(2)
    
    with col_temp1:
        if not df_filtrado['MES_ANO'].dropna().empty:
            mes_ano_counts = df_filtrado['MES_ANO'].value_counts().sort_index()
            fig_mes_ano = px.bar(
                x=mes_ano_counts.index.astype(str),
                y=mes_ano_counts.values,
                title="Processos por Mês/Ano",
                labels={'x': 'Mês/Ano', 'y': 'Quantidade'}
            )
            fig_mes_ano.update_xaxes(tickangle=45)
            st.plotly_chart(fig_mes_ano, use_container_width=True)
    
    with col_temp2:
        if not df_filtrado['ANO'].dropna().empty:
            ano_counts = df_filtrado['ANO'].value_counts().sort_index()
            fig_ano = px.bar(
                x=ano_counts.index,
                y=ano_counts.values,
                title="Processos por Ano",
                labels={'x': 'Ano', 'y': 'Quantidade'}
            )
            st.plotly_chart(fig_ano, use_container_width=True)
else:
    st.info("Nenhum dado temporal disponível para os filtros selecionados.")

# Tabela de dados detalhados
st.markdown("---")
st.subheader("📋 Dados Detalhados")

# Seleção de colunas para exibir
colunas_disponiveis = df_filtrado.columns.tolist()
colunas_selecionadas = st.multiselect(
    "Selecione as colunas para exibir:",
    options=colunas_disponiveis,
    default=['ANO/PROTOCOLO', 'DATA DE ENTRADA', 'TIPO', 'ESPÉCIE', 'ASSUNTO', 'DECISAO', 'STATUS']
)

if colunas_selecionadas:
    st.dataframe(
        df_filtrado[colunas_selecionadas],
        use_container_width=True,
        height=400
    )
else:
    st.info("Selecione pelo menos uma coluna para exibir os dados.")

# Análise de valores ausentes
st.markdown("---")
st.subheader("🔍 Análise de Qualidade dos Dados")

col_qual1, col_qual2 = st.columns(2)

with col_qual1:
    st.write("**Valores Ausentes por Coluna:**")
    missing_data = df_filtrado.isnull().sum().sort_values(ascending=False)
    missing_percent = (missing_data / len(df_filtrado) * 100).round(2)
    
    missing_df = pd.DataFrame({
        'Coluna': missing_data.index,
        'Valores Ausentes': missing_data.values,
        'Percentual (%)': missing_percent.values
    })
    
    st.dataframe(missing_df, use_container_width=True, height=300)

with col_qual2:
    # Gráfico de valores ausentes
    fig_missing = px.bar(
        x=missing_percent.values[:10],
        y=missing_percent.index[:10],
        orientation='h',
        title="Top 10 Colunas com Valores Ausentes (%)",
        labels={'x': 'Percentual de Valores Ausentes (%)', 'y': 'Coluna'}
    )
    fig_missing.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_missing, use_container_width=True)

# Insights e recomendações
st.markdown("---")
st.subheader("💡 Insights e Recomendações")

insights = [
    "**Alta Taxa de Valores Ausentes:** Muitas colunas importantes têm valores ausentes significativos, impactando a análise.",
    "**Processos Pendentes:** A maioria dos processos com status definido está pendente, indicando possível acúmulo.",
    "**Absolvição por Prescrição:** É o desfecho mais comum, sugerindo morosidade nos processos.",
    "**Diversidade de Documentos:** Há uma grande variedade de tipos de documentos, indicando complexidade processual.",
    "**Concentração Temporal:** Análise temporal pode revelar padrões sazonais ou picos de demanda."
]

for insight in insights:
    st.write(f"• {insight}")

# Recomendações
st.subheader("📋 Recomendações")

recomendacoes = [
    "**Melhoria na Coleta de Dados:** Implementar validações obrigatórias para campos críticos.",
    "**Gestão de Prazos:** Criar alertas automáticos para evitar prescrições.",
    "**Digitalização:** Reduzir dependência de documentos físicos convertidos.",
    "**Monitoramento:** Implementar dashboard em tempo real para acompanhamento contínuo.",
    "**Capacitação:** Treinar equipe para preenchimento adequado dos dados."
]

for rec in recomendacoes:
    st.write(f"• {rec}")

# Rodapé
st.markdown("---")
st.markdown("**Dashboard desenvolvido para análise de Processos Administrativos Disciplinares (PAD)**")
st.markdown("*Dados atualizados automaticamente a partir do arquivo fonte*")
