import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="ESN Porto Dashboard", layout="wide")

# --- Leitura dos dados ---
students = pd.read_csv("data/students.csv")
events = pd.read_csv("data/events.csv")
purchases = pd.read_csv("data/event_purchases.csv")

# --- Limpeza e padronização de colunas ---
# Padronizar nomes de colunas para facilitar merge
students.rename(columns={
    '_id': 'student_id',
    'email': 'student_email',
    'esnCardNumber': 'student_esnCard'
}, inplace=True)
events.rename(columns={
    '_id': 'event_id',
    'name': 'event_name'
}, inplace=True)
purchases.rename(columns={
    '_id': 'purchase_id',
    'eventId': 'event_id',
    'student_email': 'student_email',
    'student_esnCard': 'student_esnCard'
}, inplace=True)

# --- Merge dos dados ---
purchases_full = purchases.merge(events, on='event_id', how='left')
purchases_full = purchases_full.merge(students, on=['student_email', 'student_esnCard'], how='left')

# Converter datas para datetime
purchases_full['purchaseDate'] = pd.to_datetime(purchases_full['purchaseDate'], errors='coerce')
events['startDate'] = pd.to_datetime(events['startDate'], errors='coerce')
students['registerDate'] = pd.to_datetime(students['registerDate'], errors='coerce')

# --- Função para determinar o semestre ---
def get_semester(date):
    if pd.isna(date):
        return None
    month = date.month
    year = date.year
    if month in [9, 10, 11, 12, 1, 8]:  # Setembro a Janeiro + Agosto
        # Se for janeiro, usar o ano anterior para o Winter Semester
        if month == 1:
            return f"{str(year-1)[-2:]}.{str(year)[-2:]}-S1"
        return f"{str(year)[-2:]}.{str(year+1)[-2:]}-S1"
    elif month in [2, 3, 4, 5, 6, 7]:   # Fevereiro a Julho
        # Para o Semestre 2, usar o ano atual para ambos os números
        return f"{str(year-1)[-2:]}.{str(year)[-2:]}-S2"
    return None

# Adicionar coluna de semestre
purchases_full['semester'] = purchases_full['purchaseDate'].apply(get_semester)
events['semester'] = events['startDate'].apply(get_semester)

# --- SIDEBAR: Filtros ---
st.sidebar.header("Filtros")
filter_type = st.sidebar.radio("Como deseja filtrar?", ["Semestre", "Data"])

# Extrair semestres únicos dos dados
available_semesters = sorted(purchases_full['semester'].dropna().unique())
if len(available_semesters) > 0:
    semesters = ["All"] + list(available_semesters)
else:
    semesters = ["All"]

# Definir datas padrão
min_date = purchases_full['purchaseDate'].min().date()
max_date = purchases_full['purchaseDate'].max().date()

if filter_type == "Semestre":
    selected_semester = st.sidebar.selectbox("Selecione o semestre", semesters)
    if selected_semester != "All":
        purchases_filtered = purchases_full[purchases_full['semester'] == selected_semester]
        events_filtered = events[events['semester'] == selected_semester]
    else:
        purchases_filtered = purchases_full
        events_filtered = events
else:
    min_date = st.sidebar.date_input("Data mínima", min_date)
    max_date = st.sidebar.date_input("Data máxima", max_date)
    purchases_filtered = purchases_full[(purchases_full['purchaseDate'].dt.date >= min_date) & (purchases_full['purchaseDate'].dt.date <= max_date)]
    events_filtered = events[(events['startDate'].dt.date >= min_date) & (events['startDate'].dt.date <= max_date)]

# --- Interface do usuário ---
st.title("ESN Porto Dashboard")

# Criar abas para diferentes visualizações
tab_dashboard, tab_raw = st.tabs(["Dashboard", "Dados Brutos"])

with tab_dashboard:
    # --- KPIs iniciais ---
    total_arrecadado = purchases_filtered['amountPaid'].sum()
    total_participantes = purchases_filtered['student_email'].nunique()
    total_eventos = events_filtered['event_id'].nunique()
    total_vendas = len(purchases_filtered)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total arrecadado (€)", f"{total_arrecadado:,.2f}")
    col2.metric("Participantes únicos", total_participantes)
    col3.metric("Eventos organizados", total_eventos)
    col4.metric("Eventos vendidos", total_vendas)

    st.markdown("---")

    # --- Gráfico: Registros de ESN Cards por mês ---
    st.subheader("Registros de ESN Cards por mês")
    
    # Filtrar estudantes pelo mesmo período dos eventos/compras
    if filter_type == "Semestre" and selected_semester != "All":
        # Filtrar estudantes pelo mesmo semestre
        students_filtered = students[students['registerDate'].apply(get_semester) == selected_semester]
    else:
        # Usar as mesmas datas do filtro de data
        students_filtered = students[(students['registerDate'].dt.date >= min_date) & (students['registerDate'].dt.date <= max_date)]
    
    # Agrupar por mês e contar
    students_filtered['mes'] = students_filtered['registerDate'].dt.strftime('%Y-%m')
    esncards_por_mes = students_filtered.groupby('mes').size().reset_index()
    esncards_por_mes.columns = ['mes', 'quantidade']
    
    # Formatar os labels para serem mais amigáveis
    esncards_por_mes['mes'] = pd.to_datetime(esncards_por_mes['mes']).dt.strftime('%b/%Y')
    
    # Criar o gráfico com plotly
    fig = px.bar(
        esncards_por_mes,
        x='mes',
        y='quantidade',
        title='Registros de ESN Cards por Mês',
        labels={
            'mes': 'Mês',
            'quantidade': 'Número de Registros'
        }
    )
    
    # Melhorar a aparência do gráfico
    fig.update_layout(
        xaxis_title='Mês',
        yaxis_title='Número de Registros',
        showlegend=False,
        height=400
    )
    
    # Mostrar o gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar estatísticas abaixo do gráfico
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de registros no período", len(students_filtered))
    with col2:
        st.metric("Média mensal", f"{len(students_filtered)/len(esncards_por_mes):.1f}")

    st.markdown("---")

    # --- Gráfico: Eventos por mês ---
    st.subheader("Eventos por mês")
    
    # Agrupar eventos por mês
    events_filtered['mes'] = events_filtered['startDate'].dt.strftime('%Y-%m')
    eventos_por_mes = events_filtered.groupby('mes').size().reset_index()
    eventos_por_mes.columns = ['mes', 'quantidade']
    
    # Formatar os labels
    eventos_por_mes['mes'] = pd.to_datetime(eventos_por_mes['mes']).dt.strftime('%b/%Y')
    
    # Criar o gráfico
    fig_events = px.bar(
        eventos_por_mes,
        x='mes',
        y='quantidade',
        title='Número de Eventos por Mês',
        labels={
            'mes': 'Mês',
            'quantidade': 'Número de Eventos'
        }
    )
    
    fig_events.update_layout(
        xaxis_title='Mês',
        yaxis_title='Número de Eventos',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig_events, use_container_width=True)

    # --- Gráfico: Vendas de ingressos por mês ---
    st.subheader("Vendas de ingressos por mês")
    
    # Agrupar vendas por mês
    purchases_filtered['mes'] = purchases_filtered['purchaseDate'].dt.strftime('%Y-%m')
    vendas_por_mes = purchases_filtered.groupby('mes').agg({
        'amountPaid': 'sum',
        'purchase_id': 'count'
    }).reset_index()
    
    vendas_por_mes.columns = ['mes', 'valor_total', 'quantidade']
    vendas_por_mes['mes'] = pd.to_datetime(vendas_por_mes['mes']).dt.strftime('%b/%Y')
    
    # Criar dois gráficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de valor total
        fig_valor = px.bar(
            vendas_por_mes,
            x='mes',
            y='valor_total',
            title='Valor Total Arrecadado por Mês',
            labels={
                'mes': 'Mês',
                'valor_total': 'Valor Total (€)'
            }
        )
        
        fig_valor.update_layout(
            xaxis_title='Mês',
            yaxis_title='Valor Total (€)',
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig_valor, use_container_width=True)
    
    with col2:
        # Gráfico de quantidade
        fig_qtd = px.bar(
            vendas_por_mes,
            x='mes',
            y='quantidade',
            title='Quantidade de Ingressos Vendidos por Mês',
            labels={
                'mes': 'Mês',
                'quantidade': 'Quantidade de Ingressos'
            }
        )
        
        fig_qtd.update_layout(
            xaxis_title='Mês',
            yaxis_title='Quantidade de Ingressos',
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig_qtd, use_container_width=True)
    
    # Mostrar estatísticas abaixo dos gráficos
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total arrecadado", f"€ {vendas_por_mes['valor_total'].sum():,.2f}")
    with col2:
        st.metric("Total de ingressos", f"{vendas_por_mes['quantidade'].sum():,}")
    with col3:
        st.metric("Ticket médio", f"€ {vendas_por_mes['valor_total'].sum()/vendas_por_mes['quantidade'].sum():,.2f}")

    st.markdown("---")

    # --- Gráfico: Nacionalidades ---
    st.subheader("Distribuição de Nacionalidades")
    
    # Filtrar estudantes pelo mesmo período
    if filter_type == "Semestre" and selected_semester != "All":
        students_filtered = students[students['registerDate'].apply(get_semester) == selected_semester]
    else:
        students_filtered = students[(students['registerDate'].dt.date >= min_date) & (students['registerDate'].dt.date <= max_date)]
    
    # Contar nacionalidades
    nacionalidades = students_filtered['nationality'].value_counts().reset_index()
    nacionalidades.columns = ['Nacionalidade', 'Quantidade']
    
    # Opção para selecionar número de nacionalidades
    n_nacionalidades = st.slider(
        "Número de nacionalidades a mostrar",
        min_value=5,
        max_value=50,
        value=10,
        step=1
    )
    
    # Filtrar top N nacionalidades
    nacionalidades = nacionalidades.head(n_nacionalidades)
    
    # Criar gráfico
    fig_nacionalidades = px.bar(
        nacionalidades,
        x='Quantidade',
        y='Nacionalidade',
        orientation='h',
        title=f'Top {n_nacionalidades} Nacionalidades',
        labels={
            'Nacionalidade': 'Nacionalidade',
            'Quantidade': 'Número de Estudantes'
        }
    )
    
    fig_nacionalidades.update_layout(
        xaxis_title='Número de Estudantes',
        yaxis_title='Nacionalidade',
        showlegend=False,
        height=400,
        yaxis={'categoryorder':'total ascending'}
    )
    
    st.plotly_chart(fig_nacionalidades, use_container_width=True)
    
    # Mostrar estatísticas
    total_nacionalidades = students_filtered['nationality'].nunique(dropna=True)
    total_estudantes = len(students_filtered)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de nacionalidades", total_nacionalidades)
    with col2:
        st.metric("Total de estudantes", total_estudantes)

    st.markdown("---")

    # --- Análise de Coorte ---
    st.subheader("Análise de Coorte de Estudantes")
    
    # Botão de informação sobre análise de coorte
    with st.expander("ℹ️ O que é Análise de Coorte?"):
        st.markdown("""
        **Análise de Coorte** é uma técnica que agrupa usuários com base em um evento comum (neste caso, a primeira compra) e analisa seu comportamento ao longo do tempo.

        **Como interpretar este gráfico:**
        - Cada linha representa um grupo de estudantes que fizeram sua primeira compra no mesmo mês
        - Cada coluna mostra quantos desses estudantes continuaram comprando nos meses seguintes
        - As cores indicam a taxa de retenção:
          - 🟢 Verde: Alta retenção (muitos estudantes continuaram comprando)
          - 🟡 Amarelo: Retenção média
          - 🔴 Vermelho: Baixa retenção (poucos estudantes continuaram comprando)

        **Por que é importante?**
        - Ajuda a identificar padrões de engajamento dos estudantes
        - Mostra quais grupos de estudantes são mais ativos
        - Permite avaliar a efetividade de estratégias de retenção
        - Ajuda a prever o comportamento futuro dos estudantes

        **Exemplo prático:**
        Se 100 estudantes fizeram sua primeira compra em Janeiro (Mês 0) e 60 deles fizeram compras em Fevereiro (Mês 1), a retenção para esse mês é de 60%.
        """)
    
    # Preparar dados para análise de coorte
    def get_month_year(date):
        return pd.to_datetime(date).strftime('%Y-%m')
    
    # Criar coorte baseada no mês de primeira compra do estudante
    first_purchase = purchases_filtered.groupby('student_email')['purchaseDate'].min().reset_index()
    first_purchase['cohort_month'] = first_purchase['purchaseDate'].apply(get_month_year)
    
    # Adicionar mês de coorte às compras
    purchases_with_cohort = purchases_filtered.merge(
        first_purchase[['student_email', 'cohort_month']],
        on='student_email',
        how='left'
    )
    
    # Adicionar mês de compra
    purchases_with_cohort['purchase_month'] = purchases_with_cohort['purchaseDate'].apply(get_month_year)
    
    # Calcular número de meses desde a primeira compra
    purchases_with_cohort['cohort_month_dt'] = pd.to_datetime(purchases_with_cohort['cohort_month'])
    purchases_with_cohort['purchase_month_dt'] = pd.to_datetime(purchases_with_cohort['purchase_month'])
    purchases_with_cohort['month_number'] = (
        (purchases_with_cohort['purchase_month_dt'].dt.year - purchases_with_cohort['cohort_month_dt'].dt.year) * 12 +
        (purchases_with_cohort['purchase_month_dt'].dt.month - purchases_with_cohort['cohort_month_dt'].dt.month)
    )
    
    # Criar matriz de coorte
    cohort_data = purchases_with_cohort.groupby(['cohort_month', 'month_number'])['student_email'].nunique().reset_index()
    cohort_pivot = cohort_data.pivot(
        index='cohort_month',
        columns='month_number',
        values='student_email'
    )
    
    # Calcular retenção
    cohort_sizes = cohort_pivot[0]
    retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100
    
    # Formatar datas para melhor visualização
    retention_matrix.index = pd.to_datetime(retention_matrix.index).strftime('%b/%Y')
    retention_matrix.columns = [f'Mês {i}' for i in retention_matrix.columns]
    
    # Criar heatmap
    fig_cohort = px.imshow(
        retention_matrix,
        labels=dict(x="Mês desde Primeira Compra", y="Mês de Primeira Compra", color="Retenção (%)"),
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="Retenção de Estudantes por Coorte"
    )
    
    fig_cohort.update_layout(
        height=600,
        xaxis_title="Mês desde Primeira Compra",
        yaxis_title="Mês de Primeira Compra"
    )
    
    st.plotly_chart(fig_cohort, use_container_width=True)
    
    # Mostrar estatísticas da coorte
    st.markdown("### Estatísticas de Retenção")
    
    # Calcular retenção média por mês
    retention_stats = retention_matrix.mean(axis=0).reset_index()
    retention_stats.columns = ['Mês', 'Retenção Média (%)']
    
    # Criar gráfico de linha para retenção média
    fig_retention = px.line(
        retention_stats,
        x='Mês',
        y='Retenção Média (%)',
        title='Retenção Média por Mês',
        markers=True
    )
    
    fig_retention.update_layout(
        xaxis_title="Mês desde Primeira Compra",
        yaxis_title="Retenção Média (%)",
        height=400
    )
    
    st.plotly_chart(fig_retention, use_container_width=True)
    
    # Mostrar métricas de retenção
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Retenção Média", f"{retention_matrix.mean().mean():.1f}%")
    with col2:
        st.metric("Maior Retenção", f"{retention_matrix.max().max():.1f}%")
    with col3:
        st.metric("Menor Retenção", f"{retention_matrix.min().min():.1f}%")

with tab_raw:
    st.header("Dados Brutos")
    # Seletor de dataset
    dataset = st.selectbox(
        "Selecione o Dataset",
        ["Compras", "Eventos", "Estudantes"]
    )

    # Aplicar o mesmo filtro global
    if dataset == "Compras":
        df = purchases_filtered.copy()
        # Garantir que o campo semestre está presente
        if 'semester' not in df.columns:
            df['semester'] = df['purchaseDate'].apply(get_semester)
    elif dataset == "Eventos":
        df = events_filtered.copy()
        if 'semester' not in df.columns:
            df['semester'] = df['startDate'].apply(get_semester)
    else:
        df = students.copy()

    # Seletor de campos a exibir
    campos = list(df.columns)
    # Coloca o campo semestre no início se existir
    if 'semester' in campos:
        campos = ['semester'] + [c for c in campos if c != 'semester']
    campos_selecionados = st.multiselect(
        "Campos a exibir",
        options=campos,
        default=campos[:10]  # Mostra os 10 primeiros por padrão
    )
    
    # Mostrar dados filtrados
    st.subheader("Dados Filtrados")
    max_rows = 1000
    if len(df) > max_rows:
        st.warning(f"Mostrando apenas as primeiras {max_rows} linhas de {len(df)}. Refine os filtros para ver menos dados ou baixe o CSV completo.")
    st.dataframe(
        df[campos_selecionados].head(max_rows),
        use_container_width=True,
        hide_index=True
    )
    
    # Opções de download
    csv = df[campos_selecionados].to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        csv,
        f"{dataset.lower()}_filtrado.csv",
        "text/csv",
        key='download-csv'
    )

st.markdown("---")
st.info("Dashboard inicial. Sinta-se à vontade para sugerir novos gráficos ou análises!") 