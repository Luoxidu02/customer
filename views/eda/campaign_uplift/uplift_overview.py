# views/eda/campaign_uplift/uplift.py
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_campaign_with_customer_business
import plotly.graph_objects as go
import numpy as np

import holoviews as hv
from bokeh.plotting import show
from bokeh.embed import file_html
from bokeh.resources import CDN
hv.extension('bokeh')

st.title("📣 营销活动 Uplift 效果分析")
st.markdown(
    "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
    unsafe_allow_html=True
)

# ======================================================
# 数据加载
# ======================================================
df = load_campaign_with_customer_business()
st.success("""
**📂 本页数据整合说明：**
1. **活动结果层** (来自 `campaign_uplift.xlsx`): 包含 `treatment_group`, `campaign_channel`, `offer_type`, `contacted`, `responded`, `original_churn`, `churn_after_campaign`, `uplift_label`。
2. **财务价值层** (来自 `business_costs.xlsx`): 包含 `estimated_clv`, `retention_cost`, `net_gain_if_retained`。
3. **客户属性层** (来自 `full_customers.xlsx`): 包含 `customer_value_segment`, `rule_based_churn_risk_level`。
""")


# ======================================================
# 标签映射
# ======================================================
group_label_map = {
    'control': '对照组',
    'treatment': '实验组'
}

channel_label_map = {
    'none': '无触达',
    'SMS': '短信',
    'email': '邮件',
    'phone_call': '电话',
    'app_notification': 'App 推送'
}

offer_label_map = {
    'no_offer': '无优惠',
    'discount_10_percent': '九折优惠',
    'discount_20_percent': '八折优惠',
    'free_international_trial': '免费国际套餐试用',
    'free_voicemail_month': '免费语音信箱月',
    'priority_support': '优先客服支持',
'loyalty_bonus': '老客户奖励'

}

uplift_label_map = {
    'sure_thing': '自然留存型',
    'persuadable': '可被说服型',
    'do_not_disturb': '不应打扰型',
    'uncertain': '不确定型',
    'lost_cause': '挽回无望型'
}


value_label_map = {
    'high_value': '高价值',
    'medium_value': '中价值',
    'low_value': '低价值'
}

risk_label_map = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
}

df['group_label'] = df['treatment_group'].map(group_label_map).fillna(df['treatment_group'])
df['channel_label'] = df['campaign_channel'].map(channel_label_map).fillna(df['campaign_channel'])
df['offer_label'] = df['offer_type'].map(offer_label_map).fillna(df['offer_type'])
df['uplift_label'] = df['uplift_label'].astype(str).str.strip()

df['uplift_label_cn'] = df['uplift_label'].map(uplift_label_map).fillna(df['uplift_label'])
df['value_label'] = df['customer_value_segment'].map(value_label_map).fillna(df['customer_value_segment'])
df['risk_label'] = df['rule_based_churn_risk_level'].map(risk_label_map).fillna(df['rule_based_churn_risk_level'])

# ======================================================
# 通用样式
# ======================================================
common_layout = dict(
    font=dict(color='black', size=12),
    title_font=dict(color='black', size=16),
    legend_font=dict(color='black'),
    # paper_bgcolor='white',
    # plot_bgcolor='white'
)

def apply_chart_style(fig, title_text):
    """
    统一设置图表标题、横纵坐标标题和刻度文字颜色。
    """
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(color='black', size=16)
        ),
        font=dict(color='black', size=12),
        legend_font=dict(color='black'),
        paper_bgcolor='white',
        plot_bgcolor='white',
        coloraxis_colorbar=dict(
            title_font=dict(color='black'),
            tickfont=dict(color='black')
        )
    )

    fig.update_xaxes(
        title_font=dict(color='black', size=13),
        tickfont=dict(color='black', size=12),
        color='black'
    )

    fig.update_yaxes(
        title_font=dict(color='black', size=13),
        tickfont=dict(color='black', size=12),
        color='black'
    )

    return fig

def strong_divider():
    st.markdown(
        "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
        unsafe_allow_html=True
    )
def render_chord_chart(edges_df, nodes_df, title, height=760):
    """
    使用 Holoviews + Bokeh 在 Streamlit 中渲染弦图。

    参数说明：
    edges_df: 必须包含 source, target, value 三列
    nodes_df: 必须包含 index, name, group, color 四列
    title: 图标题
    height: 图表高度
    """

    if edges_df.empty:
        st.warning("当前筛选条件下没有可用于绘制弦图的数据。")
        return

    def rotate_left_labels(plot, element):
        import numpy as np
        from bokeh.models import Text

        for renderer in plot.state.renderers:
            if hasattr(renderer, "glyph") and isinstance(renderer.glyph, Text):
                source = renderer.data_source

                if "x" in source.data and "angle" in source.data:
                    x = np.array(source.data["x"])
                    angle = np.array(source.data["angle"])

                    left = x < 0

                    angle[left] = angle[left] + np.pi
                    angle = (angle + np.pi) % (2 * np.pi) - np.pi

                    source.data["angle"] = angle
                    source.data["text_align"] = np.where(left, "right", "left")

                    renderer.glyph.text_align = "text_align"
                    renderer.glyph.text_baseline = "middle"

    chord = hv.Chord((edges_df, hv.Dataset(nodes_df, 'index')))

    chord = chord.opts(
        width=900,
        height=900,
        title=title,
        labels='name',
        node_color='color',
        edge_color='source',
        cmap='Category20',
        edge_cmap='Category20',
        edge_alpha=0.62,
        node_size=16,
        label_text_font_size='11pt',
        label_text_color='black',
        bgcolor='white',
        hooks=[rotate_left_labels]
    )

    bokeh_fig = hv.render(chord, backend='bokeh')

    bokeh_fig.title.text_font_size = "18pt"
    bokeh_fig.title.text_font_style = "bold"
    bokeh_fig.title.align = "center"
    bokeh_fig.background_fill_color = "white"
    bokeh_fig.border_fill_color = "white"
    bokeh_fig.outline_line_color = None

    html = file_html(bokeh_fig, CDN, title)
    st.components.v1.html(html, height=height + 80, scrolling=False)

# ======================================================
# 核心 KPI
# ======================================================
st.subheader("📊 活动核心指标")

total_customers = len(df)
contact_rate = df['contacted_int'].mean() * 100
response_rate = df.loc[df['contacted_int'] == 1, 'responded_int'].mean() * 100
original_churn_rate = df['original_churn_int'].mean() * 100
after_churn_rate = df['churn_after_campaign_int'].mean() * 100
saved_count = df['saved_by_campaign'].sum()
worsened_count = df['worsened_after_campaign'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("客户数量", f"{total_customers:,}")
col2.metric("触达率", f"{contact_rate:.1f}%")
col3.metric("触达客户响应率", f"{response_rate:.1f}%")
col4.metric("被挽回客户数", f"{saved_count:,}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("活动前流失率", f"{original_churn_rate:.1f}%")
col6.metric("活动后流失率", f"{after_churn_rate:.1f}%")
col7.metric("流失率变化", f"{after_churn_rate - original_churn_rate:+.1f}%")
col8.metric("活动后变差客户数", f"{worsened_count:,}")

st.info(
    "💡 本页面基于 `campaign_uplift.xlsx`，并通过 `customer_id` 合并客户风险、价值分层和 CLV 财务字段。"
)












# ======================================================
# 实验组 vs 对照组：活动前后流失率
# ======================================================
strong_divider()

st.subheader("🧪 实验组 vs 对照组：活动前后流失率")

group_effect = df.groupby('group_label').agg(
    customer_count=('customer_id', 'count'),
    original_churn_rate=('original_churn_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    response_rate=('responded_int', 'mean'),
    saved_count=('saved_by_campaign', 'sum')
).reset_index()

group_effect['original_churn_rate_pct'] = group_effect['original_churn_rate'] * 100
group_effect['after_churn_rate_pct'] = group_effect['after_churn_rate'] * 100
group_effect['response_rate_pct'] = group_effect['response_rate'] * 100

plot_df = group_effect.melt(
    id_vars=['group_label', 'customer_count'],
    value_vars=['original_churn_rate_pct', 'after_churn_rate_pct'],
    var_name='metric',
    value_name='rate'
)

metric_map = {
    'original_churn_rate_pct': '活动前流失率',
    'after_churn_rate_pct': '活动后流失率'
}

plot_df['metric_label'] = plot_df['metric'].map(metric_map)

fig = px.bar(
    plot_df,
    x='group_label',
    y='rate',
    color='metric_label',
    barmode='group',
    text=plot_df['rate'].apply(lambda x: f"{x:.1f}%"),
    color_discrete_map={
        '活动前流失率': '#95A5A6',
        '活动后流失率': '#E74C3C'
    },
    labels={
        'group_label': '实验分组',
        'rate': '流失率 (%)',
        'metric_label': '指标'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12)
)

fig.update_layout(
    **common_layout,
    height=440,
    xaxis_title='实验分组',
    yaxis_title='流失率 (%)',
    legend_title_text='指标',
    margin=dict(t=70, b=40, l=40, r=40)
)

fig = apply_chart_style(fig, "实验组与对照组活动前后流失率对比")

st.plotly_chart(fig, use_container_width=True)

st.info("💡 如果实验组活动后流失率明显低于活动前，说明活动有一定挽留效果。")

# ======================================================
# 分组响应率
# ======================================================
strong_divider()

st.subheader("📬 实验组与对照组响应情况")

group_response = df.groupby('group_label').agg(
    customer_count=('customer_id', 'count'),
    contacted_count=('contacted_int', 'sum'),
    responded_count=('responded_int', 'sum')
).reset_index()

group_response['response_rate_pct'] = group_response['responded_count'] / group_response['contacted_count'].replace(0, pd.NA) * 100
group_response['response_rate_pct'] = group_response['response_rate_pct'].fillna(0)

fig = px.bar(
    group_response,
    x='group_label',
    y='response_rate_pct',
    color='group_label',
    text=group_response['response_rate_pct'].apply(lambda x: f"{x:.1f}%"),
    color_discrete_map={
        '对照组': '#95A5A6',
        '实验组': '#3498DB'
    },
    hover_data={
        'customer_count': True,
        'contacted_count': True,
        'responded_count': True
    },
    labels={
        'group_label': '实验分组',
        'response_rate_pct': '响应率 (%)',
        'customer_count': '客户数量',
        'contacted_count': '触达数量',
        'responded_count': '响应数量'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '分组: %{x}<br>'
        '响应率: %{y:.1f}%<br>'
        '客户数量: %{customdata[0]}<br>'
        '触达数量: %{customdata[1]}<br>'
        '响应数量: %{customdata[2]}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=420,
    showlegend=False,
    xaxis_title='实验分组',
    yaxis_title='响应率 (%)',
    margin=dict(t=70, b=40, l=40, r=40)
)

fig = apply_chart_style(fig, "实验组与对照组响应率对比")

st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 渠道响应率
# ======================================================
strong_divider()

st.subheader("📡 不同营销渠道的响应率")

channel_df = df[df['contacted_int'] == 1].copy()

channel_perf = channel_df.groupby('channel_label').agg(
    customer_count=('customer_id', 'count'),
    responded_count=('responded_int', 'sum'),
    response_rate=('responded_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    saved_count=('saved_by_campaign', 'sum'),
    avg_clv=('estimated_clv', 'mean')
).reset_index()

channel_perf['response_rate_pct'] = channel_perf['response_rate'] * 100
channel_perf['after_churn_rate_pct'] = channel_perf['after_churn_rate'] * 100
channel_perf = channel_perf.sort_values('response_rate_pct', ascending=True)

fig = px.bar(
    channel_perf,
    x='response_rate_pct',
    y='channel_label',
    orientation='h',
    color='response_rate_pct',
    color_continuous_scale='Blues',
    text=channel_perf['response_rate_pct'].apply(lambda x: f"{x:.1f}%"),
    hover_data={
        'customer_count': True,
        'responded_count': True,
        'after_churn_rate_pct': ':.1f',
        'saved_count': True,
        'avg_clv': ':.2f'
    },
    labels={
        'response_rate_pct': '响应率 (%)',
        'channel_label': '营销渠道',
        'customer_count': '客户数量',
        'responded_count': '响应客户数',
        'after_churn_rate_pct': '活动后流失率',
        'saved_count': '被挽回客户数',
        'avg_clv': '平均客户生命周期价值'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '渠道: %{y}<br>'
        '响应率: %{x:.1f}%<br>'
        '客户数量: %{customdata[0]}<br>'
        '响应客户数: %{customdata[1]}<br>'
        '活动后流失率: %{customdata[2]:.1f}%<br>'
        '被挽回客户数: %{customdata[3]}<br>'
        '平均客户生命周期价值: $%{customdata[4]:,.2f}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=300,
    xaxis_title='响应率 (%)',
    yaxis_title='营销渠道',
    coloraxis_showscale=False,
    margin=dict(t=70, b=40, l=80, r=80)
)

fig = apply_chart_style(fig, "不同营销渠道的响应率对比")

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图只统计已触达客户，用于比较短信、邮件、电话、App 推送等渠道的响应效果。")

# ======================================================
# 渠道活动后流失率
# ======================================================
strong_divider()

st.subheader("🚨 不同营销渠道的活动后流失率")

channel_churn = channel_perf.sort_values('after_churn_rate_pct', ascending=True)

fig = px.bar(
    channel_churn,
    x='after_churn_rate_pct',
    y='channel_label',
    orientation='h',
    color='after_churn_rate_pct',
    color_continuous_scale=['#27AE60', '#F1C40F', '#E74C3C'],
    text=channel_churn['after_churn_rate_pct'].apply(lambda x: f"{x:.1f}%"),
    hover_data={
        'customer_count': True,
        'response_rate_pct': ':.1f',
        'saved_count': True
    },
    labels={
        'after_churn_rate_pct': '活动后流失率 (%)',
        'channel_label': '营销渠道',
        'customer_count': '客户数量',
        'response_rate_pct': '响应率',
        'saved_count': '被挽回客户数'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12)
)

fig.update_layout(
    **common_layout,
    height=290,
    xaxis_title='活动后流失率 (%)',
    yaxis_title='营销渠道',
    coloraxis_showscale=False,
    margin=dict(t=70, b=40, l=80, r=80)
)

fig = apply_chart_style(fig, "不同营销渠道的活动后流失率对比")

st.plotly_chart(fig, use_container_width=True)

st.info("💡 响应率高不一定代表最终流失率低，因此需要同时观察渠道响应率和活动后流失率。")








# ======================================================
# 营销渠道响应率与活动后流失率四象限分析
# ======================================================
strong_divider()

st.subheader("📡 营销渠道响应率与活动后流失率四象限分析")

# 如果文件顶部已经导入过，则这里不用重复导入
# import plotly.graph_objects as go

channel_df = df[df['contacted_int'] == 1].copy()

channel_perf = channel_df.groupby('channel_label').agg(
    customer_count=('customer_id', 'count'),
    responded_count=('responded_int', 'sum'),
    response_rate=('responded_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    saved_count=('saved_by_campaign', 'sum'),
    avg_clv=('estimated_clv', 'mean')
).reset_index()

channel_perf['response_rate_pct'] = channel_perf['response_rate'] * 100
channel_perf['after_churn_rate_pct'] = channel_perf['after_churn_rate'] * 100

channel_perf['responded_share_text'] = channel_perf.apply(
    lambda row: f"{row['responded_count']:,.0f} / {row['customer_count']:,.0f}",
    axis=1
)


# ======================================================
# 坐标轴范围设置：根据数据自动留白，不强制从 0 开始
# ======================================================
def calc_pct_range(series, pad_ratio=0.18, min_pad=3):
    s = series.dropna()

    if s.empty:
        return 0, 100

    vmin = s.min()
    vmax = s.max()
    span = vmax - vmin

    if span == 0:
        pad = max(vmax * 0.12, min_pad)
    else:
        pad = max(span * pad_ratio, min_pad)

    range_min = max(0, vmin - pad)
    range_max = min(100, vmax + pad)

    if range_max - range_min < 6:
        mid = (range_min + range_max) / 2
        range_min = max(0, mid - 3)
        range_max = min(100, mid + 3)

    return range_min, range_max


x_min_range, x_max_range = calc_pct_range(channel_perf['response_rate_pct'])
y_min_range, y_max_range = calc_pct_range(channel_perf['after_churn_rate_pct'])

median_response = channel_perf['response_rate_pct'].median()
median_churn = channel_perf['after_churn_rate_pct'].median()

max_customer_count = channel_perf['customer_count'].max()

if pd.isna(max_customer_count) or max_customer_count <= 0:
    max_customer_count = 1

sizeref = 2.0 * max_customer_count / (46 ** 2)


# ======================================================
# 四象限气泡图
# ======================================================
fig = go.Figure()

# 第一象限：高响应、低流失，重点投入区域
fig.add_shape(
    type="rect",
    x0=median_response,
    x1=x_max_range,
    y0=y_min_range,
    y1=median_churn,
    layer="below",
    fillcolor="rgba(0, 109, 119, 0.10)",
    line=dict(width=0)
)

# 第三象限：低响应、高流失，优化调整区域
fig.add_shape(
    type="rect",
    x0=x_min_range,
    x1=median_response,
    y0=median_churn,
    y1=y_max_range,
    layer="below",
    fillcolor="rgba(183, 121, 31, 0.10)",
    line=dict(width=0)
)

# 主气泡图
fig.add_trace(
    go.Scatter(
        x=channel_perf['response_rate_pct'],
        y=channel_perf['after_churn_rate_pct'],
        mode='markers+text',
        text=channel_perf['channel_label'],
        textposition='top center',
        textfont=dict(
            size=13,
            color='#1F2D3D',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        marker=dict(
            size=channel_perf['customer_count'],
            sizemode='area',
            sizeref=sizeref,
            sizemin=18,
            color=channel_perf['saved_count'],
            colorscale=[
                [0.00, '#F4EBD0'],
                [0.35, '#C9A227'],
                [0.70, '#7A9E7E'],
                [1.00, '#006D77']
            ],
            showscale=True,
            colorbar=dict(
                title=dict(
                    text='被挽回<br>客户数',
                    font=dict(
                        size=12,
                        color='#1F2D3D',
                        family='Microsoft YaHei, SimHei, Arial'
                    )
                ),
                tickfont=dict(
                    size=11,
                    color='#1F2D3D'
                ),
                thickness=14,
                len=0.72,
                outlinewidth=0
            ),
            line=dict(
                color='white',
                width=2.5
            ),
            opacity=0.88
        ),
        customdata=channel_perf[[
            'customer_count',
            'responded_count',
            'after_churn_rate_pct',
            'saved_count',
            'avg_clv',
            'responded_share_text'
        ]],
        hovertemplate=(
            '<b>营销渠道：%{text}</b><br><br>'
            '响应率：%{x:.1f}%<br>'
            '活动后流失率：%{y:.1f}%<br>'
            '触达客户数：%{customdata[0]:,.0f}<br>'
            '响应客户数：%{customdata[1]:,.0f}<br>'
            '响应客户 / 触达客户：%{customdata[5]}<br>'
            '被挽回客户数：%{customdata[3]:,.0f}<br>'
            '平均客户生命周期价值：$%{customdata[4]:,.2f}'
            '<extra></extra>'
        )
    )
)

# 响应率中位数参考线
fig.add_vline(
    x=median_response,
    line_width=1.5,
    line_dash="dash",
    line_color="rgba(44, 62, 80, 0.45)",
    annotation_text=f"响应率中位数：{median_response:.1f}%",
    annotation_position="top left",
    annotation_font=dict(
        size=11,
        color='#566573',
        family='Microsoft YaHei, SimHei, Arial'
    )
)

# 活动后流失率中位数参考线
fig.add_hline(
    y=median_churn,
    line_width=1.5,
    line_dash="dash",
    line_color="rgba(44, 62, 80, 0.45)",
    annotation_text=f"活动后流失率中位数：{median_churn:.1f}%",
    annotation_position="bottom right",
    annotation_font=dict(
        size=11,
        color='#566573',
        family='Microsoft YaHei, SimHei, Arial'
    )
)

# 右上区域标注：高响应、低流失
fig.add_annotation(
    xref='paper',
    yref='paper',
    x=0.98,
    y=0.96,
    xanchor='right',
    yanchor='top',

    text="<b>重点投入区域</b><br><sup>高响应率 / 低流失率</sup>",
    showarrow=False,
    font=dict(
        size=13,
        color='#006D77',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    bgcolor='rgba(255,255,255,0.76)',
    bordercolor='rgba(0,109,119,0.25)',
    borderwidth=1,
    borderpad=6
)

# 左上区域标注：低响应、低流失
fig.add_annotation(
    xref='paper',
    yref='paper',
    x=0.02,
    y=0.96,
    xanchor='left',
    yanchor='top',

    text="<b>潜力提升区域</b><br><sup>低响应率 / 低流失率</sup>",
    showarrow=False,
    font=dict(
        size=13,
        color='#2874A6',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    bgcolor='rgba(255,255,255,0.68)',
    bordercolor='rgba(40,116,166,0.20)',
    borderwidth=1,
    borderpad=6
)

# 右下区域标注：高响应、高流失
fig.add_annotation(
    xref='paper',
    yref='paper',
    x=0.98,
    y=0.04,
    xanchor='right',
    yanchor='bottom',

    text="<b>质量改善区域</b><br><sup>高响应率 / 高流失率</sup>",
    showarrow=False,
    font=dict(
        size=13,
        color='#7D6608',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    bgcolor='rgba(255,255,255,0.68)',
    bordercolor='rgba(125,102,8,0.20)',
    borderwidth=1,
    borderpad=6
)

# 左下区域标注：低响应、高流失
fig.add_annotation(
    xref='paper',
    yref='paper',
    x=0.02,
    y=0.04,
    xanchor='left',
    yanchor='bottom',

    text="<b>优化调整区域</b><br><sup>低响应率 / 高流失率</sup>",
    showarrow=False,
    font=dict(
        size=13,
        color='#8A5A12',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    bgcolor='rgba(255,255,255,0.76)',
    bordercolor='rgba(183,121,31,0.25)',
    borderwidth=1,
    borderpad=6
)

fig.update_layout(
    **common_layout,
    height=600,
    title=dict(
        text="<b>不同营销渠道的响应率与活动后流失率四象限分析</b>",
        x=0.5,
        xanchor="center",
        y=0.96,
        yanchor="top",
        font=dict(
            size=22,
            color="#1F2D3D",
            family="Microsoft YaHei, SimHei, Arial"
        )
    ),
    margin=dict(t=110, b=90, l=90, r=120),
    paper_bgcolor='white',
    plot_bgcolor='rgba(248,250,252,0.96)',
    hoverlabel=dict(
        bgcolor='white',
        bordercolor='#D5DBDB',
        font=dict(
            size=13,
            color='#1F2D3D',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),
    showlegend=False
)

fig.update_xaxes(
    title_text='<b>响应率（%）</b>',

    range=[x_min_range, x_max_range],
    showgrid=True,
    gridcolor='rgba(44,62,80,0.12)',
    zeroline=False,
    tickfont=dict(
        size=12,
        color='#1F2D3D'
    ),
    title_font=dict(
        size=15,
        color='black',
        family='Microsoft YaHei, SimHei, Arial'
    )

)

# 注意：这里将 Y 轴反向，使“活动后流失率越低”的渠道显示在上方
fig.update_yaxes(
    title_text='<b>活动后流失率（%）</b>',
    range=[y_max_range, y_min_range],
    showgrid=True,
    gridcolor='rgba(44,62,80,0.12)',
    zeroline=False,
    tickfont=dict(
        size=12,
        color='#1F2D3D'
    ),
    title_font=dict(
        size=15,
        color='black',
        family='Microsoft YaHei, SimHei, Arial'
    )

)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 该四象限图以响应率和活动后流失率作为两个核心评价指标，"
    "用于比较不同营销渠道的综合活动效果。横轴表示响应率，数值越高说明渠道触达后的客户反馈越积极；"
    "纵轴表示活动后流失率，本图将纵轴反向处理，因此位置越靠上表示活动后流失率越低。"
    "气泡大小表示触达客户规模，颜色深浅表示被挽回客户数量。"
    "右上方的“重点投入区域”代表响应率较高且活动后流失率较低的渠道，可作为后续资源投入的优先对象。"
)









# ======================================================
# 高级版：营销渠道响应率与活动后流失率四象限气泡图
# ======================================================

import plotly.graph_objects as go
import pandas as pd

# ======================================================
# 坐标轴范围设置：根据数据自动留白，不强制从 0 开始
# ======================================================
def calc_pct_range(series, pad_ratio=0.20, min_pad=3):
    s = series.dropna()

    if s.empty:
        return 0, 100

    vmin = s.min()
    vmax = s.max()
    span = vmax - vmin

    if span == 0:
        pad = max(vmax * 0.12, min_pad)
    else:
        pad = max(span * pad_ratio, min_pad)

    range_min = max(0, vmin - pad)
    range_max = min(100, vmax + pad)

    if range_max - range_min < 8:
        mid = (range_min + range_max) / 2
        range_min = max(0, mid - 4)
        range_max = min(100, mid + 4)

    return range_min, range_max


x_min_range, x_max_range = calc_pct_range(channel_perf['response_rate_pct'])
y_min_range, y_max_range = calc_pct_range(channel_perf['after_churn_rate_pct'])

median_response = channel_perf['response_rate_pct'].median()
median_churn = channel_perf['after_churn_rate_pct'].median()

max_customer_count = channel_perf['customer_count'].max()

if pd.isna(max_customer_count) or max_customer_count <= 0:
    max_customer_count = 1

sizeref = 2.0 * max_customer_count / (58 ** 2)


# ======================================================
# 新增：象限分类，用于气泡描边和辅助解释
# 注意：Y 轴反向后，低流失率显示在上方
# ======================================================
def get_quadrant(row):
    response = row['response_rate_pct']
    churn = row['after_churn_rate_pct']

    if response >= median_response and churn <= median_churn:
        return "重点投入"
    elif response < median_response and churn <= median_churn:
        return "潜力提升"
    elif response >= median_response and churn > median_churn:
        return "质量改善"
    else:
        return "优化调整"


channel_perf = channel_perf.copy()
channel_perf['quadrant'] = channel_perf.apply(get_quadrant, axis=1)


# ======================================================
# 高级版四象限气泡图
# ======================================================
fig = go.Figure()

# ======================================================
# 四象限背景色块
# ======================================================
quadrant_shapes = [
    # 右上：高响应 / 低流失
    dict(
        type="rect",
        x0=median_response,
        x1=x_max_range,
        y0=y_min_range,
        y1=median_churn,
        fillcolor="rgba(0, 196, 154, 0.16)",
        line=dict(width=0),
        layer="below"
    ),
    # 左上：低响应 / 低流失
    dict(
        type="rect",
        x0=x_min_range,
        x1=median_response,
        y0=y_min_range,
        y1=median_churn,
        fillcolor="rgba(65, 105, 225, 0.13)",
        line=dict(width=0),
        layer="below"
    ),
    # 右下：高响应 / 高流失
    dict(
        type="rect",
        x0=median_response,
        x1=x_max_range,
        y0=median_churn,
        y1=y_max_range,
        fillcolor="rgba(255, 176, 0, 0.15)",
        line=dict(width=0),
        layer="below"
    ),
    # 左下：低响应 / 高流失
    dict(
        type="rect",
        x0=x_min_range,
        x1=median_response,
        y0=median_churn,
        y1=y_max_range,
        fillcolor="rgba(255, 77, 109, 0.16)",
        line=dict(width=0),
        layer="below"
    )
]

for shape in quadrant_shapes:
    fig.add_shape(**shape)


# ======================================================
# 主气泡图
# ======================================================
fig.add_trace(
    go.Scatter(
        x=channel_perf['response_rate_pct'],
        y=channel_perf['after_churn_rate_pct'],
        mode='markers+text',
        text=channel_perf['channel_label'],
        textposition='top center',
        textfont=dict(
            size=14,
            color='#F8FAFC',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        marker=dict(
            size=channel_perf['customer_count'],
            sizemode='area',
            sizeref=sizeref,
            sizemin=22,
            color=channel_perf['saved_count'],
            colorscale=[
                [0.00, '#4CC9F0'],
                [0.25, '#4895EF'],
                [0.50, '#7209B7'],
                [0.75, '#F72585'],
                [1.00, '#FFB703']
            ],
            reversescale=False,
            showscale=True,
            colorbar=dict(
                title=dict(
                    text='<b>被挽回<br>客户数</b>',
                    font=dict(
                        size=13,
                        color='#F8FAFC',
                        family='Microsoft YaHei, SimHei, Arial'
                    )
                ),
                tickfont=dict(
                    size=12,
                    color='#F8FAFC'
                ),
                thickness=16,
                len=0.74,
                outlinewidth=0,
                bgcolor='rgba(15, 23, 42, 0.70)'
            ),
            line=dict(
                color='rgba(255,255,255,0.95)',
                width=2.6
            ),
            opacity=0.92
        ),
        customdata=channel_perf[[
            'customer_count',
            'responded_count',
            'after_churn_rate_pct',
            'saved_count',
            'avg_clv',
            'responded_share_text',
            'quadrant'
        ]],
        hovertemplate=(
            '<b>营销渠道：%{text}</b><br><br>'
            '所属象限：%{customdata[6]}<br>'
            '响应率：%{x:.1f}%<br>'
            '活动后流失率：%{y:.1f}%<br>'
            '触达客户数：%{customdata[0]:,.0f}<br>'
            '响应客户数：%{customdata[1]:,.0f}<br>'
            '响应客户 / 触达客户：%{customdata[5]}<br>'
            '被挽回客户数：%{customdata[3]:,.0f}<br>'
            '平均客户生命周期价值：$%{customdata[4]:,.2f}'
            '<extra></extra>'
        )
    )
)


# ======================================================
# 中位数分割线
# ======================================================
fig.add_vline(
    x=median_response,
    line_width=2,
    line_dash="dash",
    line_color="rgba(248, 250, 252, 0.65)"
)

fig.add_hline(
    y=median_churn,
    line_width=2,
    line_dash="dash",
    line_color="rgba(248, 250, 252, 0.65)"
)


# ======================================================
# 中位数文字标注
# ======================================================
fig.add_annotation(
    x=median_response,
    y=y_min_range,
    text=f"响应率中位数 {median_response:.1f}%",
    showarrow=False,
    yshift=-34,
    font=dict(size=12, color='#CBD5E1', family='Microsoft YaHei, SimHei, Arial'),
    bgcolor='rgba(15, 23, 42, 0.78)',
    bordercolor='rgba(255,255,255,0.18)',
    borderwidth=1,
    borderpad=5
)

fig.add_annotation(
    x=x_max_range,
    y=median_churn,
    text=f"活动后流失率中位数 {median_churn:.1f}%",
    showarrow=False,
    xshift=-78,
    yshift=18,
    font=dict(size=12, color='#CBD5E1', family='Microsoft YaHei, SimHei, Arial'),
    bgcolor='rgba(15, 23, 42, 0.78)',
    bordercolor='rgba(255,255,255,0.18)',
    borderwidth=1,
    borderpad=5
)


# ======================================================
# 四象限标签
# ======================================================
quadrant_annotations = [
    dict(
        x=0.97, y=0.95,
        title="重点投入区域",
        sub="高响应率 / 低流失率",
        color="#00E0B8"
    ),
    dict(
        x=0.03, y=0.95,
        title="潜力提升区域",
        sub="低响应率 / 低流失率",
        color="#60A5FA"
    ),
    dict(
        x=0.97, y=0.05,
        title="质量改善区域",
        sub="高响应率 / 高流失率",
        color="#FBBF24"
    ),
    dict(
        x=0.03, y=0.05,
        title="优化调整区域",
        sub="低响应率 / 高流失率",
        color="#FB7185"
    )
]

for ann in quadrant_annotations:
    fig.add_annotation(
        xref='paper',
        yref='paper',
        x=ann['x'],
        y=ann['y'],
        xanchor='right' if ann['x'] > 0.5 else 'left',
        yanchor='top' if ann['y'] > 0.5 else 'bottom',
        text=f"<b>{ann['title']}</b><br><sup>{ann['sub']}</sup>",
        showarrow=False,
        font=dict(
            size=14,
            color=ann['color'],
            family='Microsoft YaHei, SimHei, Arial'
        ),
        bgcolor='rgba(15, 23, 42, 0.72)',
        bordercolor=ann['color'],
        borderwidth=1.2,
        borderpad=8
    )


# ======================================================
# 版式设置
# ======================================================
fig.update_layout(
    height=650,
    title=dict(
        text="<b>不同营销渠道响应率与活动后流失率四象限气泡图</b><br>",
             # "<sup>气泡大小表示触达客户规模，颜色表示被挽回客户数量</sup>",
        x=0.5,
        xanchor="center",
        y=0.88,
        yanchor="top",
        font=dict(
            size=24,
            color="#F8FAFC",
            family="Microsoft YaHei, SimHei, Arial"
        )
    ),
    margin=dict(t=125, b=95, l=95, r=135),
    paper_bgcolor='#020617',
    plot_bgcolor='#0F172A',
    showlegend=False,
    hoverlabel=dict(
        bgcolor='rgba(15, 23, 42, 0.96)',
        bordercolor='rgba(255,255,255,0.25)',
        font=dict(
            size=13,
            color='#F8FAFC',
            family='Microsoft YaHei, SimHei, Arial'
        )
    )
)


# ======================================================
# 坐标轴设置
# ======================================================
fig.update_xaxes(
    title_text='<b>响应率（%）</b>',
    range=[x_min_range, x_max_range],
    showgrid=True,
    gridcolor='rgba(148, 163, 184, 0.22)',
    zeroline=False,
    linecolor='rgba(248, 250, 252, 0.55)',
    tickfont=dict(
        size=12,
        color='#CBD5E1',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    title_font=dict(
        size=15,
        color='#F8FAFC',
        family='Microsoft YaHei, SimHei, Arial'
    )
)

# 注意：Y 轴反向，使“活动后流失率越低”的渠道显示在上方
fig.update_yaxes(
    title_text='<b>活动后流失率（%）</b>',
    range=[y_max_range, y_min_range],
    showgrid=True,
    gridcolor='rgba(148, 163, 184, 0.22)',
    zeroline=False,
    linecolor='rgba(248, 250, 252, 0.55)',
    tickfont=dict(
        size=12,
        color='#CBD5E1',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    title_font=dict(
        size=15,
        color='#F8FAFC',
        family='Microsoft YaHei, SimHei, Arial'
    )
)


# ======================================================
# Streamlit 展示
# ======================================================
st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 该四象限气泡图以响应率和活动后流失率作为核心指标，"
    "横轴表示响应率，越靠右说明渠道响应效果越好；"
    "纵轴表示活动后流失率，本图将纵轴反向处理，因此越靠上说明流失率越低。"
    "气泡大小表示触达客户规模，颜色表示被挽回客户数量。"
    "右上方为“重点投入区域”，代表响应率高且活动后流失率低的优质渠道。"
)
















# ======================================================
# Offer 响应率与流失率
# ======================================================
strong_divider()

# fig = apply_chart_style(fig, "不同优惠方案的响应率与活动后流失率对比")

offer_df = df[df['contacted_int'] == 1].copy()

offer_perf = offer_df.groupby('offer_label').agg(
    customer_count=('customer_id', 'count'),
    responded_count=('responded_int', 'sum'),
    response_rate=('responded_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    saved_count=('saved_by_campaign', 'sum'),
    avg_retention_cost=('retention_cost', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index()

offer_perf['response_rate_pct'] = offer_perf['response_rate'] * 100
offer_perf['after_churn_rate_pct'] = offer_perf['after_churn_rate'] * 100

plot_offer = offer_perf.melt(
    id_vars=['offer_label', 'customer_count', 'responded_count', 'saved_count'],
    value_vars=['response_rate_pct', 'after_churn_rate_pct'],
    var_name='metric',
    value_name='rate'
)

plot_offer['metric_label'] = plot_offer['metric'].map({
    'response_rate_pct': '响应率',
    'after_churn_rate_pct': '活动后流失率'
})

# ===================== 比赛级高级配色 =====================
fig = px.bar(
    plot_offer,
    x='offer_label',
    y='rate',
    color='metric_label',
    barmode='group',
    text=plot_offer['rate'].apply(lambda x: f"{x:.1f}%"),
    # 🔥 高级商务双配色：深邃蓝 + 酒红（比赛专用）
    color_discrete_map={
        '响应率': '#165DFF',       # 高级科技蓝
        '活动后流失率': '#F53F3F'  # 高级质感红
    },
    labels={
        'offer_label': '优惠方案类型',
        'rate': '比例 (%)',
        'metric_label': '指标'
    }
)

# ===================== 文字样式优化 =====================
fig.update_traces(
    textposition='outside',
    textfont=dict(color='#111111', size=11, weight='bold')  # 纯黑加粗更清晰
)

# ===================== 布局美化 =====================
fig.update_layout(
    **common_layout,
    height=520,
    title='不同优惠方案的响应率与活动后流失率对比',
    title_x=0.25,  # 标题居中
    # title_font=dict(size=16, color='#111111', weight='bold'),

    # X 轴全黑、干净
    xaxis=dict(
        title='优惠方案类型',
        title_font=dict(color='#111111', size=12),
        tickfont=dict(color='#111111', size=11),
        tickangle=-20,
        showgrid=False
    ),

    # Y 轴全黑、淡网格
    yaxis=dict(
        title='比例 (%)',
        title_font=dict(color='#111111', size=12),
        tickfont=dict(color='#111111', size=11),
        showgrid=True,
        gridcolor='#F0F2F5',
        zeroline=False
    ),

    # 图例高级样式
    legend=dict(
        title=' ',
        title_font=dict(color='#111111'),
        font=dict(color='#111111'),
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1
    ),

    margin=dict(t=80, b=100, l=40, r=40),
    # plot_bgcolor='white',  # 纯白背景
    # paper_bgcolor='white'
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 最理想的 Offer 是：响应率高、活动后流失率低、挽留成本可控。")






# ======================================================
# Offer 响应率与流失率：高级玫瑰图
# ======================================================

offer_df = df[df['contacted_int'] == 1].copy()

offer_perf = offer_df.groupby('offer_label').agg(
    customer_count=('customer_id', 'count'),
    responded_count=('responded_int', 'sum'),
    response_rate=('responded_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    saved_count=('saved_by_campaign', 'sum'),
    avg_retention_cost=('retention_cost', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index()

offer_perf['response_rate_pct'] = offer_perf['response_rate'] * 100
offer_perf['after_churn_rate_pct'] = offer_perf['after_churn_rate'] * 100

# 按响应率排序，让图形更有层次
offer_perf = offer_perf.sort_values('response_rate_pct', ascending=False).reset_index(drop=True)

n = len(offer_perf)

if n == 0:
    st.warning("当前没有可用于绘制优惠方案玫瑰图的数据。")
else:
    # ======================================================
    # 角度与半径设置
    # ======================================================
    angle_step = 360 / n
    theta_center = np.arange(n) * angle_step

    # 两个指标在同一个 Offer 方向上左右错开
    theta_response = theta_center - angle_step * 0.18
    theta_churn = theta_center + angle_step * 0.18

    bar_width = angle_step * 0.30

    # 指标最大值
    max_r = max(
        offer_perf['response_rate_pct'].max(),
        offer_perf['after_churn_rate_pct'].max()
    )

    # 中心圆半径，不要太小，否则文字挤
    center_radius = max_r * 0.26

    # 让扇形稍微压进中心圆一点点，这样视觉上无缝衔接
    bar_base = center_radius * 0.94

    # 整个极坐标最大半径 = 中心圆 + 指标长度 + 留白
    radial_max = center_radius + max_r + 8

    # 用于画圆
    theta_ring = np.linspace(0, 360, 361)

    # 自定义径向刻度，让 0% 从中心圆边缘开始算
    tick_raw = np.arange(0, np.ceil((max_r + 5) / 10) * 10 + 1, 10)
    tick_vals = center_radius + tick_raw
    tick_text = [f'{int(x)}%' for x in tick_raw]

    fig = go.Figure()

    # ======================================================
    # 背景辅助圆环：先画，放在底层
    # ======================================================
    # 外部亮色圆环，从中心圆外侧开始
    ring_raw_values = np.arange(10, np.ceil((max_r + 5) / 10) * 10 + 1, 10)

    for ring_raw in ring_raw_values:
        ring_r = center_radius + ring_raw

        fig.add_trace(
            go.Scatterpolar(
                r=[ring_r] * len(theta_ring),
                theta=theta_ring,
                mode='lines',
                line=dict(
                    color='rgba(125, 211, 252, 0.24)',
                    width=1.1
                ),
                hoverinfo='skip',
                showlegend=False
            )
        )

    # 最外层高亮粗圆框
    fig.add_trace(
        go.Scatterpolar(
            r=[radial_max] * len(theta_ring),
            theta=theta_ring,
            mode='lines',
            line=dict(
                color='rgba(56, 189, 248, 1)',
                width=4.2
            ),
            hoverinfo='skip',
            showlegend=False
        )
    )

    # ======================================================
    # 响应率花瓣：亮蓝色
    # ======================================================
    fig.add_trace(
        go.Barpolar(
            r=offer_perf['response_rate_pct'],
            base=[bar_base] * n,
            theta=theta_response,
            width=[bar_width] * n,
            name='响应率',

            marker=dict(
                color='rgba(37, 99, 235, 0.88)',
                line=dict(
                    color='rgba(147, 197, 253, 1)',
                    width=1.8
                )
            ),
            opacity=0.94,
            customdata=offer_perf[[
                'offer_label',
                'customer_count',
                'responded_count',
                'saved_count',
                'after_churn_rate_pct',
                'avg_retention_cost',
                'avg_net_gain'
            ]],
            hovertemplate=(
                '<b>优惠方案：%{customdata[0]}</b><br><br>'
                '指标：响应率<br>'
                '响应率：%{r:.1f}%<br>'
                '活动后流失率：%{customdata[4]:.1f}%<br>'
                '触达客户数：%{customdata[1]:,.0f}<br>'
                '响应客户数：%{customdata[2]:,.0f}<br>'
                '被挽回客户数：%{customdata[3]:,.0f}<br>'
                '平均挽留成本：$%{customdata[5]:,.2f}<br>'
                '平均净收益：$%{customdata[6]:,.2f}'
                '<extra></extra>'
            )
        )
    )

    # ======================================================
    # 活动后流失率花瓣：亮玫红色
    # ======================================================
    fig.add_trace(
        go.Barpolar(
            r=offer_perf['after_churn_rate_pct'],
            base=[bar_base] * n,
            theta=theta_churn,
            width=[bar_width] * n,
            name='活动后流失率',

            marker=dict(
                color='rgba(244, 63, 94, 0.84)',
                line=dict(
                    color='rgba(254, 202, 202, 1)',
                    width=1.8
                )
            ),
            opacity=0.92,
            customdata=offer_perf[[
                'offer_label',
                'customer_count',
                'responded_count',
                'saved_count',
                'response_rate_pct',
                'avg_retention_cost',
                'avg_net_gain'
            ]],
            hovertemplate=(
                '<b>优惠方案：%{customdata[0]}</b><br><br>'
                '指标：活动后流失率<br>'
                '活动后流失率：%{r:.1f}%<br>'
                '响应率：%{customdata[4]:.1f}%<br>'
                '触达客户数：%{customdata[1]:,.0f}<br>'
                '响应客户数：%{customdata[2]:,.0f}<br>'
                '被挽回客户数：%{customdata[3]:,.0f}<br>'
                '平均挽留成本：$%{customdata[5]:,.2f}<br>'
                '平均净收益：$%{customdata[6]:,.2f}'
                '<extra></extra>'
            )
        )
    )

    # ======================================================
    # 数值标签：响应率
    # ======================================================
    fig.add_trace(
        go.Scatterpolar(
            r=center_radius + offer_perf['response_rate_pct'] + 3,

            theta=theta_response,
            mode='text',
            text=offer_perf['response_rate_pct'].apply(lambda x: f"{x:.1f}%"),
            textfont=dict(
                size=12,
                color='#BAE6FD',
                family='Microsoft YaHei, SimHei, Arial'
            ),
            showlegend=False,
            hoverinfo='skip'
        )
    )

    # ======================================================
    # 数值标签：活动后流失率
    # ======================================================
    fig.add_trace(
        go.Scatterpolar(
            r=center_radius + offer_perf['after_churn_rate_pct'] + 3,
            theta=theta_churn,

            mode='text',
            text=offer_perf['after_churn_rate_pct'].apply(lambda x: f"{x:.1f}%"),
            textfont=dict(
                size=12,
                color='#FFE4E6',
                family='Microsoft YaHei, SimHei, Arial'
            ),
            showlegend=False,
            hoverinfo='skip'
        )
    )

    # ======================================================
    # 中心圆：覆盖花瓣中心，形成圆形徽章
    # ======================================================
    fig.add_trace(
        go.Scatterpolar(
            r=[center_radius] * len(theta_ring),
            theta=theta_ring,
            mode='lines',
            fill='toself',
            fillcolor='rgba(15, 23, 42, 0.96)',
            line=dict(
                color='rgba(125, 211, 252, 0.95)',
                width=2.6
            ),
            hoverinfo='skip',
            showlegend=False
        )
    )

    # 中心圆内再加一个亮色细圆环
    fig.add_trace(
        go.Scatterpolar(
            r=[center_radius * 0.82] * len(theta_ring),
            theta=theta_ring,
            mode='lines',
            line=dict(
                color='rgba(244, 114, 182, 0.85)',
                width=1.5
            ),
            hoverinfo='skip',
            showlegend=False
        )
    )

    # ======================================================
    # 布局高级美化
    # ======================================================
    fig.update_layout(
        height=760,
        title=dict(
            text=(
                "<b>不同优惠方案响应率与活动后流失率玫瑰图</b>"
                # "<br><sup>蓝色花瓣表示响应率，玫红花瓣表示活动后流失率</sup>"
            ),
            x=0.5,
            xanchor='center',
            y=0.96,
            yanchor='top',
            font=dict(
                size=24,
                color='#F8FAFC',
                family='Microsoft YaHei, SimHei, Arial'
            )
        ),

        polar=dict(
            bgcolor='rgba(15, 23, 42, 0.98)',

            radialaxis=dict(
                range=[0, radial_max],
                showline=False,
                showgrid=False,
                tickmode='array',
                tickvals=tick_vals,
                ticktext=tick_text,
                tickfont=dict(
                    size=11,
                    color='#CBD5E1',
                    family='Microsoft YaHei, SimHei, Arial'
                ),
                angle=90
            ),

            angularaxis=dict(
                tickmode='array',
                tickvals=theta_center,
                ticktext=offer_perf['offer_label'],
                rotation=90,
                direction='clockwise',
                showline=False,
                showgrid=True,
                gridcolor='rgba(125, 211, 252, 0.16)',
                gridwidth=1,
                tickfont=dict(
                    size=13,
                    color='#F8FAFC',
                    family='Microsoft YaHei, SimHei, Arial'
                )
            )
        ),

        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.05,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(15, 23, 42, 0.82)',
            bordercolor='rgba(125, 211, 252, 0.45)',
            borderwidth=1.2,
            font=dict(
                size=14,
                color='#F8FAFC',
                family='Microsoft YaHei, SimHei, Arial'
            )
        ),

        paper_bgcolor='#020617',
        plot_bgcolor='#020617',

        margin=dict(t=125, b=70, l=65, r=65),

        hoverlabel=dict(
            bgcolor='rgba(15, 23, 42, 0.96)',
            bordercolor='rgba(125, 211, 252, 0.45)',
            font=dict(
                size=13,
                color='#F8FAFC',
                family='Microsoft YaHei, SimHei, Arial'
            )
        )
    )

    # ======================================================
    # 中心圆文字
    # ======================================================
    fig.add_annotation(
        text=(
            "<span style='font-size:12px'><b>Offer 效果对比</b></span><br>"
            "<span style='font-size:9px'>高响应 / 低流失更优</span>"
        ),
        x=0.5,
        y=0.5,
        xref='paper',
        yref='paper',
        showarrow=False,
        font=dict(
            size=14,
            color='#F8FAFC',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        align='center'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "💡 该玫瑰图用于比较不同优惠方案的综合营销效果。"
        "蓝色花瓣表示响应率，花瓣越长说明客户越愿意响应；"
        "玫红色花瓣表示活动后流失率，花瓣越长说明流失风险越高。"
        "因此，理想的优惠方案应表现为蓝色花瓣较长、玫红色花瓣较短，"
        "即响应率高、活动后流失率低，同时还需要结合挽留成本和净收益综合判断。"
    )








# ======================================================
# Uplift 标签分布
# ======================================================
# ======================================================
# Uplift 标签分布
# ======================================================
strong_divider()

st.subheader("🏷️ Uplift 客户类型分布")

st.markdown(
    """
    该条形图展示了不同 **Uplift 客户类型** 的客户数量分布情况。
    横轴表示实验组客户中的 Uplift 客户类型，纵轴表示对应客户数量；
    柱子越高，说明该类型客户越多。柱子上方同时展示客户数量和占比，
    便于快速判断当前客户群体中哪些类型占比较高。
    """
)

# 固定展示
# 当前数据集实际存在的 5 个 Uplift 类型
uplift_order = [
    '自然留存型',
    '可被说服型',
    '不应打扰型',
    '挽回无望型',
    '不确定型'
]

uplift_color_map = {
    '自然留存型': '#2ECC71',
    '可被说服型': '#3498DB',
    '不应打扰型': '#E74C3C',
    '挽回无望型': '#8E44AD',
    '不确定型': '#95A5A6'
}


# 只统计实验组，不统计 control 对照组
uplift_df = df[df['treatment_group'] == 'treatment'].copy()

uplift_count = (
    uplift_df.groupby('uplift_label_cn')
    .agg(customer_count=('customer_id', 'count'))
    .reset_index()
)


uplift_count['uplift_label_cn'] = pd.Categorical(
    uplift_count['uplift_label_cn'],
    categories=uplift_order,
    ordered=True
)

uplift_count = uplift_count.sort_values('uplift_label_cn')


# 计算占比
total_uplift_customers = uplift_count['customer_count'].sum()

if total_uplift_customers > 0:
    uplift_count['customer_pct'] = uplift_count['customer_count'] / total_uplift_customers * 100
else:
    uplift_count['customer_pct'] = 0

# 设置显示标签：数量 + 占比
uplift_count['label_text'] = uplift_count.apply(
    lambda row: f"{row['customer_count']}人<br>{row['customer_pct']:.1f}%",
    axis=1
)

fig = go.Figure(
    data=[
        go.Pie(
            labels=uplift_count['uplift_label_cn'],
            values=uplift_count['customer_count'],
            hole=0.54,
            sort=False,
            direction='clockwise',
            marker=dict(
                colors=[uplift_color_map[label] for label in uplift_count['uplift_label_cn']],
                line=dict(color='white', width=3)
            ),
            pull=[0.035, 0.055, 0.035, 0.035, 0.025],
            text=uplift_count['label_text'],
            textinfo='label+text',
            textposition='outside',
            textfont=dict(
                size=14,
                color='#1F2D3D',
                family='Microsoft YaHei, SimHei, Arial'
            ),
            customdata=uplift_count[['customer_pct']],
            hovertemplate=(
                '<b>%{label}</b><br>'
                '客户数量: %{value:,} 人<br>'
                '占比: %{customdata[0]:.1f}%'
                '<extra></extra>'
            )
        )
    ]
)

fig.update_layout(
    **common_layout,
    height=560,
    title=dict(
        text="<b>实验组客户增益类型分布扇形图</b><br><sup> </sup>",
        x=0.5,
        xanchor="center",
        y=0.96,
        yanchor="top",
        font=dict(
            size=22,
            color="#1F2D3D",
            family="Microsoft YaHei, SimHei, Arial"
        )
    ),
    annotations=[
        dict(
            text=(
                f"<b>{total_uplift_customers:,}</b><br>"
                "<span style='font-size:13px'>实验组客户</span>"
            ),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(
                size=22,
                color="#1F2D3D",
                family="Microsoft YaHei, SimHei, Arial"
            )
        )
    ],
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=-0.12,
        xanchor='center',
        x=0.5,
        font=dict(
            size=13,
            color='#1F2D3D'
        )
    ),
    margin=dict(t=120, b=100, l=70, r=70)
    # paper_bgcolor='white',
    # plot_bgcolor='white'
)

fig.update_traces(
    hoverlabel=dict(
        bgcolor='white',
        font_size=13,
        font_family='Microsoft YaHei, SimHei, Arial',
        font_color='#1F2D3D',
        bordercolor='#D5DBDB'
    )
)



st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    该扇形图展示了实验组中不同 **Uplift 客户类型** 的数量占比结构。
    每个扇区代表一种客户类型，扇区越大，说明该类型客户占比越高；
    图中同时展示客户数量和占比，便于快速识别重点营销人群与应谨慎触达的人群。
    """
)



# ======================================================
# Uplift 标签下的活动效果
# ======================================================
strong_divider()

st.subheader("📉 不同 Uplift 标签的活动后流失率")

uplift_perf = df.groupby('uplift_label_cn').agg(
    customer_count=('customer_id', 'count'),
    contacted_rate=('contacted_int', 'mean'),
    response_rate=('responded_int', 'mean'),
    original_churn_rate=('original_churn_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    saved_count=('saved_by_campaign', 'sum'),
    avg_clv=('estimated_clv', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index()

uplift_perf['contacted_rate_pct'] = uplift_perf['contacted_rate'] * 100
uplift_perf['response_rate_pct'] = uplift_perf['response_rate'] * 100
uplift_perf['original_churn_rate_pct'] = uplift_perf['original_churn_rate'] * 100
uplift_perf['after_churn_rate_pct'] = uplift_perf['after_churn_rate'] * 100

uplift_perf = uplift_perf.sort_values('after_churn_rate_pct', ascending=True)

fig = px.bar(
    uplift_perf,
    x='after_churn_rate_pct',
    y='uplift_label_cn',
    orientation='h',
    color='after_churn_rate_pct',
    color_continuous_scale=['#27AE60', '#F1C40F', '#E74C3C'],
    text=uplift_perf['after_churn_rate_pct'].apply(lambda x: f"{x:.1f}%"),
    hover_data={
        'customer_count': True,
        'contacted_rate_pct': ':.1f',
        'response_rate_pct': ':.1f',
        'saved_count': True,
        'avg_clv': ':.2f',
        'avg_net_gain': ':.2f'
    },
    labels={
        'after_churn_rate_pct': '活动后流失率 (%)',
        'uplift_label_cn': '客户增益类型',
        'customer_count': '客户数量',
        'contacted_rate_pct': '触达率',
        'response_rate_pct': '响应率',
        'saved_count': '被挽回客户数',
        'avg_clv': '平均 CLV',
        'avg_net_gain': '平均净收益'
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=12),
    hovertemplate=(
        '客户增益类型: %{y}<br>'
        '活动后流失率: %{x:.1f}%<br>'
        '客户数量: %{customdata[0]}<br>'
        '触达率: %{customdata[1]:.1f}%<br>'
        '响应率: %{customdata[2]:.1f}%<br>'
        '被挽回客户数: %{customdata[3]}<br>'
        '平均客户生命周期价值: $%{customdata[4]:,.2f}<br>'
        '平均净收益: $%{customdata[5]:,.2f}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=280,
    xaxis_title='活动后流失率 (%)',
    yaxis_title='客户增益类型',
    coloraxis_showscale=False,
    xaxis=dict(range=[0, 110]),
    margin=dict(t=60, b=35, l=55, r=35)
)


fig = apply_chart_style(fig, "不同客户增益类型的活动后流失率")
fig.update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    shapes=[
        dict(
            type="rect",
            xref="paper",
            yref="paper",
            x0=0,
            y0=0,
            x1=1,
            y1=1,
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)",
            layer="above"
        )
    ]
)


# st.plotly_chart(fig, use_container_width=True)
col1, col2, col3 = st.columns([2, 5, 2])

with col2:
    st.plotly_chart(fig, use_container_width=True)


st.info("💡 不同 Uplift 标签的活动后流失率可以帮助判断模型分群是否有运营意义。")



# ======================================================
# 营销 Uplift 增益群体的 CLV 价值分布密度图 (小提琴图)
# ======================================================
strong_divider()

st.subheader("🎻 营销 Uplift 增益群体的 CLV 价值分布密度图")

st.markdown(
    """
    该**分组小提琴图**展示了不同 Uplift 客户群体在实验组与对照组中的 **预期生命周期价值 (CLV)** 分布形态。
    小提琴的“胖瘦”代表该价值区间内客户的密集程度，内部带有箱线图用于展示四分位数与离散极值，并且绘制了每一个用户的真实数据落点。
    """
)

# 过滤掉缺失 CLV 的数据
violin_df = df.dropna(subset=['estimated_clv', 'uplift_label_cn', 'group_label']).copy()

# 确保 X 轴顺序逻辑清晰（按照业务逻辑排序）
uplift_order = ['自然留存型', '可被说服型', '不应打扰型', '不确定型', '挽回无望型']
violin_df['uplift_label_cn'] = pd.Categorical(violin_df['uplift_label_cn'], categories=uplift_order, ordered=True)
violin_df = violin_df.sort_values('uplift_label_cn')

fig = go.Figure()

# 添加对照组 (不再强制裁切成左半边，使用对称完整全型)
fig.add_trace(go.Violin(
    x=violin_df.loc[violin_df['group_label'] == '对照组', 'uplift_label_cn'],
    y=violin_df.loc[violin_df['group_label'] == '对照组', 'estimated_clv'],
    legendgroup='对照组', scalegroup='对照组', name='对照组',
    line_color='#95A5A6',
    fillcolor='rgba(149, 165, 166, 0.35)',
    box_visible=True,        # 👉 核心提升 1：加入内部箱线图，展示明确的中位数与四分位卡点
    meanline_visible=True,   # 显示均值线
    points='all',            # 👉 核心提升 2：把所有真实数据点像雨滴一样铺上来，数据少时显得极为专业饱满
    jitter=0.25,             # 散点水平抖动幅度
    pointpos=0               # 散点置于提琴中心线
))

# 添加实验组
fig.add_trace(go.Violin(
    x=violin_df.loc[violin_df['group_label'] == '实验组', 'uplift_label_cn'],
    y=violin_df.loc[violin_df['group_label'] == '实验组', 'estimated_clv'],
    legendgroup='实验组', scalegroup='实验组', name='实验组',
    line_color='#3498DB',
    fillcolor='rgba(52, 152, 219, 0.35)',
    box_visible=True,
    meanline_visible=True,
    points='all',
    jitter=0.25,
    pointpos=0
))

fig.update_layout(
    **common_layout,
    height=780,
    violinmode='group',      # 👉 核心提升 3：采用 Group (并排) 模式替代 Overlay (叠透)。即使某组缺失数据，另一侧也可以优美呈现完整小提琴
    xaxis_title='Uplift 客户增益类型',
    yaxis_title='预期生命周期价值 (CLV, $)',
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='center',
        x=0.5,
        title=''
    ),
    margin=dict(t=80, b=50, l=60, r=40)
)

fig = apply_chart_style(fig, "不同 Uplift 类型的 CLV 价值分布密度与用户实际落点")

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 **业务洞察**：重点观察 **“不应打扰型 (do_not_disturb)”** 的 CLV 分布。如果该群体不仅包含大量用户，"
    "且价值重心极高，说明这批高净值客户如果遭遇到过度营销打扰，将会造成极其严重的营收折损。"
)

st.caption(
    "📂 字段来源：uplift_label_cn ← campaign_uplift.xlsx: uplift_label；"
    "estimated_clv ← business_costs.xlsx: estimated_clv；"
    "group_label ← campaign_uplift.xlsx: treatment_group。"
)



# ======================================================
# 多维交叉：Uplift类型 × 官方客户价值分层 (实验组专属小提琴图)
# ======================================================
st.markdown("---")
st.subheader("🎻 实验组营销响应特征：Uplift 类型与价值分层交叉分析")

st.markdown(
    """
    本图仅聚焦于**实验组（接受了营销干预）**的客户。
    将 **Uplift 增益类型**作为纵坐标，并将官方定义的**高、中、低价值客户**拆分为三个垂直堆叠的子图。
    每个子图拥有**独立的 X 轴刻度**以自适应不同层级的价值分布，精准定位客户的营销响应特征。
    """
)

# 1. 准备并清洗数据，【仅保留实验组】
tier_df = df.dropna(subset=['estimated_clv', 'group_label', 'customer_value_segment', 'uplift_label']).copy()
tier_df = tier_df[tier_df['group_label'] == '实验组']

# 2. 映射官方价值分层 (用于拆分子图)
segment_map = {
    'high_value': '3. 高价值层 (High Value)',
    'medium_value': '2. 中价值层 (Medium Value)',
    'low_value': '1. 低价值层 (Low Value)'
}
tier_df['value_tier_cn'] = tier_df['customer_value_segment'].map(segment_map)

# 3. 映射 Uplift 类型 (用于纵坐标)
uplift_map = {
    'sure_thing': '自然留存型',
    'do_not_disturb': '不应打扰型',
    'persuadable': '可被说服型',
    'uncertain': '不确定型',
    'lost_cause': '挽回无望型'
}
tier_df['uplift_label_cn'] = tier_df['uplift_label'].map(uplift_map)

import plotly.express as px  # 确保顶部有导入 px

# 4. 绘制堆叠子图小提琴图 (横向)
fig_cross = px.violin(
    tier_df,
    x='estimated_clv',
    y='uplift_label_cn',
    color='uplift_label_cn',     # 👈 核心修改 1：告诉图表根据 Uplift 类型使用不同颜色
    facet_row='value_tier_cn',
    orientation='h',
    box=True,
    points="all",
    color_discrete_sequence=px.colors.qualitative.Set2, # 👈 核心修改 2：换一组好看的高级马卡龙色系
    category_orders={
        'value_tier_cn': ['3. 高价值层 (High Value)', '2. 中价值层 (Medium Value)', '1. 低价值层 (Low Value)']
    },
    labels={
        'estimated_clv': '预期生命周期价值 (CLV, $)',
        'uplift_label_cn': ''
    }
)

# 5. 样式优化：让分布图重新丰满起来
fig_cross.update_traces(
    scalemode='width',
    width=0.8,
    # 👈 核心修改 3：删除了之前写死的蓝色 fillcolor 和 line.color，让它自动继承上面的彩色
    line=dict(width=1),                  # 依然保持外轮廓线较细
    marker=dict(size=4.5, opacity=0.6),  # 👈 核心修改 4：点的大小从 2.5 调大到 4.5，稍微增加一点不透明度
    jitter=0.5
)


# 6. 核心修改 2：解除 X 轴共享，让每个子图自适应数据分布
fig_cross.update_xaxes(
    matches=None,          # 解除 X 轴同步共享
    showticklabels=True,   # 强制每个子图都显示自己的 X 轴数字刻度
    showgrid=True,
    gridwidth=1,
    gridcolor='#E5E7E9',
    zeroline=True,
    zerolinecolor='#E5E7E9'
)

# 7. 整体布局优化
fig_cross.update_layout(
    height=1200,  # 稍微拉高一点，给独立的 X 轴留出空间
    plot_bgcolor='white',
    paper_bgcolor='white',
    showlegend=False,
    margin=dict(t=60, b=50, l=10, r=20)
)

# 清理子图右侧默认的 "value_tier_cn=xxx" 文本，只保留干净的层级名称
fig_cross.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig_cross.update_yaxes(showgrid=False, linecolor='#E5E7E9')

st.plotly_chart(fig_cross, use_container_width=True)

st.info(
    "💡 **业务洞察**：\n"
    "剥离对照组并自适应 X 轴后，各层级的内部结构更加清晰：\n"
    "1. **高价值层（上）**：『不应打扰型』散点高度聚集，证明高净值客户对营销动作极度敏感，触达即流失。\n"
    "2. **中/低价值层（中下）**：『可被说服型』的主力军在此聚集，且分布形态饱满。这清晰地指明了下一步的策略方向——将营销预算（发券、折扣）全部倾斜给中低价值人群。"
)







# ======================================================
# 多维交叉：Uplift类型 × 官方客户价值分层 (实验组专属小提琴图)
# ======================================================
import plotly.express as px

st.markdown("---")
st.subheader("🎻 实验组营销响应特征：Uplift 类型与价值分层交叉分析")

st.markdown(
    """
    本图仅聚焦于**实验组（接受了营销干预）**的客户。
    将 **Uplift 增益类型**作为纵坐标，并将官方定义的**高、中、低价值客户**拆分为三个垂直堆叠的子图。
    每个子图拥有**独立的 X 轴刻度**以自适应不同层级的价值分布，精准定位客户的营销响应特征。
    """
)

# 1. 准备并清洗数据，【仅保留实验组】
tier_df = df.dropna(subset=['estimated_clv', 'group_label', 'customer_value_segment', 'uplift_label']).copy()
tier_df = tier_df[tier_df['group_label'] == '实验组']

# 2. 映射官方价值分层 (用于拆分子图)
segment_map = {
    'high_value': '3. 高价值层 (High Value)',
    'medium_value': '2. 中价值层 (Medium Value)',
    'low_value': '1. 低价值层 (Low Value)'
}
tier_df['value_tier_cn'] = tier_df['customer_value_segment'].map(segment_map)

# 3. 映射 Uplift 类型 (用于纵坐标)
uplift_map = {
    'sure_thing': '自然留存型',
    'do_not_disturb': '不应打扰型',
    'persuadable': '可被说服型',
    'uncertain': '不确定型',
    'lost_cause': '挽回无望型'
}
tier_df['uplift_label_cn'] = tier_df['uplift_label'].map(uplift_map)

# 🌟 高级定制：高对比度现代商务配色
premium_colors = ['#1F77B4', '#D62728', '#2CA02C', '#FF7F0E', '#9467BD']

# 4. 绘制堆叠子图小提琴图 (横向)
fig_cross = px.violin(
    tier_df,
    x='estimated_clv',
    y='uplift_label_cn',
    color='uplift_label_cn',
    facet_row='value_tier_cn',
facet_row_spacing=0.04,      # 👈 增加这一行：控制各个子图之间的上下间距
    orientation='h',
    box=True,
    points="all",
    color_discrete_sequence=premium_colors, # 使用高对比度配色
    category_orders={
        'value_tier_cn': ['3. 高价值层 (High Value)', '2. 中价值层 (Medium Value)', '1. 低价值层 (Low Value)']
    },
    labels={
        'estimated_clv': '预期生命周期价值 (CLV, $)',
        'uplift_label_cn': ''
    }
)

# 5. 样式优化：提升内部元素质感
# 5. 样式优化：提升内部元素质感
fig_cross.update_traces(
    scalemode='width',
    width=0.7,                           # 👈 第二处：把小提琴宽度从 0.8 稍微调瘦到 0.7
    line=dict(width=1.5),
    marker=dict(size=4.5, opacity=0.75, line=dict(width=0.5, color='white')),
    jitter=0.25                          # 👈 第三处(最关键)：把 jitter 从 0.5 改小到 0.25 或 0.3，限制散点上下乱跑的范围
)


# 6. X 轴样式：独立刻度、黑线黑字、底部与顶部闭合边框
fig_cross.update_xaxes(
    matches=None,          # 解除 X 轴同步共享，自适应分布
    showticklabels=True,   # 强制显示刻度
    showline=True,         # 显示轴线
    linecolor='black',     # 轴线纯黑
    linewidth=1.5,         # 轴线加粗
    mirror=True,           # 🌟 神奇属性：在顶部镜像轴线，形成上下闭合框
    ticks='outside',
    tickcolor='black',
    tickfont=dict(color='black', size=12),
    title_font=dict(color='black', size=14),
    showgrid=False,        # X轴不显示网格线，保持画面整洁
    zeroline=False
)

# 7. Y 轴样式：横向灰线、黑线黑字、左侧与右侧闭合边框
fig_cross.update_yaxes(
    showline=True,
    linecolor='black',
    linewidth=1.5,
    mirror=True,           # 🌟 神奇属性：在右侧镜像轴线，结合X轴形成完美全闭合黑框
    ticks='outside',
    tickcolor='black',
    tickfont=dict(color='black', size=12),
    title_font=dict(color='black', size=14),
    showgrid=True,         # 🌟 开启横向网格线
    gridwidth=1,
    gridcolor='rgba(200, 200, 200, 0.6)', # 高级灰色网格线
    zeroline=False
)

# 8. 整体布局与背景优化
fig_cross.update_layout(
    height=1600,
    plot_bgcolor='white',  # 图表区纯白
    paper_bgcolor='white', # 外围区纯白
    showlegend=False,
    margin=dict(t=60, b=50, l=10, r=60),
    font=dict(color='black'), # 全局字体强制黑色
# 👇 新增下面这一段来设置总标题
    title=dict(
        text="实验组 Uplift 类型与客户价值分层交叉分布", # 👈 这里修改你的标题文字
        x=0.37,                                      # 0.5 表示标题居中
        y=0.98,                                     # 标题在垂直方向的位置，越接近1越靠上
        font=dict(size=20, color='black')           # 设置标题字体大小和颜色
    )
)

# 9. 清理子图右侧默认文本，加粗并设为黑色
# 9. 清理子图右侧默认文本，加粗并设为黑色，同时向右微调防重叠
fig_cross.for_each_annotation(
    lambda a: a.update(
        text=f"<b>{a.text.split('=')[-1]}</b>",
        font=dict(color='black', size=14),
        xshift=20   # 👈 增加这一行：控制文字向右平移20个像素（如果不满意可以调大调小）
    )
)


st.plotly_chart(fig_cross, use_container_width=True)

st.info(
    "💡 **业务洞察**：\n"
    "剥离对照组并自适应 X 轴后，各层级的内部结构更加清晰：\n"
    "1. **高价值层（上）**：『不应打扰型』散点高度聚集，证明高净值客户对营销动作极度敏感，触达即流失。\n"
    "2. **中/低价值层（中下）**：『可被说服型』的主力军在此聚集，且分布形态饱满。这清晰地指明了下一步的策略方向——将营销预算（发券、折扣）全部倾斜给中低价值人群。"
)










# ======================================================
# 渠道 × Offer 响应率热力图
# ======================================================
strong_divider()

st.subheader("🔥 渠道 × Offer 响应率热力图")

heatmap_df = df[df['contacted_int'] == 1].groupby(
    ['channel_label', 'offer_label']
).agg(
    customer_count=('customer_id', 'count'),
    response_rate=('responded_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean')
).reset_index()

heatmap_df['response_rate_pct'] = heatmap_df['response_rate'] * 100
heatmap_df['after_churn_rate_pct'] = heatmap_df['after_churn_rate'] * 100

fig = px.density_heatmap(
    heatmap_df,
    x='offer_label',
    y='channel_label',
    z='response_rate_pct',
    text_auto='.1f',
    color_continuous_scale='Blues',
    labels={
        'offer_label': '优惠方案类型',
        'channel_label': '营销渠道',
        'response_rate_pct': '响应率 (%)'
    },
    hover_data={
        'customer_count': True,
        'after_churn_rate_pct': ':.1f'
    }
)

fig.update_layout(
    **common_layout,
    height=500,
    xaxis_title='优惠方案类型',
    yaxis_title='营销渠道',
    xaxis_tickangle=-20,
    coloraxis_colorbar=dict(title='响应率 (%)'),
    margin=dict(t=70, b=100, l=80, r=40)
)

fig = apply_chart_style(fig, "渠道与优惠方案组合响应率热力图")

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该热力图用于识别哪种渠道 + Offer 组合最容易获得客户响应。")
# ======================================================
# 弦图：营销渠道 × Offer × Uplift 类型
# ======================================================
strong_divider()

st.subheader("🕸️ 营销渠道、优惠方案与 Uplift 类型弦图")

st.markdown(
    """
    该弦图展示 **营销渠道 → 优惠方案 → Uplift 客户类型** 之间的连接关系。
    弦的粗细表示对应路径下的客户数量。通过该图可以观察不同营销渠道主要搭配哪些优惠方案，
    以及这些优惠方案最终更多连接到哪类客户增益类型。
    """
)

# 只保留被实际触达的实验组客户，避免 control / none / no_offer 干扰弦图结构
chord_base = df[
    (df['treatment_group'] == 'treatment') &
    (df['contacted_int'] == 1) &
    (df['channel_label'] != '无触达') &
    (df['offer_label'] != '无优惠')
].copy()

# 可选：让用户选择弦图权重
weight_option = st.radio(
    "弦图连接强度",
    ["客户数量", "响应客户数", "被挽回客户数", "净收益"],
    horizontal=True
)

if weight_option == "客户数量":
    weight_col = None
elif weight_option == "响应客户数":
    weight_col = "responded_int"
elif weight_option == "被挽回客户数":
    weight_col = "saved_by_campaign"
else:
    weight_col = "net_gain_if_retained"

# ------------------------------
# 构造第一段边：渠道 -> Offer
# ------------------------------
if weight_col is None:
    edge_1 = chord_base.groupby(
        ['channel_label', 'offer_label']
    ).agg(
        value=('customer_id', 'count')
    ).reset_index()
else:
    edge_1 = chord_base.groupby(
        ['channel_label', 'offer_label']
    ).agg(
        value=(weight_col, 'sum')
    ).reset_index()

edge_1 = edge_1.rename(
    columns={
        'channel_label': 'source_name',
        'offer_label': 'target_name'
    }
)

# ------------------------------
# 构造第二段边：Offer -> Uplift 类型
# ------------------------------
if weight_col is None:
    edge_2 = chord_base.groupby(
        ['offer_label', 'uplift_label_cn']
    ).agg(
        value=('customer_id', 'count')
    ).reset_index()
else:
    edge_2 = chord_base.groupby(
        ['offer_label', 'uplift_label_cn']
    ).agg(
        value=(weight_col, 'sum')
    ).reset_index()

edge_2 = edge_2.rename(
    columns={
        'offer_label': 'source_name',
        'uplift_label_cn': 'target_name'
    }
)

# 合并两段边
edges_named = pd.concat([edge_1, edge_2], ignore_index=True)

# 去掉 value 为 0 的边，避免图上出现无意义连接
edges_named = edges_named[edges_named['value'] > 0].copy()

# ------------------------------
# 构造节点表
# ------------------------------
channel_nodes = pd.DataFrame({
    'name': sorted(chord_base['channel_label'].dropna().unique()),
    'group': '营销渠道'
})

offer_nodes = pd.DataFrame({
    'name': sorted(chord_base['offer_label'].dropna().unique()),
    'group': '优惠方案'
})

uplift_nodes = pd.DataFrame({
    'name': sorted(chord_base['uplift_label_cn'].dropna().unique()),
    'group': 'Uplift 类型'
})

nodes_df = pd.concat(
    [channel_nodes, offer_nodes, uplift_nodes],
    ignore_index=True
).drop_duplicates('name').reset_index(drop=True)

# 节点颜色：按节点类型区分
group_color_map = {
    '营销渠道': '#3498DB',
    '优惠方案': '#F39C12',
    'Uplift 类型': '#2ECC71'
}

# 对特殊 Uplift 类型单独上色，突出业务含义
special_node_color_map = {
    '自然留存型': '#2ECC71',
    '可被说服型': '#165DFF',
    '不应打扰型': '#E74C3C',
    '挽回无望型': '#8E44AD',
    '不确定型': '#95A5A6'
}

nodes_df['color'] = nodes_df.apply(
    lambda row: special_node_color_map.get(
        row['name'],
        group_color_map.get(row['group'], '#95A5A6')
    ),
    axis=1
)

nodes_df['index'] = range(len(nodes_df))

node_id_map = dict(zip(nodes_df['name'], nodes_df['index']))

edges_df = edges_named.copy()
edges_df['source'] = edges_df['source_name'].map(node_id_map)
edges_df['target'] = edges_df['target_name'].map(node_id_map)

edges_df = edges_df.dropna(subset=['source', 'target']).copy()
edges_df['source'] = edges_df['source'].astype(int)
edges_df['target'] = edges_df['target'].astype(int)

# Holoviews 的边表只保留 source, target, value
edges_df = edges_df[['source', 'target', 'value']]

# ------------------------------
# 渲染弦图
# ------------------------------
if edges_df.empty:
    st.warning("当前数据不足，无法绘制弦图。")
else:
    render_chord_chart(
        edges_df=edges_df,
        nodes_df=nodes_df[['index', 'name', 'group', 'color']],
        title=f"营销渠道、优惠方案与 Uplift 类型连接关系弦图（权重：{weight_option}）",
        height=760
    )

    # 补充一张边表，方便报告解释和截图
    with st.expander("查看弦图连接数据"):
        show_edges = edges_named.sort_values('value', ascending=False).copy()
        show_edges['value'] = show_edges['value'].round(2)
        st.dataframe(
            show_edges.rename(
                columns={
                    'source_name': '起点',
                    'target_name': '终点',
                    'value': '连接强度'
                }
            ),
            use_container_width=True
        )

st.info(
    "💡 弦图适合展示多个类别变量之间的连接关系。"
    "若某一渠道到某一优惠方案的弦较粗，说明该渠道主要投放该类优惠；"
    "若某一优惠方案到“可被说服型”的弦较粗，说明该方案更可能产生真实增量挽留价值；"
    "若连接大量流向“自然留存型”或“不应打扰型”，则说明可能存在营销资源浪费或过度打扰问题。"
)

st.caption(
    "📂 字段来源：campaign_channel、offer_type、uplift_label、responded、churn_after_campaign "
    "来自 campaign_uplift.xlsx；net_gain_if_retained 来自 business_costs.xlsx。"
)










import streamlit as st
import pandas as pd

st.subheader("🕸️ 营销渠道、优惠方案与 Uplift 类型流向弦图")

st.markdown(
    """
    该弦图展示了 **营销渠道 → 优惠方案 → Uplift 客户类型** 的资源流向。
    为保证视觉清晰度，节点已按业务阶段进行强制分区，并过滤了占比极小的微弱连线。
    """
)

# 1. 基础数据过滤：只保留被实际触达的实验组客户
chord_base = df[
    (df['treatment_group'] == 'treatment') &
    (df['contacted_int'] == 1) &
    (df['channel_label'] != '无触达') &
    (df['offer_label'] != '无优惠')
    ].copy()

# 2. 权重选择控件
weight_option = st.radio(
    "弦图连接强度 (连线粗细)",
    ["客户数量", "响应客户数", "被挽回客户数", "净收益"],
    horizontal=True
)

if weight_option == "客户数量":
    weight_col = None
elif weight_option == "响应客户数":
    weight_col = "responded_int"
elif weight_option == "被挽回客户数":
    weight_col = "saved_by_campaign"
else:
    weight_col = "net_gain_if_retained"

# 3. 构造两段边：渠道 -> 优惠，优惠 -> Uplift
if weight_col is None:
    edge_1 = chord_base.groupby(['channel_label', 'offer_label']).size().reset_index(name='value')
    edge_2 = chord_base.groupby(['offer_label', 'uplift_label_cn']).size().reset_index(name='value')
else:
    edge_1 = chord_base.groupby(['channel_label', 'offer_label'])[weight_col].sum().reset_index(name='value')
    edge_2 = chord_base.groupby(['offer_label', 'uplift_label_cn'])[weight_col].sum().reset_index(name='value')

edge_1.columns = ['source_name', 'target_name', 'value']
edge_2.columns = ['source_name', 'target_name', 'value']
edges_named = pd.concat([edge_1, edge_2], ignore_index=True)

# ==========================================
# 💡 核心优化 1：视觉降噪 (砍掉细碎的毛边)
# ==========================================
# 过滤掉占比不到总流量 0.5% 的微弱连线，让图形主干更加清晰
threshold = edges_named['value'].sum() * 0.005
edges_named = edges_named[edges_named['value'] > threshold].copy()

# ==========================================
# 💡 核心优化 2：强制节点排序 (避免线条在圈内乱穿)
# ==========================================
channels = sorted(chord_base['channel_label'].dropna().unique())
offers = sorted(chord_base['offer_label'].dropna().unique())
# 将 Uplift 类型按重要性排序
uplifts = ['可被说服型', '自然留存型', '不应打扰型', '挽回无望型', '不确定型']

nodes_list = []
# 按顺序逐个添加，这决定了它们在圆环上的位置（左边渠道、中间优惠、右边客群）
for c in channels: nodes_list.append({'name': c, 'group': '1_渠道'})
for o in offers:   nodes_list.append({'name': o, 'group': '2_优惠'})
for u in uplifts:
    # 只添加在边表中真实存在的 Uplift 节点
    if u in edges_named['target_name'].values or u in edges_named['source_name'].values:
        nodes_list.append({'name': u, 'group': '3_客群'})

nodes_df = pd.DataFrame(nodes_list)
nodes_df['index'] = range(len(nodes_df))
node_id_map = dict(zip(nodes_df['name'], nodes_df['index']))

# ==========================================
# 💡 核心优化 3：背景+高亮的色彩策略
# ==========================================
special_node_color_map = {
    # 渠道和优惠全部变成低调的颜色，充当背景板
    '1_渠道': '#D5D8DC',  # 浅灰
    '2_优惠': '#AED6F1',  # 浅蓝

    # 核心的 Uplift 类型使用高饱和亮度，牢牢抓住眼球
    '自然留存型': '#2ECC71',  # 亮绿 (安全/无需干预)
    '可被说服型': '#FF3366',  # 亮玫红 (绝对重点，真实增量)
    '不应打扰型': '#E74C3C',  # 亮红 (警示/反面效果)
    '挽回无望型': '#8E44AD',  # 深紫 (沉没成本)
    '不确定型': '#95A5A6'  # 深灰
}

# 赋色逻辑
nodes_df['color'] = nodes_df.apply(
    lambda row: special_node_color_map.get(row['name'], special_node_color_map.get(row['group'], '#BDC3C7')),
    axis=1
)

# 4. 映射边的 ID 并准备渲染
edges_named['source'] = edges_named['source_name'].map(node_id_map)
edges_named['target'] = edges_named['target_name'].map(node_id_map)
edges_named = edges_named.dropna(subset=['source', 'target']).copy()

edges_df = edges_named[['source', 'target', 'value']].copy()
edges_df['source'] = edges_df['source'].astype(int)
edges_df['target'] = edges_df['target'].astype(int)

# 5. 渲染图表
if edges_df.empty:
    st.warning("当前数据不足或阈值过高，无法绘制弦图。")
else:
    render_chord_chart(
        edges_df=edges_df,
        nodes_df=nodes_df[['index', 'name', 'group', 'color']],
        title=f"流量转化弦图：渠道 → 优惠 → 客群矩阵 ({weight_option})",
        height=760
    )

    # 补充一张边表，方便报告解释和截图
    with st.expander("查看弦图详细流向数据"):
        show_edges = edges_named.sort_values('value', ascending=False).copy()
        show_edges['value'] = show_edges['value'].round(2)
        st.dataframe(
            show_edges[['source_name', 'target_name', 'value']].rename(
                columns={
                    'source_name': '起点',
                    'target_name': '终点',
                    'value': '连接强度'
                }
            ),
            use_container_width=True
        )

st.info(
    "💡 **学术分析指南：**\n"
    "1. **看结构**：图表左侧为营销渠道，右上方为优惠方案，右下方为 Uplift 目标客群。连线代表了资源的流向。\n"
    "2. **看错配**：在『客户数量』权重下，大量粗壮的连线最终汇聚到了绿色的『自然留存型』和红色的『不应打扰型』，这直观揭示了传统营销中严重的资源错配与浪费。\n"
    "3. **看增量**：切换至『被挽回客户数』权重，无效人群被过滤，此时图表揭示了真正带来增量价值（流向玫红色『可被说服型』）的黄金营销路径。"
)

st.caption(
    "📂 字段来源：campaign_channel、offer_type、uplift_label、responded、churn_after_campaign "
    "来自 campaign_uplift.xlsx；net_gain_if_retained 来自 business_costs.xlsx。"
)



# ======================================================
# 平行类别多维溯源图：营销渠道 × Offer × Uplift 类型
# ======================================================
strong_divider()

st.subheader("📊 营销渠道、优惠方案与客群结构多维溯源图")

st.markdown(
    """
    该**平行类别图 (Parallel Categories)** 用于追踪多个特征维度的排列组合流向。
    它不仅避免了弦图在中心大量交叉的混乱问题，还能让你**通过颜色进行反向溯源**：
    连接带的颜色跟随最终的业务终点（Uplift 客群类型），帮助你一眼看清“高价值转化”来源于哪种触达策略。
    """
)

# 1. 基础数据过滤：只保留被实际触达的实验组客户
flow_base = df[
    (df['treatment_group'] == 'treatment') &
    (df['contacted_int'] == 1) &
    (df['channel_label'] != '无触达') &
    (df['offer_label'] != '无优惠')
    ].copy()

# 2. 权重选择控件
weight_option = st.radio(
    "观察维度 (连线流量大小)",
    ["客户数量", "响应客户数", "被挽回客户数", "净收益"],
    horizontal=True,
    key="parcats_weight_option"
)

if weight_option == "客户数量":
    weight_col = None
elif weight_option == "响应客户数":
    weight_col = "responded_int"
elif weight_option == "被挽回客户数":
    weight_col = "saved_by_campaign"
else:
    weight_col = "net_gain_if_retained"

# 3. 按所选维度聚合数据
if weight_col is None:
    agg_df = flow_base.groupby(['channel_label', 'offer_label', 'uplift_label_cn']).size().reset_index(name='value')
else:
    agg_df = flow_base.groupby(['channel_label', 'offer_label', 'uplift_label_cn'])[weight_col].sum().reset_index(
        name='value')

agg_df = agg_df[agg_df['value'] > 0].copy()

if agg_df.empty:
    st.warning("当前数据不足，无法绘制多维溯源图。")
else:
    # 4. 根据业务建立精准连续的色彩映射 (Colorscale)
    # 为 Plotly 的平行类别连接带指定颜色，我们需要把 Uplift 类型转换为数值
    color_lookup = {
        '不应打扰型': 0,  # 红色 (负面)
        '挽回无望型': 1,  # 紫色 (沉没)
        '不确定型': 2,  # 灰色 (中性)
        '自然留存型': 3,  # 绿色 (无谓花费)
        '可被说服型': 4  # 亮玫红 (真实挽回核心！)
    }

    # 构建离散分段色带，直接使用 rgba 设置 65% 透明度 (0.65)，替代 opacity 属性
    # 构建离散分段色带，使用高对比度的 RGBA 颜色，0.7 代表 70% 不透明度
    cscale = [
        # 0 - 不应打扰型：高亮火焰红（危险/触达即流失）
        [0.0, 'rgba(255, 50, 50, 0.7)'], [0.2, 'rgba(255, 50, 50, 0.7)'],

        # 1 - 挽回无望型：深邃黑紫（沉没成本）
        [0.2, 'rgba(75, 0, 130, 0.7)'], [0.4, 'rgba(75, 0, 130, 0.7)'],

        # 2 - 不确定型：浅灰白（中立/无特征）
        [0.4, 'rgba(180, 180, 180, 0.7)'], [0.6, 'rgba(180, 180, 180, 0.7)'],

        # 3 - 自然留存型：明亮湖蓝/青绿（安全/不干预也留存）
        [0.6, 'rgba(0, 190, 100, 0.7)'], [0.8, 'rgba(0, 190, 100, 0.7)'],

        # 4 - 可被说服型：刺眼亮玫红（绝对核心/高转化增量）
        [0.8, 'rgba(25, 200, 307, 0.85)'], [1.0, 'rgba(25, 200, 307, 0.85)']
    ]

    agg_df['color_val'] = agg_df['uplift_label_cn'].map(color_lookup)

    # 5. 构建与渲染绘图
    fig = go.Figure(data=[go.Parcats(
        dimensions=[
            dict(label='1. 营销触达渠道', values=agg_df['channel_label']),
            dict(label='2. 推送优惠策略', values=agg_df['offer_label']),
            dict(label='3. 命中的 Uplift 客群', values=agg_df['uplift_label_cn'])
        ],
        counts=agg_df['value'],
        line=dict(
            color=agg_df['color_val'],
            colorscale=cscale,
            cmin=0,
            cmax=4,
            shape='hspline'  # 使用高级曲线平滑过渡，已移除报错的 opacity
        ),
        hoveron='color',
        hoverinfo='count+probability',
        labelfont=dict(size=14, color='#1F2D3D', family='Microsoft YaHei, SimHei, Arial'),
        tickfont=dict(size=12, color='#1F2D3D')
    )])

    fig.update_layout(
        height=600,
        margin=dict(t=50, b=40, l=80, r=80),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "💡 **实用方法指南：溯源最优策略**\n\n"
        "因为我们在代码中赋予了**『可被说服型(真实增量)』**独占的高亮玫红色，"
        "请将目光看向最右侧柱子，找到代表该客群的类别，顺着流向那里的那些**玫红色绸带**向屏幕左侧回溯，"
        "就能一眼摸清：**哪些渠道配上哪些优惠**，能够打中最多有价值的人群。"
    )


# ======================================================
# 弦图：营销渠道 × Offer × Uplift 类型 多维溯源图
# ======================================================
import json
import streamlit.components.v1 as components

strong_divider()

st.subheader("📊 营销渠道、优惠方案与客群结构弦图溯源")

st.markdown(
    """
    该**弦图 (Chord Diagram)** 用于展示“营销渠道 → 优惠方案 → Uplift 客群类型”的多维流向关系。

    图中所有节点以环形方式排列，连接带宽度代表对应流量大小。  
    连接带颜色跟随最终命中的 **Uplift 客群类型**，因此可以通过颜色进行反向溯源：

    - 玫红色：可被说服型，代表真实增量价值；
    - 红色：不应打扰型，代表可能产生负向影响；
    - 绿色：自然留存型，代表不干预也可能留存；
    - 紫色：挽回无望型；
    - 灰色：不确定型。
    """
)

# 1. 基础数据过滤：只保留被实际触达的实验组客户
flow_base = df[
    (df['treatment_group'] == 'treatment') &
    (df['contacted_int'] == 1) &
    (df['channel_label'] != '无触达') &
    (df['offer_label'] != '无优惠')
    ].copy()

# 2. 权重选择控件
weight_option = st.radio(
    "观察维度（连接带宽度）",
    ["客户数量", "响应客户数", "被挽回客户数", "净收益"],
    horizontal=True,
    key="chord_weight_option"
)

if weight_option == "客户数量":
    weight_col = None
elif weight_option == "响应客户数":
    weight_col = "responded_int"
elif weight_option == "被挽回客户数":
    weight_col = "saved_by_campaign"
else:
    weight_col = "net_gain_if_retained"

# 3. 按所选维度聚合数据
if weight_col is None:
    agg_df = (
        flow_base
        .groupby(['channel_label', 'offer_label', 'uplift_label_cn'])
        .size()
        .reset_index(name='value')
    )
else:
    agg_df = (
        flow_base
        .groupby(['channel_label', 'offer_label', 'uplift_label_cn'])[weight_col]
        .sum()
        .reset_index(name='value')
    )

agg_df = agg_df[agg_df['value'] > 0].copy()

if agg_df.empty:
    st.warning("当前数据不足，无法绘制弦图。")

else:
    # 4. 颜色映射：连接带颜色跟随最终 Uplift 类型
    uplift_color_map = {
        '不应打扰型': 'rgba(255, 50, 50, 0.3)',  # 红色
        '挽回无望型': 'rgba(75, 0, 130, 0.52)',  # 紫色
        '不确定型': 'rgba(180, 180, 180, 0.72)',  # 灰色
        '自然留存型': 'rgba(0, 190, 50, 0.30)',  # 绿色
        '可被说服型': 'rgba(135, 206, 250, 0.88)'  # 亮玫红
    }

    node_type_color_map = {
        "channel": "#2E86DE",
        "offer": "#F39C12",
        "uplift": "#34495E"
    }

    # 5. 构建弦图节点
    channels = list(agg_df['channel_label'].dropna().unique())
    offers = list(agg_df['offer_label'].dropna().unique())
    uplifts = list(agg_df['uplift_label_cn'].dropna().unique())

    nodes = []

    for name in channels:
        nodes.append({
            "id": str(name),
            "name": str(name),
            "type": "channel",
            "typeLabel": "营销渠道",
            "color": node_type_color_map["channel"]
        })

    for name in offers:
        nodes.append({
            "id": str(name),
            "name": str(name),
            "type": "offer",
            "typeLabel": "优惠方案",
            "color": node_type_color_map["offer"]
        })

    for name in uplifts:
        nodes.append({
            "id": str(name),
            "name": str(name),
            "type": "uplift",
            "typeLabel": "Uplift 客群",
            "color": uplift_color_map.get(name, "rgba(120,120,120,0.8)")
        })

    # 6. 构建弦图连接
    # 三层关系拆成两段：
    # 渠道 -> 优惠
    # 优惠 -> Uplift
    raw_links = []

    for _, row in agg_df.iterrows():
        ch = str(row['channel_label'])
        off = str(row['offer_label'])
        up = str(row['uplift_label_cn'])
        val = float(row['value'])

        link_color = uplift_color_map.get(up, "rgba(120,120,120,0.65)")

        # 第一段：营销渠道 -> 优惠方案
        raw_links.append({
            "source": ch,
            "target": off,
            "value": val,
            "uplift": up,
            "color": link_color,
            "path": f"{ch} → {off}",
            "fullPath": f"{ch} → {off} → {up}"
        })

        # 第二段：优惠方案 -> Uplift 客群
        raw_links.append({
            "source": off,
            "target": up,
            "value": val,
            "uplift": up,
            "color": link_color,
            "path": f"{off} → {up}",
            "fullPath": f"{ch} → {off} → {up}"
        })

    # 7. 聚合同源、同目标、同 Uplift 的连接，避免重复太碎
    link_df = pd.DataFrame(raw_links)

    link_df = (
        link_df
        .groupby(['source', 'target', 'uplift', 'color', 'path', 'fullPath'], as_index=False)['value']
        .sum()
    )

    links = link_df.to_dict(orient="records")

    # 转 JSON，供 D3 使用
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    links_json = json.dumps(links, ensure_ascii=False)

    # 8. D3 弦图 HTML
    chord_html = f"""
    <div id="chord-container" style="width:100%; height:780px; position:relative;"></div>

    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>

    <script>
    const nodes = {nodes_json};
    const links = {links_json};

    const container = document.getElementById("chord-container");
    const width = container.clientWidth || 1100;
    const height = 760;

    const outerRadius = Math.min(width, height) * 0.38;
    const innerRadius = outerRadius - 20;

    const svg = d3.select("#chord-container")
        .append("svg")
        .attr("width", "100%")
        .attr("height", height)
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        .style("font-family", "Microsoft YaHei, SimHei, Arial, sans-serif")
        .style("background", "white");

    const tooltip = d3.select("#chord-container")
        .append("div")
        .style("position", "absolute")
        .style("z-index", "10")
        .style("visibility", "hidden")
        .style("background", "rgba(31, 45, 61, 0.92)")
        .style("color", "white")
        .style("padding", "10px 12px")
        .style("border-radius", "8px")
        .style("font-size", "13px")
        .style("line-height", "1.6")
        .style("box-shadow", "0 4px 12px rgba(0,0,0,0.18)");

    const nodeById = new Map(nodes.map(d => [d.id, d]));

    // 计算每个节点的总流量，用于决定环上弧长
    nodes.forEach(d => {{
        d.total = 0;
        d.links = [];
    }});

    links.forEach(l => {{
        const s = nodeById.get(l.source);
        const t = nodeById.get(l.target);

        if (s && t) {{
            s.total += +l.value;
            t.total += +l.value;
            s.links.push(l);
            t.links.push(l);
        }}
    }});

    const visibleNodes = nodes.filter(d => d.total > 0);

    // 按节点类型排序：渠道 → 优惠 → Uplift
    const typeOrder = {{
        "channel": 0,
        "offer": 1,
        "uplift": 2
    }};

    visibleNodes.sort((a, b) => {{
        const typeDiff = typeOrder[a.type] - typeOrder[b.type];
        if (typeDiff !== 0) return typeDiff;
        return b.total - a.total;
    }});

    const totalValue = d3.sum(visibleNodes, d => d.total);

    const groupGap = 0.045;
    const nodeGap = 0.012;

    let currentAngle = -Math.PI / 2;

    // 给不同类型节点之间加稍大间隔
    visibleNodes.forEach((d, i) => {{
        if (i > 0 && visibleNodes[i - 1].type !== d.type) {{
            currentAngle += groupGap;
        }} else if (i > 0) {{
            currentAngle += nodeGap;
        }}

        const angleSize = (d.total / totalValue) * (Math.PI * 2 - groupGap * 3 - nodeGap * visibleNodes.length);
        d.startAngle = currentAngle;
        d.endAngle = currentAngle + angleSize;
        d.midAngle = (d.startAngle + d.endAngle) / 2;
        currentAngle = d.endAngle;
    }});

    const visibleNodeById = new Map(visibleNodes.map(d => [d.id, d]));

    // 为每个节点内的连接分配局部角度
    visibleNodes.forEach(node => {{
        let offset = node.startAngle;

        node.links.sort((a, b) => b.value - a.value);

        node.links.forEach(l => {{
            const angleSize = (l.value / node.total) * (node.endAngle - node.startAngle);

            if (l.source === node.id) {{
                l.sourceStartAngle = offset;
                l.sourceEndAngle = offset + angleSize;
            }}

            if (l.target === node.id) {{
                l.targetStartAngle = offset;
                l.targetEndAngle = offset + angleSize;
            }}

            offset += angleSize;
        }});
    }});

    const ribbon = d3.ribbon()
        .radius(innerRadius)
        .padAngle(0.004);

    const arc = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);

    // 标题
    svg.append("text")
        .attr("x", 0)
        .attr("y", -height / 2 + 24)
        .attr("text-anchor", "middle")
        .attr("font-size", 18)
        .attr("font-weight", 700)
        .attr("fill", "#1F2D3D")
        .text("营销链路与客群转化弦图（以“{weight_option}”为权重）");

    // 图例
    const legendData = [
        {{label: "营销渠道", color: "#2E86DE"}},
        {{label: "优惠方案", color: "#F39C12"}},
        
    
        {{label: "不应打扰型", color: "rgba(255, 50, 50, 0.4)"}},
        {{label: "挽回无望型", color: "rgba(75, 0, 130, 0.52)"}},
        {{label: "不确定型", color: "rgba(180, 180, 180, 0.72)"}},
        {{label: "自然留存型", color: "rgba(0, 190, 100, 0.2)"}},
        {{label: "可被说服型", color: "rgba(135, 206, 250, 0.88)"}}


    ];

    const legend = svg.append("g")
        .attr("transform", `translate(${{-width / 2 + 250}}, ${{-height / 2 + 75}})`);

    legend.selectAll("rect")
        .data(legendData)
        .join("rect")
        .attr("x", 0)
        .attr("y", (d, i) => i * 24)
        .attr("width", 14)
        .attr("height", 14)
        .attr("rx", 3)
        .attr("fill", d => d.color);

    legend.selectAll("text")
        .data(legendData)
        .join("text")
        .attr("x", 22)
        .attr("y", (d, i) => i * 24 + 11)
        .attr("font-size", 10)
        .attr("fill", "#1F2D3D")
        .text(d => d.label);

    // 绘制连接带
    const ribbonGroup = svg.append("g")
        .attr("fill-opacity", 0.68);

    const ribbons = ribbonGroup
        .selectAll("path")
        .data(links.filter(l =>
            visibleNodeById.has(l.source) &&
            visibleNodeById.has(l.target) &&
            l.sourceStartAngle !== undefined &&
            l.targetStartAngle !== undefined
        ))
        .join("path")
        .attr("d", d => ribbon({{
            source: {{
                startAngle: d.sourceStartAngle,
                endAngle: d.sourceEndAngle
            }},
            target: {{
                startAngle: d.targetStartAngle,
                endAngle: d.targetEndAngle
            }}
        }}))
        .attr("fill", d => d.color)
        .attr("stroke", d => d3.color(d.color).darker(0.4))
        .attr("stroke-width", 0.35)
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {{
            d3.select(this)
                .attr("fill-opacity", 1)
                .attr("stroke-width", 1.3);

            tooltip
                .style("visibility", "visible")
                .html(`
                    <b>链路：</b>${{d.path}}<br/>
                    <b>完整溯源：</b>${{d.fullPath}}<br/>
                    <b>Uplift 类型：</b>${{d.uplift}}<br/>
                    <b>{weight_option}：</b>${{d3.format(",.2f")(d.value)}}
                `);
        }})
        .on("mousemove", function(event) {{
            tooltip
                .style("left", (event.offsetX + 18) + "px")
                .style("top", (event.offsetY + 18) + "px");
        }})
        .on("mouseout", function() {{
            d3.select(this)
                .attr("fill-opacity", 0.78)
                .attr("stroke-width", 0.35);

            tooltip.style("visibility", "hidden");
        }});

    // 绘制节点弧
    const nodeGroup = svg.append("g");

    const groups = nodeGroup
        .selectAll("g")
        .data(visibleNodes)
        .join("g");

    groups.append("path")
        .attr("d", d => arc({{
            startAngle: d.startAngle,
            endAngle: d.endAngle
        }}))
        .attr("fill", d => d.color)
.attr("stroke", "rgba(255,255,255,0.95)")
.attr("stroke-width", 2)

        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {{
            d3.select(this)
                .attr("stroke", "#1F2D3D")
                .attr("stroke-width", 2.5);

            ribbons
                .attr("fill-opacity", l => (l.source === d.id || l.target === d.id) ? 0.95 : 0.12)
                .attr("stroke-opacity", l => (l.source === d.id || l.target === d.id) ? 1 : 0.08);

            tooltip
                .style("visibility", "visible")
                .html(`
                    <b>节点：</b>${{d.name}}<br/>
                    <b>类型：</b>${{d.typeLabel}}<br/>
                    <b>总流量：</b>${{d3.format(",.2f")(d.total)}}
                `);
        }})
        .on("mousemove", function(event) {{
            tooltip
                .style("left", (event.offsetX + 18) + "px")
                .style("top", (event.offsetY + 18) + "px");
        }})
        .on("mouseout", function() {{
            d3.select(this)
                .attr("stroke", "#FFFFFF")
                .attr("stroke-width", 1.5);

            ribbons
                .attr("fill-opacity", 0.78)
                .attr("stroke-opacity", 1);

            tooltip.style("visibility", "hidden");
        }});

    // 节点标签
    groups.append("text")
        .each(d => {{
            d.angle = (d.startAngle + d.endAngle) / 2;
        }})
        .attr("dy", d => {{
    const isNetGain = "{weight_option}" === "净收益";

    if (isNetGain) {{
        return d.name === "可被说服型" ? "-0.5em" :
               d.name === "挽回无望型" ? "1.3em" :
               "0.35em";
    }}

    return d.name === "可被说服型" ? "-0.15em" :
           d.name === "挽回无望型" ? "0.9em" :
           "0.35em";
}})

        .attr("transform", d => {{
    const angle = d.angle * 180 / Math.PI - 90;

    // 这两个标签保持原来的位置和方向，不做环绕旋转
    const keepOriginal = ["可被说服型", "挽回无望型","不确定型"].includes(d.name);

    if (keepOriginal) {{
        const translate = outerRadius + 12;
        const flip = d.angle > Math.PI / 2 && d.angle < Math.PI * 1.5;

        return `rotate(${{angle}}) translate(${{translate}}) ${{flip ? "rotate(180)" : ""}}`;
    }}

    // 其他标签做成沿圆环环绕的效果
    const translate = outerRadius + 11;
    const flip = d.angle > Math.PI / 2 && d.angle < Math.PI * 1.5;
    const tangentRotate = flip ? -90 : 90;

    return `rotate(${{angle}}) translate(${{translate}}) rotate(${{tangentRotate}})`;
}})
.attr("text-anchor", d => {{
    const keepOriginal = ["可被说服型", "挽回无望型","不确定型"].includes(d.name);

    if (keepOriginal) {{
        const flip = d.angle > Math.PI / 2 && d.angle < Math.PI * 1.5;
        return flip ? "end" : "start";
    }}

    return "middle";
}})



        .attr("font-size", 11)
        .attr("font-weight", 500)
        .attr("fill", "#1F2D3D")
        .text(d => d.name.length > 16 ? d.name.slice(0, 15) + "…" : d.name);

    

    </script>
    """
    components.html(chord_html, height=800, scrolling=False)

    # 当前 D3 弦图使用的边表
    show_paths = agg_df.copy().sort_values('value', ascending=False)
    show_paths['value'] = show_paths['value'].round(2)

    st.write("当前弦图完整路径数据（建议用于分析）")
    st.dataframe(
        show_paths.rename(columns={
            'channel_label': '营销渠道',
            'offer_label': '优惠方案',
            'uplift_label_cn': 'Uplift 类型',
            'value': '连接强度'
        }),
        use_container_width=True
    )
    csv_paths = show_paths.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "下载完整路径数据 CSV",
        data=csv_paths,
        file_name=f"chord_complete_paths_{weight_option}.csv",
        mime="text/csv"
    )
    edge_summary = (
        pd.DataFrame(raw_links)
        .groupby(['source', 'target', 'uplift', 'path'], as_index=False)['value']
        .sum()
        .sort_values('value', ascending=False)
    )

    edge_summary['value'] = edge_summary['value'].round(2)

    st.write("当前弦图局部边汇总数据")
    st.dataframe(
        edge_summary.rename(columns={
            'source': '起点',
            'target': '终点',
            'uplift': 'Uplift 类型',
            'path': '局部路径',
            'value': '连接强度'
        }),
        use_container_width=True
    )

    uplift_summary = (
        agg_df.groupby('uplift_label_cn', as_index=False)['value']
        .sum()
        .sort_values('value', ascending=False)
    )
    uplift_summary['value'] = uplift_summary['value'].round(2)

    st.write("按 Uplift 类型汇总")
    st.dataframe(
        uplift_summary.rename(columns={
            'uplift_label_cn': 'Uplift 类型',
            'value': '总连接强度'
        }),
        use_container_width=True
    )

    offer_summary = (
        agg_df.groupby('offer_label', as_index=False)['value']
        .sum()
        .sort_values('value', ascending=False)
    )
    offer_summary['value'] = offer_summary['value'].round(2)

    st.write("按优惠方案汇总")
    st.dataframe(
        offer_summary.rename(columns={
            'offer_label': '优惠方案',
            'value': '总连接强度'
        }),
        use_container_width=True
    )

    channel_summary = (
        agg_df.groupby('channel_label', as_index=False)['value']
        .sum()
        .sort_values('value', ascending=False)
    )
    channel_summary['value'] = channel_summary['value'].round(2)

    st.write("按营销渠道汇总")
    st.dataframe(
        channel_summary.rename(columns={
            'channel_label': '营销渠道',
            'value': '总连接强度'
        }),
        use_container_width=True
    )

    st.info(
        "💡 **实用方法指南：溯源最优策略**\n\n"
        "请重点观察图中的**亮玫红色连接带**，它代表最终命中的 **『可被说服型』** 客群。"
        "顺着玫红色连接带反向观察，可以识别出哪些 **营销渠道 × 优惠方案** 组合更容易带来真实增量价值。\n\n"
        "相反，如果某些渠道或优惠方案连接了大量红色的 **『不应打扰型』** 客群，则说明这些营销动作可能存在负向干扰，应谨慎使用。"
    )








# ======================================================
# 风险等级 × Uplift 标签
# ======================================================
strong_divider()

st.subheader("⚠️ 风险等级 × Uplift 类型的客户数量")

risk_uplift = df.groupby(['risk_label', 'uplift_label_cn']).agg(
    customer_count=('customer_id', 'count'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    avg_clv=('estimated_clv', 'mean')
).reset_index()

risk_uplift['after_churn_rate_pct'] = risk_uplift['after_churn_rate'] * 100

risk_order = ['低风险', '中风险', '高风险']
risk_uplift['risk_label'] = pd.Categorical(
    risk_uplift['risk_label'],
    categories=risk_order,
    ordered=True
)

fig = px.bar(
    risk_uplift.sort_values('risk_label'),
    x='risk_label',
    y='customer_count',
    color='uplift_label_cn',
    barmode='group',
    text='customer_count',
    hover_data={
        'after_churn_rate_pct': ':.1f',
        'avg_clv': ':.2f'
    },
    labels={
        'risk_label': '风险等级',
        'customer_count': '客户数量',
        'uplift_label_cn': '客户增益类型',
        'after_churn_rate_pct': '活动后流失率',
        'avg_clv': '平均客户生命周期价值',
    }
)

fig.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=10)
)

fig.update_layout(
    **common_layout,
    height=520,
    xaxis_title='风险等级',
    yaxis_title='客户数量',
    legend_title_text='客户增益类型',
    margin=dict(t=70, b=40, l=40, r=40)
)

fig = apply_chart_style(fig, "风险等级与客户增益类型客户数量分布")


st.plotly_chart(fig, use_container_width=True)

st.info("💡 高风险且可被说服的客户，是最值得优先触达的人群。高风险且不应打扰的客户，则应谨慎营销。")
st.caption("📍 数据来源：风险等级来自 full_customers.xlsx (rule_based_churn_risk_level)；Uplift 类型来自 campaign_uplift.xlsx (uplift_label)")

st.caption(
    "📂 字段来源：risk_label ← full_customers.xlsx: rule_based_churn_risk_level；"
    "uplift_label_cn ← campaign_uplift.xlsx: uplift_label；"
    "after_churn_rate ← campaign_uplift.xlsx: churn_after_campaign；"
    "avg_clv ← business_costs.xlsx: estimated_clv。"
)

# ======================================================
# 高价值可触达客户清单
# ======================================================
strong_divider()

st.subheader("🔎 重点运营客户清单")

priority_customers = df[
    (
        (df['uplift_label'].isin(['persuadable', 'uncertain'])) |
        (df['saved_by_campaign'] == 1)
    )
].copy()

priority_customers = priority_customers.sort_values(
    ['estimated_clv', 'rule_based_churn_risk_score'],
    ascending=[False, False]
)

show_cols = [
    'customer_id',
    'group_label',
    'channel_label',
    'offer_label',
    'contacted',
    'responded',
    'original_churn',
    'churn_after_campaign',
    'saved_by_campaign',
    'uplift_label_cn',
    'estimated_clv',
    'retention_cost',
    'net_gain_if_retained',
    'value_label',
    'risk_label',
    'rule_based_churn_risk_score'
]

st.dataframe(
    priority_customers[show_cols].head(100),
    use_container_width=True
)

st.caption("""
💡 筛选规则：Uplift 类型为可被说服/不确定，或活动后被成功挽回的客户。
📍 关键列来源：CLV (`business_costs.xlsx`), 风险分数 (`full_customers.xlsx`), 活动标签 (`campaign_uplift.xlsx`)
""")

# ======================================================
# 不应打扰客户清单
# ======================================================
strong_divider()

st.subheader("🚫 不应打扰客户清单")

dnd_customers = df[df['uplift_label'] == 'do_not_disturb'].copy()

if len(dnd_customers) > 0:
    dnd_customers = dnd_customers.sort_values(
        ['estimated_clv', 'rule_based_churn_risk_score'],
        ascending=[False, False]
    )

    st.dataframe(
        dnd_customers[show_cols],
        use_container_width=True
    )

    st.caption("💡 这些客户建议减少营销触达，避免因过度打扰导致负向效果。")
else:
    st.success("当前数据中没有 do_not_disturb 类型客户。")

# ======================================================
# Sankey：活动前后流失状态流向图
# ======================================================
strong_divider()

st.subheader("🌊 活动前后客户流失状态流向图")

sankey_df = df.copy()

sankey_df['before_status'] = sankey_df['original_churn_int'].map({
    0: '活动前未流失',
    1: '活动前已流失'
})

sankey_df['after_status'] = sankey_df['churn_after_campaign_int'].map({
    0: '活动后未流失',
    1: '活动后已流失'
})

flow = sankey_df.groupby(['before_status', 'group_label', 'after_status']).agg(
    customer_count=('customer_id', 'count')
).reset_index()

labels = list(pd.unique(
    flow['before_status'].tolist() +
    flow['group_label'].tolist() +
    flow['after_status'].tolist()
))

label_to_id = {label: i for i, label in enumerate(labels)}

source = []
target = []
value = []

flow_1 = flow.groupby(['before_status', 'group_label'])['customer_count'].sum().reset_index()
for _, row in flow_1.iterrows():
    source.append(label_to_id[row['before_status']])
    target.append(label_to_id[row['group_label']])
    value.append(row['customer_count'])

flow_2 = flow.groupby(['group_label', 'after_status'])['customer_count'].sum().reset_index()
for _, row in flow_2.iterrows():
    source.append(label_to_id[row['group_label']])
    target.append(label_to_id[row['after_status']])
    value.append(row['customer_count'])

fig = go.Figure(data=[go.Sankey(
    arrangement='snap',
    node=dict(
        pad=20,
        thickness=22,
        line=dict(color='black', width=0.5),
        label=labels,
        color=[
            '#3498DB' if '未流失' in label else
            '#E74C3C' if '已流失' in label else
            '#F1C40F' if '实验组' in label else
            '#95A5A6'
            for label in labels
        ]
    ),
    link=dict(
        source=source,
        target=target,
        value=value,
        color='rgba(52, 152, 219, 0.35)'
    )
)])

fig.update_layout(
    height=560,
    font=dict(size=13, color='black'),
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(t=70, b=40, l=40, r=40)
)

fig = apply_chart_style(fig, "活动前后客户流失状态流向图")

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 Sankey 图展示客户从活动前状态，经由实验/对照分组，最终流向活动后状态。"
    "如果实验组从“活动前已流失”流向“活动后未流失”的人数较多，说明活动有挽回效果。"
)

# ======================================================
# 营销活动漏斗图
# ======================================================
strong_divider()

st.subheader("🧲 营销活动转化漏斗")

funnel_data = pd.DataFrame({
    'stage': [
        '总客户',
        '被触达客户',
        '响应客户',
        '被挽回客户',
        '活动后留存客户'
    ],
    'count': [
        len(df),
        df['contacted_int'].sum(),
        df['responded_int'].sum(),
        df['saved_by_campaign'].sum(),
        (df['churn_after_campaign_int'] == 0).sum()
    ]
})

fig = px.funnel(
    funnel_data,
    x='count',
    y='stage',
    color='stage',
    color_discrete_sequence=[
        '#2C3E50',
        '#3498DB',
        '#9B59B6',
        '#27AE60',
        '#16A085'
    ],
    labels={
        'count': '客户数量',
        'stage': '转化阶段'
    }
)

fig.update_traces(
    textposition='inside',
    textinfo='value+percent initial',
    textfont=dict(size=14, color='white')
)

fig.update_layout(
    **common_layout,
    height=520,
    showlegend=False,
    xaxis_title='客户数量',
    yaxis_title='转化阶段',
    margin=dict(t=70, b=40, l=80, r=40)
)

fig = apply_chart_style(fig, "营销活动转化漏斗图")

st.plotly_chart(fig, use_container_width=True)

st.info("💡 漏斗图可以直观看到营销活动从触达到响应、再到挽回的转化损耗。")

# ======================================================
# 渠道 × Offer 气泡矩阵
# ======================================================
# ======================================================
# 渠道 × Offer 响应气泡矩阵
# ======================================================
strong_divider()

st.subheader("🫧 渠道与优惠方案响应气泡矩阵")

# 只保留实际被触达的客户，排除无触达、无优惠
bubble_base = df[
    (df['contacted_int'] == 1) &
    (df['channel_label'] != '无触达') &
    (df['offer_label'] != '无优惠')
].copy()

# 按“营销渠道 × 优惠方案”汇总
bubble_df = bubble_base.groupby(
    ['channel_label', 'offer_label']
).agg(
    customer_count=('customer_id', 'count'),
    responded_count=('responded_int', 'sum'),
    response_rate=('responded_int', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    saved_count=('saved_by_campaign', 'sum'),
    avg_clv=('estimated_clv', 'mean')
).reset_index()

# 转为百分比
bubble_df['response_rate_pct'] = bubble_df['response_rate'] * 100
bubble_df['after_churn_rate_pct'] = bubble_df['after_churn_rate'] * 100

# 显示在气泡下方的文字
bubble_df['text_label'] = bubble_df['response_rate_pct'].apply(lambda x: f"{x:.1f}%")

# 为了让横纵轴顺序更稳定，可以手动指定顺序
channel_order = ['邮件', '短信', '电话', 'App 推送']

offer_order = [
    '九折优惠',
    '优先客服支持',
    '免费国际套餐试用',
    '免费语音信箱月',
    '八折优惠',
    '老客户奖励'
]

# 只保留当前数据中真实存在的类别，避免空类别报错
channel_order = [c for c in channel_order if c in bubble_df['channel_label'].unique()]
offer_order = [o for o in offer_order if o in bubble_df['offer_label'].unique()]

bubble_df['channel_label'] = pd.Categorical(
    bubble_df['channel_label'],
    categories=channel_order,
    ordered=True
)

bubble_df['offer_label'] = pd.Categorical(
    bubble_df['offer_label'],
    categories=offer_order,
    ordered=True
)

bubble_df = bubble_df.sort_values(['channel_label', 'offer_label'])

# 气泡大小设置
# 手动缩放气泡大小，让大小差异更明显
min_size = 24
max_size = 74

count_min = bubble_df['customer_count'].min()
count_max = bubble_df['customer_count'].max()

if pd.isna(count_max) or count_max == count_min:
    bubble_df['bubble_size'] = 42
else:
    bubble_df['bubble_size'] = (
        min_size +
        (bubble_df['customer_count'] - count_min) / (count_max - count_min) * (max_size - min_size)
    )


# ======================================================
# 绘制气泡矩阵
# ======================================================
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=bubble_df['offer_label'],
        y=bubble_df['channel_label'],
        mode='markers+text',
        text=bubble_df['text_label'],
        textposition='bottom center',
        textfont=dict(
            size=11,
            color='#4A4A4A',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        marker=dict(
            size=bubble_df['bubble_size'],

            color=bubble_df['response_rate_pct'],
            colorscale=[
                [0.00, '#A83232'],   # 低响应率：红色
                [0.25, '#C97C7C'],
                [0.50, '#D9DEE7'],
                [0.75, '#6D83A6'],
                [1.00, '#1F4E8C']    # 高响应率：深蓝
            ],
            cmin=bubble_df['response_rate_pct'].min(),
            cmax=bubble_df['response_rate_pct'].max(),
            showscale=True,
            colorbar=dict(
                title=dict(
                    text='响应率 (%)',
                    font=dict(
                        size=12,
                        color='black',
                        family='Microsoft YaHei, SimHei, Arial'
                    )
                ),
                tickfont=dict(
                    size=11,
                    color='black'
                ),
                thickness=16,
                len=0.65,
                outlinewidth=0
            ),
            line=dict(
                color='rgba(0,0,0,0)',
                width=0
            ),

            opacity=0.90
        ),
        customdata=bubble_df[[
            'customer_count',
            'responded_count',
            'response_rate_pct',
            'after_churn_rate_pct',
            'saved_count',
            'avg_clv'
        ]],
        hovertemplate=(
            '<b>营销渠道：%{y}</b><br>'
            '<b>优惠方案：%{x}</b><br><br>'
            '触达客户数：%{customdata[0]:,.0f}<br>'
            '响应客户数：%{customdata[1]:,.0f}<br>'
            '响应率：%{customdata[2]:.1f}%<br>'
            '活动后流失率：%{customdata[3]:.1f}%<br>'
            '被挽回客户数：%{customdata[4]:,.0f}<br>'
            '平均客户生命周期价值：$%{customdata[5]:,.2f}'
            '<extra></extra>'
        )
    )
)

# ======================================================
# 图表布局
# ======================================================
fig.update_layout(
    height=560,
    title=dict(
        text='<b>渠道与优惠方案响应气泡矩阵</b>',
        x=0.5,
        xanchor='center',
        y=0.92,
        yanchor='top',
        font=dict(
            size=18,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),
    xaxis_title='优惠方案类型',
    yaxis_title='营销渠道',
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(t=80, b=110, l=80, r=100),
    hoverlabel=dict(
        bgcolor='white',
        bordercolor='#D5DBDB',
        font=dict(
            size=13,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),
    showlegend=False
)

fig.update_xaxes(
    categoryorder='array',
    categoryarray=offer_order,
    tickangle=0,
    showgrid=True,
    gridcolor='rgba(180,190,200,0.28)',
    gridwidth=1,

    zeroline=False,
    linecolor='rgba(0,0,0,0.25)',
    tickfont=dict(
        size=12,
        color='black',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    title_font=dict(
        size=13,
        color='black',
        family='Microsoft YaHei, SimHei, Arial'
    )
)
fig.add_shape(
    type="rect",
    xref="paper",
    yref="paper",
    x0=0,
    y0=0,
    x1=1,
    y1=1,
    line=dict(
        color="rgba(80, 90, 110, 0.55)",
        width=1.6
    ),
    fillcolor="rgba(0,0,0,0)",
    layer="above"
)


fig.update_yaxes(
    categoryorder='array',
    categoryarray=channel_order[::-1],
    showgrid=True,
    gridcolor='rgba(180,190,200,0.35)',
    zeroline=False,
    linecolor='rgba(0,0,0,0.25)',
    tickfont=dict(
        size=12,
        color='black',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    title_font=dict(
        size=13,
        color='black',
        family='Microsoft YaHei, SimHei, Arial'
    )
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 该气泡矩阵用于比较不同营销渠道与优惠方案组合下的客户响应情况。"
    "横轴表示优惠方案类型，纵轴表示营销渠道；气泡颜色表示响应率，颜色越偏蓝说明响应率越高，"
    "颜色越偏红说明响应率较低；气泡大小表示该组合覆盖的客户数量。"
    "通过该图可以快速识别哪些渠道与优惠方案组合更容易获得客户响应。"
)

# ======================================================
# 挽回效果 vs 成本收益象限图
# ======================================================
strong_divider()

st.subheader("🎯 渠道-Offer 挽回效果与成本收益象限图")

import numpy as np  # 确保引入 numpy 用于抖动计算

# 1. 定义并计算 quad_df (之前报错就是因为缺了这一段)
quad_df = df[df['contacted_int'] == 1].groupby(
    ['channel_label', 'offer_label']
).agg(
    customer_count=('customer_id', 'count'),
    response_rate=('responded_int', 'mean'),
    saved_rate=('saved_by_campaign', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    avg_retention_cost=('retention_cost', 'mean'),
    avg_clv=('estimated_clv', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index()

# 2. 计算百分比
quad_df['response_rate_pct'] = quad_df['response_rate'] * 100
quad_df['saved_rate_pct'] = quad_df['saved_rate'] * 100
quad_df['after_churn_rate_pct'] = quad_df['after_churn_rate'] * 100

# 3. 添加抖动 (Jitter) 防止左下角重叠
np.random.seed(42)
quad_df['x_jitter'] = quad_df['avg_retention_cost'] + np.random.uniform(-0.15, 0.15, len(quad_df))
quad_df['y_jitter'] = quad_df['saved_rate_pct'] + np.random.uniform(-0.5, 0.5, len(quad_df))

# 4. 计算中位线 (使用真实的原始数据计算)
x_mid = quad_df['avg_retention_cost'].median()
y_mid = quad_df['saved_rate_pct'].median()

# 5. 绘制散点图 (使用抖动后的坐标，但悬停显示真实数据)
fig = px.scatter(
    quad_df,
    x='x_jitter',
    y='y_jitter',
    size='avg_clv',
    color='avg_net_gain',
    color_continuous_scale='RdYlGn',
    symbol='channel_label',
    hover_name='offer_label',
    hover_data={
        'x_jitter': False,             # 隐藏假坐标
        'y_jitter': False,             # 隐藏假坐标
        'channel_label': True,
        'customer_count': True,
        'response_rate_pct': ':.1f',
        'after_churn_rate_pct': ':.1f',
        'avg_retention_cost': ':.2f',  # 悬停显示真实成本
        'saved_rate_pct': ':.1f',      # 悬停显示真实挽回率
        'avg_clv': ':.2f',
        'avg_net_gain': ':.2f'
    },
    labels={
        'x_jitter': '平均挽留成本 ($)',
        'y_jitter': '被挽回率 (%)',
        'avg_clv': '平均 CLV',
        'avg_net_gain': '平均净收益',
        'response_rate_pct': '响应率',
        'after_churn_rate_pct': '活动后流失率',
        'customer_count': '客户数量',
        'channel_label': '营销渠道'
    }
)

# 6. 添加辅助线
fig.add_vline(
    x=x_mid,
    line_dash='dash',
    line_color='gray',
    annotation_text='成本中位线',
    annotation_position='top'
)

fig.add_hline(
    y=y_mid,
    line_dash='dash',
    line_color='gray',
    annotation_text='挽回率中位线',
    annotation_position='right'
)

# 7. 更新样式 (去掉了导致重叠的 textposition)
fig.update_traces(
    marker=dict(
        line=dict(width=1, color='black'),
        opacity=0.85
    )
)

# 8. 更新布局 (把图例移到正上方)
fig.update_layout(
    **common_layout,
    height=600,
    xaxis_title='平均挽留成本 ($)',
    yaxis_title='被挽回率 (%)',
    coloraxis_colorbar=dict(title='平均净收益'),
    margin=dict(t=120, b=50, l=50, r=50),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        title=""
    )
)

fig = apply_chart_style(fig, "渠道与优惠方案挽回效果及成本收益象限图")

st.plotly_chart(fig, use_container_width=True)

# 后面保留你原来的 st.info 和 st.markdown 说明即可...

st.info(
    "💡 气泡越大表示该渠道-Offer 组合覆盖客户越多；颜色越亮表示响应率越高。"
    "这张图可以快速找出高覆盖、高响应的营销组合。"
)

# ======================================================
# Uplift 类型 × 渠道 × Offer 旭日图
# ======================================================
strong_divider()

st.subheader("☀️ Uplift 客户类型结构旭日图")

sunburst_df = df.copy()

fig = px.sunburst(
    sunburst_df,
    path=['uplift_label_cn', 'channel_label', 'offer_label'],
    values=None,
    color='uplift_label_cn',
    color_discrete_map={
        '自然留存型': '#2ECC71',
        '可被说服型': '#3498DB',
        '不应打扰型': '#E74C3C',
        '挽回无望型': '#8E44AD',
        '不确定型': '#95A5A6'
    },

    hover_data={
        'responded_int': True,
        'churn_after_campaign_int': True
    }
)

fig.update_traces(
    textinfo='label+percent parent',
    insidetextorientation='radial',
    hovertemplate=(
        '路径: %{label}<br>'
        '客户数量: %{value}<br>'
        '占父级比例: %{percentParent:.1%}<br>'
        '占总体比例: %{percentRoot:.1%}'
        '<extra></extra>'
    )
)

fig.update_layout(
    **common_layout,
    height=620,
    margin=dict(t=70, b=40, l=40, r=40)
)

fig = apply_chart_style(fig, "客户增益类型、渠道与优惠方案结构旭日图")

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 旭日图展示 Uplift 类型下的渠道和 Offer 结构，适合看不同客户类型被怎样触达。"
)

# ======================================================
# 挽回效果 vs 成本收益象限图
# ======================================================
strong_divider()

st.subheader("🎯 渠道-Offer 挽回效果与成本收益象限图")

quad_df = df[df['contacted_int'] == 1].groupby(
    ['channel_label', 'offer_label']
).agg(
    customer_count=('customer_id', 'count'),
    response_rate=('responded_int', 'mean'),
    saved_rate=('saved_by_campaign', 'mean'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    avg_retention_cost=('retention_cost', 'mean'),
    avg_clv=('estimated_clv', 'mean'),
    avg_net_gain=('net_gain_if_retained', 'mean')
).reset_index()

quad_df['response_rate_pct'] = quad_df['response_rate'] * 100
quad_df['saved_rate_pct'] = quad_df['saved_rate'] * 100
quad_df['after_churn_rate_pct'] = quad_df['after_churn_rate'] * 100
# 👇 从这里开始新增 👇
# 设定随机种子，保证每次刷新页面时，散开的形状是一样的，不会乱跳
np.random.seed(42)
# 给 X 轴（成本）加上 ±0.15 的微小偏移
quad_df['x_jitter'] = quad_df['avg_retention_cost'] + np.random.uniform(-0.15, 0.15, len(quad_df))
# 给 Y 轴（挽回率）加上 ±0.5 的微小偏移
quad_df['y_jitter'] = quad_df['saved_rate_pct'] + np.random.uniform(-0.5, 0.5, len(quad_df))
# 👆 新增结束 👆
x_mid = quad_df['avg_retention_cost'].median()
y_mid = quad_df['saved_rate_pct'].median()

fig = px.scatter(
    quad_df,
    x='avg_retention_cost',
    y='saved_rate_pct',
    size='avg_clv',
    color='avg_net_gain',
    color_continuous_scale=[
        [0.00, '#D9E2EC'],
        [0.25, '#A9C5D3'],
        [0.50, '#6BA6A8'],
        [0.75, '#2A6F73'],
        [1.00, '#124559']
    ],

    symbol='channel_label',
    hover_name='offer_label',
    hover_data={
        'channel_label': True,
        'customer_count': True,
        'response_rate_pct': ':.1f',
        'after_churn_rate_pct': ':.1f',
        'avg_retention_cost': ':.2f',
        'avg_clv': ':.2f',
        'avg_net_gain': ':.2f'
    },
    labels={
        'avg_retention_cost': '平均挽留成本 ($)',
        'saved_rate_pct': '被挽回率 (%)',
        'avg_clv': '平均 CLV',
        'avg_net_gain': '平均净收益',
        'response_rate_pct': '响应率',
        'after_churn_rate_pct': '活动后流失率',
        'customer_count': '客户数量'
    }
)

fig.add_vline(
    x=x_mid,
    line_dash='dash',
    line_color='gray',
    annotation_text='成本中位线',
    annotation_position='top'
)

fig.add_hline(
    y=y_mid,
    line_dash='dash',
    line_color='gray',
    annotation_text='挽回率中位线',
    annotation_position='right'
)

fig.update_traces(
    marker=dict(
        line=dict(width=1.6, color='rgba(255,255,255,0.95)'),
        opacity=0.90
    )
)


fig.update_layout(
    **common_layout,
    height=600,
    xaxis_title='平均挽留成本 ($)',
    yaxis_title='被挽回率 (%)',
    coloraxis_colorbar=dict(title='平均净收益'),
    margin=dict(t=80, b=50, l=50, r=50),

    # 👇 新增这部分：把形状图例移到图表上方，横向排列
    legend=dict(
        orientation="h",  # 横向排列 (horizontal)
        yanchor="bottom",  # 靠下对齐
        y=1.02,  # 放在图表顶部外侧 (1.0是顶端，1.02稍微往上一点)
        xanchor="center",  # 居中对齐
        x=0.5,  # 放在中间
        title=""  # 去掉难看的 'channel_label' 英文标题
    )
)

fig = apply_chart_style(fig, "渠道与优惠方案挽回效果及成本收益象限图")

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 左上角代表低成本、高挽回率，是最优营销组合；右下角代表高成本、低挽回率，应谨慎投放。"
)
st.markdown("""
<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>
    <small>📊 <b>数据血缘说明 (象限图):</b></small><br>
    <small>• <b>横轴 (平均挽留成本):</b> 取自 <code>business_costs.xlsx</code> 的 <code>retention_cost</code> 列</small><br>
    <small>• <b>纵轴 (被挽回率):</b> 基于 <code>campaign_uplift.xlsx</code> 计算 (当 <code>original_churn</code>=1 且 <code>churn_after_campaign</code>=0 时定义为挽回)</small><br>
    <small>• <b>气泡大小 (平均 CLV):</b> 取自 <code>business_costs.xlsx</code> 的 <code>estimated_clv</code> 列</small><br>
    <small>• <b>气泡颜色 (平均净收益):</b> 取自 <code>business_costs.xlsx</code> 的 <code>net_gain_if_retained</code> 列</small><br>
    <small>• <b>分组标签:</b> 取自 <code>campaign_uplift.xlsx</code> 的 <code>campaign_channel</code> 和 <code>offer_type</code> 列</small>
</div>
""", unsafe_allow_html=True)

# ======================================================
# 客户价值分层 × Uplift 类型热力图
# ======================================================
strong_divider()

st.subheader("🔥 客户价值分层 × Uplift 类型活动后流失率")

value_uplift = df.groupby(
    ['value_label', 'uplift_label_cn']
).agg(
    customer_count=('customer_id', 'count'),
    after_churn_rate=('churn_after_campaign_int', 'mean'),
    response_rate=('responded_int', 'mean'),
    avg_clv=('estimated_clv', 'mean')
).reset_index()

value_uplift['after_churn_rate_pct'] = value_uplift['after_churn_rate'] * 100
value_uplift['response_rate_pct'] = value_uplift['response_rate'] * 100

fig = px.density_heatmap(
    value_uplift,
    x='uplift_label_cn',
    y='value_label',
    z='after_churn_rate_pct',
    text_auto='.1f',
    color_continuous_scale=['#27AE60', '#F1C40F', '#E74C3C'],
    hover_data={
        'customer_count': True,
        'response_rate_pct': ':.1f',
        'avg_clv': ':.2f'
    },
    labels={
        'uplift_label_cn': '客户增益类型',
        'value_label': '客户价值分层',
        'after_churn_rate_pct': '活动后流失率 (%)',
        'customer_count': '客户数量',
        'response_rate_pct': '响应率',
        'avg_clv': '平均 CLV'
    }
)

fig.update_layout(
    **common_layout,
    height=500,
    xaxis_title='客户增益类型',
    yaxis_title='客户价值分层',
    coloraxis_colorbar=dict(title='活动后流失率 (%)'),
    margin=dict(t=70, b=80, l=80, r=40)
)

fig = apply_chart_style(fig, "客户价值分层与客户增益类型活动后流失率热力图")


st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 这张图用于识别哪些价值层级的客户在不同 Uplift 类型下仍然存在较高流失风险。"
)
st.caption(
    "📂 字段来源：value_label ← full_customers.xlsx: customer_value_segment；"
    "uplift_label_cn ← campaign_uplift.xlsx: uplift_label；"
    "after_churn_rate ← campaign_uplift.xlsx: churn_after_campaign；"
    "avg_clv ← business_costs.xlsx: estimated_clv。"
)

