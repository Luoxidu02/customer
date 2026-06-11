# views/eda/full_customers/usage.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.data_loader import load_full_customers

st.title("📈 客户使用行为分析")
st.markdown("---")

# ======================================================
# 数据加载
# ======================================================
df = load_full_customers()
df['churn_int'] = df['churn'].astype(int)
df['churn_label'] = df['churn_int'].map({0: '留存', 1: '流失'})

# 字段语义别名：account_length 更准确地表示账户开通时长，单位为天
df['account_age_days'] = df['account_length']

# 图表通用布局
common_layout = dict(
    font=dict(color='black', size=12),
    # title_font=dict(color='black', size=14),
    # legend_font=dict(color='black'),
    # paper_bgcolor='white',
    # plot_bgcolor='white',
)

# ======================================================
# 📞 客服呼叫次数与流失
# ======================================================
st.subheader("📞 客服呼叫次数与流失关系")

st.markdown("**不同客服呼叫次数对应的流失率**")

call_stats = df.groupby('customer_service_calls').agg(
    count=('churn_int', 'count'),
    churn_rate=('churn_int', 'mean')
).reset_index()
call_stats['churn_rate'] = call_stats['churn_rate'] * 100

fig_calls = px.bar(
    call_stats, x='customer_service_calls', y='churn_rate',
    text=call_stats['churn_rate'].apply(lambda x: f'{x:.1f}%'),
    color='churn_rate',
    color_continuous_scale=['#27AE60', '#F1C40F', '#E74C3C'],
    custom_data=['count']
)
fig_calls.update_traces(
    textposition='outside',
    textfont=dict(color='black', size=11),
    hovertemplate='呼叫次数: %{x}<br>流失率: %{y:.1f}%<br>样本量: %{customdata[0]}'
)
fig_calls.update_layout(
    **common_layout,
    title='不同客服呼叫次数对应的客户流失率条形图',
    title_x=0.2,  # 让标题水平居中
    yaxis_title='流失率 (%)',
    coloraxis_showscale=False,
    height=400,
    margin=dict(t=60, b=40, l=40, r=40)
)
fig_calls.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'), dtick=1)
fig_calls.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_calls, use_container_width=True)

st.info("💡 **洞察**: 客服呼叫次数 ≥4 次的客户，流失率显著上升。这类客户可能遇到了反复未解决的问题。")

st.markdown("---")

# ======================================================
# 南丁格尔玫瑰图：客服呼叫次数与流失率
# ======================================================

call_stats = call_stats.sort_values('customer_service_calls').reset_index(drop=True)

# 计算每个扇区角度
n = len(call_stats)
call_stats['theta'] = [i * 360 / n for i in range(n)]
call_stats['label'] = call_stats['customer_service_calls'].apply(lambda x: f"{x} 次")
call_stats['text_label'] = call_stats['churn_rate'].apply(lambda x: f"{x:.1f}%")

# 给文字标签留出外圈空间
max_rate = call_stats['churn_rate'].max()
label_radius = max_rate * 1.12

fig_calls = go.Figure()

# 主玫瑰花瓣
fig_calls.add_trace(
    go.Barpolar(
        r=call_stats['churn_rate'],
        theta=call_stats['theta'],
        width=[360 / n * 0.78] * n,
        marker=dict(
            color=call_stats['churn_rate'],
            colorscale=[
                [0.00, '#1B5E20'],   # 深绿：低流失
                [0.45, '#F2C94C'],   # 鎏金：中等风险
                [1.00, '#B71C1C']    # 深红：高流失
            ],
            line=dict(
                color='rgba(255,255,255,0.95)',
                width=2.5
            ),
            opacity=0.92
        ),
        customdata=call_stats[['count', 'customer_service_calls']],
        hovertemplate=(
            '<b>客服呼叫次数：%{customdata[1]} 次</b><br>'
            '客户流失率：%{r:.1f}%<br>'
            '样本量：%{customdata[0]} 人'
            '<extra></extra>'
        ),
        name='流失率'
    )
)

# 外圈百分比标签
fig_calls.add_trace(
    go.Scatterpolar(
        r=[label_radius] * n,
        theta=call_stats['theta'],
        mode='text',
        text=call_stats['text_label'],
        textfont=dict(
            size=13,
            color='#1F2D3D',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        hoverinfo='skip',
        showlegend=False
    )
)

fig_calls.update_layout(
    **common_layout,
    title=dict(
        text="<b>客服呼叫次数与客户流失率关系南丁格尔玫瑰图</b>",
        x=0.5,
        xanchor='center',
        y=0.96,
        yanchor='top',
        font=dict(
            size=22,
            color='#1F2D3D',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),
    height=560,
    showlegend=False,
    margin=dict(t=110, b=50, l=70, r=70),
    paper_bgcolor='white',
    plot_bgcolor='white',
    polar=dict(
        bgcolor='rgba(248,250,252,0.95)',
        radialaxis=dict(
            visible=True,
            showline=False,
            showticklabels=True,
            ticks='',
            gridcolor='rgba(44,62,80,0.16)',
            gridwidth=1,
            range=[0, max_rate * 1.25],
            tickfont=dict(
                size=11,
                color='#7F8C8D'
            )
        ),
        angularaxis=dict(
            tickmode='array',
            tickvals=call_stats['theta'],
            ticktext=call_stats['label'],
            tickfont=dict(
                size=12,
                color='#1F2D3D',
                family='Microsoft YaHei, SimHei, Arial'
            ),
            rotation=90,
            direction='clockwise',
            gridcolor='rgba(44,62,80,0.12)',
            linecolor='rgba(44,62,80,0.25)'
        )
    ),
    annotations=[
        dict(
            text=(
                "<b>     </b><br>"
                "<span style='font-size:12px;color:#7F8C8D'>   </span>"
            ),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(
                size=18,
                color='#1F2D3D',
                family='Microsoft YaHei, SimHei, Arial'
            )
        )
    ]
)

fig_calls.update_traces(
    hoverlabel=dict(
        bgcolor='white',
        bordercolor='#D5DBDB',
        font=dict(
            size=13,
            color='#1F2D3D',
            family='Microsoft YaHei, SimHei, Arial'
        )
    )
)

st.plotly_chart(fig_calls, use_container_width=True)






# ======================================================
# 💰 费用与通话时长对比
# ======================================================
st.subheader("💰 费用与通话时长分布 (流失 vs 留存)")

# 图1: 总费用分布
st.markdown("**总费用分布**")
fig_charge = px.box(
    df, x='churn_label', y='total_charges',
    color='churn_label',
    color_discrete_map={'留存': '#3498DB', '流失': '#E74C3C'},
    points='outliers'
)
fig_charge.update_layout(
    **common_layout,
    title='箱线图：流失与留存客户的总费用分布',
    xaxis_title='客户状态',
    yaxis_title='总费用 ($)',
    showlegend=False,
    margin=dict(t=60, b=30, l=30, r=30),
    height=400
)
fig_charge.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_charge.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_charge, use_container_width=True)

st.markdown("")

# 图2: 总通话时长分布
st.markdown("**总通话时长分布**")
fig_mins = px.box(
    df, x='churn_label', y='total_minutes',
    color='churn_label',
    color_discrete_map={'留存': '#3498DB', '流失': '#E74C3C'},
    points='outliers'
)
fig_mins.update_layout(
    **common_layout,
    title='箱线图：流失与留存客户的总通话时长分布',
    xaxis_title='客户状态',
    yaxis_title='总通话时长 (分钟)',
    showlegend=False,
    margin=dict(t=60, b=30, l=30, r=30),
    height=400
)
fig_mins.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_mins.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_mins, use_container_width=True)

st.markdown("---")

# ======================================================
# 🌞🌙 日间/夜间/晚间使用对比
# ======================================================
st.subheader("🌞 时段使用行为分析")

# 图3: 各时段平均费用
st.markdown("**各时段平均费用 (流失 vs 留存)**")

time_cols = ['total_day_charge', 'total_eve_charge', 'total_night_charge', 'total_intl_charge']
time_labels = ['日间', '傍晚', '夜间', '国际']

time_data = []
for col, label in zip(time_cols, time_labels):
    for status in [0, 1]:
        avg_val = df[df['churn_int'] == status][col].mean()
        time_data.append({
            'time_period': label,
            'churn_label': '留存' if status == 0 else '流失',
            'avg_charge': avg_val
        })

time_df = pd.DataFrame(time_data)

fig_time = px.bar(
    time_df, x='time_period', y='avg_charge', color='churn_label',
    barmode='group',
    color_discrete_map={'留存': '#3498DB', '流失': '#E74C3C'},
    text=time_df['avg_charge'].apply(lambda x: f'${x:.1f}')
)
fig_time.update_traces(textposition='outside', textfont=dict(color='black', size=10))
fig_time.update_layout(
    **common_layout,
    title='流失与留存客户在各时段的平均费用对比分组条形图',
    xaxis_title='时段',
    title_x=0.1,  # 让标题水平居中
    yaxis_title='平均费用 ($)',
    legend_title='客户状态',
    margin=dict(t=60, b=30, l=30, r=30),
    height=450
)
fig_time.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_time.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_time, use_container_width=True)

st.markdown("")




# ======================================================
# 🌞🌙 日间/夜间/晚间使用对比
# ======================================================
st.subheader("🌞 时段使用行为分析")

# 图3: 各时段平均费用
st.markdown("**各时段平均费用 (流失 vs 留存)**")

time_cols = [
    'total_day_charge',
    'total_eve_charge',
    'total_night_charge',
    'total_intl_charge'
]

time_labels = ['日间', '傍晚', '夜间', '国际']

time_data = []
for col, label in zip(time_cols, time_labels):
    for status in [0, 1]:
        avg_val = df[df['churn_int'] == status][col].mean()
        time_data.append({
            'time_period': label,
            'churn_label': '留存' if status == 0 else '流失',
            'avg_charge': avg_val
        })

time_df = pd.DataFrame(time_data)


# ======================================================
# 🌞🌙 日间/夜间/晚间使用对比
# ======================================================


import plotly.graph_objects as go

time_cols = [
    'total_day_charge',
    'total_eve_charge',
    'total_night_charge',
    'total_intl_charge'
]

time_labels = ['日间', '傍晚', '夜间', '国际']

time_data = []
for col, label in zip(time_cols, time_labels):
    for status in [0, 1]:
        avg_val = df[df['churn_int'] == status][col].mean()
        time_data.append({
            'time_period': label,
            'churn_label': '留存' if status == 0 else '流失',
            'avg_charge': avg_val
        })

time_df = pd.DataFrame(time_data)

# ======================================================
# 高级玫瑰图：各时段平均费用（流失 vs 留存）
# ======================================================
# ======================================================
# 🌞🌙 日间/夜间/晚间使用对比
# ======================================================


import plotly.graph_objects as go
import numpy as np

time_cols = [
    'total_day_charge',
    'total_eve_charge',
    'total_night_charge',
    'total_intl_charge'
]

time_labels = ['日间', '傍晚', '夜间', '国际']

time_data = []
for col, label in zip(time_cols, time_labels):
    for status in [0, 1]:
        avg_val = df[df['churn_int'] == status][col].mean()
        time_data.append({
            'time_period': label,
            'churn_label': '留存' if status == 0 else '流失',
            'avg_charge': avg_val
        })

time_df = pd.DataFrame(time_data)
# ======================================================
# 🌞🌙 日间/夜间/晚间使用对比
# ======================================================
st.subheader("🌞 时段使用行为分析")

# 图3: 各时段平均费用
st.markdown("**各时段平均费用 (流失 vs 留存)**")

import plotly.graph_objects as go
import numpy as np

time_cols = [
    'total_day_charge',
    'total_eve_charge',
    'total_night_charge',
    'total_intl_charge'
]

time_labels = ['日间', '傍晚', '夜间', '国际']

time_data = []
for col, label in zip(time_cols, time_labels):
    for status in [0, 1]:
        avg_val = df[df['churn_int'] == status][col].mean()
        time_data.append({
            'time_period': label,
            'churn_label': '留存' if status == 0 else '流失',
            'avg_charge': avg_val
        })

time_df = pd.DataFrame(time_data)

# ======================================================
# 高级玫瑰图：每个条形变成一个独立扇形，紧挨排列
# ======================================================

pivot_time = (
    time_df
    .pivot(index='time_period', columns='churn_label', values='avg_charge')
    .reindex(time_labels)
    .fillna(0)
)

# 四个时段的中心角度
base_angles = np.array([0, 90, 180, 270])

# 每个时段两个扇形紧挨着
# 每个时段总共占 90 度，留存 45 度，流失 45 度
angle_offset = 22.5
sector_width = 45

theta_retention = base_angles - angle_offset
theta_churn = base_angles + angle_offset

# 高级高对比配色：不用红蓝
color_retention = '#0E7C7B'   # 深松石绿
color_churn = '#8E44AD'       # 紫罗兰

fig_time = go.Figure()

# 留存客户扇形
fig_time.add_trace(
    go.Barpolar(
        r=pivot_time['留存'],
        theta=theta_retention,
        width=[sector_width] * len(theta_retention),
        name='留存',
        marker=dict(
            color=color_retention,
            line=dict(
                color='rgba(0,0,0,0)',
                width=0
            )
        ),
        opacity=0.95,
        customdata=np.array([
            ['日间', '留存'],
            ['傍晚', '留存'],
            ['夜间', '留存'],
            ['国际', '留存']
        ]),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '客户状态：%{customdata[1]}<br>'
            '平均费用：$%{r:.2f}'
            '<extra></extra>'
        )
    )
)

# 流失客户扇形
fig_time.add_trace(
    go.Barpolar(
        r=pivot_time['流失'],
        theta=theta_churn,
        width=[sector_width] * len(theta_churn),
        name='流失',
        marker=dict(
            color=color_churn,
            line=dict(
                color='rgba(0,0,0,0)',
                width=0
            )
        ),
        opacity=0.95,
        customdata=np.array([
            ['日间', '流失'],
            ['傍晚', '流失'],
            ['夜间', '流失'],
            ['国际', '流失']
        ]),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '客户状态：%{customdata[1]}<br>'
            '平均费用：$%{r:.2f}'
            '<extra></extra>'
        )
    )
)

# 数值标签
max_r = max(
    pivot_time['留存'].max(),
    pivot_time['流失'].max()
)

label_offset = max_r * 0.08

fig_time.add_trace(
    go.Scatterpolar(
        r=pivot_time['留存'] + label_offset,
        theta=theta_retention,
        mode='text',
        text=[f'${v:.1f}' for v in pivot_time['留存']],
        textfont=dict(
            color=color_retention,
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        ),
        showlegend=False,
        hoverinfo='skip'
    )
)

fig_time.add_trace(
    go.Scatterpolar(
        r=pivot_time['流失'] + label_offset,
        theta=theta_churn,
        mode='text',
        text=[f'${v:.1f}' for v in pivot_time['流失']],
        textfont=dict(
            color=color_churn,
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        ),
        showlegend=False,
        hoverinfo='skip'
    )
)

# 布局
fig_time.update_layout(
    **common_layout,

    title=dict(
        text='<b>流失与留存客户在各时段的平均费用对比玫瑰图</b>',
        x=0.5,
        xanchor='center',
        font=dict(
            size=21,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    height=540,

    legend=dict(
        title='客户状态',
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5,
        font=dict(
            size=12,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        title_font=dict(
            size=12,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    paper_bgcolor='white',
    plot_bgcolor='white',

    margin=dict(
        t=95,
        b=35,
        l=35,
        r=35
    ),

    hoverlabel=dict(
        bgcolor='white',
        bordercolor='black',
        font=dict(
            color='black',
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        )
    )
)

# 删除坐标轴、网格线、刻度文字
fig_time.update_layout(
    polar=dict(
        bgcolor='white',

        radialaxis=dict(
            visible=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            ticks='',
            range=[0, max_r * 1.25]
        ),

        angularaxis=dict(
            visible=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            ticks='',
            rotation=90,
            direction='clockwise'
        )
    )
)

st.plotly_chart(fig_time, use_container_width=True)

# ======================================================
# 🌞 各时段平均费用：左右对比横向柱状图（带大边框 + 渐变配色）
# ======================================================
st.subheader("🌞 时段使用行为分析")

st.markdown("**各时段平均费用对比（流失 vs 留存）**")

import plotly.graph_objects as go
import pandas as pd

# 1. 定义字段和中文标签
time_cols = [
    'total_day_charge',
    'total_eve_charge',
    'total_night_charge',
    'total_intl_charge'
]

time_labels = ['日间', '傍晚', '夜间', '国际']

# 2. 计算不同客户状态下，各时段平均费用
time_data = []

for col, label in zip(time_cols, time_labels):
    retention_avg = df[df['churn_int'] == 0][col].mean()
    churn_avg = df[df['churn_int'] == 1][col].mean()

    time_data.append({
        'time_period': label,
        '留存客户': retention_avg,
        '流失客户': churn_avg
    })

time_df = pd.DataFrame(time_data)

# 3. 为了让流失客户显示在左侧，将数值转为负数
time_df['流失客户_left'] = -time_df['流失客户']

# 4. 计算坐标轴范围，左右对称
max_value = max(
    time_df['流失客户'].max(),
    time_df['留存客户'].max()
)

axis_range = max_value * 1.45

# 5. 绘图
fig_time_compare = go.Figure()

# 左侧：流失客户平均费用，红橙渐变
fig_time_compare.add_trace(
    go.Bar(
        y=time_df['time_period'],
        x=time_df['流失客户_left'],
        orientation='h',
        name='流失客户',
        marker=dict(
            color=time_df['流失客户'],
            colorscale=[
                [0.00, '#FADBD8'],   # 浅红
                [0.45, '#F1948A'],   # 柔和红
                [0.75, '#E74C3C'],   # 红色
                [1.00, '#922B21']    # 深红
            ],
            cmin=0,
            cmax=max_value,
            showscale=False,
            line=dict(
                color='rgba(255,255,255,0.9)',
                width=1.2
            )
        ),
        text=time_df['流失客户'].apply(lambda x: f'${x:.1f}'),
        textposition='outside',
        textfont=dict(
            color='#922B21',
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        ),
        customdata=time_df['流失客户'],
        hovertemplate=(
            '<b>%{y}</b><br>'
            '客户状态：流失客户<br>'
            '平均费用：$%{customdata:.2f}'
            '<extra></extra>'
        )
    )
)

# 右侧：留存客户平均费用，蓝紫渐变
fig_time_compare.add_trace(
    go.Bar(
        y=time_df['time_period'],
        x=time_df['留存客户'],
        orientation='h',
        name='留存客户',
        marker=dict(
            color=time_df['留存客户'],
            colorscale=[
                [0.00, '#D6EAF8'],   # 浅蓝
                [0.45, '#85C1E9'],   # 柔和蓝
                [0.75, '#3498DB'],   # 蓝色
                [1.00, '#1A5276']    # 深蓝
            ],
            cmin=0,
            cmax=max_value,
            showscale=False,
            line=dict(
                color='rgba(255,255,255,0.9)',
                width=1.2
            )
        ),
        text=time_df['留存客户'].apply(lambda x: f'${x:.1f}'),
        textposition='outside',
        textfont=dict(
            color='#1A5276',
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        ),
        customdata=time_df['留存客户'],
        hovertemplate=(
            '<b>%{y}</b><br>'
            '客户状态：留存客户<br>'
            '平均费用：$%{customdata:.2f}'
            '<extra></extra>'
        )
    )
)

# 6. 布局美化
fig_time_compare.update_layout(
    title=dict(
        text='<b>流失与留存客户在各时段的平均费用左右对比图</b>',
        x=0.5,
        xanchor='center',
        y=0.96,
        yanchor='top',
        font=dict(
            size=20,
            color='#1F2D3D',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    barmode='relative',
    height=350,

    # 背景色
    paper_bgcolor='white',
    plot_bgcolor='#FAFBFC',

    xaxis=dict(
        title='平均费用 ($)',
        range=[-axis_range, axis_range],

        # 中间 0 轴线
        zeroline=True,
        zerolinecolor='#2C3E50',
        zerolinewidth=2.5,

        # 网格线
        showgrid=True,
        gridcolor='rgba(180,180,180,0.22)',
        gridwidth=1,

        tickvals=[
            -axis_range,
            -axis_range / 2,
            0,
            axis_range / 2,
            axis_range
        ],
        ticktext=[
            f'${axis_range:.0f}',
            f'${axis_range / 2:.0f}',
            '$0',
            f'${axis_range / 2:.0f}',
            f'${axis_range:.0f}'
        ],

        # 坐标轴边框
        showline=True,
        linecolor='#2C3E50',
        linewidth=1.2,
        mirror=True,

        title_font=dict(
            size=13,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        tickfont=dict(
            size=12,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    yaxis=dict(
        title='时段',
        autorange='reversed',

        showline=True,
        linecolor='#2C3E50',
        linewidth=1.2,
        mirror=True,

        title_font=dict(
            size=13,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        tickfont=dict(
            size=13,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    legend=dict(
        title=' ',
        orientation='h',
        yanchor='bottom',
        y=1.21,
        xanchor='center',
        x=0.5,
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor='rgba(44,62,80,0.25)',
        borderwidth=0,
        font=dict(
            size=11,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        title_font=dict(
            size=2,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    margin=dict(
        t=110,
        b=65,
        l=85,
        r=85
    ),

    hoverlabel=dict(
        bgcolor='white',
        bordercolor='#2C3E50',
        font=dict(
            color='black',
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        )
    )
)

# 7. 添加中间基准线说明
fig_time_compare.add_annotation(
    x=0,
    y=0.98,
    xref='x',
    yref='paper',
    text='<b>费用对比基准线</b>',
    showarrow=False,
    font=dict(
        size=12,
        color='#2C3E50',
        family='Microsoft YaHei, SimHei, Arial'
    ),
    bgcolor='rgba(255,255,255,0.9)',
    bordercolor='rgba(44,62,80,0.25)',
    borderwidth=1,
    borderpad=3
)

# 8. 添加一个大边框，罩住整个图表主体
fig_time_compare.add_shape(
    type='rect',
    xref='paper',
    yref='paper',
    x0=-0.10,
    y0=-0.18,
    x1=1.10,
    y1=1.20,
    line=dict(
        color='#2C3E50',
        width=2.2
    ),
    fillcolor='rgba(0,0,0,0)',
    layer='above'
)

st.plotly_chart(fig_time_compare, use_container_width=True)





# 图4: 日间费用 vs 夜间费用散点图
st.markdown("**日间费用 vs 夜间费用散点图**")

# 抽样防止太密集
sample_df = df.sample(min(1000, len(df)), random_state=42)

fig_scatter = px.scatter(
    sample_df, x='total_day_charge', y='total_night_charge',
    color='churn_label', opacity=0.6,
    color_discrete_map={'留存': '#3498DB', '流失': '#E74C3C'},
    hover_data=['customer_service_calls', 'total_charges']
)
fig_scatter.update_layout(
    **common_layout,
    title='散点图：客户日间费用与夜间费用关系',
    xaxis_title='日间费用 ($)',
    yaxis_title='夜间费用 ($)',
    legend_title='客户状态',
    margin=dict(t=60, b=30, l=30, r=30),
    height=500
)
fig_scatter.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_scatter.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")




# ======================================================
# 📊 单位费用效率分析
# ======================================================
st.subheader("📊 消费效率分析")

# 图5: 每分钟平均费用分布
st.markdown("**每分钟平均费用分布**")
fig_efficiency = px.histogram(
    df, x='avg_charge_per_minute', color='churn_label',
    nbins=40, barmode='overlay', opacity=0.7,
    color_discrete_map={'留存': '#3498DB', '流失': '#E74C3C'}
)
fig_efficiency.update_layout(
    **common_layout,
    title='直方图：流失与留存客户的每分钟平均费用分布',
    xaxis_title='每分钟平均费用 ($)',
    yaxis_title='客户数量',
    legend_title='客户状态',
    margin=dict(t=60, b=30, l=30, r=30),
    height=400
)
fig_efficiency.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_efficiency.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_efficiency, use_container_width=True)

st.markdown("")

# 图6: 客服呼叫率分布
st.markdown("**客服呼叫率分布 (Support Call Rate)**")
fig_support = px.histogram(
    df, x='support_call_rate', color='churn_label',
    nbins=30, barmode='overlay', opacity=0.7,
    color_discrete_map={'留存': '#3498DB', '流失': '#E74C3C'}
)
fig_support.update_layout(
    **common_layout,
    title='直方图：流失与留存客户的客服呼叫率分布',
    xaxis_title='客服呼叫率',
    yaxis_title='客户数量',
    legend_title='客户状态',
    margin=dict(t=60, b=30, l=30, r=30),
    height=400
)
fig_support.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_support.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
st.plotly_chart(fig_support, use_container_width=True)

st.markdown("---")

# ======================================================
# 🔗 关键特征相关性热力图
# ======================================================
st.subheader("🔗 关键特征相关性")

st.markdown("**主要数值特征的相关性矩阵**")

numeric_cols = [
    'account_age_days', 'total_day_charge', 'total_eve_charge', 'total_night_charge',
    'total_intl_charge', 'customer_service_calls', 'total_charges', 'churn_int'
]
corr_labels = [
    '账户开通时长（天）', '日间费用', '傍晚费用', '夜间费用',
    '国际费用', '客服呼叫次数', '总费用', '是否流失'
]

corr_matrix = df[numeric_cols].corr()

fig_corr = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=corr_labels,
    y=corr_labels,
    colorscale='RdBu_r',
    zmin=-1, zmax=1,
    text=np.round(corr_matrix.values, 2),
    texttemplate='%{text}',
    textfont=dict(color='black', size=10),
    hovertemplate='%{x} vs %{y}<br>相关系数: %{z:.2f}<extra></extra>'
))

fig_corr.update_layout(
    **common_layout,
    title='热力图：主要数值特征之间的相关性矩阵',
    height=550,
    margin=dict(t=60, b=40, l=40, r=40),
    xaxis=dict(tickfont=dict(color='black')),
    yaxis=dict(tickfont=dict(color='black'))
)
st.plotly_chart(fig_corr, use_container_width=True)

st.info("💡 **洞察**: `customer_service_calls` 与 `churn_int` 呈正相关，是最直接的流失预警信号之一。")
# ======================================================
# 📞 国际套餐 × 客服呼叫次数 的流失率哑铃图
# ======================================================
st.subheader("📞 国际套餐 × 客服呼叫次数流失率差异图")

import plotly.graph_objects as go

heat_df = df.copy()

heat_df['intl_label'] = heat_df['has_international_plan'].map({
    0: '无国际套餐',
    1: '有国际套餐'
})

# 将客服呼叫次数分组，避免横轴过碎
heat_df['calls_group'] = heat_df['customer_service_calls'].apply(
    lambda x: '4次及以上' if x >= 4 else f'{int(x)}次'
)

order_calls = ['0次', '1次', '2次', '3次', '4次及以上']

heat_df['calls_group'] = pd.Categorical(
    heat_df['calls_group'],
    categories=order_calls,
    ordered=True
)

# 计算每组客户数、流失客户数、流失率
summary = (
    heat_df
    .groupby(['calls_group', 'intl_label'])
    .agg(
        customer_count=('churn_int', 'count'),
        churn_count=('churn_int', 'sum'),
        churn_rate=('churn_int', 'mean')
    )
    .reset_index()
)

summary['churn_rate'] = summary['churn_rate'] * 100

# 转成宽表，方便画哑铃图
rate_pivot = summary.pivot(
    index='calls_group',
    columns='intl_label',
    values='churn_rate'
).reindex(order_calls)

count_pivot = summary.pivot(
    index='calls_group',
    columns='intl_label',
    values='customer_count'
).reindex(order_calls)

churn_pivot = summary.pivot(
    index='calls_group',
    columns='intl_label',
    values='churn_count'
).reindex(order_calls)

# 防止某些组合缺失
rate_pivot = rate_pivot.fillna(0)
count_pivot = count_pivot.fillna(0)
churn_pivot = churn_pivot.fillna(0)

rate_pivot['差异'] = rate_pivot['有国际套餐'] - rate_pivot['无国际套餐']

# y轴反向，让 0次 在最上方
y_order = order_calls[::-1]

fig = go.Figure()

# --------------------------
# 1. 添加连接线
# --------------------------
for call in order_calls:
    no_rate = rate_pivot.loc[call, '无国际套餐']
    yes_rate = rate_pivot.loc[call, '有国际套餐']

    # 如果有国际套餐流失率更高，用红色线，否则用蓝色线
    line_color = '#E74C3C' if yes_rate >= no_rate else '#3498DB'

    fig.add_trace(
        go.Scatter(
            x=[no_rate, yes_rate],
            y=[call, call],
            mode='lines',
            line=dict(
                color=line_color,
                width=4
            ),
            opacity=0.65,
            hoverinfo='skip',
            showlegend=False
        )
    )

# --------------------------
# 2. 无国际套餐点
# --------------------------
fig.add_trace(
    go.Scatter(
        x=rate_pivot['无国际套餐'],
        y=rate_pivot.index,
        mode='markers+text',
        name='无国际套餐',
        marker=dict(
            size=18,
            color='#1F77B4',
            line=dict(
                color='white',
                width=2
            )
        ),
        text=rate_pivot['无国际套餐'].apply(lambda x: f'{x:.1f}%'),
        textposition='middle left',
        textfont=dict(
            color='#1F77B4',
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        ),
        customdata=list(zip(
            count_pivot['无国际套餐'],
            churn_pivot['无国际套餐']
        )),
        hovertemplate=(
            '<b>无国际套餐</b><br>'
            '客服呼叫次数：%{y}<br>'
            '流失率：%{x:.1f}%<br>'
            '客户数量：%{customdata[0]:,.0f} 人<br>'
            '流失客户数：%{customdata[1]:,.0f} 人'
            '<extra></extra>'
        )
    )
)

# --------------------------
# 3. 有国际套餐点
# --------------------------
fig.add_trace(
    go.Scatter(
        x=rate_pivot['有国际套餐'],
        y=rate_pivot.index,
        mode='markers+text',
        name='有国际套餐',
        marker=dict(
            size=18,
            color='#E74C3C',
            line=dict(
                color='white',
                width=2
            )
        ),
        text=rate_pivot['有国际套餐'].apply(lambda x: f'{x:.1f}%'),
        textposition='middle right',
        textfont=dict(
            color='#E74C3C',
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        ),
        customdata=list(zip(
            count_pivot['有国际套餐'],
            churn_pivot['有国际套餐']
        )),
        hovertemplate=(
            '<b>有国际套餐</b><br>'
            '客服呼叫次数：%{y}<br>'
            '流失率：%{x:.1f}%<br>'
            '客户数量：%{customdata[0]:,.0f} 人<br>'
            '流失客户数：%{customdata[1]:,.0f} 人'
            '<extra></extra>'
        )
    )
)

# --------------------------
# 4. 添加差异标注
# --------------------------
x_max = max(
    rate_pivot['无国际套餐'].max(),
    rate_pivot['有国际套餐'].max()
)

for call in order_calls:
    diff = rate_pivot.loc[call, '差异']
    no_rate = rate_pivot.loc[call, '无国际套餐']
    yes_rate = rate_pivot.loc[call, '有国际套餐']

    label_x = max(no_rate, yes_rate) + 10

    fig.add_annotation(
        x=label_x,
        y=call,
        text=(
            f"+{diff:.1f}%" if diff >= 0 else f"{diff:.1f}%"
        ),
        showarrow=False,
        font=dict(
            color='#E74C3C' if diff >= 0 else '#1F77B4',
            size=13,
            family='Microsoft YaHei, SimHei, Arial'
        ),
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor='#DDDDDD',
        borderwidth=1,
        borderpad=3
    )

# --------------------------
# 5. 高级布局
# --------------------------
fig.update_layout(
    **common_layout,

    title=dict(
        text='<b>国际套餐客户在不同客服呼叫次数下的流失率差异哑铃图</b>',
        x=0.5,
        xanchor='center',
        font=dict(
            size=21,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    height=460,

    xaxis=dict(
        title='流失率 (%)',
        range=[0, min(max(x_max + 15, 40), 100)],

        # 网格线
        showgrid=True,
        gridcolor='rgba(180,180,180,0.25)',

        # 黑色边框关键设置
        showline=True,
        linecolor='black',
        linewidth=1.5,
        mirror=True,

        # 坐标轴刻度线
        ticks='outside',
        tickcolor='black',
        tickwidth=1,
        ticklen=5,

        zeroline=False,
        ticksuffix='%',

        # X轴标题和刻度文字改黑
        title_font=dict(
            size=13,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        tickfont=dict(
            size=12,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    yaxis=dict(
        title='客服呼叫次数',
        categoryorder='array',
        categoryarray=y_order,

        showgrid=False,

        # 黑色边框关键设置
        showline=True,
        linecolor='black',
        linewidth=1.5,
        mirror=True,

        # 坐标轴刻度线
        ticks='outside',
        tickcolor='black',
        tickwidth=1,
        ticklen=5,

        # Y轴标题和刻度文字改黑
        title_font=dict(
            size=13,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        ),
        tickfont=dict(
            size=13,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    legend=dict(
        title=' ',
        orientation='h',
        yanchor='bottom',
        y=1.08,
        xanchor='center',
        x=0.5,
        font=dict(
            size=12,
            color='black',
            family='Microsoft YaHei, SimHei, Arial'
        )
    ),

    plot_bgcolor='white',
    paper_bgcolor='white',

    margin=dict(
        t=120,
        b=50,
        l=80,
        r=90
    ),

    hoverlabel=dict(
        bgcolor='white',
        bordercolor='black',
        font=dict(
            color='black',
            size=12,
            family='Microsoft YaHei, SimHei, Arial'
        )
    )
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "💡 这张差异图用于比较同一客服呼叫次数下，有无国际套餐客户的流失率差距。"
    "右侧红色差异值越大，说明国际套餐客户在该呼叫次数段的流失风险越突出。"
)


st.markdown("---")

# ======================================================
# 🔺 日间/傍晚/夜间使用结构三元图
# ======================================================
st.subheader("🔺 日间/傍晚/夜间使用结构三元图")

ternary_df = df.copy()

main_minutes = (
    ternary_df['total_day_minutes'] +
    ternary_df['total_eve_minutes'] +
    ternary_df['total_night_minutes']
)

ternary_df['day_pct'] = ternary_df['total_day_minutes'] / main_minutes
ternary_df['eve_pct'] = ternary_df['total_eve_minutes'] / main_minutes
ternary_df['night_pct'] = ternary_df['total_night_minutes'] / main_minutes

sample_ternary = ternary_df.sample(min(1200, len(ternary_df)), random_state=42)

fig = px.scatter_ternary(
    sample_ternary,
    a='day_pct',
    b='eve_pct',
    c='night_pct',
    color='churn_label',
    size='total_charges',
    hover_data={
        'customer_id': True,
        'total_charges': ':.1f',
        'customer_service_calls': True,
        'day_pct': ':.2f',
        'eve_pct': ':.2f',
        'night_pct': ':.2f'
    },
    color_discrete_map={
        '留存': '#3498DB',
        '流失': '#E74C3C'
    },
    labels={
        'day_pct': '日间占比',
        'eve_pct': '傍晚占比',
        'night_pct': '夜间占比'
    }
)

fig.update_layout(
    title='三元散点图：客户日间、傍晚、夜间通话时长占比结构',
    height=620,
    font=dict(color='black', size=13),
    title_font=dict(color='black', size=14),
    legend_font=dict(color='black'),
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(t=60, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 每个点代表一个客户，位置表示其日间、傍晚、夜间通话时长占比，点越大表示总费用越高。")


st.markdown("---")

# ======================================================
# 🧊 3D 客户使用行为空间
# ======================================================
st.subheader("🧊 3D 客户使用行为空间")

sample_3d = df.sample(min(1500, len(df)), random_state=42)

fig = px.scatter_3d(
    sample_3d,
    x='total_minutes',
    y='total_charges',
    z='customer_service_calls',
    color='churn_label',
    size='rule_based_churn_risk_score',
    opacity=0.75,
    hover_data={
        'customer_id': True,
        'state': True,
        'total_calls': True,
        'rule_based_churn_risk_score': True,
        'customer_value_segment': True
    },
    color_discrete_map={
        '留存': '#3498DB',
        '流失': '#E74C3C'
    },
    labels={
        'total_minutes': '总通话时长',
        'total_charges': '总费用',
        'customer_service_calls': '客服呼叫次数',
        'churn_label': '客户状态'
    }
)

fig.update_layout(
    title='3D 散点图：客户总通话时长、总费用与客服呼叫次数空间分布',
    height=700,
    font=dict(color='black', size=12),
    title_font=dict(color='black', size=14),
    legend_font=dict(color='black'),
    paper_bgcolor='white',
    scene=dict(
        xaxis=dict(backgroundcolor='white', gridcolor='#D5DBDB'),
        yaxis=dict(backgroundcolor='white', gridcolor='#D5DBDB'),
        zaxis=dict(backgroundcolor='white', gridcolor='#D5DBDB')
    ),
    margin=dict(t=60, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 可以观察流失客户是否集中在高费用、高客服呼叫、高风险分数区域。")


st.markdown("---")

# ======================================================
# 🧭 生命周期与风险分层分析
# ======================================================
st.subheader("🧭 生命周期与风险分层分析")

# 如果前面还没有创建 account_age_days，则这里兜底创建
if 'account_age_days' not in df.columns:
    df['account_age_days'] = df['account_length']



# ======================================================
# 图A：账户开通时长分箱客户数量与流失率组合图
# ======================================================
st.markdown("**不同账户开通时长区间的客户数量与流失率**")

age_bins = [0, 30, 60, 90, 120, 150, 180, np.inf]
age_labels = ['0-30天', '31-60天', '61-90天', '91-120天', '121-150天', '151-180天', '180天以上']

age_df = df.copy()
age_df['account_age_group'] = pd.cut(
    age_df['account_age_days'],
    bins=age_bins,
    labels=age_labels,
    right=True,
    include_lowest=True
)

age_stats = age_df.groupby('account_age_group', observed=False).agg(
    customer_count=('churn_int', 'count'),
    churn_rate=('churn_int', 'mean')
).reset_index()

age_stats['churn_rate'] = age_stats['churn_rate'] * 100

fig_age = go.Figure()

# 高级蓝色柱子
fig_age.add_trace(go.Bar(
    x=age_stats['account_age_group'],
    y=age_stats['customer_count'],
    name='客户数量',
    marker_color='#165DFF',
    marker_line_width=0,
    text=age_stats['customer_count'],
    textposition='outside',
    textfont=dict(color='black', size=11, weight='bold'),
    yaxis='y1',
    hovertemplate='账户开通时长区间: %{x}<br>客户数量: %{y}<extra></extra>'
))

# 高级红色线条
fig_age.add_trace(go.Scatter(
    x=age_stats['account_age_group'],
    y=age_stats['churn_rate'],
    name='流失率',
    mode='lines+markers+text',
    line=dict(color='#F53F3F', width=3),
    marker=dict(
        size=9,
        color='#F53F3F',
        line=dict(color='white', width=1.5)
    ),
    text=age_stats['churn_rate'].apply(lambda x: f'{x:.1f}%'),
    textposition='bottom center',  # 放在下方
    # ✅ 正确调整距离的写法，不报错！
    textfont=dict(color='#F53F3F', size=11, weight='bold'),
    yaxis='y2',
    hovertemplate='账户开通时长区间: %{x}<br>流失率: %{y:.1f}%<extra></extra>'
))

# ===================== 修复冲突版布局 =====================
fig_age.update_layout(
    **common_layout,
    title='不同账户开通时长区间的客户数量与流失率组合图',
    title_x=0.2,
    title_font=dict(size=16, color='black', weight='bold'),

    # X 轴全黑
    xaxis=dict(
        title='账户开通时长区间',
        title_font=dict(color='black', size=12),
        tickfont=dict(color='black', size=11),
        showgrid=False,
    ),

    # 左侧 Y 轴全黑
    yaxis=dict(
        title='客户数量',
        title_font=dict(color='black', size=12),
        tickfont=dict(color='black', size=11),
        showgrid=True,
        gridcolor='#F0F2F5',
        zeroline=False
    ),

    # 右侧 Y 轴全黑
    yaxis2=dict(
        title='流失率 (%)',
        title_font=dict(color='black', size=12),
        tickfont=dict(color='black', size=11),
        overlaying='y',
        side='right',
        showgrid=False,
        rangemode='tozero'
    ),

    # 图例黑色
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.06,
        xanchor='right',
        x=1,
        font=dict(color='black')
    ),

    height=480,
    margin=dict(t=80, b=50, l=50, r=50)
)

st.plotly_chart(fig_age, use_container_width=True)

st.info(
    "💡 **洞察方向**: 该图用于观察客户生命周期中的高流失阶段。"
    "如果短账龄客户流失率较高，可能说明新客激活或早期体验存在问题；"
    "如果长账龄客户流失率升高，可能与套餐老化、价格敏感或竞品迁移有关。"
)

st.markdown("")











# ======================================================
# 图B：客服呼叫次数 × 总费用 流失率热力图
# ======================================================
st.markdown("**客服呼叫次数与总费用组合下的流失率**")

risk_heat_df = df.copy()

# 客服呼叫次数分组，避免高次数太稀疏
risk_heat_df['service_call_group'] = risk_heat_df['customer_service_calls'].apply(
    lambda x: '4次及以上' if x >= 4 else f'{int(x)}次'
)

service_order = ['0次', '1次', '2次', '3次', '4次及以上']
risk_heat_df['service_call_group'] = pd.Categorical(
    risk_heat_df['service_call_group'],
    categories=service_order,
    ordered=True
)

# 总费用按分位数分组，增强每组样本稳定性
risk_heat_df['charge_group'] = pd.qcut(
    risk_heat_df['total_charges'],
    q=4,
    labels=['低费用', '中低费用', '中高费用', '高费用'],
    duplicates='drop'
)

risk_matrix = risk_heat_df.groupby(
    ['charge_group', 'service_call_group'],
    observed=False
).agg(
    churn_rate=('churn_int', 'mean'),
    customer_count=('churn_int', 'count')
).reset_index()

risk_matrix['churn_rate'] = risk_matrix['churn_rate'] * 100

risk_pivot = risk_matrix.pivot(
    index='charge_group',
    columns='service_call_group',
    values='churn_rate'
)

count_pivot = risk_matrix.pivot(
    index='charge_group',
    columns='service_call_group',
    values='customer_count'
)

# 保证列顺序稳定
risk_pivot = risk_pivot.reindex(columns=service_order)
count_pivot = count_pivot.reindex(columns=service_order)

hover_text = []
for charge_group in risk_pivot.index:
    row_text = []
    for call_group in risk_pivot.columns:
        rate = risk_pivot.loc[charge_group, call_group]
        count = count_pivot.loc[charge_group, call_group]

        if pd.isna(rate):
            row_text.append('无样本')
        else:
            row_text.append(
                f'费用分组: {charge_group}<br>'
                f'客服呼叫次数: {call_group}<br>'
                f'流失率: {rate:.1f}%<br>'
                f'样本量: {int(count)}'
            )
    hover_text.append(row_text)

fig_risk_heat = go.Figure(data=go.Heatmap(
    z=risk_pivot.values,
    x=risk_pivot.columns.astype(str),
    y=risk_pivot.index.astype(str),
    colorscale='YlOrRd',
    text=np.round(risk_pivot.values, 1),
    texttemplate='%{text}%',
    textfont=dict(color='black', size=11),
    customdata=hover_text,
    hovertemplate='%{customdata}<extra></extra>',
    colorbar=dict(title='流失率 (%)')
))

fig_risk_heat.update_layout(
    **common_layout,
    title='热力图：客服呼叫次数与总费用组合下的客户流失率',
    xaxis_title='客服呼叫次数分组',
    yaxis_title='总费用分组',
    height=430,
    margin=dict(t=70, b=50, l=60, r=40)
)

fig_risk_heat.update_xaxes(tickfont=dict(color='black'), title_font=dict(color='black'))
fig_risk_heat.update_yaxes(tickfont=dict(color='black'), title_font=dict(color='black'))

st.plotly_chart(fig_risk_heat, use_container_width=True)

st.info(
    "💡 **洞察方向**: 该热力图可以帮助定位高价值但高风险的客户组合。"
    "如果高费用客户同时存在多次客服呼叫，且对应流失率明显升高，"
    "这类客户通常应优先纳入人工回访、账单解释或专属挽留策略。"
)


st.markdown("")









# ======================================================
# 图C：使用强度 -> 客户价值 -> 风险等级 -> 流失状态 桑基图
# ======================================================
st.markdown("**客户使用强度、价值分层、风险等级与流失状态路径**")

sankey_cols = [
    'usage_intensity',
    'customer_value_segment',
    'rule_based_churn_risk_level',
    'churn_label'
]

missing_sankey_cols = [col for col in sankey_cols if col not in df.columns]

if missing_sankey_cols:
    st.warning(f"缺少字段，暂时无法绘制桑基图：{missing_sankey_cols}")
else:
    sankey_df = df[sankey_cols].copy()

    # 中文标签映射，让图更适合展示
    usage_map = {
        'low_usage': '低使用强度',
        'medium_usage': '中使用强度',
        'high_usage': '高使用强度'
    }

    value_map = {
        'low_value': '低价值客户',
        'medium_value': '中价值客户',
        'high_value': '高价值客户'
    }

    risk_map = {
        'low': '低风险',
        'medium': '中风险',
        'high': '高风险'
    }

    sankey_df['usage_intensity_label'] = sankey_df['usage_intensity'].map(usage_map).fillna(sankey_df['usage_intensity'])
    sankey_df['customer_value_label'] = sankey_df['customer_value_segment'].map(value_map).fillna(sankey_df['customer_value_segment'])
    sankey_df['risk_level_label'] = sankey_df['rule_based_churn_risk_level'].map(risk_map).fillna(sankey_df['rule_based_churn_risk_level'])

    # 为避免不同层级中出现相同名称导致节点混淆，内部节点名加前缀，展示标签不加前缀
    sankey_df['node_usage'] = '使用强度｜' + sankey_df['usage_intensity_label'].astype(str)
    sankey_df['node_value'] = '客户价值｜' + sankey_df['customer_value_label'].astype(str)
    sankey_df['node_risk'] = '风险等级｜' + sankey_df['risk_level_label'].astype(str)
    sankey_df['node_churn'] = '流失状态｜' + sankey_df['churn_label'].astype(str)

    # 构造三段路径
    link_1 = sankey_df.groupby(['node_usage', 'node_value']).size().reset_index(name='value')
    link_1.columns = ['source', 'target', 'value']

    link_2 = sankey_df.groupby(['node_value', 'node_risk']).size().reset_index(name='value')
    link_2.columns = ['source', 'target', 'value']

    link_3 = sankey_df.groupby(['node_risk', 'node_churn']).size().reset_index(name='value')
    link_3.columns = ['source', 'target', 'value']

    links = pd.concat([link_1, link_2, link_3], ignore_index=True)

    # 构造节点
    nodes = pd.unique(links[['source', 'target']].values.ravel('K')).tolist()
    node_index = {node: idx for idx, node in enumerate(nodes)}

    links['source_id'] = links['source'].map(node_index)
    links['target_id'] = links['target'].map(node_index)

    # 展示标签去掉内部前缀
    display_labels = [
        node.split('｜', 1)[1] if '｜' in node else node
        for node in nodes
    ]

    # 节点颜色
    node_colors = []
    for node in nodes:
        if node.startswith('使用强度'):
            node_colors.append('#85C1E9')
        elif node.startswith('客户价值'):
            node_colors.append('#F8C471')
        elif node.startswith('风险等级'):
            node_colors.append('#BB8FCE')
        elif node.endswith('流失'):
            node_colors.append('#E74C3C')
        elif node.endswith('留存'):
            node_colors.append('#3498DB')
        else:
            node_colors.append('#BDC3C7')

    # 连线颜色
    link_colors = []
    for target in links['target']:
        if target.endswith('流失'):
            link_colors.append('rgba(231, 76, 60, 0.35)')
        elif target.endswith('留存'):
            link_colors.append('rgba(52, 152, 219, 0.30)')
        else:
            link_colors.append('rgba(149, 165, 166, 0.25)')

    fig_sankey = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=18,
            thickness=18,
            line=dict(color='black', width=0.4),
            label=display_labels,
            color=node_colors
        ),
        link=dict(
            source=links['source_id'],
            target=links['target_id'],
            value=links['value'],
            color=link_colors,
            customdata=links[['source', 'target', 'value']],
            hovertemplate=(
                '来源: %{customdata[0]}<br>'
                '去向: %{customdata[1]}<br>'
                '客户数: %{customdata[2]}'
                '<extra></extra>'
            )
        )
    )])

    fig_sankey.update_layout(
        **common_layout,
        title='桑基图：客户使用强度、价值分层、风险等级与流失状态路径',
        height=620,
        margin=dict(t=70, b=30, l=30, r=30)
    )

    st.plotly_chart(fig_sankey, use_container_width=True)

    st.info(
        "💡 **洞察方向**: 桑基图用于观察客户从使用强度、价值分层、风险等级到最终流失状态的路径。"
        "如果某些路径明显流向“流失”，例如“高使用强度 → 高价值客户 → 中/高风险 → 流失”，"
        "说明这类客户虽然价值较高，但体验或资费压力可能较大，应优先制定挽留策略。"
    )
