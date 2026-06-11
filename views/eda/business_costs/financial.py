# views/eda/business_costs/financial.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_business_with_customer
import numpy as np

st.title("💰 客户财务价值与挽留成本分析")
st.markdown(
    "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
    unsafe_allow_html=True
)

# ======================================================
# 数据加载
# ======================================================
df = load_business_with_customer()

# ======================================================
# 基础预处理
# ======================================================
offer_label_map = {
    'no_offer': '无优惠',
    'discount_10_percent': '九折优惠',
    'discount_20_percent': '八折优惠',
    'free_international_trial': '免费国际套餐试用',
    'free_voicemail_month': '免费语音信箱月',
    'priority_support': '优先客服支持'
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

df['offer_label'] = df['offer_type'].map(offer_label_map).fillna(df['offer_type'])
df['value_label'] = df['customer_value_segment'].map(value_label_map).fillna(df['customer_value_segment'])
df['usage_label'] = df['usage_intensity'].map(usage_label_map).fillna(df['usage_intensity'])
df['risk_label'] = df['rule_based_churn_risk_level'].map(risk_label_map).fillna(df['rule_based_churn_risk_level'])

# 避免 retention_cost 为 0 时 ROI 除零
df['roi'] = df.apply(
    lambda x: x['net_gain_if_retained'] / x['retention_cost'] if x['retention_cost'] > 0 else None,
    axis=1
)

# 对没有 offer 的客户，单独标记
df['has_offer'] = df['offer_type'].apply(lambda x: '有挽留策略' if x != 'no_offer' else '无挽留策略')

# ======================================================
# 通用样式
# ======================================================
common_layout = dict(
    font=dict(color='black', size=12),
    title_font=dict(color='black', size=14),
    legend_font=dict(color='black'),
    # paper_bgcolor='white',
    # plot_bgcolor='white',
    title=None,
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
# 核心财务 KPI
# ======================================================
st.subheader("📊 核心财务指标")

total_customers = len(df)
total_clv = df['estimated_clv'].sum()
total_retention_cost = df['retention_cost'].sum()
total_expected_loss = df['expected_loss_if_churn'].sum()
total_net_gain = df['net_gain_if_retained'].sum()

avg_clv = df['estimated_clv'].mean()
avg_monthly_revenue = df['monthly_revenue'].mean()
offer_rate = (df['offer_type'] != 'no_offer').mean() * 100

col1, col2, col3, col4 = st.columns(4)

col1.metric("客户数量", f"{total_customers:,}")
col2.metric("总预估 CLV", f"${total_clv:,.0f}")
col3.metric("总挽留成本", f"${total_retention_cost:,.0f}")
col4.metric("总潜在流失损失", f"${total_expected_loss:,.0f}")

col5, col6, col7, col8 = st.columns(4)

col5.metric("总净收益", f"${total_net_gain:,.0f}")
col6.metric("人均 CLV", f"${avg_clv:,.2f}")
col7.metric("人均月收入", f"${avg_monthly_revenue:,.2f}")
col8.metric("挽留策略覆盖率", f"{offer_rate:.1f}%")

st.info(
    "💡 本页面基于 `business_costs.xlsx`，并通过 `customer_id` 合并了客户流失状态、价值分层、使用强度和风险等级。"
)

# ======================================================
# 挽留预算 - 预期收益曲线
# ======================================================
strong_divider()

st.subheader("🚀 挽留预算与预期收益曲线")

target_df = df.copy()

# 风险概率近似：用规则风险分数转成 0-1
target_df["risk_prob"] = target_df["rule_based_churn_risk_score"] / 100

# 风险调整后的潜在价值
target_df["risk_adjusted_value"] = target_df["estimated_clv"] * target_df["risk_prob"]

# 挽留优先净价值
target_df["priority_net_value"] = target_df["risk_adjusted_value"] - target_df["retention_cost"]

# 只保留有正向挽留价值的客户
target_df = target_df[target_df["priority_net_value"] > 0].copy()

target_df = target_df.sort_values("priority_net_value", ascending=False).reset_index(drop=True)

target_df["rank"] = np.arange(1, len(target_df) + 1)
target_df["customer_pct"] = target_df["rank"] / len(target_df) * 100
target_df["cum_expected_value"] = target_df["priority_net_value"].cumsum()
target_df["cum_retention_cost"] = target_df["retention_cost"].cumsum()
target_df["cum_customers"] = target_df["rank"]

fig = go.Figure()

# 左轴：累计预期净价值
fig.add_trace(
    go.Scatter(
        x=target_df["customer_pct"],
        y=target_df["cum_expected_value"],
        mode="lines",
        name="累计预期净价值",
        line=dict(
            color="#1ABC9C",
            width=4,
            shape="spline"
        ),
        fill="tozeroy",
        fillcolor="rgba(26, 188, 156, 0.16)",
        hovertemplate=(
            "<b>累计预期净价值</b><br>"
            "覆盖客户比例: %{x:.1f}%<br>"
            "累计净价值: $%{y:,.0f}<extra></extra>"
        )
    )
)

# 右轴：累计挽留成本
fig.add_trace(
    go.Scatter(
        x=target_df["customer_pct"],
        y=target_df["cum_retention_cost"],
        mode="lines",
        name="累计挽留成本",
        line=dict(
            color="#E67E22",
            width=3.5,
            dash="dash",
            shape="spline"
        ),
        yaxis="y2",
        hovertemplate=(
            "<b>累计挽留成本</b><br>"
            "覆盖客户比例: %{x:.1f}%<br>"
            "累计成本: $%{y:,.0f}<extra></extra>"
        )
    )
)

# 标注前 20% 客户
if len(target_df) > 0:
    top20_idx = max(int(len(target_df) * 0.2) - 1, 0)
    top20_row = target_df.iloc[top20_idx]

    fig.add_vline(
        x=20,
        line_dash="dot",
        line_color="#2C3E50",
        line_width=2,
        annotation_text="Top 20%",
        annotation_position="top",
        annotation_font=dict(
            color="#2C3E50",
            size=12
        )
    )

    fig.add_annotation(
        x=20,
        y=top20_row["cum_expected_value"],
        text=(
            f"<b>前20%客户</b><br>"
            f"累计净价值 ${top20_row['cum_expected_value']:,.0f}"
        ),
        showarrow=True,
        arrowhead=2,
        arrowwidth=1.5,
        arrowcolor="#2C3E50",
        ax=60,
        ay=-55,
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="#1ABC9C",
        borderwidth=1.5,
        borderpad=6,
        font=dict(color="#2C3E50", size=12)
    )

fig.update_layout(
    **common_layout,
    height=580,

    xaxis=dict(
        title=dict(
            text="按优先级覆盖的客户比例 (%)",
            font=dict(color="#2C3E50", size=13)
        ),
        tickfont=dict(color="#2C3E50"),
        showgrid=True,
        gridcolor="rgba(189, 195, 199, 0.35)",
        zeroline=False,
        linecolor="#BDC3C7",
        linewidth=1
    ),

    # 左侧 Y 轴：绿色系，对应净价值
    yaxis=dict(
        title=dict(
            text="累计预期净价值 ($)",
            font=dict(color="#1ABC9C", size=13)
        ),
        tickfont=dict(color="#1ABC9C"),
        showgrid=True,
        gridcolor="rgba(26, 188, 156, 0.12)",
        zeroline=False,
        linecolor="#1ABC9C",
        linewidth=2,
        ticks="outside",
        tickcolor="#1ABC9C"
    ),

    # 右侧 Y 轴：橙色系，对应成本
    yaxis2=dict(
        title=dict(
            text="累计挽留成本 ($)",
            font=dict(color="#E67E22", size=13)
        ),
        tickfont=dict(color="#E67E22"),
        overlaying="y",
        side="right",
        showgrid=False,
        zeroline=False,
        linecolor="#E67E22",
        linewidth=2,
        ticks="outside",
        tickcolor="#E67E22"
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.03,
        xanchor="right",
        x=1,
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(44,62,80,0.15)",
        borderwidth=1,
        font=dict(size=12, color="#2C3E50")
    ),

    hovermode="x unified",

    margin=dict(t=70, b=55, l=70, r=75),

    paper_bgcolor="white",
    plot_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 该图用于模拟挽留预算投放过程：优先选择风险调整后净价值最高的客户，"
    "观察随着覆盖客户比例提升，累计净价值和累计成本如何变化。"
)



# ======================================================
# CLV 帕累托曲线
# ======================================================
strong_divider()

st.subheader("👑 客户生命周期价值 CLV 帕累托曲线")

pareto_df = df.sort_values("estimated_clv", ascending=False).reset_index(drop=True).copy()

pareto_df["rank"] = np.arange(1, len(pareto_df) + 1)
pareto_df["customer_pct"] = pareto_df["rank"] / len(pareto_df) * 100
pareto_df["cum_clv"] = pareto_df["estimated_clv"].cumsum()
pareto_df["cum_clv_pct"] = pareto_df["cum_clv"] / pareto_df["estimated_clv"].sum() * 100

top20_clv_pct = pareto_df.loc[
    pareto_df["customer_pct"] <= 20, "estimated_clv"
].sum() / pareto_df["estimated_clv"].sum() * 100

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=pareto_df["customer_pct"],
        y=pareto_df["cum_clv_pct"],
        mode="lines",
        name="累计 CLV 占比",
        line=dict(color="#8E44AD", width=4),
        fill="tozeroy",
        fillcolor="rgba(142, 68, 173, 0.18)",
        hovertemplate=(
            "客户累计占比: %{x:.1f}%<br>"
            "累计 CLV 占比: %{y:.1f}%<extra></extra>"
        )
    )
)

# 平均分布参考线
fig.add_trace(
    go.Scatter(
        x=[0, 100],
        y=[0, 100],
        mode="lines",
        name="完全平均分布",
        line=dict(color="#95A5A6", width=2, dash="dash")
    )
)

fig.add_vline(
    x=20,
    line_dash="dot",
    line_color="#2C3E50"
)

fig.add_annotation(
    x=20,
    y=top20_clv_pct,
    text=f"前20%客户贡献<br>{top20_clv_pct:.1f}% CLV",
    showarrow=True,
    arrowhead=2,
    ax=60,
    ay=-50,
    bgcolor="white",
    bordercolor="#2C3E50",
    font=dict(color="black")
)

fig.update_layout(
    **common_layout,
    height=540,
    xaxis_title="客户累计占比 (%)",
    yaxis_title="累计 CLV 占比 (%)",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(t=60, b=50, l=60, r=60)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    f"💡 前 20% 高价值客户贡献了约 {top20_clv_pct:.1f}% 的总 CLV，"
    "说明客户价值具有明显集中性，应优先针对高价值客户制定精细化运营策略。"
)







# ======================================================
# 客户投资组合地图：CLV × 流失风险
# ======================================================
strong_divider()

st.subheader("🧭 客户财务价值投资组合地图")

portfolio_df = df.copy()

portfolio_df["risk_prob"] = portfolio_df["rule_based_churn_risk_score"] / 100
portfolio_df["risk_adjusted_value"] = portfolio_df["estimated_clv"] * portfolio_df["risk_prob"]
portfolio_df["priority_net_value"] = portfolio_df["risk_adjusted_value"] - portfolio_df["retention_cost"]

# 抽样，避免点太多
portfolio_sample = portfolio_df.sample(min(1800, len(portfolio_df)), random_state=42)

x_mid = portfolio_df["rule_based_churn_risk_score"].median()
y_mid = portfolio_df["estimated_clv"].median()

fig = px.scatter(
    portfolio_sample,
    x="rule_based_churn_risk_score",
    y="estimated_clv",
    size="monthly_revenue",
    color="priority_net_value",
    color_continuous_scale="RdYlGn",
    hover_data={
        "customer_id": True,
        "monthly_revenue": ":.2f",
        "estimated_clv": ":.2f",
        "retention_cost": ":.2f",
        "priority_net_value": ":.2f",
        "offer_label": True,
        "churn_label": True,
        "value_label": True,
        "risk_label": True
    },
    labels={
        "rule_based_churn_risk_score": "流失风险分数",
        "estimated_clv": "预估 CLV",
        "monthly_revenue": "月收入",
        "priority_net_value": "挽留优先净价值"
    }
)

# 四象限分割线
fig.add_vline(x=x_mid, line_dash="dash", line_color="#34495E")
fig.add_hline(y=y_mid, line_dash="dash", line_color="#34495E")

# 四象限文字
fig.add_annotation(
    x=portfolio_df["rule_based_churn_risk_score"].quantile(0.85),
    y=portfolio_df["estimated_clv"].quantile(0.9),
    text="重点挽留<br>高价值 × 高风险",
    showarrow=False,
    bgcolor="rgba(231,76,60,0.15)",
    bordercolor="#E74C3C",
    font=dict(color="#C0392B", size=13)
)

fig.add_annotation(
    x=portfolio_df["rule_based_churn_risk_score"].quantile(0.15),
    y=portfolio_df["estimated_clv"].quantile(0.9),
    text="重点维护<br>高价值 × 低风险",
    showarrow=False,
    bgcolor="rgba(46,204,113,0.15)",
    bordercolor="#27AE60",
    font=dict(color="#1E8449", size=13)
)

fig.add_annotation(
    x=portfolio_df["rule_based_churn_risk_score"].quantile(0.85),
    y=portfolio_df["estimated_clv"].quantile(0.15),
    text="控制成本<br>低价值 × 高风险",
    showarrow=False,
    bgcolor="rgba(241,196,15,0.18)",
    bordercolor="#F1C40F",
    font=dict(color="#B7950B", size=13)
)

fig.add_annotation(
    x=portfolio_df["rule_based_churn_risk_score"].quantile(0.15),
    y=portfolio_df["estimated_clv"].quantile(0.15),
    text="常规运营<br>低价值 × 低风险",
    showarrow=False,
    bgcolor="rgba(149,165,166,0.15)",
    bordercolor="#95A5A6",
    font=dict(color="#566573", size=13)
)

fig.update_traces(
    marker=dict(
        opacity=0.72,
        line=dict(width=0.5, color="white")
    )
)

fig.update_layout(
    **common_layout,
    height=620,
    xaxis_title="流失风险分数",
    yaxis_title="预估 CLV ($)",
    coloraxis_colorbar=dict(title="优先净价值"),
    margin=dict(t=50, b=50, l=60, r=60)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 该图将客户按 CLV 和流失风险划分为四类。右上角客户具有最高挽留优先级，"
    "适合优先投入优惠、客服跟进或专项关怀资源。"
)


# ======================================================
# Offer 类型分布
# ======================================================
strong_divider()

st.subheader("🎁 挽留策略类型分布")

offer_count = df.groupby('offer_label').agg(
    customer_count=('customer_id', 'count'),
    avg_retention_cost=('retention_cost', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index().sort_values('customer_count', ascending=True)

fig = px.bar(
    offer_count,
    x='customer_count',
    y='offer_label',
    orientation='h',
    color='offer_label',
    text='customer_count',
    labels={
        'customer_count': '客户数量',
        'offer_label': '挽留策略'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '挽留策略: %{y}<br>'
        '客户数量: %{x}<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=460,
    showlegend=False,
    xaxis_title='客户数量',
    yaxis_title='挽留策略',
    margin=dict(t=40, b=40, l=80, r=80)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图展示不同挽留策略的覆盖人数，帮助观察策略投放结构是否合理。")

# ======================================================
# 不同 Offer 的平均净收益
# ======================================================
strong_divider()

st.subheader("📈 不同挽留策略的平均净收益")

offer_profit = df.groupby('offer_label').agg(
    customer_count=('customer_id', 'count'),
    avg_clv=('estimated_clv', 'mean'),
    avg_retention_cost=('retention_cost', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean'),
    total_net_gain=('net_gain_if_retained', 'sum')
).reset_index()

offer_profit = offer_profit.sort_values('avg_net_gain', ascending=True)

fig = px.bar(
    offer_profit,
    x='avg_net_gain',
    y='offer_label',
    orientation='h',
    color='avg_net_gain',
    color_continuous_scale='Blues',
    text=offer_profit['avg_net_gain'].apply(lambda x: f"${x:,.0f}"),
    hover_data={
        'customer_count': True,
        'avg_clv': ':.2f',
        'avg_retention_cost': ':.2f',
        'total_net_gain': ':.2f'
    },
    labels={
        'avg_net_gain': '平均净收益',
        'offer_label': '挽留策略',
        'customer_count': '客户数量',
        'avg_clv': '平均 CLV',
        'avg_retention_cost': '平均挽留成本',
        'total_net_gain': '总净收益'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '挽留策略: %{y}<br>'
        '平均净收益: $%{x:,.2f}<br>'
        '客户数量: %{customdata[0]}<br>'
        '平均 CLV: $%{customdata[1]:,.2f}<br>'
        '平均挽留成本: $%{customdata[2]:,.2f}<br>'
        '总净收益: $%{customdata[3]:,.2f}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=460,
    xaxis_title='平均净收益 ($)',
    yaxis_title='挽留策略',
    coloraxis_showscale=False,
    margin=dict(t=40, b=40, l=80, r=80)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 平均净收益越高，说明该策略覆盖的客户长期价值更高，或策略成本更低。")

# ======================================================
# 不同 Offer 的 ROI
# ======================================================
strong_divider()

st.subheader("💹 不同挽留策略的投入产出比 ROI")

offer_roi_df = df[df['retention_cost'] > 0].copy()

offer_roi = offer_roi_df.groupby('offer_label').agg(
    customer_count=('customer_id', 'count'),
    total_retention_cost=('retention_cost', 'sum'),
    total_net_gain=('net_gain_if_retained', 'sum'),
    avg_roi=('roi', 'mean')
).reset_index()

offer_roi['overall_roi'] = offer_roi['total_net_gain'] / offer_roi['total_retention_cost']
offer_roi = offer_roi.sort_values('overall_roi', ascending=True)

fig = px.bar(
    offer_roi,
    x='overall_roi',
    y='offer_label',
    orientation='h',
    color='overall_roi',
    color_continuous_scale='Greens',
    text=offer_roi['overall_roi'].apply(lambda x: f"{x:.1f}x"),
    hover_data={
        'customer_count': True,
        'total_retention_cost': ':.2f',
        'total_net_gain': ':.2f',
        'avg_roi': ':.2f'
    },
    labels={
        'overall_roi': '整体 ROI',
        'offer_label': '挽留策略',
        'customer_count': '客户数量',
        'total_retention_cost': '总挽留成本',
        'total_net_gain': '总净收益',
        'avg_roi': '平均客户 ROI'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '挽留策略: %{y}<br>'
        '整体 ROI: %{x:.1f}x<br>'
        '客户数量: %{customdata[0]}<br>'
        '总挽留成本: $%{customdata[1]:,.2f}<br>'
        '总净收益: $%{customdata[2]:,.2f}<br>'
        '平均客户 ROI: %{customdata[3]:.1f}x'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=440,
    xaxis_title='整体 ROI，净收益 / 挽留成本',
    yaxis_title='挽留策略',
    coloraxis_showscale=False,
    margin=dict(t=40, b=40, l=80, r=80)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 ROI = 净收益 / 挽留成本。这里只计算 retention_cost > 0 的策略，"
    "因为无优惠客户成本为 0，不能直接计算 ROI。"
)

# ======================================================
# CLV 分布
# ======================================================
strong_divider()

st.subheader("📦 客户预估 CLV 分布")

fig = px.histogram(
    df,
    x='estimated_clv',
    color='churn_label',
    nbins=40,
    barmode='overlay',
    opacity=0.75,
    color_discrete_map={
        '留存': '#3498DB',
        '流失': '#E74C3C'
    },
    labels={
        'estimated_clv': '预估 CLV',
        'churn_label': '客户状态'
    }
)

fig.update_layout(
    **common_layout,
    height=440,
    xaxis_title='预估 CLV ($)',
    yaxis_title='客户数量',
    legend_title_text='客户状态',
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图用于观察留存与流失客户在长期价值 CLV 上是否存在明显差异。")

# ======================================================
# 留存 vs 流失客户财务价值对比
# ======================================================
strong_divider()

st.subheader("👥 留存 vs 流失客户财务价值对比")

churn_finance = df.groupby('churn_label').agg(
    customer_count=('customer_id', 'count'),
    avg_monthly_revenue=('monthly_revenue', 'mean'),
    avg_clv=('estimated_clv', 'mean'),
    avg_expected_loss=('expected_loss_if_churn', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index()

fig = px.bar(
    churn_finance,
    x='churn_label',
    y=['avg_monthly_revenue', 'avg_clv', 'avg_expected_loss', 'avg_net_gain'],
    barmode='group',
    text_auto='.1f',
    labels={
        'churn_label': '客户状态',
        'value': '金额 ($)',
        'variable': '财务指标'
    }
)

fig.update_layout(
    **common_layout,
    height=480,
    xaxis_title='客户状态',
    yaxis_title='平均金额 ($)',
    legend_title_text='财务指标',
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 这里用平均值对比，避免留存客户和流失客户数量不同导致总量对比偏差。")

# ======================================================
# 挽留成本 vs 净收益散点图
# ======================================================
strong_divider()

st.subheader("🎯 挽留成本 vs 净收益客户散点图")

sample_df = df.sample(min(1500, len(df)), random_state=42)

fig = px.scatter(
    sample_df,
    x='retention_cost',
    y='net_gain_if_retained',
    color='offer_label',
    size='estimated_clv',
    symbol='churn_label',
    hover_data={
        'customer_id': True,
        'monthly_revenue': ':.2f',
        'estimated_remaining_months': True,
        'estimated_clv': ':.2f',
        'expected_loss_if_churn': ':.2f',
        'rule_based_churn_risk_score': True,
        'risk_label': True
    },
    labels={
        'retention_cost': '挽留成本',
        'net_gain_if_retained': '挽留后净收益',
        'offer_label': '挽留策略',
        'estimated_clv': '预估 CLV',
        'churn_label': '客户状态'
    }
)

fig.update_layout(
    **common_layout,
    height=560,
    xaxis_title='挽留成本 ($)',
    yaxis_title='挽留后净收益 ($)',
    legend_title_text='挽留策略',
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 理想客户位于左上方：挽留成本低、净收益高。"
    "右下方客户则可能存在高成本低回报，需要谨慎投放。"
)

# ======================================================
# 风险等级下的潜在流失损失
# ======================================================
strong_divider()

st.subheader("⚠️ 不同风险等级的潜在流失损失")

risk_loss = df.groupby('risk_label').agg(
    customer_count=('customer_id', 'count'),
    total_expected_loss=('expected_loss_if_churn', 'sum'),
    avg_expected_loss=('expected_loss_if_churn', 'mean'),
    avg_clv=('estimated_clv', 'mean')
).reset_index()

risk_order = ['低风险', '中风险', '高风险']
risk_loss['risk_label'] = pd.Categorical(risk_loss['risk_label'], categories=risk_order, ordered=True)
risk_loss = risk_loss.sort_values('risk_label')

fig = px.bar(
    risk_loss,
    x='risk_label',
    y='total_expected_loss',
    color='risk_label',
    text=risk_loss['total_expected_loss'].apply(lambda x: f"${x:,.0f}"),
    color_discrete_map={
        '低风险': '#27AE60',
        '中风险': '#F1C40F',
        '高风险': '#E74C3C'
    },
    hover_data={
        'customer_count': True,
        'avg_expected_loss': ':.2f',
        'avg_clv': ':.2f'
    },
    labels={
        'risk_label': '风险等级',
        'total_expected_loss': '总潜在流失损失',
        'customer_count': '客户数量',
        'avg_expected_loss': '人均潜在损失',
        'avg_clv': '人均 CLV'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '风险等级: %{x}<br>'
        '总潜在流失损失: $%{y:,.2f}<br>'
        '客户数量: %{customdata[0]}<br>'
        '人均潜在损失: $%{customdata[1]:,.2f}<br>'
        '人均 CLV: $%{customdata[2]:,.2f}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=460,
    xaxis_title='风险等级',
    yaxis_title='总潜在流失损失 ($)',
    showlegend=False,
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 高风险客户如果同时具备较高 CLV，就是最应该优先治理的客户群体。")

# ======================================================
# 客户价值分层下的财务指标
# ======================================================
strong_divider()

st.subheader("🏷️ 客户价值分层下的财务表现")

value_finance = df.groupby('value_label').agg(
    customer_count=('customer_id', 'count'),
    avg_monthly_revenue=('monthly_revenue', 'mean'),
    avg_clv=('estimated_clv', 'mean'),
    avg_retention_cost=('retention_cost', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index()

value_order = ['高价值', '中价值', '低价值']
value_finance['value_label'] = pd.Categorical(value_finance['value_label'], categories=value_order, ordered=True)
value_finance = value_finance.sort_values('value_label')

fig = px.bar(
    value_finance,
    x='value_label',
    y='avg_net_gain',
    color='value_label',
    text=value_finance['avg_net_gain'].apply(lambda x: f"${x:,.0f}"),
    color_discrete_map={
        '高价值': '#27AE60',
        '中价值': '#F1C40F',
        '低价值': '#95A5A6'
    },
    hover_data={
        'customer_count': True,
        'avg_monthly_revenue': ':.2f',
        'avg_clv': ':.2f',
        'avg_retention_cost': ':.2f'
    },
    labels={
        'value_label': '客户价值分层',
        'avg_net_gain': '平均净收益',
        'customer_count': '客户数量',
        'avg_monthly_revenue': '平均月收入',
        'avg_clv': '平均 CLV',
        'avg_retention_cost': '平均挽留成本'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '客户价值分层: %{x}<br>'
        '平均净收益: $%{y:,.2f}<br>'
        '客户数量: %{customdata[0]}<br>'
        '平均月收入: $%{customdata[1]:,.2f}<br>'
        '平均 CLV: $%{customdata[2]:,.2f}<br>'
        '平均挽留成本: $%{customdata[3]:,.2f}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=460,
    xaxis_title='客户价值分层',
    yaxis_title='平均净收益 ($)',
    showlegend=False,
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图用于判断不同价值层级客户的平均净收益，辅助制定差异化挽留预算。")

# ======================================================
# 潜在流失损失 Top 客户
# ======================================================
strong_divider()

st.subheader("🔎 潜在流失损失 Top 客户")

top_loss_customers = df.sort_values('expected_loss_if_churn', ascending=False).head(30)

show_cols = [
    'customer_id',
    'monthly_revenue',
    'estimated_remaining_months',
    'estimated_clv',
    'offer_label',
    'retention_cost',
    'expected_loss_if_churn',
    'net_gain_if_retained',
    'churn_label',
    'value_label',
    'risk_label',
    'rule_based_churn_risk_score'
]

st.dataframe(
    top_loss_customers[show_cols],
    use_container_width=True
)

st.caption(
    "💡 该表展示潜在流失损失最高的客户，可作为优先挽留名单。"
)
