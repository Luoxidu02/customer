# views/eda/full_customers/geo.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.data_loader import load_full_customers

st.title("📈 地域分析")
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
    # title=None,  # 防止显示 undefined
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
# 🗺️ 地域分布分析
# ======================================================
st.subheader("🗺️ 地域分布分析")
# 州缩写 -> 完整州名映射
state_name_map = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}
# 图5: 各州客户数量
# st.markdown("**各州客户数量 **")
# ======================================================
# 🌹 各州客户数量玫瑰图
# ======================================================

st.markdown("#### 🌹 各州客户数量玫瑰图")

# 显示全部州
top_n = df['state'].nunique()

state_count = df['state'].value_counts().reset_index()
state_count.columns = ['state', 'count']

# 映射完整州名
state_count['state_name'] = state_count['state'].map(state_name_map).fillna(state_count['state'])
state_count['state_label'] = state_count['state_name'] + ' (' + state_count['state'] + ')'

# 计算占比
total_count = state_count['count'].sum()
state_count['percent'] = state_count['count'] / total_count * 100

# 按数量排序
state_count = state_count.sort_values('count', ascending=False).reset_index(drop=True)

# 为标签计算位置
max_count = state_count['count'].max()
state_count['count_label_r'] = state_count['count'] + max_count * 0.03
# state_count['state_text_r'] = state_count['count'] * 0.55

# 玫瑰图
fig_state_count = px.bar_polar(
    state_count,
    r='count',
    theta='state',
    color='count',
    template='plotly_white',
    color_continuous_scale=[
        [0.00, "#E8F1FF"],
        [0.25, "#A9C9FF"],
        [0.50, "#5B8FF9"],
        [0.75, "#2F54EB"],
        [1.00, "#10239E"]
    ],
    custom_data=['state_name', 'state', 'count', 'percent', 'state_label']
)

# 花瓣样式
fig_state_count.update_traces(
    marker=dict(
        line=dict(
            color='white',
            width=1.4
        ),
        opacity=0.92
    ),
    hovertemplate=
    "<b>%{customdata[0]} (%{customdata[1]})</b><br>" +
    "客户数量：%{customdata[2]}<br>" +
    "占比：%{customdata[3]:.2f}%<extra></extra>"
)

# 布局美化
fig_state_count.update_layout(
    title=dict(
        text=f'各州客户数量分布玫瑰图',
        x=0.5,
        xanchor='center',
        font=dict(
            size=22,
            color='#111827',
            family='Microsoft YaHei, Arial'
        )
    ),

    height=820,

    paper_bgcolor='white',
    plot_bgcolor='white',

    margin=dict(t=50, b=50, l=40, r=40),

    font=dict(
        family='Microsoft YaHei, Arial',
        color='#111827'
    ),

    coloraxis=dict(
        showscale=True,
        colorbar=dict(
            title='客户数量',
            thickness=14,
            len=0.72
        )
    ),

    polar=dict(
        bgcolor='rgba(248,250,252,1)',

        radialaxis=dict(
            showline=False,
            showgrid=True,
            showticklabels=False,
            gridcolor='rgba(148,163,184,0.35)',
            gridwidth=1,
            range=[0, max_count * 1.06]
        ),

        angularaxis=dict(
            showline=False,
            showgrid=True,
            gridcolor='rgba(203,213,225,0.45)',
            tickfont=dict(
                size=10,
                color='#334155'
            ),
            rotation=90,
            direction='clockwise'
        )
    )
)


# 在每个小扇形外侧标注客户数量
fig_state_count.add_trace(
    go.Scatterpolar(
        r=state_count['count_label_r'],
        theta=state_count['state'],
        mode='text',
        text=state_count['count'].astype(str),
        textfont=dict(
            size=9,
            color='#0F172A',
            family='Microsoft YaHei, Arial'
        ),
        hoverinfo='skip',
        showlegend=False
    )
)

# 中心小圆：显示州数量
fig_state_count.add_trace(
    go.Scatterpolar(
        r=[0],
        theta=[state_count['state'].iloc[0]],
        mode='markers+text',
        marker=dict(
            size=86,
            color='white',
            line=dict(
                color='rgba(148,163,184,0.55)',
                width=1.5
            )
        ),
        text=[f"<b>{top_n}</b><br>states"],
        textfont=dict(
            size=15,
            color='#0F172A',
            family='Microsoft YaHei, Arial'
        ),
        textposition='middle center',
        hoverinfo='skip',
        showlegend=False
    )
)


st.plotly_chart(fig_state_count, use_container_width=True)


light_divider()
# 图5-补充: 美国各州客户数量地图热力图
st.markdown("**美国各州客户数量热力图**")

# 各州客户数量统计
state_count_all = df['state'].value_counts().reset_index()
state_count_all.columns = ['state', 'count']



state_count_all['state_name'] = state_count_all['state'].map(state_name_map)
state_count_all['map_label'] = state_count_all.apply(
    lambda r: f"{r['state']}<br>{int(r['count'])}",
    axis=1
)

fig_state_count_map = px.choropleth(
    state_count_all,
    locations='state',
    locationmode='USA-states',
    color='count',
    color_continuous_scale='Blues',
    range_color=[
        state_count_all['count'].min(),
        state_count_all['count'].max()
    ],
    scope='north america',
    hover_data={
        'state': True,
        'state_name': True,
        'count': True
    },
    labels={
        'count': '客户数量',
        'state': '州',
        'state_name': '州名'
    }
)
fig_state_count_map.add_trace(
    go.Scattergeo(
        locations=state_count_all['state'],
        locationmode='USA-states',
        text=state_count_all['map_label'],
        mode='text',
        textfont=dict(color='black', size=9),
        hoverinfo='skip',
        showlegend=False
    )
)


fig_state_count_map.update_layout(
    **common_layout,
    geo=dict(
        visible=True,
        scope='north america',
        projection_type='mercator',

        # 控制显示范围：美国本土 + 加拿大南部 + 墨西哥北部
        lonaxis=dict(range=[-130, -60]),
        lataxis=dict(range=[20, 58]),

        bgcolor='#DFF3FF',

        showland=True,
        landcolor='#EFE6D3',

        showocean=True,
        oceancolor='#B8E3F5',

        showlakes=True,
        lakecolor='#A9DDF5',

        showrivers=True,
        rivercolor='#7EC8E3',

        showcoastlines=True,
        coastlinecolor='#4F5B62',
        coastlinewidth=1,

        showcountries=True,
        countrycolor='#666666',
        countrywidth=1,

        showsubunits=True,
        subunitcolor='white',
        subunitwidth=0.7,

        showframe=False,
        resolution=50
    ),

    title=dict(
        text='各州客户数量热力图',
        x=0.5,
        xanchor='center',
        font=dict(color='black', size=18)
    ),
    coloraxis_colorbar=dict(
        title=dict(text='客户数量', font=dict(color='black')),
        tickfont=dict(color='black'),
    ),
    height=800,
    margin=dict(t=55, b=20, l=10, r=90),

    hoverlabel=dict(
        bgcolor='white',
        font=dict(color='black', size=13),
        bordercolor='black'
    )
)

st.plotly_chart(fig_state_count_map, use_container_width=True)

light_divider()

# 图6: 各州流失率
# 图6: 各州流失率
# ======================================================
# 🌹 各州客户流失率玫瑰图
# ======================================================

st.markdown("#### 🌹 各州客户流失率玫瑰图")

# 各州客户流失率统计
state_churn = df.groupby('state')['churn_int'].agg(['count', 'mean']).reset_index()

# 如果你要显示所有州，就不要筛选 count >= 15
# state_churn = state_churn[state_churn['count'] >= 15]

# 计算流失率
state_churn['churn_rate'] = state_churn['mean'] * 100

# 按流失率排序
state_churn = state_churn.sort_values('churn_rate', ascending=False).reset_index(drop=True)

# 映射完整州名
state_churn['state_name'] = state_churn['state'].map(state_name_map).fillna(state_churn['state'])
state_churn['state_label'] = state_churn['state_name'] + ' (' + state_churn['state'] + ')'

# 显示州数量
top_n_churn = state_churn['state'].nunique()

# 为标签计算位置
max_churn_rate = state_churn['churn_rate'].max()
state_churn['churn_label_r'] = state_churn['churn_rate'] + max_churn_rate * 0.05

# 玫瑰图
fig_state_churn = px.bar_polar(
    state_churn,
    r='churn_rate',
    theta='state',
    color='churn_rate',
    template='plotly_white',
    color_continuous_scale=[
        [0.00, "#D1FAE5"],
        [0.25, "#A7F3D0"],
        [0.50, "#FDE68A"],
        [0.75, "#FDBA74"],
        [1.00, "#EF4444"]
    ],
    custom_data=['state_name', 'state', 'count', 'churn_rate', 'state_label']
)

# 花瓣样式
fig_state_churn.update_traces(
    marker=dict(
        line=dict(
            color='white',
            width=1.4
        ),
        opacity=0.92
    ),
    hovertemplate=
    "<b>%{customdata[0]} (%{customdata[1]})</b><br>" +
    "客户数量：%{customdata[2]}<br>" +
    "流失率：%{customdata[3]:.2f}%<extra></extra>"
)

# 布局美化
fig_state_churn.update_layout(
    title=dict(
        text='各州客户流失率分布玫瑰图',
        x=0.5,
        xanchor='center',
        font=dict(
            size=22,
            color='#111827',
            family='Microsoft YaHei, Arial'
        )
    ),

    height=900,

    paper_bgcolor='white',
    plot_bgcolor='white',

    margin=dict(t=50, b=50, l=40, r=40),

    font=dict(
        family='Microsoft YaHei, Arial',
        color='#111827'
    ),

    coloraxis=dict(
        showscale=True,
        colorbar=dict(
            title='流失率 (%)',
            thickness=14,
            len=0.72
        )
    ),

    polar=dict(
        bgcolor='rgba(248,250,252,1)',

        radialaxis=dict(
            showline=False,
            showgrid=True,
            showticklabels=False,
            gridcolor='rgba(148,163,184,0.35)',
            gridwidth=1,
            range=[0, max_churn_rate * 1.08]
        ),

        angularaxis=dict(
            showline=False,
            showgrid=True,
            gridcolor='rgba(203,213,225,0.45)',
            tickfont=dict(
                size=10,
                color='#334155'
            ),
            rotation=90,
            direction='clockwise'
        )
    )
)

# 在每个小扇形外侧标注流失率
fig_state_churn.add_trace(
    go.Scatterpolar(
        r=state_churn['churn_label_r'],
        theta=state_churn['state'],
        mode='text',
        text=state_churn['churn_rate'].apply(lambda x: f'{x:.1f}'),
        textfont=dict(
            size=[7 if i >= len(state_churn) - 5 else 9 for i in range(len(state_churn))],

            color='#0F172A',
            family='Microsoft YaHei, Arial'
        ),
        hoverinfo='skip',
        showlegend=False
    )
)

# 中心小圆：显示州数量
fig_state_churn.add_trace(
    go.Scatterpolar(
        r=[0],
        theta=[state_churn['state'].iloc[0]],
        mode='markers+text',
        marker=dict(
            size=86,
            color='white',
            line=dict(
                color='rgba(148,163,184,0.55)',
                width=1.5
            )
        ),
        text=[f"<b>{top_n_churn}</b><br>states"],
        textfont=dict(
            size=15,
            color='#0F172A',
            family='Microsoft YaHei, Arial'
        ),
        textposition='middle center',
        hoverinfo='skip',
        showlegend=False
    )
)

st.plotly_chart(fig_state_churn, use_container_width=True)


light_divider()

# 图7: 各州流失率地图热力图
st.markdown("**美国各州客户流失率热力图**")

state_churn_all = df.groupby('state')['churn_int'].agg(['count', 'mean']).reset_index()
# state_churn_all = state_churn_all[state_churn_all['count'] >= 15]
state_churn_all['churn_rate'] = state_churn_all['mean'] * 100

state_churn_all['state_name'] = state_churn_all['state'].map(state_name_map)
state_churn_all['map_label'] = state_churn_all.apply(
    lambda r: f"{r['state']}<br>{r['churn_rate']:.1f}%",
    axis=1
)

fig_map = px.choropleth(
    state_churn_all,
    locations='state',
    locationmode='USA-states',
    color='churn_rate',
    color_continuous_scale='YlOrRd',
    range_color=[state_churn_all['churn_rate'].min(), state_churn_all['churn_rate'].max()],
    scope='north america',

    hover_data={'state': True, 'state_name': True, 'churn_rate': ':.1f', 'count': True},
    labels={'churn_rate': '流失率 (%)', 'count': '客户数', 'state': '州', 'state_name': '州名'}
)
fig_map.add_trace(
    go.Scattergeo(
        locations=state_churn_all['state'],
        locationmode='USA-states',
        text=state_churn_all['map_label'],
        mode='text',
        textfont=dict(color='black', size=9),
        hoverinfo='skip',
        showlegend=False
    )
)

fig_map.update_layout(
    **common_layout,
    geo=dict(
        visible=True,
        scope='north america',
        projection_type='mercator',

        # 控制显示范围：美国本土 + 加拿大南部 + 墨西哥北部
        lonaxis=dict(range=[-130, -60]),
        lataxis=dict(range=[20, 58]),

        bgcolor='#DFF3FF',

        showland=True,
        landcolor='#EFE6D3',

        showocean=True,
        oceancolor='#B8E3F5',

        showlakes=True,
        lakecolor='#A9DDF5',

        showrivers=True,
        rivercolor='#7EC8E3',

        showcoastlines=True,
        coastlinecolor='#4F5B62',
        coastlinewidth=1,

        showcountries=True,
        countrycolor='#666666',
        countrywidth=1,

        showsubunits=True,
        subunitcolor='white',
        subunitwidth=0.7,

        showframe=False,
        resolution=50
    ),

    title=dict(
        text='各州客户流失率热力图',
        x=0.5,
        xanchor='center',
        font=dict(color='black', size=18)
    ),
    coloraxis_colorbar=dict(
        title=dict(text='客户数量', font=dict(color='black')),
        tickfont=dict(color='black'),
        x=0.98,
        len=0.75,
        thickness=16
    ),

    height=800,
    margin=dict(t=30, b=30, l=0, r=0)
)
st.plotly_chart(fig_map, use_container_width=True)



light_divider()

# ======================================================
# 🧭 各州用户行为特征环形热力图
# ======================================================
st.subheader("🧭 各州用户行为特征环形热力图")

st.caption(
    "该图以州为圆周方向，每一圈表示一个用户行为特征，颜色表示该州在该特征上的相对水平。"
    "为便于不同量纲特征之间比较，所有指标均按特征维度进行 Min-Max 标准化。"
)

# -----------------------------
# 1. 构造各州行为特征聚合表
# -----------------------------
state_behavior = df.groupby('state').agg(
    customer_count=('churn_int', 'size'),
    churn_rate=('churn_int', 'mean')
).reset_index()

state_behavior['churn_rate'] = state_behavior['churn_rate'] * 100
state_behavior['state_name'] = state_behavior['state'].map(state_name_map).fillna(state_behavior['state'])

# 可选行为特征：如果字段存在，就自动加入
candidate_behavior_features = [
    ('total_minutes', '平均总通话时长', '分钟'),
    ('total_calls', '平均总通话次数', '次'),
    ('total_charges', '平均总费用', '$'),
    ('customer_service_calls', '平均客服拨打次数', '次'),
    ('total_day_minutes', '平均白天通话时长', '分钟'),
    ('total_eve_minutes', '平均傍晚通话时长', '分钟'),
    ('total_night_minutes', '平均夜间通话时长', '分钟'),
    ('total_intl_minutes', '平均国际通话时长', '分钟'),
    ('avg_charge_per_minute', '平均每分钟费用', '$/分钟'),
    ('rule_based_churn_risk_score', '平均规则流失风险评分', '分')
]

available_metrics = [
    ('churn_rate', '客户流失率', '%')
]

for col, label, unit in candidate_behavior_features:
    if col in df.columns:
        tmp = df.groupby('state')[col].mean().reset_index()
        metric_key = f'avg_{col}'
        tmp = tmp.rename(columns={col: metric_key})
        state_behavior = state_behavior.merge(tmp, on='state', how='left')
        available_metrics.append((metric_key, label, unit))

# 默认展示前 7 个指标，避免圈数太多
metric_label_map = {m[0]: m[1] for m in available_metrics}

default_metrics = [m[0] for m in available_metrics[:7]]

selected_metric_keys = st.multiselect(
    "选择要展示的用户行为特征",
    options=[m[0] for m in available_metrics],
    default=default_metrics,
    format_func=lambda x: metric_label_map.get(x, x)
)

selected_metrics = [m for m in available_metrics if m[0] in selected_metric_keys]

if len(selected_metrics) == 0:
    st.info("请选择至少一个行为特征。")
else:
    # -----------------------------
    # 2. 按流失率排序，让高风险州聚集在一起
    # -----------------------------
    state_behavior = state_behavior.sort_values(
        'churn_rate',
        ascending=False
    ).reset_index(drop=True)

    n_states = len(state_behavior)
    n_rings = len(selected_metrics)

    # 每个州对应一个角度
    angle_step = 360 / n_states
    state_behavior['theta'] = np.arange(n_states) * angle_step
    bar_width = angle_step * 0.92

    # -----------------------------
    # 3. 指标格式化函数
    # -----------------------------
    def format_metric_value(value, unit):
        if pd.isna(value):
            return "NA"
        if unit == '%':
            return f"{value:.1f}%"
        elif unit == '$':
            return f"${value:,.1f}"
        elif unit == '$/分钟':
            return f"${value:.3f}/分钟"
        elif unit == '次':
            return f"{value:.2f} 次"
        elif unit == '分钟':
            return f"{value:.1f} 分钟"
        elif unit == '分':
            return f"{value:.2f} 分"
        else:
            return f"{value:.2f}"

    # -----------------------------
    # 4. 为每个特征做 Min-Max 标准化
    # -----------------------------
    for metric_key, metric_label, unit in selected_metrics:
        vals = state_behavior[metric_key].astype(float)

        if vals.max() == vals.min():
            state_behavior[f'{metric_key}_norm'] = 50
        else:
            state_behavior[f'{metric_key}_norm'] = (
                (vals - vals.min()) / (vals.max() - vals.min()) * 100
            )

        state_behavior[f'{metric_key}_raw_label'] = vals.apply(
            lambda x: format_metric_value(x, unit)
        )

    # -----------------------------
    # 4.5 输出环形热力图使用的数据，方便报告分析
    # -----------------------------

    # 原始数据表：图中每个州各指标的真实均值
    raw_cols = ['state', 'state_name', 'customer_count'] + [m[0] for m in selected_metrics]
    ring_raw_data = state_behavior[raw_cols].copy()

    # 标准化数据表：图中颜色实际对应的 0-100 数值
    norm_cols = ['state', 'state_name', 'customer_count'] + [f'{m[0]}_norm' for m in selected_metrics]
    ring_norm_data = state_behavior[norm_cols].copy()

    # 重命名列，方便查看
    raw_rename_map = {
        'state': '州缩写',
        'state_name': '州名',
        'customer_count': '客户数量'
    }

    norm_rename_map = {
        'state': '州缩写',
        'state_name': '州名',
        'customer_count': '客户数量'
    }

    for metric_key, metric_label, unit in selected_metrics:
        raw_rename_map[metric_key] = metric_label
        norm_rename_map[f'{metric_key}_norm'] = metric_label + '_标准化得分'

    ring_raw_data = ring_raw_data.rename(columns=raw_rename_map)
    ring_norm_data = ring_norm_data.rename(columns=norm_rename_map)

    # 每个指标取标准化得分最高的前 8 个州
    top_metric_rows = []

    for metric_key, metric_label, unit in selected_metrics:
        temp_top = state_behavior.sort_values(
            f'{metric_key}_norm',
            ascending=False
        ).head(8)

        for _, row in temp_top.iterrows():
            top_metric_rows.append({
                '指标': metric_label,
                '州缩写': row['state'],
                '州名': row['state_name'],
                '客户数量': int(row['customer_count']),
                '原始值': row[f'{metric_key}_raw_label'],
                '标准化得分': round(row[f'{metric_key}_norm'], 2),
                '流失率': f"{row['churn_rate']:.1f}%"
            })

    ring_top_data = pd.DataFrame(top_metric_rows)

    # 在页面中折叠展示，避免影响图表阅读
    with st.expander("查看环形热力图使用的数据"):
        st.markdown("##### 1. 各州原始行为指标数据")
        st.dataframe(ring_raw_data, use_container_width=True)

        st.download_button(
            label="下载原始指标数据 CSV",
            data=ring_raw_data.to_csv(index=False).encode('utf-8-sig'),
            file_name="各州用户行为特征_原始数据.csv",
            mime="text/csv"
        )

        st.markdown("##### 2. 各州标准化后热力图数据 0-100")
        st.dataframe(ring_norm_data.round(2), use_container_width=True)

        st.download_button(
            label="下载标准化热力图数据 CSV",
            data=ring_norm_data.round(2).to_csv(index=False).encode('utf-8-sig'),
            file_name="各州用户行为特征_标准化数据.csv",
            mime="text/csv"
        )

        st.markdown("##### 3. 每个指标标准化得分 Top 8 州")
        st.dataframe(ring_top_data, use_container_width=True)

        st.download_button(
            label="下载各指标 Top 8 州 CSV",
            data=ring_top_data.to_csv(index=False).encode('utf-8-sig'),
            file_name="各指标Top8州_环形热力图.csv",
            mime="text/csv"
        )

    # -----------------------------
    # 5. 绘制环形热力图
    # -----------------------------
    fig_ring = go.Figure()

    # 高级感配色：深蓝 -> 蓝紫 -> 青色 -> 金黄 -> 红色
    premium_colorscale = [
        [0.00, "#0F172A"],
        [0.18, "#1E3A8A"],
        [0.38, "#2563EB"],
        [0.58, "#06B6D4"],
        [0.76, "#FACC15"],
        [1.00, "#EF4444"]
    ]

    ring_width = 0.78
    inner_radius = 0.85

    for i, (metric_key, metric_label, unit) in enumerate(selected_metrics):
        ring_base = inner_radius + i
        ring_mid = ring_base + ring_width / 2

        customdata = np.stack([
            state_behavior['state_name'],
            state_behavior['state'],
            state_behavior['customer_count'].astype(str),
            state_behavior[f'{metric_key}_raw_label']
        ], axis=-1)

        fig_ring.add_trace(
            go.Barpolar(
                r=np.full(n_states, ring_width),
                base=np.full(n_states, ring_base),
                theta=state_behavior['theta'],
                width=np.full(n_states, bar_width),

                marker=dict(
                    color=state_behavior[f'{metric_key}_norm'],
                    colorscale=premium_colorscale,
                    cmin=0,
                    cmax=100,
                    line=dict(
                        color='rgba(255,255,255,0.65)',
                        width=0.7
                    ),
                    showscale=True if i == 0 else False,
                    colorbar=dict(
                        title=dict(
                            text='标准化强度<br>0-100',
                            font=dict(color='#111827', size=12)
                        ),
                        tickfont=dict(color='#111827', size=11),
                        thickness=15,
                        len=0.72,
                        x=1.08
                    ) if i == 0 else None
                ),

                opacity=0.96,
                name=metric_label,
                customdata=customdata,

                hovertemplate=
                "<b>%{customdata[0]} (%{customdata[1]})</b><br>" +
                f"指标：{metric_label}<br>" +
                "原始均值：%{customdata[3]}<br>" +
                "标准化强度：%{marker.color:.1f}<br>" +
                "客户数量：%{customdata[2]}<extra></extra>"
            )
        )

        # 每一圈右侧标注指标名称
        fig_ring.add_trace(
            go.Scatterpolar(
                r=[ring_mid],
                theta=[358],
                mode='text',
                text=[metric_label],
                textfont=dict(
                    size=11,
                    color='white',
                    family='Microsoft YaHei, Arial'
                ),
                textposition='middle right',
                hoverinfo='skip',
                showlegend=False
            )
        )

    # 中心圆
    # ======================================================
    # 自适应中心圆：半径跟随最内圈位置变化，不再使用像素 size
    # ======================================================

    # 中心圆半径必须小于 inner_radius，确保不会盖住最里面一圈
    center_radius = inner_radius * 0.72

    # 字体大小跟中心圆半径自适应
    center_font_size = int(np.clip(center_radius * 16, 10, 15))
    center_sub_font_size = int(np.clip(center_radius * 12, 8, 11))

    # 先画一个真正的极坐标圆盘，而不是 marker 点
    fig_ring.add_trace(
        go.Barpolar(
            r=[center_radius],
            theta=[0],
            width=[360],
            base=[0],
            marker=dict(
                color='rgba(255,255,255,0.96)',
                line=dict(
                    color='rgba(148,163,184,0.80)',
                    width=1.6
                )
            ),
            opacity=1,
            hoverinfo='skip',
            showlegend=False
        )
    )

    # 再单独添加中心文字
    fig_ring.add_trace(
        go.Scatterpolar(
            r=[center_radius * 0.15],
            theta=[0],
            mode='text',
            text=[f"<b>{n_states}</b><br>States"],

            textfont=dict(
                size=center_font_size,
                color='#0F172A',
                family='Microsoft YaHei, Arial'
            ),
            textposition='middle center',
            hoverinfo='skip',
            showlegend=False
        )
    )

    # 外圈州名
    tick_vals = state_behavior['theta'].tolist()
    tick_text = state_behavior['state'].tolist()

    fig_ring.update_layout(
        title=dict(
            text='各州用户行为特征环形热力图',
            x=0.5,
            xanchor='center',
            font=dict(
                size=24,
                color='#0F172A',
                family='Microsoft YaHei, Arial'
            )
        ),

        height=920,

        paper_bgcolor='white',
        plot_bgcolor='white',

        margin=dict(t=80, b=60, l=40, r=120),

        font=dict(
            family='Microsoft YaHei, Arial',
            color='#111827'
        ),

        polar=dict(
            bgcolor='#020617',

            radialaxis=dict(
                range=[0, inner_radius + n_rings + 0.85],
                showline=False,
                showgrid=True,
                gridcolor='rgba(148,163,184,0.18)',
                gridwidth=1,
                showticklabels=False,
                ticks=''
            ),

            angularaxis=dict(
                tickmode='array',
                tickvals=tick_vals,
                ticktext=tick_text,

                rotation=90,
                direction='clockwise',

                showline=False,
                showgrid=True,
                gridcolor='rgba(148,163,184,0.22)',
                gridwidth=1,

                tickfont=dict(
                    size=10,
                    color='#0F172A',
                    family='Microsoft YaHei, Arial'
                )
            )
        ),

        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#334155',
            font=dict(
                color='#0F172A',
                size=13,
                family='Microsoft YaHei, Arial'
            )
        ),

        showlegend=False
    )

    st.plotly_chart(fig_ring, use_container_width=True)

    st.info(
        "💡 该环形热力图用于比较不同州在多个用户行为特征上的相对表现。"
        "颜色越接近红色，表示该州在对应特征上的标准化水平越高；颜色越接近深蓝，表示水平越低。"
    )



strong_divider()

# 各州客户数量 vs 流失率气泡图...哪些州客户多且流失率高？
st.subheader("🗺️ 各州客户规模与流失率气泡图")

state_bubble = df.groupby('state').agg(
    customer_count=('customer_id', 'count'),
    churn_rate=('churn_int', 'mean'),
    avg_revenue=('total_charges', 'mean')
).reset_index()

state_bubble['churn_rate'] *= 100
state_bubble['state_name'] = state_bubble['state'].map(state_name_map)

fig = px.scatter(
    state_bubble,
    x='customer_count',
    y='churn_rate',
    size='avg_revenue',
    color='churn_rate',
    text='state',
    color_continuous_scale=[
        [0.00, "#DBEAFE"],  # 浅冰蓝
        [0.25, "#60A5FA"],  # 高级蓝
        [0.50, "#2563EB"],  # 深蓝
        [0.72, "#F59E0B"],  # 琥珀金
        [1.00, "#B91C1C"]  # 高级酒红
    ],

    hover_data={
        'state_name': True,
        'customer_count': True,
        'churn_rate': ':.1f',
        'avg_revenue': ':.1f'
    },
    labels={
        'customer_count': '客户数量',
        'churn_rate': '流失率 (%)',
        'avg_revenue': '平均费用'
    }
)

fig.update_traces(
    textposition='top center',
    textfont=dict(
        color='#0F172A',
        size=10,
        family='Microsoft YaHei, Arial'
    ),
    marker=dict(
        line=dict(
            color='rgba(15, 23, 42, 0.85)',  # 深蓝灰边框
            width=1.4
        ),
        opacity=0.88
    )
)


fig.update_layout(
    height=800,

    paper_bgcolor='white',
    plot_bgcolor='#F8FAFC',

    font=dict(
        family='Microsoft YaHei, Arial',
        color='#111827',
        size=12
    ),

    title=dict(
        text='各州客户规模与流失率气泡图',
        x=0.5,
        xanchor='center',
        font=dict(
            color='#0F172A',
            size=20,
            family='Microsoft YaHei, Arial'
        )
    ),

    xaxis_title='客户数量',
    yaxis_title='流失率 (%)',

    coloraxis_colorbar=dict(
        title=dict(
            text='流失率 (%)',
            font=dict(color='#111827')
        ),
        tickfont=dict(color='#111827'),
        thickness=15,
        len=0.72
    ),

    margin=dict(t=65, b=55, l=75, r=65),

    hoverlabel=dict(
        bgcolor='white',
        bordercolor='#334155',
        font=dict(
            color='#0F172A',
            size=13,
            family='Microsoft YaHei, Arial'
        )
    )
)


# X轴：加坐标轴线 + 黑色字体 + 竖向网格线
fig.update_xaxes(
    showline=True,              # 显示x轴线
    linecolor='black',          # x轴线颜色
    linewidth=1,
    mirror=True,

    ticks='outside',
    tickcolor='black',
    tickfont=dict(color='black', size=11),
    title_font=dict(color='black', size=13),

    showgrid=True,              # 显示竖向网格线
    gridcolor='rgba(180,180,180,0.35)',
    gridwidth=1,

    zeroline=False
)

# Y轴：加坐标轴线 + 黑色字体
fig.update_yaxes(
    showline=True,              # 显示y轴线
    linecolor='black',          # y轴线颜色
    linewidth=1,
    mirror=True,

    ticks='outside',
    tickcolor='black',
    tickfont=dict(color='black', size=11),
    title_font=dict(color='black', size=13),

    # 如果你也想要横向背景线，设为 True
    showgrid=True,
    gridcolor='rgba(180,180,180,0.25)',
    gridwidth=1,

    zeroline=False
)

st.plotly_chart(fig, use_container_width=True)

strong_divider()

st.subheader("💸 各州流失客户收入损失 Top 15")

state_loss = df.groupby('state').agg(
    customer_count=('customer_id', 'count'),
    churn_count=('churn_int', 'sum'),
    churn_rate=('churn_int', 'mean'),
    total_revenue=('total_charges', 'sum'),
    lost_revenue=('total_charges', lambda x: x[df.loc[x.index, 'churn_int'] == 1].sum())
).reset_index()

state_loss['churn_rate'] *= 100
state_loss['lost_revenue_rate'] = state_loss['lost_revenue'] / state_loss['total_revenue'] * 100
state_loss['state_name'] = state_loss['state'].map(state_name_map)

top_loss = state_loss.sort_values('lost_revenue', ascending=False).head(15)
top_loss['state_label'] = top_loss['state_name'] + '（' + top_loss['state'] + '）'

fig = px.bar(
    top_loss,
    x='lost_revenue',
    y='state_label',
    orientation='h',
    color='lost_revenue_rate',
    text=top_loss['lost_revenue'].apply(lambda x: f"${x:,.0f}"),
    color_continuous_scale='YlOrRd',
    hover_data={
        'customer_count': True,
        'churn_count': True,
        'churn_rate': ':.1f',
        'lost_revenue_rate': ':.1f'
    },
    labels={
        'lost_revenue': '流失客户收入损失',
        'state_label': '州',
        'lost_revenue_rate': '收入损失占比 (%)'
    }
)

fig.update_traces(textposition='outside', textfont=dict(color='black', size=11))

fig.update_layout(
    **common_layout,
    height=550,
    yaxis=dict(categoryorder='total ascending'),
    xaxis_title='流失客户收入损失 ($)',
    yaxis_title='州',
    coloraxis_colorbar=dict(title='收入损失占比'),
    margin=dict(t=40, b=40, l=120, r=80)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 该图结合了地域、流失和收入，可以帮助定位最需要治理的重点市场。")
