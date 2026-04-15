import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
from pathlib import Path

# настройка страницы
st.set_page_config(
    page_title="Анализ CLV",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

#вспомогательные
def clean_customer_id(cust_id):
    # Убирает CUST_ из ID клиента
    return cust_id.replace('CUST_', '')

def translate_segment(segment):
    # перевод сегментов
    translation = {
        'premium': 'Премиум',
        'regular': 'Постоянный',
        'occasional': 'Эпизодический'
    }
    return translation.get(segment, segment)

def translate_category(category):
    # перевод категорий
    translation = {
        'VIP': 'VIP',
        'High': 'Высокий',
        'Medium': 'Средний',
        'Low': 'Низкий'
    }
    return translation.get(category, category)

# загрузка данных
CURRENT_DIR = Path(__file__).parent
PROJECT_DIR = CURRENT_DIR.parent
DATA_DIR = PROJECT_DIR / 'analyst' / 'output'

@st.cache_data
def load_clv_data():
    df = pd.read_csv(DATA_DIR / 'clv_results.csv')
    df['customer_id_clean'] = df['customer_id'].apply(clean_customer_id)
    df['segment_ru'] = df['segment'].apply(translate_segment)
    df['clv_category_ru'] = df['clv_category'].apply(translate_category)
    return df

@st.cache_data
def load_transactions_data():
    df = pd.read_csv(DATA_DIR / 'transactions.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['customer_id_clean'] = df['customer_id'].apply(clean_customer_id)
    df['segment_ru'] = df['segment'].apply(translate_segment)
    return df

@st.cache_data
def load_metadata():
    with open(DATA_DIR / 'metadata.json', 'r', encoding='utf-8') as f:
        return json.load(f)

try:
    clv_df = load_clv_data()
    transactions_df = load_transactions_data()
    metadata = load_metadata()
    data_loaded = True
except FileNotFoundError as e:
    st.error(f"❌ Ошибка загрузки данных: {e}")
    st.info("Убедитесь, что файлы clv_results.csv, transactions.csv и metadata.json находятся в папке analyst/output")
    data_loaded = False

# кастомка
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FFB7B2 !important;
    }
    .stMetric {
        background-color: #1E1E2E;
        border-radius: 15px;
        padding: 15px;
        border: 1px solid #2D2D3D;
    }
    .stMetric label {
        color: #C0C0C0 !important;
    }
    .stMetric .stMetricValue {
        color: #7EC8B3 !important;
    }
    .stButton button {
        background-color: #1E1E2E;
        color: #F0F0F0;
        border: 1px solid #2D2D3D;
        border-radius: 25px;
    }
    .stButton button:hover {
        background-color: #5BAF97;
        color: #0E1117;
    }
</style>
""", unsafe_allow_html=True)

# шапка
st.title("📊 Анализ пожизненной ценности клиента")

if data_loaded:
    # Информация о данных
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Клиентов", f"{metadata['statistics']['total_customers']}")
    with col2:
        st.metric("💳 Транзакций", f"{metadata['statistics']['total_transactions']:,}")
    with col3:
        st.metric("💰 Общий доход", f"{metadata['statistics']['total_revenue']:,.0f} ₽")
    
    st.markdown("---")
    

    # БЛОК 1: КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ CLV
    st.subheader("💎 Ключевые показатели CLV")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Средний CLV", f"{metadata['statistics']['clv_stats']['mean']:,.0f} ₽")
    with col2:
        st.metric("Медианный CLV", f"{metadata['statistics']['clv_stats']['median']:,.0f} ₽")
    with col3:
        st.metric("Максимальный CLV", f"{metadata['statistics']['clv_stats']['max']:,.0f} ₽")
    with col4:
        st.metric("Минимальный CLV", f"{metadata['statistics']['clv_stats']['min']:,.0f} ₽")
    
    st.markdown("---")
    
    # БЛОК 2: ГИСТОГРАММА РАСПРЕДЕЛЕНИЯ CLV
    st.subheader("📊 Распределение CLV")
    
    fig1 = px.histogram(
        clv_df,
        x='clv_simple',
        nbins=25,
        title='Распределение CLV среди клиентов',
        labels={'clv_simple': 'CLV (руб)', 'count': 'Количество клиентов'},
        color_discrete_sequence=['#FFB7B2'],
        opacity=0.8
    )
    
    mean_val = clv_df['clv_simple'].mean()
    median_val = clv_df['clv_simple'].median()
    
    fig1.add_vline(
        x=mean_val, 
        line_dash="dash", 
        line_color="#7EC8B3",
        line_width=2,
        annotation_text=f"Среднее: {mean_val:,.0f} ₽",
        annotation_position="top right"
    )
    fig1.add_vline(
        x=median_val, 
        line_dash="dash", 
        line_color="#FFD700",
        line_width=2,
        annotation_text=f"Медиана: {median_val:,.0f} ₽",
        annotation_position="top left"
    )
    
    fig1.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font_color='#F0F0F0',
        font_color='#F0F0F0',
        xaxis=dict(tickformat=',.0f', title="CLV (руб)"),
        yaxis=dict(title="Количество клиентов"),
        bargap=0.05
    )
    
    fig1.update_traces(
        hovertemplate='CLV: %{x:,.0f} ₽<br>Клиентов: %{y}',
        marker=dict(line=dict(width=1, color='#FFFFFF'))
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("---")
    
    # БЛОК 3: ТОП-10 КЛИЕНТОВ
    st.subheader("🏆 Топ-10 клиентов по CLV")
    top10 = clv_df.nlargest(10, 'clv_simple')[['customer_id_clean', 'segment_ru', 'clv_simple', 'total_revenue']].copy()
    top10['customer_display'] = 'Клиент ' + top10['customer_id_clean'].astype(str)
    top10 = top10.sort_values('clv_simple', ascending=True)

    colors_per_client = ['#FFB7B2', '#FFC4C0', '#FFD1CC', '#FFDDD8', '#FFEAE4',
                        '#D4F1E8', '#C0EBDF', '#ACE5D6', '#98DFCD', '#84D9C4']

    fig2 = px.bar(
        top10,
        x='clv_simple',
        y='customer_display',
        orientation='h',
        title='Топ-10 клиентов по CLV',
        labels={'clv_simple': 'CLV (руб)', 'customer_display': 'Клиент'},
        text='clv_simple',
        color='customer_display',
        color_discrete_sequence=colors_per_client
    )
    fig2.update_traces(
        texttemplate='%{text:,.0f} ₽',
        textposition='outside',
        marker=dict(line=dict(width=1, color='#FFFFFF'))
    )
    fig2.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font_color='#F0F0F0',
        font_color='#F0F0F0',
        xaxis=dict(tickformat=',.0f'),
        showlegend=False
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Таблица топ-10
    with st.expander("📋 Показать таблицу топ-10"):
        display_table = top10[['customer_display', 'segment_ru', 'clv_simple', 'total_revenue']].copy()
        display_table = display_table.rename(columns={
            'customer_display': 'Клиент',
            'segment_ru': 'Сегмент',
            'clv_simple': 'CLV (руб)',
            'total_revenue': 'Доход (руб)'
        })
        st.dataframe(display_table, hide_index=True)
            
    st.markdown("---")

    # БЛОК 4: СЕГМЕНТАЦИЯ
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Распределение по сегментам")
        segment_dist = clv_df['segment_ru'].value_counts()
        fig3 = px.pie(
            values=segment_dist.values,
            names=segment_dist.index,
            title='Доля клиентов по сегментам',
            color=segment_dist.index,
            color_discrete_map={
                'Премиум': '#FFB7B2',
                'Постоянный': '#7EC8B3',
                'Эпизодический': '#FFD700'
            }
        )
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            title_font_color='#F0F0F0',
            font_color='#F0F0F0'
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        st.subheader("📊 Распределение по категориям CLV")
        category_dist = clv_df['clv_category_ru'].value_counts()
        order = ['VIP', 'Высокий', 'Средний', 'Низкий']
        category_dist = category_dist.reindex(order)
        fig4 = px.pie(
            values=category_dist.values,
            names=category_dist.index,
            title='Доля клиентов по категориям CLV',
            color=category_dist.index,
            color_discrete_map={
                'VIP': '#FFD700',
                'Высокий': '#FFB7B2',
                'Средний': '#7EC8B3',
                'Низкий': '#FF9F9F'
            }
        )
        fig4.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            title_font_color='#F0F0F0',
            font_color='#F0F0F0'
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    
    # БЛОК 5: ДИНАМИКА ПО МЕСЯЦАМ
    st.subheader("📈 Динамика продаж по месяцам")
    
    transactions_df['month'] = transactions_df['date'].dt.to_period('M').astype(str)
    monthly_revenue = transactions_df.groupby('month')['amount'].sum().reset_index()
    
    month_names_ru = {
        '01': 'Янв', '02': 'Фев', '03': 'Мар', '04': 'Апр',
        '05': 'Май', '06': 'Июн', '07': 'Июл', '08': 'Авг',
        '09': 'Сен', '10': 'Окт', '11': 'Ноя', '12': 'Дек'
    }
    
    def format_month_ru(month_str):
        try:
            year, month = month_str.split('-')
            return f"{month_names_ru[month]} {year}"
        except:
            return month_str
    
    monthly_revenue['month_ru'] = monthly_revenue['month'].apply(format_month_ru)
    
    fig5 = px.line(
        monthly_revenue,
        x='month_ru',
        y='amount',
        title='Выручка по месяцам',
        labels={'month_ru': 'Месяц', 'amount': 'Выручка (руб)'},
        markers=True,
        color_discrete_sequence=['#7EC8B3']
    )
    fig5.update_traces(
        line=dict(width=3),
        marker=dict(size=8, color='#FFB7B2', line=dict(width=2, color='#FFFFFF'))
    )
    fig5.update_layout(
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font_color='#F0F0F0',
        font_color='#F0F0F0'
    )
    st.plotly_chart(fig5, use_container_width=True)
    
    st.markdown("---")
    
    # БЛОК 6: СРАВНЕНИЕ СЕГМЕНТОВ 
    st.subheader("📊 Сравнение сегментов")

    segment_avg_clv = clv_df.groupby('segment_ru')['clv_simple'].mean().reset_index()
    segment_avg_clv = segment_avg_clv.rename(columns={
        'segment_ru': 'Сегмент',
        'clv_simple': 'Средний CLV (руб)'
    })

    fig7 = px.bar(
        segment_avg_clv,
        x='Сегмент',
        y='Средний CLV (руб)',
        title='Средний CLV по сегментам',
        text='Средний CLV (руб)',
        color='Сегмент',
        color_discrete_map={
            'Премиум': '#FFB7B2',
            'Постоянный': '#7EC8B3',
            'Эпизодический': '#FFD700'
        }
    )
    fig7.update_traces(
        texttemplate='%{text:,.0f} ₽',
        textposition='outside',
        marker=dict(line=dict(width=1, color='#FFFFFF'), cornerradius=8)
    )
    fig7.update_layout(
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font_color='#F0F0F0',
        font_color='#F0F0F0',
        yaxis=dict(tickformat=',.0f')
    )
    st.plotly_chart(fig7, use_container_width=True)

    # таблица со статистикой
    st.subheader("📋 Статистика по сегментам")
    segment_stats = clv_df.groupby('segment_ru').agg({
        'clv_simple': ['mean', 'median', 'min', 'max'],
        'customer_id': 'count'
    }).round(0)
    segment_stats.columns = ['Средний CLV', 'Медианный CLV', 'Мин CLV', 'Макс CLV', 'Кол-во']
    segment_stats = segment_stats.reset_index()
    segment_stats = segment_stats.rename(columns={'segment_ru': 'Сегмент'})

    st.dataframe(
        segment_stats,
        column_config={
            "Сегмент": st.column_config.TextColumn("Сегмент"),
            "Средний CLV": st.column_config.NumberColumn("Средний CLV", format="%.0f ₽"),
            "Медианный CLV": st.column_config.NumberColumn("Медианный CLV", format="%.0f ₽"),
            "Мин CLV": st.column_config.NumberColumn("Мин CLV", format="%.0f ₽"),
            "Макс CLV": st.column_config.NumberColumn("Макс CLV", format="%.0f ₽"),
            "Кол-во": "Количество клиентов"
        },
        hide_index=True
    )
        
    st.markdown("---")
    
    # БЛОК: ЧАСТОТА vs СРЕДНИЙ ЧЕК
    st.subheader("📈 Частота покупок vs Средний чек")

    # Копируем данные
    scatter_df = clv_df.copy()

    # Цветовая шкала
    colors_scatter = ['#FFB7B2', '#FFC4C0', '#FFD1CC', '#FFDDD8', '#FFEAE4',
                    '#D4F1E8', '#C0EBDF', '#ACE5D6', '#98DFCD', '#84D9C4']

    fig_scatter = px.scatter(
        scatter_df,
        x='frequency',
        y='avg_check',
        title='Частота покупок и средний чек',
        labels={
            'frequency': 'Частота покупок (количество)',
            'avg_check': 'Средний чек (руб)',
            'customer_id_clean': 'ID клиента',
            'segment_ru': 'Сегмент',
            'clv_simple': 'CLV (руб)'
        },
        color='clv_simple',
        color_continuous_scale=colors_scatter,
        size='clv_simple',
        size_max=15,
        hover_data=['customer_id_clean', 'segment_ru', 'clv_simple']  # ← простой список
    )

    # Настройка внешнего вида
    fig_scatter.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font_color='#F0F0F0',
        font_color='#F0F0F0',
        xaxis=dict(
            title=dict(text='Частота покупок (количество)', font=dict(color='#F0F0F0')),
            gridcolor='#2D2D3D',
            color='#F0F0F0'
        ),
        yaxis=dict(
            title=dict(text='Средний чек (руб)', font=dict(color='#F0F0F0')),
            gridcolor='#2D2D3D',
            color='#F0F0F0',
            tickformat=',.0f'
        )
    )

    # Настройка цветовой шкалы
    fig_scatter.update_coloraxes(
        colorbar=dict(
            title=dict(text='CLV (руб)', font=dict(color='#F0F0F0')),
            tickformat=',.0f',
            tickfont=dict(color='#F0F0F0')
        )
    )

    # Форматирование чисел в hover
    fig_scatter.update_traces(
        hovertemplate='<b>Частота покупок:</b> %{x}<br>' +
                    '<b>Средний чек:</b> %{y:,.0f} ₽<br>' +
                    '<b>ID клиента:</b> %{customdata[0]}<br>' +
                    '<b>Сегмент:</b> %{customdata[1]}<br>' +
                    '<b>CLV:</b> %{customdata[2]:,.0f} ₽<extra></extra>'
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

    # БЛОК 7: ДЕТАЛЬНАЯ СТАТИСТИКА ПО КЛИЕНТУ
    st.subheader("🔍 Детальная статистика по клиенту")

    client_options = {clean_customer_id(cid): cid for cid in clv_df['customer_id'].tolist()}

    selected_client_clean = st.selectbox(
        "Выберите клиента для детального анализа",
        options=list(client_options.keys()),
        format_func=lambda x: f"Клиент {x}"
    )

    if selected_client_clean:
        selected_client = client_options[selected_client_clean]
        client_info = clv_df[clv_df['customer_id'] == selected_client].iloc[0]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("💰 Общий доход", f"{client_info['total_revenue']:,.0f} ₽")
        with col2:
            st.metric("📊 Средний чек", f"{client_info['avg_check']:,.0f} ₽")
        with col3:
            st.metric("🔄 Частота", f"{client_info['frequency']} раз")
        with col4:
            st.metric("💎 CLV", f"{client_info['clv_simple']:,.0f} ₽")
        with col5:
            st.metric("🏷️ Категория", client_info['clv_category_ru'])
        
        client_transactions = transactions_df[transactions_df['customer_id'] == selected_client].copy()
        
        if len(client_transactions) > 0:
            st.subheader(f"📈 Динамика покупок клиента {selected_client_clean}")
            
            client_transactions['month'] = client_transactions['date'].dt.to_period('M').astype(str)
            
            month_names_ru = {
                '01': 'Янв', '02': 'Фев', '03': 'Мар', '04': 'Апр',
                '05': 'Май', '06': 'Июн', '07': 'Июл', '08': 'Авг',
                '09': 'Сен', '10': 'Окт', '11': 'Ноя', '12': 'Дек'
            }
            
            def format_month_ru(month_str):
                try:
                    year, month = month_str.split('-')
                    return f"{month_names_ru[month]} {year}"
                except:
                    return month_str
            
            client_transactions['month_ru'] = client_transactions['month'].apply(format_month_ru)
            monthly_client = client_transactions.groupby('month_ru')['amount'].sum().reset_index()
            
            fig6 = px.bar(
                monthly_client,
                x='month_ru',
                y='amount',
                title=f'Покупки клиента {selected_client_clean} по месяцам',
                labels={'month_ru': 'Месяц', 'amount': 'Сумма покупок (руб)'},
                text='amount',
                color_discrete_sequence=['#7EC8B3']
            )
            fig6.update_traces(
                texttemplate='%{text:,.0f} ₽',
                textposition='outside',
                marker=dict(line=dict(width=1, color='#FFFFFF'), cornerradius=8)
            )
            fig6.update_layout(
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title_font_color='#F0F0F0',
                font_color='#F0F0F0',
                xaxis=dict(tickangle=45)
            )
            st.plotly_chart(fig6, use_container_width=True)
            
            with st.expander("📋 История транзакций"):
                display_df = client_transactions[['date', 'amount', 'has_discount', 'discount_percent']].copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                st.dataframe(
                    display_df,
                    column_config={
                        "date": "Дата",
                        "amount": st.column_config.NumberColumn("Сумма", format="%.2f ₽"),
                        "has_discount": "Скидка",
                        "discount_percent": st.column_config.NumberColumn("Размер скидки", format="%.1f%%")
                    },
                    hide_index=True
                )
    
    st.markdown("---")

    # БЛОК 8: ЭКСПОРТ
    st.subheader("📥 Экспорт данных")
    
    export_df = clv_df.copy()
    export_df['customer_id'] = export_df['customer_id_clean']
    export_df['segment'] = export_df['segment_ru']
    export_df['clv_category'] = export_df['clv_category_ru']
    export_df = export_df.drop(columns=['customer_id_clean', 'segment_ru', 'clv_category_ru'])
    
    csv_export = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Скачать CLV данные (CSV)",
        data=csv_export,
        file_name=f"clv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

# подвал
st.markdown("---")
if data_loaded:
    st.caption(f"📅 Данные от: {metadata['generation_date']}")