# views/eda/full_customers/risk.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_full_customers
import pandas as pd
import numpy as np
st.title("📈 风险分析")
st.markdown("---")

# ======================================================
# 数据加载
# ======================================================
df = load_full_customers()
df['churn_int'] = df['churn'].astype(int)
df['churn_label'] = df['churn_int'].map({0: '留存', 1: '流失'})

# 图表通用布局
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
# 高级版：留存 vs 流失客户画像雷达图
# ======================================================
strong_divider()

st.subheader("🕸️ 留存 vs 流失客户画像雷达图")

radar_df = df.copy()

# ------------------------------
# 1. 基础标签处理
# ------------------------------
if 'churn_label' not in radar_df.columns:
    radar_df['churn_int'] = radar_df['churn'].astype(int)
    radar_df['churn_label'] = radar_df['churn_int'].map({0: '留存', 1: '流失'})

# ------------------------------
# 2. 构造总通话时长
# ------------------------------
minute_cols = [
    col for col in [
        'total_day_minutes',
        'total_eve_minutes',
        'total_night_minutes',
        'total_intl_minutes'
    ]
    if col in radar_df.columns
]

if len(minute_cols) > 0:
    radar_df['total_call_minutes'] = radar_df[minute_cols].sum(axis=1)
else:
    radar_df['total_call_minutes'] = np.nan

# ------------------------------
# 3. 构造总费用
# ------------------------------
charge_cols = [
    col for col in [
        'total_day_charge',
        'total_eve_charge',
        'total_night_charge',
        'total_intl_charge'
    ]
    if col in radar_df.columns
]

if len(charge_cols) > 0:
    radar_df['total_charge'] = radar_df[charge_cols].sum(axis=1)
else:
    radar_df['total_charge'] = np.nan

# ------------------------------
# 4. 构造每分钟费用
# ------------------------------
radar_df['avg_charge_per_minute'] = (
    radar_df['total_charge'] / radar_df['total_call_minutes'].replace(0, np.nan)
)

# ------------------------------
# 5. 客服呼叫字段兼容
# ------------------------------
if 'customer_service_calls' not in radar_df.columns:
    if 'number_customer_service_calls' in radar_df.columns:
        radar_df['customer_service_calls'] = radar_df['number_customer_service_calls']
    else:
        radar_df['customer_service_calls'] = np.nan

# ------------------------------
# 6. 雷达图指标配置
# ------------------------------
radar_features = {
    '总费用': 'total_charge',
    '总通话时长': 'total_call_minutes',
    '客服呼叫': 'customer_service_calls',
    '国际通话时长': 'total_intl_minutes',
    '日间费用': 'total_day_charge',
    '每分钟费用': 'avg_charge_per_minute'
}

# 只保留实际存在的字段
radar_features = {
    label: col for label, col in radar_features.items()
    if col in radar_df.columns and radar_df[col].notna().sum() > 0
}

# ------------------------------
# 7. 计算每组均值
# ------------------------------
profile_mean = radar_df.groupby('churn_label')[
    list(radar_features.values())
].mean()

# ------------------------------
# 8. 转成 percentile score，避免 0/1 大饼
#    含义：该组均值在全体客户中的位置，越高说明该指标越突出
# ------------------------------
def percentile_score(series, value):
    series = series.dropna()
    if len(series) == 0:
        return np.nan
    return (series <= value).mean() * 100

radar_plot_data = []

for label, col in radar_features.items():
    for group in ['留存', '流失']:
        if group in profile_mean.index:
            group_mean_value = profile_mean.loc[group, col]
            score = percentile_score(radar_df[col], group_mean_value)

            radar_plot_data.append({
                '客户类型': group,
                '指标': label,
                '画像分数': score,
                '原始均值': group_mean_value
            })

radar_plot_df = pd.DataFrame(radar_plot_data)

# 闭合雷达图
categories = list(radar_features.keys())

fig = go.Figure()
# ==============================
# 9. 高级版雷达图绘制
# ==============================

fig = go.Figure()

# 高级蓝 + 高级红
color_map = {
    '留存': '#165DFF',
    '流失': '#F53F3F'
}

fill_map = {
    '留存': 'rgba(22, 93, 255, 0.18)',
    '流失': 'rgba(245, 63, 63, 0.20)'
}

for group in ['留存', '流失']:
    temp = radar_plot_df[radar_plot_df['客户类型'] == group].copy()

    # 保证顺序
    temp['指标'] = pd.Categorical(temp['指标'], categories=categories, ordered=True)
    temp = temp.sort_values('指标')

    r_values = temp['画像分数'].tolist()
    theta_values = temp['指标'].tolist()

    # 闭合雷达图
    r_values += r_values[:1]
    theta_values += theta_values[:1]

    fig.add_trace(go.Scatterpolar(
        r=r_values,
        theta=theta_values,
        mode='lines+markers',
        name=group,

        # 线条高级化
        line=dict(
            color=color_map[group],
            width=3.5
        ),

        # 点样式高级化
        marker=dict(
            size=9,
            color=color_map[group],
            symbol='circle',
            line=dict(
                color='black',
                width=1.2
            )
        ),

        # 半透明填充
        fill='toself',
        fillcolor=fill_map[group],

        hovertemplate=(
            '<b>%{theta}</b><br>'
            f'客户类型：{group}<br>'
            '画像分数：%{r:.1f}<br>'
            '<extra></extra>'
        )
    ))

fig.update_layout(
    height=650,
    paper_bgcolor='white',
    plot_bgcolor='white',

    # 全局字体：全部黑色
    font=dict(
        color='black',
        size=14,
        family='Microsoft YaHei'
    ),

    title=dict(
        text='<b>留存 vs 流失客户行为特征雷达图</b>',
        x=0.5,
        xanchor='center',
        y=0.96,
        font=dict(
            color='black',
            size=20,
            family='Microsoft YaHei'
        )
    ),

    polar=dict(
        bgcolor='white',

        radialaxis=dict(
            visible=True,
            range=[0, 100],
            tickvals=[20, 40, 60, 80, 100],
            ticktext=['20', '40', '60', '80', '100'],

            # 半径刻度文字：黑色
            tickfont=dict(
                size=11,
                color='black',
                family='Microsoft YaHei'
            ),

            # 网格线更淡，更高级
            gridcolor='rgba(0, 0, 0, 0.12)',
            gridwidth=1,

            linecolor='rgba(0, 0, 0, 0.35)',
            linewidth=1,

            showline=True
        ),

        angularaxis=dict(
            direction='clockwise',
            rotation=90,

            # 外圈指标文字：黑色
            tickfont=dict(
                size=14,
                color='black',
                family='Microsoft YaHei'
            ),

            gridcolor='rgba(0, 0, 0, 0.10)',
            gridwidth=1,

            linecolor='rgba(0, 0, 0, 0.35)',
            linewidth=1,

            showline=True
        )
    ),

    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.06,
        xanchor='center',
        x=0.5,

        font=dict(
            size=14,
            color='black',
            family='Microsoft YaHei'
        ),

        bgcolor='rgba(255,255,255,0)',
        bordercolor='rgba(0,0,0,0)'
    ),

    hoverlabel=dict(
        bgcolor='white',
        bordercolor='black',
        font=dict(
            color='black',
            size=13,
            family='Microsoft YaHei'
        )
    ),

    margin=dict(
        t=110,
        b=60,
        l=90,
        r=90
    )
)

st.plotly_chart(fig, use_container_width=True)


st.info(
    "💡 这里的画像分数不是简单 0/1 归一化，而是该组均值在全体客户中的百分位位置。"
    "分数越高，说明该客户群体在该指标上越突出，因此比普通 min-max 雷达图更有解释力。"
)


strong_divider()


#高费用 + 高风险 = 重点挽留（高价值客户挽留优先级四象限图）
st.subheader("🎯 高价值客户挽留优先级四象限图")

priority_df = df.copy()

risk_median = priority_df['rule_based_churn_risk_score'].median()
charge_median = priority_df['total_charges'].median()

def assign_priority(row):
    if row['rule_based_churn_risk_score'] >= risk_median and row['total_charges'] >= charge_median:
        return '重点挽留'
    elif row['rule_based_churn_risk_score'] >= risk_median and row['total_charges'] < charge_median:
        return '风险观察'
    elif row['rule_based_churn_risk_score'] < risk_median and row['total_charges'] >= charge_median:
        return '高价值维护'
    else:
        return '普通客户'

priority_df['priority_group'] = priority_df.apply(assign_priority, axis=1)

fig = px.scatter(
    priority_df,
    x='rule_based_churn_risk_score',
    y='total_charges',
    size='customer_service_calls',
    color='priority_group',
    symbol='churn_label',
    hover_data={
        'customer_id': True,
        'state': True,
        'customer_service_calls': True,
        'total_minutes': ':.1f',
        'total_charges': ':.1f',
        'rule_based_churn_risk_score': True,
        'churn_label': True
    },
    color_discrete_map={
        '重点挽留': '#E74C3C',
        '风险观察': '#F39C12',
        '高价值维护': '#3498DB',
        '普通客户': '#95A5A6'
    },
    labels={
        'rule_based_churn_risk_score': '规则风险分数',
        'total_charges': '总费用',
        'priority_group': '客户优先级',
        'churn_label': '客户状态'
    }
)

fig.add_vline(
    x=risk_median,
    line_width=2,
    line_dash="dash",
    line_color="#7F8C8D"
)

fig.add_hline(
    y=charge_median,
    line_width=2,
    line_dash="dash",
    line_color="#7F8C8D"
)

fig.update_layout(
    **common_layout,
    height=620,
    legend_title='客户优先级',
    margin=dict(t=40, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

target_count = priority_df[
    (priority_df['priority_group'] == '重点挽留') &
    (priority_df['churn_int'] == 0)
].shape[0]

st.info(f"💡 当前仍未流失、但处于“重点挽留”象限的客户共有 {target_count} 人，建议优先运营干预。")





#国际套餐 -> 语音套餐 -> 使用强度 -> 客户价值 -> 风险等级 -> 是否流失
# Parallel Categories 客户路径图
strong_divider()

st.subheader("🧬 客户路径平行类别图")

path_df = df.copy()

path_df['国际套餐'] = path_df['has_international_plan'].map({0: '无国际套餐', 1: '有国际套餐'})
path_df['语音套餐'] = path_df['has_voice_mail_plan'].map({0: '无语音套餐', 1: '有语音套餐'})

path_df['使用强度'] = path_df['usage_intensity'].map({
    'high_usage': '高使用',
    'medium_usage': '中使用',
    'low_usage': '低使用'
})

path_df['客户价值'] = path_df['customer_value_segment'].map({
    'high_value': '高价值',
    'medium_value': '中价值',
    'low_value': '低价值'
})

path_df['风险等级'] = path_df['rule_based_churn_risk_level'].map({
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
})

path_df['流失状态'] = path_df['churn_label']

fig = px.parallel_categories(
    path_df,
    dimensions=[
        '国际套餐',
        '语音套餐',
        '使用强度',
        '客户价值',
        '风险等级',
        '流失状态'
    ],
    color='churn_int',
    color_continuous_scale=[
        [0, '#3498DB'],
        [1, '#E74C3C']
    ],
    labels={
        'churn_int': '是否流失'
    }
)

fig.update_layout(
    height=650,
    font=dict(color='black', size=13),
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(t=80, b=40, l=40, r=40),
title='客户属性与流失状态平行路径分析图',
    title_x=0.3,
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 从左到右观察客户路径，可以识别哪些套餐组合、使用强度和风险等级更容易流向流失。")



#国际套餐 -> 语音套餐 -> 使用强度 -> 客户价值 -> 风险等级 -> 是否流失
# Parallel Categories 客户路径图
strong_divider()

st.subheader("🧬 客户路径平行类别图")

path_df = df.copy()

path_df['国际套餐'] = path_df['has_international_plan'].map({0: '无国际套餐', 1: '有国际套餐'})
path_df['语音套餐'] = path_df['has_voice_mail_plan'].map({0: '无语音套餐', 1: '有语音套餐'})

path_df['使用强度'] = path_df['usage_intensity'].map({
    'high_usage': '高使用',
    'medium_usage': '中使用',
    'low_usage': '低使用'
})

path_df['客户价值'] = path_df['customer_value_segment'].map({
    'high_value': '高价值',
    'medium_value': '中价值',
    'low_value': '低价值'
})

path_df['风险等级'] = path_df['rule_based_churn_risk_level'].map({
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
})

path_df['流失状态'] = path_df['churn_label']

fig = px.parallel_categories(
    path_df,
    dimensions=[
        '国际套餐',
        '语音套餐',
        '使用强度',
        '客户价值',
        '风险等级',
        '流失状态'
    ],
    color='churn_int',
    # 🔥 高级比赛配色：科技蓝 + 质感红
    color_continuous_scale=[
        [0, '#165DFF'],   # 未流失：高级蓝
        [1, '#F53F3F']    # 已流失：高级红
    ],
    labels={
        'churn_int': '是否流失'
    }

)

# ===================== 高级布局 + 大标题 =====================
fig.update_layout(
    # 🔥 比赛级标题（居中、加粗、大黑）
    title='客户属性与流失状态平行路径分析图',
    title_x=0.3,
    title_font=dict(size=17, color='black', weight='bold'),

    height=800,
    font=dict(color='black', size=13),
    paper_bgcolor='white',

    # 去掉重复冲突的 plot_bgcolor（避免报错）
    # plot_bgcolor='white',

    margin=dict(t=80, b=40, l=40, r=40),

    # 颜色条样式美化
    coloraxis_colorbar=dict(
        title='是否流失',
        title_font=dict(color='black'),
        tickfont=dict(color='black')
    )
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 从左到右观察客户路径，可以识别哪些套餐组合、使用强度和风险等级更容易流向流失。")







import plotly.graph_objects as go

# 国际套餐 -> 语音套餐 -> 使用强度 -> 客户价值 -> 风险等级 -> 是否流失
# Parallel Categories 客户路径图

strong_divider()

st.subheader("🧬 客户路径平行类别图")

path_df = df.copy()

path_df["国际套餐"] = path_df["has_international_plan"].map({
    0: "无国际套餐",
    1: "有国际套餐"
})

path_df["语音套餐"] = path_df["has_voice_mail_plan"].map({
    0: "无语音套餐",
    1: "有语音套餐"
})

path_df["使用强度"] = path_df["usage_intensity"].map({
    "high_usage": "高使用",
    "medium_usage": "中使用",
    "low_usage": "低使用"
})

path_df["客户价值"] = path_df["customer_value_segment"].map({
    "high_value": "高价值",
    "medium_value": "中价值",
    "low_value": "低价值"
})

path_df["风险等级"] = path_df["rule_based_churn_risk_level"].map({
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险"
})

path_df["流失状态"] = path_df["churn_label"]

path_df["churn_int"] = path_df["churn_int"].astype(int)

# ===================== 维度顺序 =====================

dim_cols = [
    "国际套餐",
    "语音套餐",
    "使用强度",
    "客户价值",
    "风险等级",
    "流失状态"
]

dimension_orders = {
    "国际套餐": ["无国际套餐", "有国际套餐"],
    "语音套餐": ["无语音套餐", "有语音套餐"],
    "使用强度": ["低使用", "中使用", "高使用"],
    "客户价值": ["低价值", "中价值", "高价值"],
    "风险等级": ["低风险", "中风险", "高风险"],
    "流失状态": ["留存", "流失"]
}

# ===================== 核心优化：聚合路径，减少杂乱 =====================
# 原来是一人一条路径，太乱；
# 现在是同一种路径合并成一条，线宽由 count 决定。

plot_df = (
    path_df
    .groupby(dim_cols + ["churn_int"])
    .size()
    .reset_index(name="count")
)

dimensions = []

for col in dim_cols:
    dimensions.append(
        dict(
            label=col,
            values=plot_df[col],
            categoryorder="array",
            categoryarray=dimension_orders[col]
        )
    )

# ===================== 画图 =====================

fig = go.Figure(
    data=[
        go.Parcats(
            dimensions=dimensions,

            # 用 counts 控制路径粗细，而不是每个客户画一条线
            counts=plot_df["count"],

            line=dict(
                color=plot_df["churn_int"],

                # 不用深蓝，改成浅蓝 + 柔红，文字不会被吞
                colorscale=[
                    [0.00, "#DBEAFE"],   # 留存：浅科技蓝
                    [0.49, "#DBEAFE"],
                    [0.50, "#FCA5A5"],   # 流失：柔和红
                    [1.00, "#FCA5A5"]
                ],
                cmin=0,
                cmax=1,
                shape="hspline",

                # 去掉右侧连续颜色条，更干净
                showscale=False
            ),

            # 不要加 opacity，你这个版本不支持！
            # opacity=0.38,

            arrangement="fixed",
            bundlecolors=True,
            sortpaths="forward",

            labelfont=dict(
                size=18,
                color="#111827",
                family="Microsoft YaHei, SimHei, Arial"
            ),

            tickfont=dict(
                size=15,
                color="#111827",
                family="Microsoft YaHei, SimHei, Arial"
            ),

            hoveron="color",
            hoverinfo="count+probability"
        )
    ]
)

fig.update_layout(
    title=dict(
        text="<b>客户属性与流失状态平行路径分析图</b><br>"
             "<sup>Customer Journey and Churn Path Analysis</sup>",
        x=0.5,
        xanchor="center",
        y=0.96,
        font=dict(
            size=24,
            color="#111827",
            family="Microsoft YaHei, SimHei, Arial"
        )
    ),

    height=780,

    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",

    font=dict(
        size=14,
        color="#111827",
        family="Microsoft YaHei, SimHei, Arial"
    ),

    margin=dict(
        t=110,
        b=60,
        l=60,
        r=60
    )
)

st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #EFF6FF 0%, #FEF2F2 100%);
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 14px 18px;
        margin-top: 8px;
        font-size: 15px;
        color: #374151;
        line-height: 1.8;
    ">
        <b>图表解读：</b>
        浅蓝色路径代表留存客户，浅红色路径代表流失客户。
        路径越粗，说明该客户组合出现次数越多。
        从左到右观察套餐选择、使用强度、客户价值和风险等级，可以识别更容易流向流失的客户画像。
    </div>
    """,
    unsafe_allow_html=True
)





import plotly.graph_objects as go

# 国际套餐 -> 语音套餐 -> 使用强度 -> 客户价值 -> 风险等级 -> 是否流失
# Parallel Categories 客户路径图

strong_divider()

st.subheader("🧬 客户路径平行类别图")

path_df = df.copy()

path_df["国际套餐"] = path_df["has_international_plan"].map({
    0: "无国际套餐",
    1: "有国际套餐"
})

path_df["语音套餐"] = path_df["has_voice_mail_plan"].map({
    0: "无语音套餐",
    1: "有语音套餐"
})

path_df["使用强度"] = path_df["usage_intensity"].map({
    "high_usage": "高使用",
    "medium_usage": "中使用",
    "low_usage": "低使用"
})

path_df["客户价值"] = path_df["customer_value_segment"].map({
    "high_value": "高价值",
    "medium_value": "中价值",
    "low_value": "低价值"
})

path_df["风险等级"] = path_df["rule_based_churn_risk_level"].map({
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险"
})

path_df["流失状态"] = path_df["churn_label"]

path_df["churn_int"] = path_df["churn_int"].astype(int)

# ===================== 维度设置 =====================

dim_cols = [
    "国际套餐",
    "语音套餐",
    "使用强度",
    "客户价值",
    "风险等级",
    "流失状态"
]

dimension_orders = {
    "国际套餐": ["无国际套餐", "有国际套餐"],
    "语音套餐": ["无语音套餐", "有语音套餐"],
    "使用强度": ["低使用", "中使用", "高使用"],
    "客户价值": ["低价值", "中价值", "高价值"],
    "风险等级": ["低风险", "中风险", "高风险"],
    "流失状态": ["留存", "流失"]
}

# ===================== 聚合路径，避免图太乱 =====================
# 同一种客户路径合并为一条，count 控制路径粗细

plot_df = (
    path_df
    .groupby(dim_cols + ["churn_int"])
    .size()
    .reset_index(name="count")
)

dimensions = []

for col in dim_cols:
    dimensions.append(
        dict(
            label=col,
            values=plot_df[col],
            categoryorder="array",
            categoryarray=dimension_orders[col]
        )
    )

# ===================== 黑色高级科技风绘图 =====================

fig = go.Figure(
    data=[
        go.Parcats(
            dimensions=dimensions,

            counts=plot_df["count"],

            line=dict(
                color=plot_df["churn_int"],

                # 黑色背景下的高级配色：
                # 留存：青蓝色
                # 流失：玫红色
                # 用 rgba 模拟透明度，解决你当前版本不支持 opacity 的问题
                colorscale=[
                    [0.00, "rgba(14, 165, 233, 0.78)"],  # 留存：更亮的青蓝
                    [0.49, "rgba(14, 165, 233, 0.78)"],
                    [0.50, "rgba(244, 63, 94, 0.88)"],  # 流失：更亮的玫红
                    [1.00, "rgba(244, 63, 94, 0.88)"]
                ],
                # colorscale=[
                #     [0.00, "rgba(0, 191, 255, 0.90)"],
                #     [0.49, "rgba(0, 191, 255, 0.90)"],
                #     [0.50, "rgba(255, 48, 96, 0.95)"],
                #     [1.00, "rgba(255, 48, 96, 0.95)"]
                # ],



        cmin=0,
                cmax=1,
                shape="hspline",

                # 二分类不需要连续颜色条
                showscale=False
            ),

            arrangement="fixed",
            bundlecolors=True,
            sortpaths="forward",

            labelfont=dict(
                size=18,
                color="#F9FAFB",
                family="Microsoft YaHei, SimHei, Arial"
            ),

            tickfont=dict(
                size=15,
                color="#E5E7EB",
                family="Microsoft YaHei, SimHei, Arial"
            ),

            hoveron="color",
            hoverinfo="count+probability"
        )
    ]
)

fig.update_layout(
    title=dict(
        text="<b>客户属性与流失状态平行路径分析图</b><br>"
             ,
        x=0.5,
        xanchor="center",
        y=0.96,
        font=dict(
            size=25,
            color="#F9FAFB",
            family="Microsoft YaHei, SimHei, Arial"
        )
    ),

    height=800,

    # 黑色高级背景
    paper_bgcolor="#020617",
    plot_bgcolor="#020617",

    font=dict(
        size=14,
        color="#F9FAFB",
        family="Microsoft YaHei, SimHei, Arial"
    ),

    margin=dict(
        t=85,
        b=65,
        l=60,
        r=60
    )
)

st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, rgba(56,189,248,0.16), rgba(251,113,133,0.16));
        border: 1px solid rgba(148,163,184,0.35);
        border-radius: 16px;
        padding: 16px 20px;
        margin-top: 10px;
        font-size: 15px;
        color: #E5E7EB;
        line-height: 1.8;
        box-shadow: 0 8px 24px rgba(15,23,42,0.35);
    ">
        <b style="color:#FFFFFF;">图表解读：</b>
        青蓝色路径代表留存客户，玫红色路径代表流失客户。
        路径越粗，说明该客户组合出现次数越多。
        如果玫红色路径集中流向“高风险”和“流失”，说明该客户画像具有较强的流失预警价值。
    </div>
    """,
    unsafe_allow_html=True
)





import plotly.graph_objects as go

# 国际套餐 -> 语音套餐 -> 使用强度 -> 客户价值 -> 风险等级 -> 是否流失
# Parallel Categories 客户路径图：黑色背景 + 直线版

strong_divider()

st.subheader("🧬 客户路径平行类别图")

path_df = df.copy()

path_df["国际套餐"] = path_df["has_international_plan"].map({
    0: "无国际套餐",
    1: "有国际套餐"
})

path_df["语音套餐"] = path_df["has_voice_mail_plan"].map({
    0: "无语音套餐",
    1: "有语音套餐"
})

path_df["使用强度"] = path_df["usage_intensity"].map({
    "high_usage": "高使用",
    "medium_usage": "中使用",
    "low_usage": "低使用"
})

path_df["客户价值"] = path_df["customer_value_segment"].map({
    "high_value": "高价值",
    "medium_value": "中价值",
    "low_value": "低价值"
})

path_df["风险等级"] = path_df["rule_based_churn_risk_level"].map({
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险"
})

path_df["流失状态"] = path_df["churn_label"]

path_df["churn_int"] = path_df["churn_int"].astype(int)

# ===================== 维度设置 =====================

dim_cols = [
    "国际套餐",
    "语音套餐",
    "使用强度",
    "客户价值",
    "风险等级",
    "流失状态"
]

dimension_orders = {
    "国际套餐": ["无国际套餐", "有国际套餐"],
    "语音套餐": ["无语音套餐", "有语音套餐"],
    "使用强度": ["低使用", "中使用", "高使用"],
    "客户价值": ["低价值", "中价值", "高价值"],
    "风险等级": ["低风险", "中风险", "高风险"],
    "流失状态": ["留存", "流失"]
}

# ===================== 聚合路径，避免图太乱 =====================
# 同一种客户路径合并成一条，count 控制路径粗细

plot_df = (
    path_df
    .groupby(dim_cols + ["churn_int"])
    .size()
    .reset_index(name="count")
)

dimensions = []

for col in dim_cols:
    dimensions.append(
        dict(
            label=col,
            values=plot_df[col],
            categoryorder="array",
            categoryarray=dimension_orders[col]
        )
    )

# ===================== 黑色高级科技风绘图：直线版 =====================

fig = go.Figure(
    data=[
        go.Parcats(
            dimensions=dimensions,

            # 用 counts 控制路径粗细
            counts=plot_df["count"],

            line=dict(
                color=plot_df["churn_int"],

                # 黑底更鲜艳配色
                colorscale=[
                    [0.00, "rgba(14, 165, 233, 0.78)"],  # 留存：更亮的青蓝
                    [0.49, "rgba(14, 165, 233, 0.78)"],
                    [0.50, "rgba(244, 63, 94, 0.88)"],  # 流失：更亮的玫红
                    [1.00, "rgba(244, 63, 94, 0.88)"]
                ],

                cmin=0,
                cmax=1,

                # 关键修改：直线
                shape="linear",

                # 不显示颜色条
                showscale=False
            ),

            arrangement="fixed",
            bundlecolors=True,
            sortpaths="forward",

            labelfont=dict(
                size=18,
                color="#F9FAFB",
                family="Microsoft YaHei, SimHei, Arial"
            ),

            tickfont=dict(
                size=15,
                color="#E5E7EB",
                family="Microsoft YaHei, SimHei, Arial"
            ),

            hoveron="color",
            hoverinfo="count+probability"
        )
    ]
)

fig.update_layout(
    title=dict(
        # text="<b>客户属性与流失状态平行路径分析图</b><br>",
        #      # "<sup>Customer Journey and Churn Risk Flow - Linear Paths</sup>",
text="<b>客户属性与流失状态平行路径分析图</b><br>"
     "<span style='font-size:14px; color:#E5E7EB;'>"
     "<span style='color:rgba(0,191,255,0.95);'>━━━━</span> 留存客户"
     "&nbsp;&nbsp;&nbsp;&nbsp;"
     "<span style='color:rgba(255,48,96,0.95);'>━━━━</span> 流失客户"
     "</span>",

        x=0.5,
        xanchor="center",
        y=0.96,
        font=dict(
            size=25,
            color="#F9FAFB",
            family="Microsoft YaHei, SimHei, Arial"
        )
    ),

    height=800,

    paper_bgcolor="#020617",
    plot_bgcolor="#020617",

    font=dict(
        size=14,
        color="#F9FAFB",
        family="Microsoft YaHei, SimHei, Arial"
    ),

    margin=dict(
        t=115,
        b=65,
        l=60,
        r=60
    )
)

st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, rgba(0,191,255,0.16), rgba(255,48,96,0.16));
        border: 1px solid rgba(148,163,184,0.35);
        border-radius: 16px;
        padding: 16px 20px;
        margin-top: 10px;
        font-size: 15px;
        color: #E5E7EB;
        line-height: 1.8;
        box-shadow: 0 8px 24px rgba(15,23,42,0.35);
    ">
        <b style="color:#FFFFFF;">图表解读：</b>
        青蓝色直线路径代表留存客户，玫红色直线路径代表流失客户。
        路径越粗，说明该客户组合出现次数越多。
        直线版更强调不同客户属性之间的直接流向关系，适合观察路径分叉和汇聚。
    </div>
    """,
    unsafe_allow_html=True
)







# ======================================================
# 🧩 Treemap：风险等级 × 客户价值 × 流失率结构
# ======================================================
strong_divider()

st.subheader("🧩 风险等级 × 客户价值客户结构 Treemap")

st.caption(
    "该图用于展示不同风险等级和客户价值组合下的客户规模与流失率。"
    "矩形面积越大，说明该群体客户数量越多；颜色越红，说明该群体流失率越高。"
)

treemap_df = df.copy()

# ------------------------------
# 1. 中文标签映射
# ------------------------------
risk_label_map = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
}

value_label_map = {
    'high_value': '高价值',
    'medium_value': '中价值',
    'low_value': '低价值'
}

treemap_df['风险等级'] = treemap_df['rule_based_churn_risk_level'].map(
    risk_label_map
).fillna(treemap_df['rule_based_churn_risk_level'])

treemap_df['客户价值'] = treemap_df['customer_value_segment'].map(
    value_label_map
).fillna(treemap_df['customer_value_segment'])

# ------------------------------
# 2. 固定展示顺序
# ------------------------------
risk_order = ['低风险', '中风险', '高风险']
value_order = ['高价值', '中价值', '低价值']

treemap_df['风险等级'] = pd.Categorical(
    treemap_df['风险等级'],
    categories=risk_order,
    ordered=True
)

treemap_df['客户价值'] = pd.Categorical(
    treemap_df['客户价值'],
    categories=value_order,
    ordered=True
)

# ------------------------------
# 3. 聚合统计
# ------------------------------
tree_summary = treemap_df.groupby(
    ['风险等级', '客户价值'],
    observed=False
).agg(
    customer_count=('customer_id', 'count'),
    churn_count=('churn_int', 'sum'),
    churn_rate=('churn_int', 'mean'),
    avg_risk_score=('rule_based_churn_risk_score', 'mean'),
    avg_total_charges=('total_charges', 'mean'),
    avg_service_calls=('customer_service_calls', 'mean')
).reset_index()

tree_summary['churn_rate_pct'] = tree_summary['churn_rate'] * 100

# 防止空组合影响图表
tree_summary = tree_summary[tree_summary['customer_count'] > 0].copy()








# ------------------------------
# 4. 绘制高对比 Treemap
# ------------------------------

fig = px.treemap(
    tree_summary,
    path=[
        px.Constant("全体客户"),
        '风险等级',
        '客户价值'
    ],
    values='customer_count',
    color='churn_rate_pct',

    # 高对比配色：深蓝 → 青绿 → 金黄 → 橙红 → 深红
    color_continuous_scale=[
        [0.00, '#08306B'],   # 深蓝
        [0.25, '#0077B6'],   # 亮蓝
        [0.50, '#F4D35E'],   # 金黄
        [0.75, '#F77F00'],   # 橙色
        [1.00, '#B00020']    # 深红
    ],

    range_color=[
        tree_summary['churn_rate_pct'].min(),
        tree_summary['churn_rate_pct'].max()
    ],

    custom_data=[
        'customer_count',
        'churn_count',
        'churn_rate_pct',
        'avg_risk_score',
        'avg_total_charges',
        'avg_service_calls'
    ],

    labels={
        'churn_rate_pct': '流失率 (%)',
        'customer_count': '客户数量',
        'churn_count': '流失客户数',
        'avg_risk_score': '平均风险分数',
        'avg_total_charges': '平均总费用',
        'avg_service_calls': '平均客服呼叫次数'
    }
)
treemap_text_colors = [
    'black' if str(label) in ['中风险', '高风险'] else 'white'
    for label in fig.data[0].labels
]

fig.update_traces(
    # 显示标签、客户数、流失率
    texttemplate=(
        "<b>%{label}</b><br>"
        "%{customdata[0]:,} 人<br>"
        "流失率 %{customdata[2]:.1f}%"
    ),

    # 关键：深色背景用白字
    textfont=dict(
color=treemap_text_colors,

        size=15,
        family='Microsoft YaHei, SimHei, Arial'
    ),

    textposition='middle center',

    marker=dict(
        line=dict(
            color='white',
            width=3
        )
    ),

    hovertemplate=(
        '<b>%{label}</b><br><br>'
        '客户数量：%{customdata[0]:,} 人<br>'
        '流失客户数：%{customdata[1]:,} 人<br>'
        '流失率：%{customdata[2]:.1f}%<br>'
        '平均风险分数：%{customdata[3]:.1f}<br>'
        '平均总费用：$%{customdata[4]:,.2f}<br>'
        '平均客服呼叫次数：%{customdata[5]:.2f}<br>'
        '<extra></extra>'
    )
)

fig.update_layout(
    height=700,

    paper_bgcolor='white',
    plot_bgcolor='white',

    font=dict(
        color='black',
        size=13,
        family='Microsoft YaHei, SimHei, Arial'
    ),

    title=dict(
        text='<b>风险等级与客户价值分层矩形树图</b>',
        x=0.5,
        xanchor='center',
        y=0.96,
        font=dict(
            color='black',
            size=22,
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    coloraxis_colorbar=dict(
        title=dict(
            text='流失率 (%)',
            font=dict(color='black', size=13)
        ),
        tickfont=dict(
            color='black',
            size=12
        ),
        thickness=16,
        len=0.74,
        outlinewidth=0
    ),

    hoverlabel=dict(
        bgcolor='white',
        bordercolor='black',
        font=dict(
            color='black',
            size=13,
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    margin=dict(
        t=90,
        b=40,
        l=40,
        r=40
    ),

    # 不隐藏小格子文字，尽量全部显示
    uniformtext=dict(
        minsize=8,
        mode='show'
    )
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 Treemap 的面积表示客户数量，颜色表示该风险等级 × 客户价值组合下的流失率。"
    "理想情况下，应重点关注面积较大且颜色偏红的区域，尤其是高价值客户中的中高风险群体。"
)
