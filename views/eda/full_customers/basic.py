# views/eda/full_customers/basic.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_full_customers

st.title("👥 基础画像与流失概览")
st.markdown(
    "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
    unsafe_allow_html=True
)


# ======================================================
# 数据加载与预处理
# ======================================================
df = load_full_customers()
df['churn_int'] = df['churn'].astype(int)
df['churn_label'] = df['churn_int'].map({0: '留存', 1: '流失'})

# 图表通用布局配置（黑色字体）
common_layout = dict(
    font=dict(color='black', size=12),
    title_font=dict(color='black', size=14),
    legend_font=dict(color='black'),
    paper_bgcolor='white',
    plot_bgcolor='white',
    title=None,  # 防止显示 undefined
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
# 📊 核心 KPI 指标卡
# ======================================================
st.subheader("📊 核心业务指标")

col1, col2, col3, col4 = st.columns(4)

total_users = len(df)
churn_rate = df['churn_int'].mean() * 100
intl_plan_rate = df['has_international_plan'].mean() * 100
voicemail_rate = df['has_voice_mail_plan'].mean() * 100

col1.metric("总客户数", f"{total_users:,}")
col2.metric("整体流失率", f"{churn_rate:.1f}%")
col3.metric("国际套餐开通率", f"{intl_plan_rate:.1f}%")
col4.metric("语音信箱开通率", f"{voicemail_rate:.1f}%")

col5, col6, col7, col8 = st.columns(4)

avg_tenure = df['account_length'].mean()
avg_charges = df['total_charges'].mean()
avg_calls = df['customer_service_calls'].mean()
high_risk_rate = (df['rule_based_churn_risk_level'] != 'low').mean() * 100

col5.metric("平均在网时长", f"{avg_tenure:.0f} 天")
col6.metric("平均总费用", f"${avg_charges:.1f}")
col7.metric("平均客服呼叫", f"{avg_calls:.1f} 次")
col8.metric("中高风险客户占比", f"{high_risk_rate:.1f}%")

strong_divider()

# ======================================================
# 📈 流失分布分析
# ======================================================
st.subheader("📈 流失分布分析")

# 图1: 客户流失占比
st.markdown("**客户流失占比**")
churn_counts = df['churn_int'].value_counts().reset_index()
churn_counts.columns = ['churn', 'count']
churn_counts['label'] = churn_counts['churn'].map({0: '留存', 1: '流失'})

fig_pie = px.pie(
    churn_counts, names='label', values='count',
    color='label',
    color_discrete_map={'留存': '#3498DB', '流失': '#E74C3C'},
    hole=0.45
)
fig_pie.update_traces(
    textposition='inside',
    textinfo='percent+label',
    textfont=dict(color='white', size=14)
)
fig_pie.update_layout(**common_layout, showlegend=False, margin=dict(t=30, b=30, l=30, r=30), height=400)
st.plotly_chart(fig_pie, use_container_width=True)

light_divider()

# 图2: 不同套餐组合的流失率
st.markdown("**不同套餐组合的流失率**")
df['plan_combo'] = df.apply(
    lambda x: f"国际{'✓' if x['has_international_plan'] else '✗'} / 语音{'✓' if x['has_voice_mail_plan'] else '✗'}",
    axis=1
)
combo_churn = df.groupby('plan_combo')['churn_int'].agg(['count', 'mean']).reset_index()
combo_churn['churn_rate'] = combo_churn['mean'] * 100
combo_churn = combo_churn.sort_values('churn_rate', ascending=True)

fig_combo = px.bar(
    combo_churn, x='churn_rate', y='plan_combo', orientation='h',
    text=combo_churn['churn_rate'].apply(lambda x: f'{x:.1f}%'),
    color='churn_rate',
    color_continuous_scale=['#27AE60', '#F1C40F', '#E74C3C'],
)
fig_combo.update_traces(textposition='outside', textfont=dict(color='black', size=12))
fig_combo.update_layout(
    **common_layout,
    xaxis_title='流失率 (%)',
    yaxis_title='套餐组合',
    coloraxis_showscale=False,
    margin=dict(t=30, b=30, l=30, r=80),
    height=350
)
fig_combo.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_combo.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_combo, use_container_width=True)

strong_divider()

# ======================================================
# 🏷️ 客户分群分析
# ======================================================
st.subheader("🏷️ 客户分群分析")

# 图3: 客户价值分层的流失率
st.markdown("**客户价值分层的流失率**")

value_order = ['high_value', 'medium_value', 'low_value']
value_labels = {'high_value': '高价值', 'medium_value': '中价值', 'low_value': '低价值'}

val_stats = df.groupby('customer_value_segment').agg(
    count=('churn_int', 'count'),
    churn_rate=('churn_int', 'mean')
).reset_index()
val_stats['churn_rate'] = val_stats['churn_rate'] * 100
val_stats['label'] = val_stats['customer_value_segment'].map(value_labels)
val_stats['customer_value_segment'] = pd.Categorical(
    val_stats['customer_value_segment'], categories=value_order, ordered=True
)
val_stats = val_stats.sort_values('customer_value_segment')

fig_val = px.bar(
    val_stats, x='label', y='churn_rate',
    text=val_stats['churn_rate'].apply(lambda x: f'{x:.1f}%'),
    color='label',
    color_discrete_map={'高价值': '#27AE60', '中价值': '#F1C40F', '低价值': '#E74C3C'}
)
fig_val.update_traces(textposition='outside', textfont=dict(color='black', size=12))
fig_val.update_layout(
    **common_layout,
    xaxis_title='客户价值分层',
    yaxis_title='流失率 (%)',
    showlegend=False,
    margin=dict(t=30, b=30, l=30, r=30),
    height=400
)
fig_val.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_val.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_val, use_container_width=True)

light_divider()

# 图4: 使用强度分层的流失率
st.markdown("**使用强度分层的流失率**")

usage_order = ['high_usage', 'medium_usage', 'low_usage']
usage_labels = {'high_usage': '高使用', 'medium_usage': '中使用', 'low_usage': '低使用'}

usage_stats = df.groupby('usage_intensity').agg(
    count=('churn_int', 'count'),
    churn_rate=('churn_int', 'mean')
).reset_index()
usage_stats['churn_rate'] = usage_stats['churn_rate'] * 100
usage_stats['label'] = usage_stats['usage_intensity'].map(usage_labels)
usage_stats['usage_intensity'] = pd.Categorical(
    usage_stats['usage_intensity'], categories=usage_order, ordered=True
)
usage_stats = usage_stats.sort_values('usage_intensity')

fig_usage = px.bar(
    usage_stats, x='label', y='churn_rate',
    text=usage_stats['churn_rate'].apply(lambda x: f'{x:.1f}%'),
    color='label',
    color_discrete_map={'高使用': '#3498DB', '中使用': '#9B59B6', '低使用': '#95A5A6'}
)
fig_usage.update_traces(textposition='outside', textfont=dict(color='black', size=12))
fig_usage.update_layout(
    **common_layout,
    xaxis_title='使用强度',
    yaxis_title='流失率 (%)',
    showlegend=False,
    margin=dict(t=30, b=30, l=30, r=30),
    height=400
)
fig_usage.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_usage.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_usage, use_container_width=True)

strong_divider()






# ======================================================
# ⚠️ 风险等级分布
# ======================================================
st.subheader("⚠️ 规则风险评分分析")

risk_order = {'low': '低风险', 'medium': '中风险', 'high': '高风险'}

# 图7: 规则风险等级分布
st.markdown("**规则风险等级分布**")
risk_counts = df['rule_based_churn_risk_level'].value_counts().reset_index()
risk_counts.columns = ['level', 'count']
risk_counts['label'] = risk_counts['level'].map(risk_order)

fig_risk_dist = px.pie(
    risk_counts, names='label', values='count',
    color='label',
    color_discrete_map={'低风险': '#27AE60', '中风险': '#F1C40F', '高风险': '#E74C3C'}
)
fig_risk_dist.update_traces(
    textposition='inside',
    textinfo='percent+label',
    textfont=dict(color='white', size=13)
)
fig_risk_dist.update_layout(**common_layout, showlegend=False, margin=dict(t=30, b=30, l=30, r=30), height=400)
st.plotly_chart(fig_risk_dist, use_container_width=True)

light_divider()




# 图8: 规则风险等级 vs 实际流失率
st.markdown("**规则风险等级 vs 实际流失率**")
risk_churn = df.groupby('rule_based_churn_risk_level')['churn_int'].agg(['count', 'mean']).reset_index()
risk_churn['churn_rate'] = risk_churn['mean'] * 100
risk_churn['label'] = risk_churn['rule_based_churn_risk_level'].map(risk_order)
risk_churn['rule_based_churn_risk_level'] = pd.Categorical(
    risk_churn['rule_based_churn_risk_level'], categories=['low', 'medium', 'high'], ordered=True
)
risk_churn = risk_churn.sort_values('rule_based_churn_risk_level')

fig_risk_churn = px.bar(
    risk_churn, x='label', y='churn_rate',
    text=risk_churn['churn_rate'].apply(lambda x: f'{x:.1f}%'),
    color='label',
    color_discrete_map={'低风险': '#27AE60', '中风险': '#F1C40F', '高风险': '#E74C3C'}
)
fig_risk_churn.update_traces(textposition='outside', textfont=dict(color='black', size=12))
fig_risk_churn.update_layout(
    **common_layout,
    xaxis_title='规则风险等级',
    yaxis_title='实际流失率 (%)',
    showlegend=False,
    margin=dict(t=30, b=30, l=30, r=30),
    height=400
)
fig_risk_churn.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_risk_churn.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_risk_churn, use_container_width=True)

strong_divider()




# 图9：Sankey 桑基图 - 客户流转路径分析
st.subheader("🔄 客户流转路径分析 (Sankey)")

# 强制类型转换，避免 KeyError
df['churn'] = df['churn'].astype(int)

# 构建 Sankey 数据
sankey_data = df.groupby(['customer_value_segment', 'usage_intensity', 'churn']).size().reset_index(name='count')

# 创建节点映射
value_nodes = {'high_value': 0, 'medium_value': 1, 'low_value': 2}
usage_nodes = {'high_usage': 3, 'medium_usage': 4, 'low_usage': 5}
churn_nodes = {0: 6, 1: 7}

# 计算每个节点的总流量，用于在标签中显示数量
node_totals = [0] * 8
for _, row in sankey_data.iterrows():
    node_totals[value_nodes[row['customer_value_segment']]] += row['count']
    node_totals[usage_nodes[row['usage_intensity']]] += row['count']
    node_totals[churn_nodes[row['churn']]] += row['count']

# 节点标签（带数量）
labels = [
    f'高价值<br>({node_totals[0]:,})',
    f'中价值<br>({node_totals[1]:,})',
    f'低价值<br>({node_totals[2]:,})',
    f'高使用<br>({node_totals[3]:,})',
    f'中使用<br>({node_totals[4]:,})',
    f'低使用<br>({node_totals[5]:,})',
    f'留存<br>({node_totals[6]:,})',
    f'流失<br>({node_totals[7]:,})',
]

sources, targets, values, colors = [], [], [], []

# 价值层 → 使用强度（蓝色）
for _, row in sankey_data.iterrows():
    sources.append(value_nodes[row['customer_value_segment']])
    targets.append(usage_nodes[row['usage_intensity']])
    values.append(row['count'])
    colors.append('rgba(52, 152, 219, 0.4)')

# 使用强度 → 流失状态（红/绿）
for _, row in sankey_data.iterrows():
    sources.append(usage_nodes[row['usage_intensity']])
    is_churned = (row['churn'] == 1)
    targets.append(churn_nodes[row['churn']])
    values.append(row['count'])
    color = 'rgba(231, 76, 60, 0.5)' if is_churned else 'rgba(39, 174, 96, 0.5)'
    colors.append(color)

# 固定节点 x/y 位置，让布局更整齐
node_x = [0.01, 0.01, 0.01, 0.5, 0.5, 0.5, 0.99, 0.99]
node_y = [0.1, 0.5, 0.9, 0.1, 0.5, 0.9, 0.3, 0.8]

fig_sankey = go.Figure(data=[go.Sankey(
    arrangement='snap',  # 固定排列方式
    node=dict(
        pad=25,
        thickness=25,
        line=dict(color='black', width=1),
        label=labels,
        color=['#27AE60', '#F1C40F', '#E74C3C',
               '#3498DB', '#9B59B6', '#95A5A6',
               '#27AE60', '#E74C3C'],
        x=node_x,
        y=node_y,
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color=colors,
    ),
    textfont=dict(
        family='Microsoft YaHei, SimHei, Arial',  # 关键：中文字体
        size=15,
        color='black',
    )
)])

fig_sankey.update_layout(
    title=dict(
        text='<b>客户价值 → 使用强度 → 流失状态 流转路径</b>',
        font=dict(family='Microsoft YaHei, SimHei', size=18, color='#2C3E50'),
        x=0.5,
        xanchor='center',
    ),
    font=dict(family='Microsoft YaHei, SimHei, Arial', size=14, color='black'),
    height=650,
    margin=dict(t=80, b=40, l=80, r=80),
    paper_bgcolor='white',
    plot_bgcolor='white',
hoverlabel=dict(
        bgcolor='white',
        font=dict(family='Microsoft YaHei, SimHei, Arial', size=14, color='black'),
        bordercolor='black',
    ),
)

st.plotly_chart(fig_sankey, use_container_width=True)

# 添加图例说明
st.caption("💡 **解读说明**：左侧为客户价值分层 → 中间为使用强度 → 右侧为最终流失状态。"
           "🟢 绿色流线表示留存客户，🔴 红色流线表示流失客户。流线越粗代表客户数量越多。")








strong_divider()
#图10：Sunburst 旭日图import streamlit as st
# ======================================================
# 图10：Sunburst 旭日图
# ======================================================
st.subheader("☀️ 客户分层深度钻取分析")
st.markdown("**Top 15 州 -> 价值分层 -> 流失状态 穿透视图**")
st.info("💡 本图仅展示客户数量排名 Top 15 的州。点击图中的各个扇区，可以向下钻取查看详细占比。")

# 1. 标签映射
value_label_map = {
    'high_value': '高价值',
    'medium_value': '中价值',
    'low_value': '低价值'
}

churn_label_map = {
    0: '留存',
    1: '流失'
}

df['value_label'] = df['customer_value_segment'].map(value_label_map)
df['churn_label'] = df['churn_int'].map(churn_label_map)

# 2. 固定顺序
value_order = ['高价值', '中价值', '低价值']
churn_order = ['留存', '流失']

# 3. 筛选 Top 15 个州
top_states = df['state'].value_counts().head(15).index.tolist()
df_sun = df[df['state'].isin(top_states)].copy()

# 州顺序：客户数量从多到少
state_order = df_sun['state'].value_counts().index.tolist()

# 4. 聚合统计
sun_counts = (
    df_sun
    .groupby(['state', 'value_label', 'churn_label'])
    .size()
    .reset_index(name='count')
)

# 5. 手动构建 Sunburst 节点，固定顺序
ids = []
labels = []
parents = []
values = []
colors = []

root_label = '客户数量 Top 15 州'

# 颜色配置
root_color = '#c1c6fc'
state_color = '#95d0fc'

value_color_map = {
    '高价值': '#2E7D32',
    '中价值': '#F9A825',
    '低价值': '#C62828'
}

churn_color_map = {
    ('高价值', '留存'): '#66BB6A',
    ('高价值', '流失'): '#A5D6A7',

    ('中价值', '留存'): '#F9A825',
    ('中价值', '流失'): '#FFE082',

    ('低价值', '留存'): '#EF9A9A',
    ('低价值', '流失'): '#C62828',
}

# 根节点
total_count = len(df_sun)

ids.append('root')
labels.append(root_label)
parents.append('')
values.append(total_count)
colors.append(root_color)

# 州节点 -> 价值节点 -> 流失节点
for state in state_order:
    state_df = sun_counts[sun_counts['state'] == state]
    state_total = state_df['count'].sum()

    state_id = f'state/{state}'

    ids.append(state_id)
    labels.append(state)
    parents.append('root')
    values.append(state_total)
    colors.append(state_color)

    # 固定每个州下面都是：高价值 -> 中价值 -> 低价值
    for value_label in value_order:
        value_df = state_df[state_df['value_label'] == value_label]
        value_total = value_df['count'].sum()

        if value_total == 0:
            continue

        value_id = f'value/{state}/{value_label}'

        ids.append(value_id)
        labels.append(value_label)
        parents.append(state_id)
        values.append(value_total)
        colors.append(value_color_map[value_label])

        # 固定每个价值层下面都是：留存 -> 流失
        for churn_label in churn_order:
            churn_df = value_df[value_df['churn_label'] == churn_label]
            churn_total = churn_df['count'].sum()

            if churn_total == 0:
                continue

            churn_id = f'churn/{state}/{value_label}/{churn_label}'

            ids.append(churn_id)
            labels.append(churn_label)
            parents.append(value_id)
            values.append(churn_total)
            colors.append(churn_color_map[(value_label, churn_label)])

# 6. 构建旭日图
fig_sun = go.Figure(go.Sunburst(
    ids=ids,
    labels=labels,
    parents=parents,
    values=values,
    branchvalues='total',
    sort=False,  # 关键：关闭自动排序，按照我们添加节点的顺序显示
    maxdepth=4,
    marker=dict(
        colors=colors,
        line=dict(color='white', width=1.5)
    ),
    hovertemplate=(
        '<b>层级:</b> %{label}<br>'
        '<b>客户数:</b> %{value}<br>'
        '<b>占父级比例:</b> %{percentParent:.1%}'
        '<extra></extra>'
    )
))

# 7. 样式美化
fig_sun.update_layout(
    height=720,
    margin=dict(t=60, b=20, l=20, r=20),
    font=dict(
        family='Microsoft YaHei, SimHei, Arial',
        color='black',
        size=14
    ),
    paper_bgcolor='white',
    plot_bgcolor='white',
    title=dict(
        text='客户数量 Top 15 州客户分层与流失状态旭日图',
        x=0.5,
        xanchor='center',
        font=dict(size=18, color='#2C3E50')
    )
)

# 8. 渲染图表
st.plotly_chart(fig_sun, use_container_width=True)

# 9. 补充说明
with st.expander("📊 如何解读此图？"):
    st.write("""
    - **本图范围**：仅展示客户数量排名 **Top 15 的州**，用于避免州数量过多导致图形拥挤。
    - **中心圆环**：表示“客户数量 Top 15 州”这个总体范围。
    - **第二层圆环**：代表 Top 15 州中的各个州，面积越大说明该州客户数量越多。
    - **第三层圆环**：代表该州内的客户价值分层，包括高价值、中价值、低价值。
    - **最外层圆环**：代表最终流失状态。
    - **颜色含义**：
        - 绿色系：高价值客户；
        - 黄色系：中价值客户；
        - 红色系：低价值客户；
        - 同一价值层级下，留存和流失用深浅颜色区分。
    - **顺序说明**：每个州下面的价值层级顺序固定为：高价值 → 中价值 → 低价值；流失状态顺序固定为：留存 → 流失。
    - **交互**：点击某个州，例如“CA”，图表会自动放大展示该州内部的客户价值与流失分布。
    """)


strong_divider()



# ======================================================
# 🪜 客户流失风险漏斗
# ======================================================
strong_divider()

st.subheader("🪜 客户流失风险漏斗")
st.caption("从全体客户中逐层筛选，定位最值得关注的高价值流失风险客户。")

# 防止风险分数存在空值
df['rule_based_churn_risk_score'] = df['rule_based_churn_risk_score'].fillna(0)

# 1. 全体客户
total_customers = len(df)

# 2. 触发风险规则客户：风险分数 > 0
risk_customers_df = df[df['rule_based_churn_risk_score'] > 0]
risk_customers = len(risk_customers_df)

# 3. 中高风险客户：在触发风险规则客户中继续筛选
medium_high_risk_df = risk_customers_df[
    risk_customers_df['rule_based_churn_risk_level'].isin(['medium', 'high'])
]
medium_high_risk = len(medium_high_risk_df)

# 4. 中高风险且实际流失客户
medium_high_churned_df = medium_high_risk_df[
    medium_high_risk_df['churn_int'] == 1
]
medium_high_churned = len(medium_high_churned_df)

# 5. 高价值 + 中高风险 + 实际流失客户
high_value_medium_high_churned_df = medium_high_churned_df[
    medium_high_churned_df['customer_value_segment'] == 'high_value'
]
high_value_medium_high_churned = len(high_value_medium_high_churned_df)

# 漏斗数据
funnel_y = [
    "全体客户",
    "触发风险规则",
    "中高风险",
    "中高风险已流失",
    "高价值已流失"
]

funnel_x = [
    total_customers,
    risk_customers,
    medium_high_risk,
    medium_high_churned,
    high_value_medium_high_churned
]

# 每层占总客户比例
percent_total = [
    x / total_customers * 100 if total_customers > 0 else 0
    for x in funnel_x
]

# 自定义显示文字
funnel_text = [
    f"{count:,} 人<br>{pct:.1f}%"
    for count, pct in zip(funnel_x, percent_total)
]

# hover 解释文字
hover_text = [
    "数据集中全部客户",
    "风险分数 > 0，即至少触发一条风险规则的客户",
    "风险等级为 medium 或 high 的客户",
    "中高风险客户中，实际已经流失的客户",
    "中高风险且已流失客户中，属于高价值客户的部分"
]
fig_funnel = go.Figure(go.Funnel(
    y=funnel_y,
    x=funnel_x,
    text=funnel_text,
    textinfo="text",

    # 【关键修改 1】用列表的形式，指定前4个在内部(inside)，最后1个在外部(outside)
    textposition=["inside", "inside", "inside", "inside", "outside"],

    # 【关键修改 2】分别设置内部和外部的字体颜色
    insidetextfont=dict(
        family="Microsoft YaHei, SimHei, Arial",
        size=16,
        color="white"  # 内部文字保持纯白
    ),
    outsidetextfont=dict(
        family="Microsoft YaHei, SimHei, Arial",
        size=16,
        color="#7F1D1D"  # 外部文字改成深血红色（与最后一块图形颜色呼应，高级感拉满）
    ),

    hovertext=hover_text,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "客户数：%{x:,} 人<br>"
        "%{hovertext}"
        "<extra></extra>"
    ),
    marker=dict(
        color=[
            "#1E3A8A",  # 深邃蓝
            "#3B82F6",  # 科技蓝
            "#F59E0B",  # 质感黄
            "#EF4444",  # 珊瑚红
            "#7F1D1D"  # 深血红
        ],
        line=dict(
            color="rgba(255, 255, 255, 0.9)",
            width=1.5
        )
    ),
    connector=dict(
        fillcolor="rgba(148, 163, 184, 0.5)", # 👈 修改这里：加深了
        line=dict(width=0)
    ),
    opacity=1.0
))

fig_funnel.update_layout(
    title=dict(
        text="<b>客户流失风险分层漏斗图</b>",
        x=0.5,
        xanchor="center",
        font=dict(
            family="Microsoft YaHei, SimHei, Arial",
            size=22,
            color="#0F172A"  # 标题用极深灰替代纯黑，更柔和高级
        )
    ),
    height=520,  # 【关键点】高度稍微压扁一点，漏斗的梯形斜率会更好看、更稳重
    margin=dict(t=80, b=40, l=160, r=60),
    paper_bgcolor="white",
    plot_bgcolor="white",
    yaxis=dict(
        tickfont=dict(
            family="Microsoft YaHei, SimHei, Arial",
            size=15,
            color="#334155"  # 左侧文字用高级灰，突出右侧漏斗的色彩
        ),
        title=None
    )
)


st.plotly_chart(fig_funnel, use_container_width=True)

st.info(
    "💡 本漏斗表示逐层筛选过程：先从全体客户中筛选出触发风险规则的客户，"
    "再筛出中高风险客户，然后观察其中已经实际流失的客户，最后定位到高价值且已流失的重点客户。"
)
