# views/eda/full_customers/eda_audit.py
import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_full_customers
import matplotlib.pyplot as plt   # 新增这一行
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
# ======================================================
# Matplotlib / Seaborn 中文字体设置
# ======================================================
plt.rcParams['font.sans-serif'] = [
    'Microsoft YaHei',      # Windows
    'SimHei',               # Windows
    'PingFang SC',          # macOS
    'Arial Unicode MS',     # macOS
    'Noto Sans CJK SC',     # Linux / Docker
    'WenQuanYi Micro Hei'   # Linux
]
plt.rcParams['axes.unicode_minus'] = False

st.title("🔎 全量客户 EDA 数据体检")
st.markdown(
    "<hr style='border: none; height: 3px; background-color: #2C3E50; margin: 35px 0;'>",
    unsafe_allow_html=True
)

# ======================================================
# 数据加载
# ======================================================
df = load_full_customers().copy()

# 兼容 churn 类型
df['churn_int'] = pd.to_numeric(df['churn'], errors='coerce').fillna(0).astype(int)
df['churn_label'] = df['churn_int'].map({0: '留存', 1: '流失'})

st.success("Data loaded successfully.")

# 通用样式
common_layout = dict(
    font=dict(color='black', size=12),
    title_font=dict(color='black', size=14),
    legend_font=dict(color='black'),
    paper_bgcolor='white',
    plot_bgcolor='white'
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

def pct_crosstab(data, row_col, target_col='churn_label'):
    ct = pd.crosstab(
        data[row_col].astype(str),
        data[target_col],
        normalize='index'
    ) * 100

    for col in ['留存', '流失']:
        if col not in ct.columns:
            ct[col] = 0

    ct = ct[['留存', '流失']]
    return ct

# ======================================================
# 1. 数据基本信息
# 对应原代码：
# print("Data loaded successfully.")
# print(f"Shape: {df.shape}")
# print(df.head())
# df.info()
# df.isnull().sum()
# ======================================================
st.subheader("1️⃣ 数据基本信息")

col1, col2, col3, col4 = st.columns(4)
col1.metric("样本行数", f"{df.shape[0]:,}")
col2.metric("字段列数", f"{df.shape[1]:,}")
col3.metric("数值字段数", f"{len(df.select_dtypes(include=[np.number]).columns):,}")
col4.metric("类别/文本字段数", f"{len(df.select_dtypes(exclude=[np.number]).columns):,}")

st.markdown("#### 前 5 行数据")
st.dataframe(df.head(), use_container_width=True)

light_divider()

st.markdown("#### Dataset info")

buffer = io.StringIO()
df.info(buf=buffer)
info_text = buffer.getvalue()
st.code(info_text, language="text")

light_divider()

st.markdown("#### 缺失值统计")

missing_df = pd.DataFrame({
    'column': df.columns,
    'missing_count': df.isnull().sum().values,
    'missing_rate_pct': df.isnull().mean().values * 100,
    'dtype': df.dtypes.astype(str).values
}).sort_values('missing_count', ascending=False)

st.dataframe(
    missing_df,
    use_container_width=True
)

missing_nonzero = missing_df[missing_df['missing_count'] > 0]

if len(missing_nonzero) == 0:
    st.success("当前数据集中没有缺失值。")
else:
    st.warning(f"当前共有 {len(missing_nonzero)} 个字段存在缺失值。")

# 缺失值柱状图
if len(missing_nonzero) > 0:
    fig = px.bar(
        missing_nonzero.sort_values('missing_rate_pct', ascending=True),
        x='missing_rate_pct',
        y='column',
        orientation='h',
        text=missing_nonzero.sort_values('missing_rate_pct', ascending=True)['missing_rate_pct'].apply(lambda x: f"{x:.1f}%"),
        labels={
            'missing_rate_pct': '缺失率 (%)',
            'column': '字段'
        },
        color='missing_rate_pct',
        color_continuous_scale='Reds'
    )

    fig.update_traces(
        textposition='outside',
        textfont=dict(color='black', size=11)
    )

    fig.update_layout(
        **common_layout,
        height=max(360, 24 * len(missing_nonzero)),
        coloraxis_showscale=False,
        margin=dict(t=30, b=30, l=80, r=80)
    )

    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 2. Target variable analysis
# 对应原代码：
# churn_counts = df['churn'].value_counts()
# print(churn_counts)
# print(f"Churn rate: ...")
# sns.countplot(...)
# ======================================================
strong_divider()

st.subheader("2️⃣ 目标变量 churn 分布")

churn_counts = df['churn_int'].value_counts().reindex([0, 1], fill_value=0)
churn_rate = df['churn_int'].mean() * 100

churn_table = pd.DataFrame({
    'churn': [0, 1],
    'label': ['留存', '流失'],
    'count': [churn_counts.loc[0], churn_counts.loc[1]],
})
churn_table['rate_pct'] = churn_table['count'] / len(df) * 100

col1, col2, col3 = st.columns(3)
col1.metric("留存客户数", f"{churn_counts.loc[0]:,}")
col2.metric("流失客户数", f"{churn_counts.loc[1]:,}")
col3.metric("整体流失率", f"{churn_rate:.2f}%")

st.markdown("#### Churn distribution")
st.dataframe(churn_table, use_container_width=True)
fig = go.Figure(
    data=[
        go.Pie(
            labels=churn_table['label'],
            values=churn_table['count'],
            hole=0.38,
            pull=[0.02, 0.12],
            rotation=135,
            sort=False,

            marker=dict(
                colors=['#1F4E79', '#B03A2E'],
                line=dict(
                    color='white',
                    width=3
                )
            ),

            textinfo='label+percent',
            texttemplate='<b>%{label}</b><br>%{value:,} 人<br>%{percent}',
            textposition='outside',

            textfont=dict(
                color='black',
                size=15,
                family='Microsoft YaHei'
            ),

            hovertemplate=(
                '<b>%{label}</b><br>'
                '客户数量：%{value:,}<br>'
                '占比：%{percent}<br>'
                '<extra></extra>'
            )
        )
    ]
)

fig.update_layout(
    title=dict(
        text='客户整体流失情况扇形图',
        x=0.5,
        xanchor='center',
        font=dict(
            color='black',
            size=22,
            family='Microsoft YaHei'
        )
    ),

    height=520,

    paper_bgcolor='white',
    plot_bgcolor='white',

    showlegend=True,

    legend=dict(
        orientation='h',
        x=0.5,
        y=-0.08,
        xanchor='center',
        font=dict(
            color='black',
            size=14
        )
    ),

    annotations=[
        dict(
            text=f"<b>流失率</b><br><span style='font-size:24px;color:#B03A2E'>{churn_rate:.2f}%</span>",
            x=0.5,
            y=0.5,
            font=dict(
                color='black',
                size=16,
                family='Microsoft YaHei'
            ),
            showarrow=False
        )
    ],

    margin=dict(t=80, b=80, l=80, r=80)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("#### 3D Churn Pie Chart")

labels = churn_table['label'].tolist()
values = churn_table['count'].tolist()

color_map = {
    '留存': '#1F4E79',
    '流失': '#B03A2E'
}

colors = [color_map[label] for label in labels]

side_color_map = {
    '留存': '#143653',
    '流失': '#7A241E'
}

side_colors = [side_color_map[label] for label in labels]

explode = [
    0.03 if label == '留存' else 0.13
    for label in labels
]

total = sum(values)

fig_3d, ax = plt.subplots(figsize=(4, 3), dpi=150)



depth = 18

for i in range(depth, 0, -1):
    ax.pie(
        values,
        labels=None,
        colors=side_colors,
        explode=explode,
        startangle=135,
        counterclock=False,
        radius=1,
        center=(0, -i * 0.012),
        wedgeprops=dict(
            edgecolor='none'
        )
    )

wedges, texts, autotexts = ax.pie(
    values,
    labels=labels,
    colors=colors,
    explode=explode,
    startangle=135,
    counterclock=False,
    radius=1,
    center=(0, 0),
    autopct=lambda pct: f'{pct:.1f}%\n{int(round(pct * total / 100)):,} 人',
    pctdistance=0.68,
    labeldistance=1.15,
    shadow=True,
    wedgeprops=dict(
        edgecolor='white',
        linewidth=2.2
    )
)

for text in texts:
    text.set_fontsize(9)
    text.set_color('black')
    text.set_fontweight('bold')

for autotext in autotexts:
    autotext.set_fontsize(8)
    autotext.set_color('white')
    autotext.set_fontweight('bold')

ax.set_title(
    '客户流失状态 3D 扇形图',
    fontsize=10,
    fontweight='bold',
    color='black',
    pad=25
)

ax.axis('equal')

fig_3d.patch.set_facecolor('white')
ax.set_facecolor('white')

plt.tight_layout()

st.pyplot(fig_3d)

# ======================================================
# 3. Descriptive statistics
# 对应原代码：
# num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# print(df[num_cols].describe())
# ======================================================
strong_divider()

st.subheader("3️⃣ 数值特征描述性统计")

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if len(num_cols) > 0:
    desc_df = df[num_cols].describe().T.reset_index().rename(columns={'index': 'feature'})
    st.dataframe(desc_df, use_container_width=True)
else:
    st.warning("当前数据中没有数值型字段。")

strong_divider()

st.subheader("4️⃣ 数值特征分布与流失对比")

feature_name_map = {
    'account_length': '账户时长',
    'total_day_minutes': '白天通话时长',
    'total_eve_minutes': '傍晚通话时长',
    'total_night_minutes': '夜间通话时长',
    'total_intl_minutes': '国际通话时长',
    'customer_service_calls': '拨打客服次数',

    'total_minutes': '总通话时长',
    'total_calls': '总通话次数',
    'total_charges': '总费用',
    'avg_charge_per_minute': '每分钟平均费用',
    'rule_based_churn_risk_score': '规则流失风险评分'
}

default_num_features = [
    'account_length',
    'total_day_minutes',
    'total_eve_minutes',
    'total_night_minutes',
    'total_intl_minutes',
    'customer_service_calls',
    'total_minutes',
    'total_calls',
    'total_charges',
    'avg_charge_per_minute',
    'rule_based_churn_risk_score'
]

available_num_features = [col for col in default_num_features if col in df.columns]

selected_num_features = available_num_features


if len(selected_num_features) == 0:
    st.info("请选择至少一个数值特征。")
else:
    for col in selected_num_features:
        col_cn = feature_name_map.get(col, col)

        st.markdown(f"#### {col_cn}")

        left, right = st.columns(2)

        # -------------------------------
        # 左侧：直方图 + KDE 曲线
        # -------------------------------
        with left:
            fig_hist = go.Figure()

            clean_data = df[col].dropna()

            bin_edges = np.histogram_bin_edges(clean_data, bins='auto')
            bin_width = bin_edges[1] - bin_edges[0]

            fig_hist.add_trace(go.Histogram(
                x=clean_data,
                xbins=dict(
                    start=bin_edges[0],
                    end=bin_edges[-1],
                    size=bin_width
                ),
                histnorm='probability density',
                marker_color='#3B6EA8',

                opacity=0.7,
                name='直方图'
            ))

            try:
                from scipy.stats import gaussian_kde

                if len(clean_data) >= 2:
                    kde = gaussian_kde(clean_data)
                    x_range = np.linspace(clean_data.min(), clean_data.max(), 300)
                    y_kde = kde(x_range)

                    fig_hist.add_trace(go.Scatter(
                        x=x_range,
                        y=y_kde,
                        mode='lines',
                        line=dict(color='#D55E00', width=2.5),

                        name='核密度曲线'
                    ))
            except Exception as e:
                st.warning(f"{col_cn} 的核密度曲线绘制失败：{e}")

            fig_hist.update_layout(
                title=dict(
                    text=f"{col_cn}的分布",
                    x=0.5,
                    xanchor='center',
                    font=dict(color='black', size=16)
                ),

                xaxis=dict(
                    title=dict(text=col_cn, font=dict(color='black')),
                    tickfont=dict(color='black'),
                    showline=True,
                    linecolor='black',
                    linewidth=1,
                    ticks='outside',
                    tickcolor='black',
                    showgrid=True,
                    gridcolor='lightgray',
                    zeroline=False
                ),

                yaxis=dict(
                    title=dict(text='密度', font=dict(color='black')),
                    tickfont=dict(color='black'),
                    showline=True,
                    linecolor='black',
                    linewidth=1,
                    ticks='outside',
                    tickcolor='black',
                    showgrid=True,
                    gridcolor='lightgray',
                    zeroline=False
                ),

                template="plotly_white",
                height=400,
                margin=dict(t=60, b=50, l=60, r=40),
                legend=dict(x=0.02, y=0.98),
                bargap=0.05,
                font=dict(color='black')
            )

            st.plotly_chart(fig_hist, use_container_width=True)

        # -------------------------------
        # 右侧：按 churn 分组的箱线图
        # -------------------------------
        with right:
            fig_box = px.box(
                df,
                x='churn_label',
                y=col,
                color='churn_label',
                points='outliers',
                color_discrete_map={
                    '留存': '#2F5597',
                    '流失': '#C44E52'
                },

                labels={
                    'churn_label': '客户状态',
                    col: col_cn
                }
            )

            fig_box.update_traces(
                marker=dict(
                    opacity=0.45
                )
            )

            fig_box.update_layout(
                title=dict(
                    text=f"不同客户状态下的{col_cn}分布",
                    x=0.5,
                    xanchor='center',
                    font=dict(color='black', size=16)
                ),

                xaxis=dict(
                    title=dict(text='客户状态', font=dict(color='black')),
                    tickfont=dict(color='black'),
                    showline=True,
                    linecolor='black',
                    linewidth=1,
                    ticks='outside',
                    tickcolor='black',
                    showgrid=False,
                    zeroline=False
                ),

                yaxis=dict(
                    title=dict(text=col_cn, font=dict(color='black')),
                    tickfont=dict(color='black'),
                    showline=True,
                    linecolor='black',
                    linewidth=1,
                    ticks='outside',
                    tickcolor='black',
                    showgrid=True,
                    gridcolor='lightgray',
                    zeroline=False
                ),

                template="plotly_white",
                height=400,
                margin=dict(t=60, b=50, l=60, r=40),
                showlegend=False,
                font=dict(color='black')
            )

            st.plotly_chart(fig_box, use_container_width=True)











strong_divider()

st.subheader("4️⃣ 数值特征分布与流失对比")

feature_name_map = {
    'account_length': '账户时长',
    'total_day_minutes': '白天通话时长',
    'total_eve_minutes': '傍晚通话时长',
    'total_night_minutes': '夜间通话时长',
    'total_intl_minutes': '国际通话时长',
    'customer_service_calls': '拨打客服次数',
    'total_minutes': '总通话时长',
    'total_calls': '总通话次数',
    'total_charges': '总费用',
    'avg_charge_per_minute': '每分钟平均费用',
    'rule_based_churn_risk_score': '规则流失风险评分'
}

default_num_features = [
    'account_length',
    'total_day_minutes',
    'total_eve_minutes',
    'total_night_minutes',
    'total_intl_minutes',
    'customer_service_calls',
    'total_minutes',
    'total_calls',
    'total_charges',
    'avg_charge_per_minute',
    'rule_based_churn_risk_score'
]

available_num_features = [col for col in default_num_features if col in df.columns]
selected_num_features = available_num_features

if len(selected_num_features) == 0:
    st.info("请选择至少一个数值特征。")
else:
    st.caption("每行展示 2 组特征；每组包含：左侧分布图，右侧按流失分组箱线图。")

    # =========================
    # 页面展示：一行 2 组特征
    # =========================
    for i in range(0, len(selected_num_features), 2):
        row_features = selected_num_features[i:i + 2]
        outer_cols = st.columns(2)

        for j, col in enumerate(row_features):
            col_cn = feature_name_map.get(col, col)

            with outer_cols[j]:
                st.markdown(f"<h4 style='text-align:center;'>{col_cn}</h4>", unsafe_allow_html=True)


                left, right = st.columns(2)

                # -------------------------------
                # 左侧：直方图 + KDE 曲线
                # -------------------------------
                with left:
                    fig_hist = go.Figure()

                    clean_data = df[col].dropna()

                    if len(clean_data) > 0:
                        try:
                            bin_edges = np.histogram_bin_edges(clean_data, bins='auto')
                            if len(bin_edges) >= 2:
                                bin_width = bin_edges[1] - bin_edges[0]
                            else:
                                bin_width = 1

                            fig_hist.add_trace(go.Histogram(
                                x=clean_data,
                                xbins=dict(
                                    start=float(clean_data.min()),
                                    end=float(clean_data.max()),
                                    size=float(bin_width) if bin_width > 0 else 1
                                ),
                                histnorm='probability density',
                                marker_color='#3B6EA8',
                                opacity=0.7,
                                name='直方图'
                            ))
                        except Exception:
                            fig_hist.add_trace(go.Histogram(
                                x=clean_data,
                                histnorm='probability density',
                                marker_color='#3B6EA8',
                                opacity=0.7,
                                name='直方图'
                            ))

                        try:
                            from scipy.stats import gaussian_kde

                            if len(clean_data) >= 2 and clean_data.nunique() > 1:
                                kde = gaussian_kde(clean_data)
                                x_range = np.linspace(clean_data.min(), clean_data.max(), 300)
                                y_kde = kde(x_range)

                                fig_hist.add_trace(go.Scatter(
                                    x=x_range,
                                    y=y_kde,
                                    mode='lines',
                                    line=dict(color='#D55E00', width=2.5),
                                    name='核密度曲线'
                                ))
                        except Exception as e:
                            st.warning(f"{col_cn} 的核密度曲线绘制失败：{e}")
                    else:
                        st.warning(f"{col_cn} 没有可用于绘图的非空数据。")

                    fig_hist.update_layout(
                        title=dict(
                            text=f"{col_cn}的分布",
                            x=0.5,
                            xanchor='center',
                            font=dict(color='black', size=14)
                        ),
                        xaxis=dict(
                            title=dict(text=col_cn, font=dict(color='black')),
                            tickfont=dict(color='black'),
                            showline=True,
                            linecolor='black',
                            linewidth=1,
                            ticks='outside',
                            tickcolor='black',
                            showgrid=True,
                            gridcolor='lightgray',
                            zeroline=False
                        ),
                        yaxis=dict(
                            title=dict(text='密度', font=dict(color='black')),
                            tickfont=dict(color='black'),
                            showline=True,
                            linecolor='black',
                            linewidth=1,
                            ticks='outside',
                            tickcolor='black',
                            showgrid=True,
                            gridcolor='lightgray',
                            zeroline=False
                        ),
                        template="plotly_white",
                        height=340,
                        margin=dict(t=55, b=45, l=55, r=25),
                        legend=dict(
                            orientation='h',
                            x=0.02,
                            y=1.02,
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        bargap=0.05,
                        font=dict(color='black')
                    )

                    st.plotly_chart(fig_hist, use_container_width=True)

                # -------------------------------
                # 右侧：按 churn 分组的箱线图
                # -------------------------------
                with right:
                    plot_df = df[[col, 'churn_label']].dropna().copy()

                    if len(plot_df) == 0:
                        st.warning(f"{col_cn} 没有可用于箱线图的非空数据。")
                    else:
                        fig_box = px.box(
                            plot_df,
                            x='churn_label',
                            y=col,
                            color='churn_label',
                            points='outliers',
                            category_orders={'churn_label': ['留存', '流失']},
                            color_discrete_map={
                                '留存': '#2F5597',
                                '流失': '#C44E52'
                            },
                            labels={
                                'churn_label': '客户状态',
                                col: col_cn
                            }
                        )

                        fig_box.update_traces(
                            marker=dict(opacity=0.45)
                        )

                        fig_box.update_layout(
                            title=dict(
                                text=f"不同客户状态下的{col_cn}分布",
                                x=0.5,
                                xanchor='center',
                                font=dict(color='black', size=14)
                            ),
                            xaxis=dict(
                                title=dict(text='客户状态', font=dict(color='black')),
                                tickfont=dict(color='black'),
                                showline=True,
                                linecolor='black',
                                linewidth=1,
                                ticks='outside',
                                tickcolor='black',
                                showgrid=False,
                                zeroline=False
                            ),
                            yaxis=dict(
                                title=dict(text=col_cn, font=dict(color='black')),
                                tickfont=dict(color='black'),
                                showline=True,
                                linecolor='black',
                                linewidth=1,
                                ticks='outside',
                                tickcolor='black',
                                showgrid=True,
                                gridcolor='lightgray',
                                zeroline=False
                            ),
                            template="plotly_white",
                            height=340,
                            margin=dict(t=55, b=45, l=55, r=25),
                            showlegend=False,
                            font=dict(color='black')
                        )

                        st.plotly_chart(fig_box, use_container_width=True)

        light_divider()


    @st.cache_data(show_spinner=False)
    def make_numeric_big_figure(data, features, feature_name_map):
        import math
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np

        if len(features) == 0:
            return None

        n_features = len(features)
        nrows = math.ceil(n_features / 2)
        ncols = 4  # 一行 2 组，每组 2 张图 => 共 4 列

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=(22, 4.8 * nrows),
            dpi=300
        )

        # 保证 axes 一定是二维数组
        if nrows == 1:
            axes = np.array([axes])

        for idx, col in enumerate(features):
            row = idx // 2
            pos_in_row = idx % 2

            ax_hist = axes[row, pos_in_row * 2]
            ax_box = axes[row, pos_in_row * 2 + 1]

            col_cn = feature_name_map.get(col, col)
            clean_data = data[col].dropna()

            # 左图：直方图 + KDE
            # 左图：直方图 + KDE
            if len(clean_data) > 0:
                sns.histplot(
                    clean_data,
                    kde=False,
                    stat='density',
                    color='#3B6EA8',
                    alpha=0.75,
                    edgecolor='white',
                    ax=ax_hist,
                    label='直方图'
                )

                if len(clean_data) >= 2 and clean_data.nunique() > 1:
                    sns.kdeplot(
                        clean_data,
                        ax=ax_hist,
                        color='#E67E22',
                        linewidth=2.5,
                        label='核密度曲线'
                    )

                ax_hist.legend(frameon=False, fontsize=9, loc='upper right')

            ax_hist.set_title(f"{col_cn}的分布", fontsize=12, fontweight='bold')

            ax_hist.set_xlabel(col_cn, fontsize=10)
            ax_hist.set_ylabel("密度", fontsize=10)
            ax_hist.grid(axis='y', linestyle='--', alpha=0.35)

            # 右图：按 churn 分组箱线图
            plot_df = data[[col, 'churn_label']].dropna().copy()
            if len(plot_df) > 0:
                sns.boxplot(
                    data=plot_df,
                    x='churn_label',
                    y=col,
                    order=['留存', '流失'],
                    palette={'留存': '#2F5597', '流失': '#C44E52'},
                    ax=ax_box
                )
            ax_box.set_title(f"不同客户状态下的{col_cn}分布", fontsize=12, fontweight='bold')
            ax_box.set_xlabel("客户状态", fontsize=10)
            ax_box.set_ylabel(col_cn, fontsize=10)
            ax_box.grid(axis='y', linestyle='--', alpha=0.35)

        # 隐藏最后一行可能多余的子图
        total_axes = nrows * ncols
        used_axes = n_features * 2
        flat_axes = axes.flatten()

        for k in range(used_axes, total_axes):
            flat_axes[k].axis('off')

        fig.suptitle("数值特征分布与流失对比总图", fontsize=18, fontweight='bold', y=1.01)
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(
            buf,
            format='png',
            dpi=300,
            bbox_inches='tight',
            facecolor='white'
        )
        buf.seek(0)
        plt.close(fig)

        return buf.getvalue()


    # =========================
    # 论文总图下载
    # =========================
    st.markdown("#### 📥 下载论文版总图")

    big_fig_png = make_numeric_big_figure(
        df,
        selected_num_features,
        feature_name_map
    )

    if big_fig_png is not None:
        st.download_button(
            label="下载第4部分数值特征总图（PNG，300dpi）",
            data=big_fig_png,
            file_name="numeric_features_churn_comparison_big_figure.png",
            mime="image/png"
        )

        st.caption("建议直接将该 PNG 用于论文、答辩或报告排版。")
    else:
        st.warning("总图生成失败。")






# ======================================================
# 5. Categorical features
# 对应原代码：
# for col in cat_cols:
#   print(value_counts)
#   pd.crosstab(... normalize='index')
#   stacked bar
# ======================================================
strong_divider()

st.subheader("5️⃣ 类别特征分布与流失占比")
# -----------------------------
# 单独绘制 state 图：与原 Notebook 版本保持一致
# -----------------------------
if 'state' in df.columns:
    st.markdown("#### state")

    st.markdown("**Value counts**")

    state_counts = df['state'].value_counts().reset_index()
    state_counts.columns = ['state', 'count']

    st.dataframe(
        state_counts,
        use_container_width=True
    )

    # Cross-tab with churn
    ct_state = pd.crosstab(
        df['state'],
        df['churn_int'],
        normalize='index'
    ) * 100

    # 保证列顺序为 0, 1
    for c in [0, 1]:
        if c not in ct_state.columns:
            ct_state[c] = 0

    ct_state = ct_state[[0, 1]]

    st.markdown("**Cross-tab with churn，按 state 归一化，单位：%**")
    st.dataframe(ct_state.reset_index(), use_container_width=True)

    fig_state, ax = plt.subplots(figsize=(10, 5))

    ct_state.plot(
        kind='bar',
        stacked=True,
        colormap='coolwarm',
        ax=ax
    )

    ax.set_title('Churn rate by state')
    ax.set_ylabel('Percentage')
    ax.set_xlabel('state')
    ax.legend(title='Churn', labels=['No', 'Yes'])
    ax.tick_params(axis='x', labelrotation=45)

    fig_state.tight_layout()

    st.pyplot(fig_state)

    plt.close(fig_state)

light_divider()

default_cat_cols = [
    'state',
    'area_code',
    'international_plan',
    'voice_mail_plan',
    'has_international_plan',
    'has_voice_mail_plan',
    'high_service_calls',
    'usage_intensity',
    'customer_value_segment',
    'rule_based_churn_risk_level',
    'split'
]

available_cat_cols = [col for col in default_cat_cols if col in df.columns]

selected_cat_cols = st.multiselect(
    "选择要分析的类别特征",
    options=available_cat_cols,
    default=[col for col in ['usage_intensity', 'customer_value_segment', 'rule_based_churn_risk_level'] if col in available_cat_cols]
)

top_n_for_high_cardinality = st.slider(
    "高基数字段图表展示 Top N 类别",
    min_value=5,
    max_value=30,
    value=15,
    step=5
)

if len(selected_cat_cols) == 0:
    st.info("请选择至少一个类别特征。")
else:
    for col in selected_cat_cols:
        st.markdown(f"#### {col}")

        vc = df[col].astype(str).value_counts().reset_index()
        vc.columns = [col, 'count']

        st.markdown("**Value counts**")
        st.dataframe(vc, use_container_width=True)

        # 对 state 这种类别很多的字段，只展示 Top N，避免图太挤
        if df[col].nunique() > top_n_for_high_cardinality:
            top_values = df[col].astype(str).value_counts().head(top_n_for_high_cardinality).index
            plot_df = df[df[col].astype(str).isin(top_values)].copy()
            st.caption(f"该字段类别数较多，图表仅展示样本数 Top {top_n_for_high_cardinality} 的类别。")
        else:
            plot_df = df.copy()

        ct = pct_crosstab(plot_df, col)
        ct_display = ct.reset_index()

        st.markdown("**Cross-tab with churn，按类别归一化，单位：%**")
        st.dataframe(ct_display, use_container_width=True)

        ct_plot = ct.reset_index().melt(
            id_vars=col,
            value_vars=['留存', '流失'],
            var_name='客户状态',
            value_name='占比'
        )

        fig = px.bar(
            ct_plot,
            x=col,
            y='占比',
            color='客户状态',
            barmode='stack',
            text=ct_plot['占比'].apply(lambda x: f"{x:.1f}%"),
            color_discrete_map={
                '留存': '#3498DB',
                '流失': '#E74C3C'
            },
            labels={
                col: col,
                '占比': 'Percentage (%)',
                '客户状态': 'Churn'
            }
        )

        fig.update_traces(
            textposition='inside',
            textfont=dict(color='white', size=10)
        )

        fig.update_layout(
            **common_layout,
            height=480,
            xaxis_title=col,
            yaxis_title='Percentage (%)',
            legend_title_text='Churn',
            xaxis_tickangle=-35,
            margin=dict(t=40, b=120, l=40, r=40)
        )

        st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 6. Correlation analysis
# 对应原代码：
# corr = numeric_df.corr()
# sns.heatmap(...)
# churn_corr = corr['churn'].sort_values(...)
# print(churn_corr)
# ======================================================
strong_divider()

st.subheader("6️⃣ 数值特征相关性分析")

numeric_df = df.select_dtypes(include=[np.number]).copy()

# 确保 churn_int 在数值相关性中
if 'churn_int' not in numeric_df.columns:
    numeric_df['churn_int'] = df['churn_int']

if numeric_df.shape[1] < 2:
    st.warning("数值字段不足，无法计算相关性矩阵。")
else:
    corr = numeric_df.corr()

    # 上三角 mask
    mask = np.triu(np.ones_like(corr, dtype=bool))
    corr_masked = corr.mask(mask)

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_masked.values,
            x=corr.columns,
            y=corr.index,
            colorscale='RdBu',
            zmin=-1,
            zmax=1,

            # 颜色块之间的白色分隔线
            xgap=2,
            ygap=2,

            colorbar=dict(
                title=dict(
                    text='相关系数',
                    font=dict(color='black')
                ),
                tickfont=dict(color='black')
            ),
            hovertemplate='%{y} vs %{x}<br>相关系数: %{z:.3f}<extra></extra>'
        )
    )

    fig.update_layout(
        **common_layout,

        title=dict(
            text='数值特征相关性热力图',
            x=0.5,
            xanchor='center',
            font=dict(color='black', size=16)
        ),

        height=760,

        xaxis=dict(
            tickangle=-45,
            tickfont=dict(color='black', size=11),
            title_font=dict(color='black'),
            showgrid=False,
            zeroline=False,
            linecolor='black',
            tickcolor='black'
        ),

        yaxis=dict(
            autorange='reversed',
            tickfont=dict(color='black', size=11),
            title_font=dict(color='black'),
            showgrid=False,
            zeroline=False,
            linecolor='black',
            tickcolor='black'
        ),

        margin=dict(t=70, b=160, l=120, r=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Correlation with churn")

    churn_corr = corr['churn_int'].sort_values(ascending=False).reset_index()
    churn_corr.columns = ['feature', 'corr_with_churn']

    st.dataframe(churn_corr, use_container_width=True)

    churn_corr_for_plot = churn_corr[~churn_corr['feature'].isin(['churn_int', 'churn'])].copy()
    churn_corr_for_plot = churn_corr_for_plot.sort_values('corr_with_churn', ascending=True)

    fig = px.bar(
        churn_corr_for_plot,
        x='corr_with_churn',
        y='feature',
        orientation='h',
        color='corr_with_churn',
        color_continuous_scale='RdBu_r',
        range_color=[-1, 1],
        labels={
            'corr_with_churn': '与 churn 的相关系数',
            'feature': '特征'
        },
        text='corr_with_churn'
    )

    # 先应用通用样式
    fig.update_layout(**common_layout)

    # 再单独设置当前图的标题和字体样式，避免和 common_layout 参数冲突
    fig.update_layout(
        title=dict(
            text='各数值特征与客户流失的相关性',
            x=0.5,
            xanchor='center',
            font=dict(color='black', size=16)
        ),

        height=max(500, 22 * len(churn_corr_for_plot)),

        # 全局字体颜色改成黑色
        font=dict(color='black'),

        xaxis=dict(
            title=dict(
                text='与 churn 的相关系数',
                font=dict(color='black')
            ),
            tickfont=dict(color='black'),
            zeroline=True,
            zerolinecolor='black',
            linecolor='black',
            tickcolor='black'
        ),

        yaxis=dict(
            title=dict(
                text='特征',
                font=dict(color='black')
            ),
            tickfont=dict(color='black'),
            linecolor='black',
            tickcolor='black'
        ),

        coloraxis_colorbar=dict(
            title=dict(
                text='相关系数',
                font=dict(color='black')
            ),
            tickfont=dict(color='black')
        ),

        margin=dict(t=70, b=40, l=130, r=40)
    )
    fig.update_traces(
        texttemplate='%{text:.3f}',
        textposition='outside',
        textfont=dict(color='black')
    )

    st.plotly_chart(fig, use_container_width=True)
@st.cache_data(show_spinner=False)
def make_seaborn_pairplot_png(data, key_features, sample_n=1000, random_state=42):
    sample_df = data[key_features].dropna().sample(
        n=min(sample_n, len(data)),
        random_state=random_state
    )

    g = sns.pairplot(
        sample_df,
        hue='churn',
        diag_kind='hist',
        palette='Set1',
        plot_kws={'alpha': 0.45, 's': 18}
    )

    if g._legend is not None:
        g._legend.set_title('churn')

    plt.suptitle('关键特征成对关系图', y=1.02)


    buf = io.BytesIO()
    g.fig.savefig(
        buf,
        format='png',
        dpi=120,
        bbox_inches='tight'
    )
    buf.seek(0)

    plt.close(g.fig)

    return buf.getvalue()

# ======================================================
# 7. Pairplot for key features
# Seaborn pairplot 版本，尽量与原 Notebook 一致
# ======================================================
# ======================================================
# 7. Pairplot for key features./bheader("7️⃣ 关键特征 Scatter Matrix")
# Seaborn pairplot 版本，和原 Notebook 保持一致
# ======================================================
strong_divider()

st.subheader(" 关键特征成对关系图")


key_features = [
    'total_minutes',
    'customer_service_calls',
    'total_charges',
    'avg_charge_per_minute',
    'rule_based_churn_risk_score',
    'churn'
]

if all(f in df.columns for f in key_features):

    with st.spinner("正在生成 Seaborn Pairplot，首次生成可能较慢..."):
        pairplot_png = make_seaborn_pairplot_png(
            df,
            key_features,
            sample_n=1000,
            random_state=42
        )

    st.image(pairplot_png, use_container_width=True)

    st.caption(
        "💡 这里使用 seaborn.pairplot，与原 Notebook 图形风格保持一致。"
        "图像已缓存，首次生成后再次刷新会快很多。"
    )

else:
    missing_features = [f for f in key_features if f not in df.columns]
    st.warning(f"缺少以下字段，无法绘制 Pairplot：{missing_features}")


# ======================================================
# 8. Feature engineering insights
# 对应原代码：
# groupby churn describe
# crosstab customer_service_calls / usage_intensity / customer_value_segment
# ======================================================
strong_divider()

st.subheader("8️⃣ 派生字段与业务分层分析")

if 'avg_charge_per_minute' in df.columns:
    st.markdown("#### Average charge per minute by churn")

    avg_charge_desc = df.groupby('churn_label')['avg_charge_per_minute'].describe().reset_index()
    st.dataframe(avg_charge_desc, use_container_width=True)

    fig = px.box(
        df,
        x='churn_label',
        y='avg_charge_per_minute',
        color='churn_label',
        points='outliers',
        color_discrete_map={
            '留存': '#3498DB',
            '流失': '#E74C3C'
        },
        labels={
            'churn_label': '客户状态',
            'avg_charge_per_minute': '每分钟平均费用'
        }
    )

    fig.update_layout(
        **common_layout,
        height=430,
        showlegend=False,
        margin=dict(t=40, b=40, l=40, r=40)
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": ["select2d", "lasso2d"]
        }
    )

light_divider()

analysis_cols = [
    ('customer_service_calls', 'Customer service calls distribution by churn'),
    ('usage_intensity', 'Usage intensity vs churn'),
    ('customer_value_segment', 'Customer value segment vs churn')
]

for col, title in analysis_cols:
    if col in df.columns:
        st.markdown(f"#### {title}")

        ct = pct_crosstab(df, col).reset_index()
        st.dataframe(ct, use_container_width=True)

        ct_plot = ct.melt(
            id_vars=col,
            value_vars=['留存', '流失'],
            var_name='客户状态',
            value_name='占比'
        )

        fig = px.bar(
            ct_plot,
            x=col,
            y='占比',
            color='客户状态',
            barmode='stack',
            text=ct_plot['占比'].apply(lambda x: f"{x:.1f}%"),
            color_discrete_map={
                '留存': '#3498DB',
                '流失': '#E74C3C'
            },
            labels={
                col: col,
                '占比': 'Percentage (%)'
            }
        )

        fig.update_traces(
            textposition='inside',
            textfont=dict(color='white', size=10)
        )

        fig.update_layout(
            **common_layout,
            height=430,
            xaxis_tickangle=-25,
            margin=dict(t=40, b=80, l=40, r=40)
        )

        st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 9. Split analysis
# 对应原代码：
# if 'split' in df.columns:
#   print(df['split'].value_counts())
#   print(df.groupby('split')['churn'].mean())
#   boxplot by split
# ======================================================
strong_divider()

st.subheader("9️⃣ Train/Test Split 分析")

if 'split' not in df.columns:
    st.info("当前 full_customers 数据中没有 `split` 字段，因此跳过 Split 分析。")
else:
    split_count = df['split'].value_counts().reset_index()
    split_count.columns = ['split', 'count']

    st.markdown("#### Split distribution")
    st.dataframe(split_count, use_container_width=True)

    split_churn = df.groupby('split').agg(
        customer_count=('customer_id', 'count') if 'customer_id' in df.columns else ('churn_int', 'count'),
        churn_rate=('churn_int', 'mean')
    ).reset_index()
    split_churn['churn_rate_pct'] = split_churn['churn_rate'] * 100

    st.markdown("#### Churn rate by split")
    st.dataframe(split_churn, use_container_width=True)

    fig = px.bar(
        split_churn,
        x='split',
        y='churn_rate_pct',
        color='split',
        text=split_churn['churn_rate_pct'].apply(lambda x: f"{x:.2f}%"),
        labels={
            'split': 'Split',
            'churn_rate_pct': '流失率 (%)'
        }
    )

    fig.update_traces(
        textposition='outside',
        textfont=dict(color='black', size=12)
    )

    fig.update_layout(
        **common_layout,
        height=420,
        showlegend=False,
        margin=dict(t=40, b=40, l=40, r=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    features_compare = [
        'total_minutes',
        'customer_service_calls',
        'total_charges',
        'avg_charge_per_minute'
    ]

    available_features_compare = [f for f in features_compare if f in df.columns]

    if len(available_features_compare) > 0:
        selected_split_features = st.multiselect(
            "选择要比较 train/test 分布的特征",
            options=available_features_compare,
            default=available_features_compare
        )

        for feat in selected_split_features:
            fig = px.box(
                df,
                x='split',
                y=feat,
                color='split',
                points='outliers',
                labels={
                    'split': 'Split',
                    feat: feat
                }
            )

            fig.update_layout(
                **common_layout,
                height=420,
                showlegend=False,
                margin=dict(t=40, b=40, l=40, r=40)
            )

            st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 10. Outlier detection
# 对应原代码：
# IQR method outlier counts
# ======================================================
strong_divider()

st.subheader("🔟 离群值检测：IQR 方法")

outlier_features = [col for col in default_num_features if col in df.columns]

outlier_rows = []

for col in outlier_features:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outlier_mask = (df[col] < lower) | (df[col] > upper)
    outlier_count = outlier_mask.sum()
    outlier_rate = outlier_count / len(df) * 100

    outlier_rows.append({
        'feature': col,
        'Q1': Q1,
        'Q3': Q3,
        'IQR': IQR,
        'lower_bound': lower,
        'upper_bound': upper,
        'outlier_count': outlier_count,
        'outlier_rate_pct': outlier_rate
    })

outlier_df = pd.DataFrame(outlier_rows).sort_values('outlier_count', ascending=False)

st.dataframe(outlier_df, use_container_width=True)

if len(outlier_df) > 0:
    fig = px.bar(
        outlier_df.sort_values('outlier_rate_pct', ascending=True),
        x='outlier_rate_pct',
        y='feature',
        orientation='h',
        color='outlier_rate_pct',
        text=outlier_df.sort_values('outlier_rate_pct', ascending=True)['outlier_rate_pct'].apply(lambda x: f"{x:.2f}%"),
        color_continuous_scale='OrRd',
        labels={
            'outlier_rate_pct': '离群值比例 (%)',
            'feature': '特征'
        }
    )

    fig.update_traces(
        textposition='outside',
        textfont=dict(color='black', size=11)
    )

    fig.update_layout(
        **common_layout,
        title=dict(
            text='基于 IQR 方法的各数值特征离群值比例',
            x=0.5,
            xanchor='center',
            font=dict(color='black', size=18)
        ),

        xaxis=dict(
            title=dict(
                text='离群值比例 (%)',
                font=dict(color='black', size=14)
            ),
            tickfont=dict(color='black', size=12),
            showline=True,
            linecolor='black',
            linewidth=1,
            mirror=False,
            ticks='outside',
            tickcolor='black',
            showgrid=True,
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='black'
        ),

        yaxis=dict(
            title=dict(
                text='特征',
                font=dict(color='black', size=14)
            ),
            tickfont=dict(color='black', size=12),
            showline=True,
            linecolor='black',
            linewidth=1,
            mirror=False,
            ticks='outside',
            tickcolor='black',
            showgrid=False
        ),

        height=480,
        coloraxis_showscale=False,
        margin=dict(t=70, b=40, l=130, r=80)
    )

    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 11. EDA Summary
# 对应原代码：
# print("=== EDA Summary ===")
# print(f"Total customers: ...")
# print(f"Overall churn rate: ...")
# print top corr features
# ======================================================
strong_divider()

st.subheader("📌 EDA Summary")

total_customers = len(df)
overall_churn_rate = df['churn_int'].mean() * 100

col1, col2, col3 = st.columns(3)
col1.metric("Total customers", f"{total_customers:,}")
col2.metric("Overall churn rate", f"{overall_churn_rate:.2f}%")
col3.metric("Feature count", f"{df.shape[1]:,}")

if 'corr' in locals() and 'churn_corr_for_plot' in locals() and len(churn_corr_for_plot) > 0:
    positive_top3 = churn_corr_for_plot.sort_values('corr_with_churn', ascending=False).head(3)
    negative_top3 = churn_corr_for_plot.sort_values('corr_with_churn', ascending=True).head(3)

    left, right = st.columns(2)

    with left:
        st.markdown("#### Top 3 features positively correlated with churn")
        st.dataframe(positive_top3, use_container_width=True)

    with right:
        st.markdown("#### Top 3 features negatively correlated with churn")
        st.dataframe(negative_top3, use_container_width=True)

st.info(
    "💡 本页面融合了传统 Notebook EDA 中的 print、describe、info、missing values、"
    "churn 分布、数值特征分布、类别交叉表、相关性分析、pairplot、split 检查和 IQR 离群值检测。"
)

st.success(
    "Key observations can be derived from the plots above. "
    "Consider further analysis: feature importance, uplift modeling, etc."
)
