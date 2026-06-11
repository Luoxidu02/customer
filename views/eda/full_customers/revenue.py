# views/eda/full_customers/revenue.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_business_with_customer


st.title("👥 客户费用贡献分析")
st.markdown(
    "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
    unsafe_allow_html=True
)

# ======================================================
# 数据加载与预处理
# ======================================================
# df = load_full_customers()
df = load_business_with_customer()
st.markdown("""
### 📌 数据说明

本页面主要用于分析客户的收入贡献情况。  
数据来自两个表：

- **business_costs.xlsx**：提供客户的月收入、预估客户价值、挽留成本等业务指标；
- **full_customers.xlsx**：提供客户是否流失、客户价值分层、使用强度等客户属性。

两个表通过 `customer_id` 进行关联，形成当前页面使用的分析数据集。  
本页面主要使用 `monthly_revenue` 作为客户收入贡献指标，并结合 `churn_label`、`customer_value_segment` 和 `usage_intensity` 进行分组分析。
""")

df['churn_label'] = df['churn_int'].map({0: '留存', 1: '流失'})

# 图表通用布局配置
common_layout = dict(
    font=dict(color='black', size=12),
    title_font=dict(color='black', size=14),
    legend_font=dict(color='black'),
    # paper_bgcolor='white',
    # plot_bgcolor='white',
    # title=None,
)

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
# 留存与流失客户人均费用贡献分析
# ======================================================
st.subheader("💸 留存与流失客户人均月收入贡献对比")
st.caption(
    "数据处理说明：先将客户按照价值分层和使用强度进行分组，"
    "再在每个分组内区分留存与流失客户，计算各组的人均月收入贡献，"
    "用于分析不同客户群体的收入价值差异。"
)


contribution_df = df.groupby('churn_label').agg(
    customer_count=('customer_id', 'count'),
    total_charge_contribution=('monthly_revenue', 'sum'),
    avg_charge_contribution=('monthly_revenue', 'mean'),
    median_charge_contribution=('monthly_revenue', 'median')
).reset_index()


# 取留存、流失两组数据
retained_row = contribution_df[contribution_df['churn_label'] == '留存'].iloc[0]
churned_row = contribution_df[contribution_df['churn_label'] == '流失'].iloc[0]

retained_count = retained_row['customer_count']
churned_count = churned_row['customer_count']

retained_avg_charge = retained_row['avg_charge_contribution']
churned_avg_charge = churned_row['avg_charge_contribution']

retained_median_charge = retained_row['median_charge_contribution']
churned_median_charge = churned_row['median_charge_contribution']

avg_diff_rate = (churned_avg_charge - retained_avg_charge) / retained_avg_charge * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "留存客户数量",
        f"{retained_count:,.0f} 人"
    )

with col2:
    st.metric(
        "流失客户数量",
        f"{churned_count:,.0f} 人"
    )

with col3:
    st.metric(
        "留存客户人均费用",
        f"${retained_avg_charge:,.2f}"
    )

with col4:
    st.metric(
        "流失客户人均费用",
        f"${churned_avg_charge:,.2f}",
        f"较留存客户 {avg_diff_rate:+.1f}%"
    )

fig = px.bar(
    contribution_df,
    x='churn_label',
    y='avg_charge_contribution',
    color='churn_label',
    text=contribution_df['avg_charge_contribution'].apply(lambda x: f"${x:,.2f}"),
    color_discrete_map={
        '留存': '#3498DB',
        '流失': '#E74C3C'
    },
    labels={
        'churn_label': '客户状态',
        'avg_charge_contribution': '人均费用贡献'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=13),
    hovertemplate='客户状态: %{x}<br>人均费用贡献: $%{y:,.2f}<extra></extra>'
)

fig.update_layout(
    **common_layout,
    height=430,
    xaxis_title='客户状态',
    yaxis_title='人均费用贡献 ($)',
    showlegend=False,
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 留存客户和流失客户数量不同，直接比较总费用贡献容易受到样本规模影响。"
    "因此这里重点比较人均费用贡献，用于判断单个客户的平均价值差异。"
)


# ======================================================
# 费用贡献分布分析
# ======================================================
strong_divider()

st.subheader("📦 留存与流失客户费用贡献分布")

fig = px.box(
    df,
    x='churn_label',
    y='monthly_revenue',
    color='churn_label',
    points='outliers',
    color_discrete_map={
        '留存': '#3498DB',
        '流失': '#E74C3C'
    },
    labels={
        'churn_label': '客户状态',
        'monthly_revenue': '客户月收入贡献'
    }

)

fig.update_traces(
    hovertemplate='客户状态: %{x}<br>月收入贡献: $%{y:,.2f}<extra></extra>'
)


fig.update_layout(
    **common_layout,
    height=480,
    xaxis_title='客户状态',
    yaxis_title='客户月收入贡献 ($)',
    showlegend=False,
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    f"💡 流失客户人均费用贡献为 ${churned_avg_charge:,.2f}，"
    f"留存客户人均费用贡献为 ${retained_avg_charge:,.2f}。"
    f"从中位数看，流失客户为 ${churned_median_charge:,.2f}，"
    f"留存客户为 ${retained_median_charge:,.2f}。"
)


# ======================================================
# 客户价值分层与人均费用贡献结构
# ======================================================
strong_divider()

st.subheader("🧩 客户价值分层与人均月收入贡献对比")


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

segment_df = df.copy()
segment_df['value_label'] = segment_df['customer_value_segment'].map(value_label_map)
segment_df['usage_label'] = segment_df['usage_intensity'].map(usage_label_map)

segment_avg_df = segment_df.groupby(
    ['value_label', 'usage_label', 'churn_label']
).agg(
    customer_count=('customer_id', 'count'),
    avg_charge_contribution=('monthly_revenue', 'mean'),
    median_charge_contribution=('monthly_revenue', 'median')
).reset_index()


fig = px.bar(
    segment_avg_df,
    x='value_label',
    y='avg_charge_contribution',
    color='churn_label',
    barmode='group',
    facet_col='usage_label',
    text=segment_avg_df['avg_charge_contribution'].apply(lambda x: f"${x:,.1f}"),
    color_discrete_map={
        '留存': '#3498DB',
        '流失': '#E74C3C'
    },
    labels={
        'value_label': '客户价值分层',
        'usage_label': '使用强度',
        'churn_label': '客户状态',
        'avg_charge_contribution': '人均月收入贡献'
    },

    hover_data={
        'customer_count': True,
        'median_charge_contribution': ':.2f',
        'avg_charge_contribution': ':.2f'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=11),
    hovertemplate=(
        '客户价值分层: %{x}<br>'
        '人均费用贡献: $%{y:,.2f}<br>'
        '客户数量: %{customdata[0]}<br>'
        '中位数费用贡献: $%{customdata[1]:,.2f}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=560,
    xaxis_title=None,
    yaxis_title='人均月收入贡献 ($)',
    legend_title_text='客户状态',
    margin=dict(t=120, b=80, l=40, r=40),
    title=dict(
        text="<b>客户价值分层与人均月收入贡献对比</b>",
        x=0.5,
        xanchor="center",
        y=0.98,
        yanchor="top",
        font=dict(
            size=20,
            color="#2C3E50",
            family="Microsoft YaHei, SimHei, Arial"
        )
    )
)

fig.update_xaxes(title_text='')


st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 这里按客户价值分层和使用强度比较人均月收入贡献，"
    "避免因为某一类客户人数更多而造成总收入贡献偏高的误判。"
)








# ======================================================
# 3. 客户价值分层与结构 (升级为旭日图)
# ======================================================
strong_divider()
st.subheader("🌞 多维客户画像与收入贡献结构 (旭日图)")
st.caption("从内到外依次为：客户价值分层 ➡️ 使用强度 ➡️ 客户状态。色块大小代表该群体的【总收入贡献】，颜色深浅代表【人均收入】。可点击色块进行下钻交互。")

value_label_map = {'high_value': '高价值', 'medium_value': '中价值', 'low_value': '低价值'}
usage_label_map = {'high_usage': '高使用', 'medium_usage': '中使用', 'low_usage': '低使用'}

sunburst_df = df.copy()
sunburst_df['value_label'] = sunburst_df['customer_value_segment'].map(value_label_map)
sunburst_df['usage_label'] = sunburst_df['usage_intensity'].map(usage_label_map)

# 聚合数据用于旭日图
sun_agg = sunburst_df.groupby(['value_label', 'usage_label', 'churn_label']).agg(
    total_revenue=('monthly_revenue', 'sum'),
    avg_revenue=('monthly_revenue', 'mean'),
    customer_count=('customer_id', 'count')
).reset_index()

fig_sun = px.sunburst(
    sun_agg,
    path=['value_label', 'usage_label', 'churn_label'], # 核心：层级路径
    values='total_revenue',                             # 扇形大小：总收入
    color='avg_revenue',                                # 扇形颜色：人均收入
    color_continuous_scale='Blues',
    hover_data={'customer_count': True, 'avg_revenue': ':.2f'}
)

fig_sun.update_traces(
    hovertemplate=(
        '<b>%{id}</b><br>'
        '总收入贡献: $%{value:,.2f}<br>'
        '人均收入: $%{color:,.2f}<br>'
        '客户数: %{customdata[0]} 人<extra></extra>'
    ),
    textinfo='label+percent parent'
)

fig_sun.update_layout(
    height=650,
    margin=dict(t=40, l=0, r=0, b=0),
    coloraxis_colorbar=dict(title="人均收入 ($)")
)

st.plotly_chart(fig_sun, use_container_width=True)







# ======================================================
# 3. 客户价值分层与结构 (升级为分面多维气泡矩阵图)
# ======================================================
strong_divider()

st.subheader("🫧 客户圈层特征与收入贡献矩阵 (气泡矩阵图)")
st.caption(
    "左图为「留存客户」，右图为「流失客户」。\n\n"
    "• 坐标轴：构建客户【价值分层】与【使用强度】的交叉特征矩阵\n"
    "• 气泡大小：代表该特征群体下的【客户数量规模】\n"
    "• 气泡颜色：代表该特征群体下的【人均月收入贡献】（颜色越暖越深，人均贡献越高）"
)

# 标签映射，明确排序逻辑
value_label_map = {'low_value': '低价值', 'medium_value': '中价值', 'high_value': '高价值'}
usage_label_map = {'low_usage': '低使用', 'medium_usage': '中使用', 'high_usage': '高使用'}

matrix_df = df.copy()
matrix_df['value_label'] = matrix_df['customer_value_segment'].map(value_label_map)
matrix_df['usage_label'] = matrix_df['usage_intensity'].map(usage_label_map)

# 对多维度进行聚合
matrix_agg = matrix_df.groupby(['value_label', 'usage_label', 'churn_label']).agg(
    customer_count=('customer_id', 'count'),
    avg_revenue=('monthly_revenue', 'mean'),
    total_revenue=('monthly_revenue', 'sum')
).reset_index()

# 绘制多维气泡矩阵图
fig_matrix = px.scatter(
    matrix_agg,
    x='value_label',
    y='usage_label',
    size='customer_count',     # 气泡大小代表底层基数(人数)
    color='avg_revenue',       # 颜色深浅代表单客含金量(人均收入)
    facet_col='churn_label',   # 左右分面对比流失状态
    facet_col_spacing=0.08,
    color_continuous_scale='Sunsetdark',  # 使用具有商业感的暖色渐变
    size_max=72,               # 【修改点】调大此数值，气泡整体按比例放大
    hover_data={
        'churn_label': False,
        'value_label': False,
        'usage_label': False,
        'customer_count': True,
        'avg_revenue': ':.2f',
        'total_revenue': ':.2f'
    },
    category_orders={          # 强制按业务逻辑排序，避免按照首字母乱排
        'value_label': ['低价值', '中价值', '高价值'],
        'usage_label': ['低使用', '中使用', '高使用'],
        'churn_label': ['留存', '流失']
    }
)

# 优化 Hover 提示框显示效果
fig_matrix.update_traces(
    hovertemplate=(
        '<b>客户属性:</b> %{x} - %{y}<br>'
        '<b>客户数量:</b> %{customdata[0]} 人<br>'
        '<b>人均收入:</b> $%{customdata[1]:,.2f}<br>'
        '<b>总计贡献:</b> $%{customdata[2]:,.2f}<extra></extra>'
    )
)

# 整体布局更新
fig_matrix.update_layout(
    **common_layout,
    height=550,
    # 【修改点】添加正中间的黑色主标题
    title=dict(
        text="<b>客户价值与使用强度交叉矩阵分析</b>",
        x=0.5,
        xanchor="center",
        y=0.96,
        font=dict(size=18, color="black")
    ),
    coloraxis_colorbar=dict(
        title=dict(text="人均月贡献 ($)", font=dict(color="black")),
        tickfont=dict(color="black")
    ),
    margin=dict(t=100, b=40, l=40, r=40),
    plot_bgcolor='white',
    paper_bgcolor='white'
)

# 【修改点】子图标题设为黑色
# 【修改点】子图标题设为黑色，并向上移动避免与边框重叠
fig_matrix.for_each_annotation(
    lambda a: a.update(
        text=f"<b>{a.text.split('=')[1]}客户</b>",
        font=dict(size=15, color="black"),
        yshift=15  # <--- 就是加了这一个参数，数值越大往上移得越多
    )
)


# 【修改点】X轴：黑色边框包裹、黑色字体、网格线
fig_matrix.update_xaxes(
    title_text="客户价值分层",
    title_font=dict(color="black", size=13),
    tickfont=dict(color="black", size=12),
    showline=True, linewidth=1.5, linecolor='black', mirror=True,  # mirror=True 形成完整黑框
    showgrid=True, gridcolor='lightgray', gridwidth=0.5
)

# 【修改点】Y轴：黑色边框包裹、黑色字体、网格线
fig_matrix.update_yaxes(
    title_font=dict(color="black", size=13),
    tickfont=dict(color="black", size=12),
    showline=True, linewidth=1.5, linecolor='black', mirror=True,  # mirror=True 形成完整黑框
    showgrid=True, gridcolor='lightgray', gridwidth=0.5
)

# 仅保留最左侧子图的 Y 轴标题
fig_matrix.layout.yaxis.title.text = "业务使用强度"
if hasattr(fig_matrix.layout, 'yaxis2'):
    fig_matrix.layout.yaxis2.title.text = ""

st.plotly_chart(fig_matrix, use_container_width=True)

st.info(
    "💡 交互提示：你可以将鼠标悬浮在气泡上，同时查看该群组的【客户基数】和【人均/总计收入】。"
    "在业务分析中，重点关注“大且颜色深”的气泡（即人数多且人均高的高优群体）。"
)
with st.expander("📊 点击查看/复制底层数据"):
    st.write("下面是用于生成气泡矩阵图的聚合数据。你可以点击右上角的复制按钮")
    # 将数据转换为 Markdown 格式，这样填给 AI 分析时格式最完美、绝不会乱码
    # st.code(matrix_agg.to_markdown(index=False), language="markdown")
    st.code(matrix_agg.to_csv(index=False), language="csv")




# ======================================================
# 帕累托分析
# ======================================================
strong_divider()

st.subheader("📈 客户月收入贡献帕累托分析")
st.caption(
    "数据处理说明：按照 monthly_revenue 从高到低对客户排序，"
    "计算客户累计占比和月收入累计贡献占比，"
    "用于判断少数高收入客户是否贡献了大部分收入。"
)

pareto_df = df[['customer_id', 'monthly_revenue', 'churn_label']].copy()

# 按月收入贡献从高到低排序
pareto_df = pareto_df.sort_values('monthly_revenue', ascending=False).reset_index(drop=True)

pareto_df['customer_rank'] = pareto_df.index + 1

# 累计月收入贡献
pareto_df['cum_revenue'] = pareto_df['monthly_revenue'].cumsum()

# 累计月收入贡献占比
pareto_df['cum_revenue_pct'] = (
    pareto_df['cum_revenue'] / pareto_df['monthly_revenue'].sum() * 100
)

# 客户累计占比
pareto_df['customer_pct'] = pareto_df['customer_rank'] / len(pareto_df) * 100

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=pareto_df['customer_pct'],
    y=pareto_df['cum_revenue_pct'],
    mode='lines',
    line=dict(color='#E67E22', width=4),
    name='累计月收入贡献占比',
    hovertemplate=(
        '客户累计占比: %{x:.1f}%<br>'
        '月收入贡献累计占比: %{y:.1f}%'
        '<extra></extra>'
    )
))

# 前 20% 客户参考线
fig.add_shape(
    type="line",
    x0=20,
    x1=20,
    y0=0,
    y1=100,
    line=dict(color="#E74C3C", width=2, dash="dash")
)

# 80% 收入贡献参考线
fig.add_shape(
    type="line",
    x0=0,
    x1=100,
    y0=80,
    y1=80,
    line=dict(color="#3498DB", width=2, dash="dash")
)

# 找到最接近前 20% 客户的位置
top20_idx = pareto_df['customer_pct'].sub(20).abs().idxmin()
top20_revenue_pct = pareto_df.loc[top20_idx, 'cum_revenue_pct']

fig.add_annotation(
    x=20,
    y=top20_revenue_pct,
    text=f"前20%客户贡献约 {top20_revenue_pct:.1f}%",
    showarrow=True,
    arrowhead=2,
    font=dict(color='black')
)

fig.update_layout(
    **common_layout,
    title=dict(
        text="<b>客户月收入贡献帕累托分析</b>",
        x=0.5,
        xanchor="center",
        y=0.96,
        yanchor="top",
        font=dict(
            size=20,
            color="#2C3E50",
            family="Microsoft YaHei, SimHei, Arial"
        )
    ),
    height=500,
    xaxis_title='客户累计占比 (%)',
    yaxis_title='月收入贡献累计占比 (%)',
    margin=dict(t=80, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    f"💡 前 20% 高月收入客户贡献了约 {top20_revenue_pct:.1f}% 的总月收入贡献，"
    "说明客户收入贡献存在一定集中度。"
)

# ======================================================
# 4. 帕累托分析 (升级为十分位双轴图)
# ======================================================
strong_divider()
st.subheader("📊 客户收入贡献十分位分析 (Decile Pareto)")
st.caption("将所有客户按月收入从高到低排序并均分为 10 组（每组 10% 的客户）。柱状图表示该组客户的收入总和，折线图表示累计收入占比。")

pareto_df = df[['customer_id', 'monthly_revenue']].copy()
pareto_df = pareto_df.sort_values('monthly_revenue', ascending=False).reset_index(drop=True)

# 将客户均分为 10 组 (十分位)
import numpy as np
pareto_df['decile'] = pd.qcut(pareto_df.index, 10, labels=[f"Top {i*10}%" for i in range(1, 11)])

# 聚合每组的数据
decile_df = pareto_df.groupby('decile').agg(
    group_revenue=('monthly_revenue', 'sum')
).reset_index()

# 计算累计占比
decile_df['cum_revenue'] = decile_df['group_revenue'].cumsum()
total_revenue_all = decile_df['group_revenue'].sum()
decile_df['cum_pct'] = decile_df['cum_revenue'] / total_revenue_all * 100

from plotly.subplots import make_subplots

# 创建双轴图
fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])

# 添加柱状图 (单组贡献)
fig_pareto.add_trace(
    go.Bar(
        x=decile_df['decile'],
        y=decile_df['group_revenue'],
        name="该组总收入",
        marker_color='#34495E',
        opacity=0.8,
        hovertemplate='%{x} 客户<br>总收入: $%{y:,.2f}<extra></extra>'
    ),
    secondary_y=False,
)

# 添加折线图 (累计贡献占比)
fig_pareto.add_trace(
    go.Scatter(
        x=decile_df['decile'],
        y=decile_df['cum_pct'],
        name="累计收入占比",
        mode='lines+markers',
        line=dict(color='#E67E22', width=4),
        marker=dict(size=8, color='white', line=dict(width=2, color='#E67E22')),
        hovertemplate='累计至 %{x}<br>累计占比: %{y:.1f}%<extra></extra>'
    ),
    secondary_y=True,
)

# 80% 黄金分割线
fig_pareto.add_shape(
    type="line", x0=-0.5, x1=9.5, y0=80, y1=80,
    line=dict(color="#E74C3C", width=2, dash="dash"),
    yref="y2"
)
fig_pareto.add_annotation(
    x=8, y=82, text="80% 收入贡献线", showarrow=False, font=dict(color="#E74C3C"), yref="y2"
)

fig_pareto.update_layout(
    **common_layout,
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig_pareto.update_yaxes(title_text="组内总收入 ($)", secondary_y=False)
fig_pareto.update_yaxes(title_text="累计占比 (%)", range=[0, 105], secondary_y=True)

st.plotly_chart(fig_pareto, use_container_width=True)
