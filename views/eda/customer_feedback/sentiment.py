# views/eda/customer_feedback/sentiment.py
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_feedback_with_customer

st.title("🎭 客户反馈与流失分析")
st.markdown(
    "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
    unsafe_allow_html=True
)

# ======================================================
# 数据加载
# ======================================================
df = load_feedback_with_customer()

# ======================================================
# 通用图表样式函数
# ======================================================
def apply_common_layout(
    fig,
    title,
    xaxis_title,
    yaxis_title,
    height=420,
    showlegend=True,
    margin=None
):
    """
    统一设置所有图表样式：
    1. 中文标题
    2. 坐标轴标题
    3. 坐标轴文字黑色
    4. 白色背景
    """
    if margin is None:
        margin = dict(t=70, b=50, l=60, r=60)

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color='black', size=18, family="Arial, sans-serif"),
            x=0.5,
            xanchor='center'
        ),

        font=dict(color='black', size=12),
        legend=dict(
            font=dict(color='black', size=12),
            title=dict(font=dict(color='black', size=13))
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=height,
        showlegend=showlegend,
        margin=margin
    )

    fig.update_xaxes(
        title=dict(
            text=xaxis_title,
            font=dict(color='black', size=14)
        ),
        tickfont=dict(color='black', size=12),
        showline=True,
        linewidth=1,
        linecolor='black',
        ticks='outside',
        tickcolor='black',
        showgrid=True,
        gridcolor='#E5E7EB',
        zeroline=False,
        automargin=True
    )

    fig.update_yaxes(
        title=dict(
            text=yaxis_title,
            font=dict(color='black', size=14)
        ),
        tickfont=dict(color='black', size=12),
        showline=True,
        linewidth=1,
        linecolor='black',
        ticks='outside',
        tickcolor='black',
        showgrid=True,
        gridcolor='#E5E7EB',
        zeroline=False,
        automargin=True
    )

    return fig


def strong_divider():
    st.markdown(
        "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
        unsafe_allow_html=True
    )


def light_divider():
    st.markdown(
        "<hr style='border: none; height: 1.5px; background-color: #BDC3C7; margin: 25px 0;'>",
        unsafe_allow_html=True
    )


# ======================================================
# 标签映射
# ======================================================
category_label_map = {
    'pricing': '价格问题',
    'service_quality': '服务质量',
    'customer_support': '客服支持',
    'churn_intent': '流失意向'
}

sentiment_label_map = {
    'positive': '正面',
    'neutral': '中性',
    'negative': '负面'
}

value_label_map = {
    'high_value': '高价值',
    'medium_value': '中价值',
    'low_value': '低价值'
}

usage_label_map = {
    'high_usage': '高使用',
    'medium_usage': '中使用',
    'low_usage': '低使用'
}

risk_label_map = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
}

df['feedback_category_label'] = df['feedback_category'].map(category_label_map).fillna(df['feedback_category'])
df['sentiment_label_cn'] = df['sentiment'].map(sentiment_label_map).fillna(df['sentiment'])
df['value_label'] = df['customer_value_segment'].map(value_label_map).fillna(df['customer_value_segment'])
df['usage_label'] = df['usage_intensity'].map(usage_label_map).fillna(df['usage_intensity'])
df['risk_label'] = df['rule_based_churn_risk_level'].map(risk_label_map).fillna(df['rule_based_churn_risk_level'])

# ======================================================
# 核心指标
# ======================================================
st.subheader("📊 客户反馈核心指标")

total_feedback = len(df)
negative_rate = (df['sentiment'] == 'negative').mean() * 100
avg_intensity = df['complaint_intensity'].mean()
feedback_churn_rate = df['churn_int'].mean() * 100

col1, col2, col3, col4 = st.columns(4)

col1.metric("反馈客户数", f"{total_feedback:,}")
col2.metric("负面反馈占比", f"{negative_rate:.1f}%")
col3.metric("平均投诉强度", f"{avg_intensity:.2f}")
col4.metric("反馈客户流失率", f"{feedback_churn_rate:.1f}%")

st.info(
    "💡 本页面将 `customer_feedback.xlsx` 与 `full_customers.xlsx` 通过 `customer_id` 合并，"
    "用于分析反馈类别、情绪、投诉强度与客户流失之间的关系。"
)

# ======================================================
# 反馈类别分布：按情绪拆分为正面、负面、中性
# ======================================================
strong_divider()

st.subheader("📌 反馈类别分布")

# 按反馈类别 + 情绪统计客户数量
category_count = df.groupby(
    ['feedback_category_label', 'sentiment_label_cn']
).agg(
    customer_count=('customer_id', 'count')
).reset_index()

# 设置显示顺序
category_order = ['服务质量', '价格问题', '流失意向', '客服支持']
sentiment_order = ['正面', '负面', '中性']

category_count['feedback_category_label'] = pd.Categorical(
    category_count['feedback_category_label'],
    categories=category_order,
    ordered=True
)

category_count['sentiment_label_cn'] = pd.Categorical(
    category_count['sentiment_label_cn'],
    categories=sentiment_order,
    ordered=True
)

category_count = category_count.sort_values(
    ['feedback_category_label', 'sentiment_label_cn']
)

fig = px.bar(
    category_count,
    x='feedback_category_label',
    y='customer_count',
    color='sentiment_label_cn',
    barmode='group',
    text='customer_count',
    color_discrete_map={
        '正面': '#2ECC71',
        '负面': '#E74C3C',
        '中性': '#F1C40F'
    },
    category_orders={
        'feedback_category_label': category_order,
        'sentiment_label_cn': sentiment_order
    },
    labels={
        'feedback_category_label': '反馈类别',
        'customer_count': '客户数量',
        'sentiment_label_cn': '反馈情绪'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '反馈类别: %{x}<br>'
        '客户数量: %{y}<br>'
        '反馈情绪: %{fullData.name}'
        '<extra></extra>'
    )
)

fig = apply_common_layout(
    fig,
    title='客户反馈类别分布',
    xaxis_title='反馈类别',
    yaxis_title='客户数量',
    height=460,
    showlegend=True,
    margin=dict(t=70, b=60, l=60, r=60)
)

fig.update_layout(
    legend_title_text='反馈情绪'
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图展示不同反馈类别下，正面、负面、中性反馈客户数量的分布情况。")


# ======================================================
# 情绪分布
# ======================================================
strong_divider()

st.subheader("🎭 客户反馈情绪分布")

sentiment_count = df.groupby('sentiment_label_cn').agg(
    customer_count=('customer_id', 'count')
).reset_index()

sentiment_count['percent'] = sentiment_count['customer_count'] / sentiment_count['customer_count'].sum() * 100

sentiment_order = ['正面', '中性', '负面']
sentiment_count['sentiment_label_cn'] = pd.Categorical(
    sentiment_count['sentiment_label_cn'],
    categories=sentiment_order,
    ordered=True
)
sentiment_count = sentiment_count.sort_values('sentiment_label_cn')

fig = px.bar(
    sentiment_count,
    x='sentiment_label_cn',
    y='customer_count',
    color='sentiment_label_cn',
    text=sentiment_count['percent'].apply(lambda x: f"{x:.1f}%"),
    color_discrete_map={
        '正面': '#2ECC71',
        '中性': '#F1C40F',
        '负面': '#E74C3C'
    },
    labels={
        'sentiment_label_cn': '反馈情绪',
        'customer_count': '客户数量'
    },
    hover_data={
        'percent': ':.1f'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '反馈情绪: %{x}<br>'
        '客户数量: %{y}<br>'
        '占比: %{customdata[0]:.1f}%'
        '<extra></extra>'
    )
)

fig = apply_common_layout(
    fig,
    title='客户反馈情绪分布',
    xaxis_title='反馈情绪',
    yaxis_title='客户数量',
    height=420,
    showlegend=False,
    margin=dict(t=70, b=50, l=60, r=60)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图展示客户反馈整体情绪结构，负面反馈客户通常需要重点关注。")

# ======================================================
# 不同反馈类别的流失率
# ======================================================
strong_divider()

st.subheader("🚨 不同反馈类别的流失率")

category_churn = df.groupby('feedback_category_label').agg(
    customer_count=('customer_id', 'count'),
    churn_rate=('churn_int', 'mean'),
    avg_complaint_intensity=('complaint_intensity', 'mean'),
    avg_total_charges=('total_charges', 'mean')
).reset_index()

category_churn['churn_rate_pct'] = category_churn['churn_rate'] * 100
category_churn = category_churn.sort_values('churn_rate_pct', ascending=True)

fig = px.bar(
    category_churn,
    x='churn_rate_pct',
    y='feedback_category_label',
    orientation='h',
    color='churn_rate_pct',
    text=category_churn['churn_rate_pct'].apply(lambda x: f"{x:.1f}%"),
    color_continuous_scale=['#27AE60', '#F1C40F', '#E74C3C'],
    hover_data={
        'customer_count': True,
        'avg_complaint_intensity': ':.2f',
        'avg_total_charges': ':.2f'
    },
    labels={
        'churn_rate_pct': '流失率 (%)',
        'feedback_category_label': '反馈类别',
        'customer_count': '客户数量',
        'avg_complaint_intensity': '平均投诉强度',
        'avg_total_charges': '人均费用贡献'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '反馈类别: %{y}<br>'
        '流失率: %{x:.1f}%<br>'
        '客户数量: %{customdata[0]}<br>'
        '平均投诉强度: %{customdata[1]:.2f}<br>'
        '人均费用贡献: $%{customdata[2]:,.2f}'
        '<extra></extra>'
    )
)

fig = apply_common_layout(
    fig,
    title='不同反馈类别的客户流失率对比',
    xaxis_title='流失率 (%)',
    yaxis_title='反馈类别',
    height=250,
    showlegend=False,
    margin=dict(t=70, b=50, l=80, r=100)
)

fig.update_layout(
    coloraxis_showscale=False
)

st.plotly_chart(fig, use_container_width=True)

top_category = category_churn.sort_values('churn_rate_pct', ascending=False).iloc[0]

st.info(
    f"💡 流失率最高的反馈类别是 **{top_category['feedback_category_label']}**，"
    f"流失率约为 **{top_category['churn_rate_pct']:.1f}%**。"
)
# ======================================================
# 不同情绪的流失率
# ======================================================
strong_divider()

st.subheader("📉 不同反馈情绪的流失率")

feedback_category_order = ['服务质量', '价格问题', '流失意向', '客服支持']

sentiment_churn = df.groupby(
    ['sentiment_label_cn', 'feedback_category_label']
).agg(
    customer_count=('customer_id', 'count'),
    churn_rate=('churn_int', 'mean'),
    avg_complaint_intensity=('complaint_intensity', 'mean'),
    avg_total_charges=('total_charges', 'mean')
).reset_index()

sentiment_churn['churn_rate_pct'] = sentiment_churn['churn_rate'] * 100

sentiment_churn['sentiment_label_cn'] = pd.Categorical(
    sentiment_churn['sentiment_label_cn'],
    categories=sentiment_order,
    ordered=True
)

sentiment_churn['feedback_category_label'] = pd.Categorical(
    sentiment_churn['feedback_category_label'],
    categories=feedback_category_order,
    ordered=True
)

sentiment_churn = sentiment_churn.sort_values(
    ['sentiment_label_cn', 'feedback_category_label']
)

sentiment_churn['text_label'] = sentiment_churn['churn_rate_pct'].apply(
    lambda x: f"{x:.1f}%"
)

fig = px.bar(
    sentiment_churn,
    x='sentiment_label_cn',
    y='churn_rate_pct',
    color='feedback_category_label',
    barmode='group',
    text='text_label',
    category_orders={
        'sentiment_label_cn': sentiment_order,
        'feedback_category_label': feedback_category_order
    },
    color_discrete_map={
        '服务质量': '#2ECC71',
        '价格问题': '#F1C40F',
        '流失意向': '#E74C3C',
        '客服支持': '#3498DB'
    },
    custom_data=[
        'feedback_category_label',
        'customer_count',
        'avg_complaint_intensity',
        'avg_total_charges'
    ],
    labels={
        'sentiment_label_cn': '反馈情绪',
        'feedback_category_label': '反馈类别',
        'churn_rate_pct': '流失率 (%)',
        'customer_count': '客户数量',
        'avg_complaint_intensity': '平均投诉强度',
        'avg_total_charges': '人均费用贡献'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '反馈情绪: %{x}<br>'
        '反馈类别: %{customdata[0]}<br>'
        '流失率: %{y:.1f}%<br>'
        '客户数量: %{customdata[1]}<br>'
        '平均投诉强度: %{customdata[2]:.2f}<br>'
        '人均费用贡献: $%{customdata[3]:,.2f}'
        '<extra></extra>'
    )
)

fig = apply_common_layout(
    fig,
    title='不同反馈情绪下各反馈类别的客户流失率对比',
    xaxis_title='反馈情绪',
    yaxis_title='流失率 (%)',
    height=420,
    showlegend=True,
    margin=dict(t=70, b=50, l=60, r=60)
)

fig.update_layout(
    legend_title_text='反馈类别'
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 每种反馈情绪下进一步拆分为四类反馈类别，便于比较不同类别在同一情绪下的流失风险。")


# ======================================================
# 投诉强度与流失率
# ======================================================
strong_divider()

st.subheader("🔥 投诉强度与流失率关系")

intensity_churn = df.groupby('complaint_intensity').agg(
    customer_count=('customer_id', 'count'),
    churn_rate=('churn_int', 'mean')
).reset_index()

intensity_churn['churn_rate_pct'] = intensity_churn['churn_rate'] * 100

fig = px.line(
    intensity_churn,
    x='complaint_intensity',
    y='churn_rate_pct',
    markers=True,
    text=intensity_churn['churn_rate_pct'].apply(lambda x: f"{x:.1f}%"),
    hover_data={
        'customer_count': True
    },
    labels={
        'complaint_intensity': '投诉强度',
        'churn_rate_pct': '流失率 (%)',
        'customer_count': '客户数量'
    }
)

fig.update_traces(
    line=dict(color='#E74C3C', width=4),
    marker=dict(size=11, color='#E74C3C'),
    textposition='top center',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '投诉强度: %{x}<br>'
        '流失率: %{y:.1f}%<br>'
        '客户数量: %{customdata[0]}'
        '<extra></extra>'
    )
)

fig = apply_common_layout(
    fig,
    title='投诉强度与客户流失率趋势',
    xaxis_title='投诉强度等级',
    yaxis_title='流失率 (%)',
    height=430,
    showlegend=False,
    margin=dict(t=70, b=50, l=60, r=60)
)

fig.update_xaxes(dtick=1)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图用于观察投诉强度从 1 到 5 上升时，客户流失率是否同步上升。")

# ======================================================
# 反馈类别 × 情绪 流失率热力图
# ======================================================
strong_divider()

st.subheader("🧯 反馈类别 × 情绪的流失率热力图")

heatmap_df = df.groupby(
    ['feedback_category_label', 'sentiment_label_cn']
).agg(
    customer_count=('customer_id', 'count'),
    churn_rate=('churn_int', 'mean')
).reset_index()

heatmap_df['churn_rate_pct'] = heatmap_df['churn_rate'] * 100

fig = px.density_heatmap(
    heatmap_df,
    x='sentiment_label_cn',
    y='feedback_category_label',
    z='churn_rate_pct',
    text_auto='.1f',
    color_continuous_scale='YlOrRd',
    labels={
        'sentiment_label_cn': '反馈情绪',
        'feedback_category_label': '反馈类别',
        'churn_rate_pct': '流失率 (%)'
    },
    hover_data={
        'customer_count': True,
        'churn_rate_pct': ':.1f'
    }
)

fig = apply_common_layout(
    fig,
    title='反馈类别与反馈情绪对客户流失率的综合影响',
    xaxis_title='反馈情绪',
    yaxis_title='反馈类别',
    height=450,
    showlegend=False,
    margin=dict(t=70, b=50, l=80, r=80)
)

fig.update_layout(
    coloraxis_colorbar=dict(
        title=dict(
            text='流失率 (%)',
            font=dict(color='black', size=13)
        ),
        tickfont=dict(color='black', size=12)
    )
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 热力图可以帮助识别“高风险反馈组合”，例如价格问题 + 负面情绪、客服支持 + 负面情绪等。"
)

# ======================================================
# 客户价值分层下的反馈流失率
# ======================================================
strong_divider()

st.subheader("🏷️ 客户价值分层下的反馈流失率")

value_feedback = df.groupby(
    ['value_label', 'feedback_category_label']
).agg(
    customer_count=('customer_id', 'count'),
    churn_rate=('churn_int', 'mean'),
    avg_complaint_intensity=('complaint_intensity', 'mean')
).reset_index()

value_feedback['churn_rate_pct'] = value_feedback['churn_rate'] * 100

fig = px.bar(
    value_feedback,
    x='value_label',
    y='churn_rate_pct',
    color='feedback_category_label',
    barmode='group',
    text=value_feedback['churn_rate_pct'].apply(lambda x: f"{x:.1f}%"),
    hover_data={
        'customer_count': True,
        'avg_complaint_intensity': ':.2f'
    },
    labels={
        'value_label': '客户价值分层',
        'churn_rate_pct': '流失率 (%)',
        'feedback_category_label': '反馈类别',
        'customer_count': '客户数量',
        'avg_complaint_intensity': '平均投诉强度'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=10),
    hovertemplate=(
        '客户价值分层: %{x}<br>'
        '流失率: %{y:.1f}%<br>'
        '客户数量: %{customdata[0]}<br>'
        '平均投诉强度: %{customdata[1]:.2f}'
        '<extra></extra>'
    )
)

fig = apply_common_layout(
    fig,
    title='不同客户价值分层下各类反馈问题的流失率对比',
    xaxis_title='客户价值分层',
    yaxis_title='流失率 (%)',
    height=500,
    showlegend=True,
    margin=dict(t=70, b=50, l=60, r=60)
)

fig.update_layout(
    legend_title_text='反馈类别'
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图用于识别不同客户价值层级中，哪些反馈问题最容易触发流失。")

# ======================================================
# 高风险反馈客户明细
# ======================================================
strong_divider()

st.subheader("🔎 高风险反馈客户明细")

high_risk_feedback = df[
    (df['sentiment'] == 'negative') |
    (df['complaint_intensity'] >= 4) |
    (df['feedback_category'] == 'churn_intent')
].copy()

show_cols = [
    'customer_id',
    'feedback_text',
    'feedback_category_label',
    'sentiment_label_cn',
    'complaint_intensity',
    'churn_label',
    'total_charges',
    'customer_service_calls',
    'value_label',
    'risk_label'
]

st.dataframe(
    high_risk_feedback[show_cols].sort_values(
        ['complaint_intensity', 'churn_label'],
        ascending=[False, True]
    ),
    use_container_width=True
)

st.caption(
    "💡 筛选规则：负面反馈、投诉强度 ≥ 4、或反馈类别为流失意向的客户。"
)
