import streamlit as st

st.title("📊 挽留策略与 ROI 模拟")
st.warning("🔧 开发中：结合预测结果与财务数据计算挽留投资回报率")
st.markdown("**使用数据：** `business_costs.xlsx` + 模型预测结果")

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

from matplotlib_venn import venn3
from upsetplot import UpSet

from utils.data_loader import (
    load_full_customers,
    load_feedback,
    load_business,
    load_campaign
)

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_customer_risk_upset_plotly(df, selected_signals, top_n=15):
    """
    高级 Plotly 版 UpSet Plot
    上方为交集规模柱状图，下方为信号组合矩阵。
    """

    plot_df = df.copy()

    # 只保留至少命中一个信号的客户
    plot_df = plot_df[plot_df[selected_signals].any(axis=1)].copy()

    if plot_df.empty:
        return None

    # 按信号组合统计人数
    combo_df = (
        plot_df
        .groupby(selected_signals)
        .agg(
            客户数=("customer_id", "count"),
            流失率=("churn_int", "mean"),
            平均CLV=("estimated_clv", "mean"),
            平均预期流失损失=("expected_loss_if_churn", "mean")
        )
        .reset_index()
    )

    combo_df = combo_df.sort_values("客户数", ascending=False).head(top_n).reset_index(drop=True)

    # 构造组合标签
    combo_df["组合标签"] = [
        f"C{i + 1}" for i in range(len(combo_df))
    ]

    combo_df["命中信号"] = combo_df[selected_signals].apply(
        lambda row: " ∩ ".join([sig for sig in selected_signals if row[sig]]),
        axis=1
    )

    # 颜色配置：高级蓝紫渐变
    bar_colors = combo_df["客户数"]

    # 创建上下两个子图
    fig = make_subplots(
        rows=2,
        cols=2,
        shared_xaxes=True,
        shared_yaxes=False,
        vertical_spacing=0.045,
        horizontal_spacing=0.08,
        row_heights=[0.58, 0.42],
        column_widths=[0.28, 0.72],
        specs=[
            [None, {"type": "bar"}],
            [{"type": "bar"}, {"type": "scatter"}]
        ]
    )

    # =========================
    # 上方柱状图
    # =========================
    fig.add_trace(
        go.Bar(
            x=combo_df["组合标签"],
            y=combo_df["客户数"],
            marker=dict(
                color=bar_colors,
                colorscale=[
                    [0.0, "#C7D2FE"],
                    [0.35, "#818CF8"],
                    [0.7, "#6366F1"],
                    [1.0, "#312E81"]
                ],
                line=dict(
                    color="rgba(255,255,255,0.85)",
                    width=1.3
                )
            ),
            text=combo_df["客户数"],
            textposition="outside",
            textfont=dict(
                size=13,
                color="#1E293B",
                family="Microsoft YaHei"
            ),
            customdata=np.stack(
                [
                    combo_df["命中信号"],
                    combo_df["流失率"],
                    combo_df["平均CLV"],
                    combo_df["平均预期流失损失"]
                ],
                axis=-1
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "客户数：%{y}<br>"
                "组合：%{customdata[0]}<br>"
                "流失率：%{customdata[1]:.2%}<br>"
                "平均 CLV：%{customdata[2]:,.2f}<br>"
                "平均预期流失损失：%{customdata[3]:,.2f}"
                "<extra></extra>"
            ),
            name="交集客户数"
        ),
        row=1,
        col=2
    )

    # =========================
    # 下方矩阵点阵
    # =========================
    signal_y_map = {
        signal: len(selected_signals) - i
        for i, signal in enumerate(selected_signals)
    }
    signal_color_map = {
        "已流失": "#EF4444",  # 红
        "高价值": "#F59E0B",  # 金橙
        "中高风险": "#8B5CF6",  # 紫
        "高频客服": "#06B6D4",  # 青
        "负面反馈": "#EC4899",  # 玫红
        "高投诉强度": "#DC2626",  # 深红
        "营销触达": "#3B82F6",  # 蓝
        "营销响应": "#10B981",  # 绿
        "有国际套餐": "#6366F1",  # 靛蓝
        "高使用强度": "#14B8A6"  # 青绿
    }
    # =========================
    # 左侧集合人数条形图
    # =========================
    set_size_df = pd.DataFrame({
        "信号": selected_signals,
        "人数": [
            df.loc[df[sig], "customer_id"].nunique()
            for sig in selected_signals
        ],
        "y": [
            signal_y_map[sig]
            for sig in selected_signals
        ],
        "颜色": [
            signal_color_map.get(sig, "#64748B")
            for sig in selected_signals
        ]
    })

    fig.add_trace(
        go.Bar(
            x=-set_size_df["人数"],
            y=set_size_df["y"],
            orientation="h",
            marker=dict(
                color=set_size_df["颜色"],
                line=dict(
                    color="rgba(255,255,255,0.95)",
                    width=1
                )
            ),
            text=set_size_df["人数"].map(lambda x: f"{x:,}"),
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(
                size=12,
                color="#FFFFFF",
                family="Microsoft YaHei"
            ),
            customdata=set_size_df[["信号", "人数"]],
            hovertemplate=(
                "风险信号：%{customdata[0]}<br>"
                "命中客户数：%{customdata[1]:,}"
                "<extra></extra>"
            ),
            showlegend=False,
            name="集合人数"
        ),
        row=2,
        col=1
    )

    # 背景浅灰点
    bg_x = []
    bg_y = []

    for combo_label in combo_df["组合标签"]:
        for signal in selected_signals:
            bg_x.append(combo_label)
            bg_y.append(signal_y_map[signal])

    fig.add_trace(
        go.Scatter(
            x=bg_x,
            y=bg_y,
            mode="markers",
            marker=dict(
                size=11,
                color="rgba(203,213,225,0.55)",
                line=dict(
                    width=0
                )
            ),
            hoverinfo="skip",
            showlegend=False,
            name="未命中"
        ),
        row=2,
        col=2
    )

    # 命中点和连线
    active_x = []
    active_y = []
    active_text = []
    active_colors = []

    for _, row in combo_df.iterrows():
        combo_label = row["组合标签"]
        active_signals = [sig for sig in selected_signals if row[sig]]

        y_values = [signal_y_map[sig] for sig in active_signals]

        # 连线
        if len(y_values) >= 2:
            fig.add_trace(
                go.Scatter(
                    x=[combo_label, combo_label],
                    y=[min(y_values), max(y_values)],
                    mode="lines",
                    line=dict(
                        color="rgba(49,46,129,0.72)",
                        width=3
                    ),
                    hoverinfo="skip",
                    showlegend=False
                ),
                row=2,
                col=2
            )

        for sig in active_signals:
            active_x.append(combo_label)
            active_y.append(signal_y_map[sig])
            active_text.append(sig)
            active_colors.append(signal_color_map.get(sig, "#312E81"))

    fig.add_trace(
        go.Scatter(
            x=active_x,
            y=active_y,
            mode="markers",
            marker=dict(
                size=17,
                color=active_colors,

                line=dict(
                    color="#EEF2FF",
                    width=2
                )
            ),
            text=active_text,
            hovertemplate=(
                "组合：%{x}<br>"
                "命中信号：%{text}"
                "<extra></extra>"
            ),
            showlegend=False,
            name="命中"
        ),
        row=2,
        col=2
    )

    # =========================
    # 美化布局
    # =========================
    fig.update_yaxes(
        title_text="交集客户数",
        row=1,
        col=2,
        showgrid=True,
        gridcolor="rgba(226,232,240,0.8)",
        zeroline=False,
        showline=True,
        linecolor="#000000",
        linewidth=1.5,
        ticks="outside",
        tickcolor="#000000",
        tickwidth=1.2,
        title_font=dict(size=13, color="#111827"),
        tickfont=dict(size=12, color="#111827")
    )

    fig.update_yaxes(
        row=2,
        col=2,
        tickmode="array",
        tickvals=list(signal_y_map.values()),
        ticktext=[""] * len(signal_y_map),
        range=[0.5, len(selected_signals) + 0.5],
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="#000000",
        linewidth=1.5,
        ticks="outside",
        title_text=""
    )

    fig.update_yaxes(
        row=2,
        col=1,
        tickmode="array",
        tickvals=list(signal_y_map.values()),
        ticktext=list(signal_y_map.keys()),
        range=[0.5, len(selected_signals) + 0.5],
        showgrid=False,
        zeroline=False,
        showticklabels=True,
        side="right",
        showline=True,
        mirror=True,
        linecolor="#000000",
        linewidth=2,
        ticks="outside",
        tickcolor="#000000",
        tickwidth=1.5,
        tickfont=dict(size=12, color="#111827"),
        title_text=""
    )

    max_set_size = max(set_size_df["人数"].max(), 1)

    fig.update_xaxes(
        row=2,
        col=1,
        title_text="集合人数",
        range=[-max_set_size * 1.18, 0],
        showgrid=True,
        gridcolor="rgba(226,232,240,0.65)",
        zeroline=False,
        showline=True,
        mirror=True,
        linecolor="#000000",
        linewidth=2,
        ticks="outside",
        tickcolor="#000000",
        tickwidth=1.5,
        tickvals=[
            -max_set_size,
            -max_set_size * 0.5,
            0
        ],
        ticktext=[
            f"{int(max_set_size):,}",
            f"{int(max_set_size * 0.5):,}",
            "0"
        ],
        title_font=dict(size=13, color="#111827"),
        tickfont=dict(size=11, color="#111827")
    )

    fig.update_xaxes(
        row=1,
        col=2,
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="#000000",
        linewidth=1.5,
        ticks="outside",
        tickcolor="#000000",
        tickwidth=1.2
    )

    fig.update_xaxes(
        row=2,
        col=2,
        title_text="交集组合",
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="#000000",
        linewidth=1.5,
        ticks="outside",
        tickcolor="#000000",
        tickwidth=1.2,
        tickfont=dict(size=12, color="#111827"),
        title_font=dict(size=13, color="#111827")
    )

    fig.update_layout(
        height=840,
        title=dict(
            text="多风险信号组合 UpSet 分析",
            x=0.5,
            y=0.9,
            xanchor="center",
            font=dict(
                size=22,
                color="#0F172A",
                family="Microsoft YaHei"
            )
        ),

        plot_bgcolor="#F8FAFC",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=90, r=45, t=110, b=85),
        bargap=0.32,
        showlegend=False,
        font=dict(
            family="Microsoft YaHei, Arial",
            color="#1E293B"
        )
    )

    # 添加副标题
    fig.add_annotation(
        text="",
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.03,
        showarrow=False,
        font=dict(
            size=13,
            color="#64748B"
        ),
        align="center",
        xanchor="center"
    )

    return fig

# =========================
# 页面基础配置
# =========================


# 解决 matplotlib 中文显示问题
plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans"
]
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 数据合并函数
# =========================
@st.cache_data
def build_intersection_analysis_df():
    customer_df = load_full_customers().copy()
    feedback_df = load_feedback().copy()
    business_df = load_business().copy()
    campaign_df = load_campaign().copy()

    # churn 在你的 load_full_customers 中已经转成 str，这里统一转回来
    customer_df["churn_int"] = customer_df["churn"].astype(int)
    customer_df["churn_label"] = customer_df["churn_int"].map({
        0: "留存",
        1: "流失"
    })

    # 反馈表字段
    feedback_cols = [
        "customer_id",
        "feedback_text",
        "feedback_category",
        "sentiment",
        "complaint_intensity"
    ]
    feedback_df = feedback_df[feedback_cols].copy()

    # 成本表字段
    business_cols = [
        "customer_id",
        "monthly_revenue",
        "estimated_remaining_months",
        "estimated_clv",
        "retention_cost",
        "expected_loss_if_churn",
        "net_gain_if_retained"
    ]

    # business_costs 里也有 offer_type，避免和 campaign 的 offer_type 冲突
    if "offer_type" in business_df.columns:
        business_df = business_df.rename(columns={"offer_type": "business_offer_type"})

    business_df = business_df[
        [col for col in business_cols if col in business_df.columns]
    ].copy()

    # 营销表字段
    campaign_cols = [
        "customer_id",
        "treatment_group",
        "campaign_channel",
        "offer_type",
        "contacted",
        "responded",
        "original_churn",
        "churn_after_campaign",
        "uplift_label"
    ]

    campaign_df = campaign_df[
        [col for col in campaign_cols if col in campaign_df.columns]
    ].copy()

    if "offer_type" in campaign_df.columns:
        campaign_df = campaign_df.rename(columns={"offer_type": "campaign_offer_type"})

    # 合并
    df = (
        customer_df
        .merge(feedback_df, on="customer_id", how="left")
        .merge(business_df, on="customer_id", how="left")
        .merge(campaign_df, on="customer_id", how="left")
    )

    # 缺失值处理
    df["sentiment"] = df["sentiment"].fillna("unknown")
    df["feedback_category"] = df["feedback_category"].fillna("unknown")
    df["complaint_intensity"] = df["complaint_intensity"].fillna(0)

    for col in ["contacted", "responded", "original_churn", "churn_after_campaign"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    for col in [
        "estimated_clv",
        "monthly_revenue",
        "retention_cost",
        "expected_loss_if_churn",
        "net_gain_if_retained"
    ]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df


# =========================
# 风险信号构造
# =========================
def add_risk_signal_columns(
    df,
    risk_levels=("medium", "high"),
    service_call_threshold=4,
    complaint_threshold=4
):
    df = df.copy()

    df["已流失"] = df["churn_int"] == 1

    df["高价值"] = df["customer_value_segment"] == "high_value"

    df["中高风险"] = df["rule_based_churn_risk_level"].isin(risk_levels)

    df["高频客服"] = df["customer_service_calls"] >= service_call_threshold

    df["负面反馈"] = df["sentiment"] == "negative"

    df["高投诉强度"] = df["complaint_intensity"] >= complaint_threshold

    df["营销触达"] = df["contacted"] == 1

    df["营销响应"] = df["responded"] == 1

    if "has_international_plan" in df.columns:
        df["有国际套餐"] = df["has_international_plan"] == 1
    else:
        df["有国际套餐"] = False

    if "usage_intensity" in df.columns:
        df["高使用强度"] = df["usage_intensity"] == "high_usage"
    else:
        df["高使用强度"] = False

    return df


# =========================
# 韦恩图
# =========================
def plot_priority_customer_venn(df):
    high_value_set = set(
        df.loc[df["高价值"], "customer_id"]
    )

    high_risk_set = set(
        df.loc[df["中高风险"], "customer_id"]
    )

    negative_feedback_set = set(
        df.loc[df["负面反馈"], "customer_id"]
    )

    center_set = high_value_set & high_risk_set & negative_feedback_set

    fig, ax = plt.subplots(figsize=(8.5, 7))

    venn = venn3(
        subsets=[
            high_value_set,
            high_risk_set,
            negative_feedback_set
        ],
        set_labels=[
            "高价值客户",
            "中高风险客户",
            "负面反馈客户"
        ],
        ax=ax
    )

    # 高级配色
    colors = {
        "100": "#4C78A8",
        "010": "#F58518",
        "001": "#E45756",
        "110": "#72B7B2",
        "101": "#B279A2",
        "011": "#FF9DA6",
        "111": "#54A24B"
    }

    for region_id, color in colors.items():
        patch = venn.get_patch_by_id(region_id)
        if patch is not None:
            patch.set_color(color)
            patch.set_alpha(0.68)
            patch.set_edgecolor("white")
            patch.set_linewidth(1.5)

    if venn.set_labels is not None:
        for text in venn.set_labels:
            if text is not None:
                text.set_fontsize(12)
                text.set_fontweight("bold")

    if venn.subset_labels is not None:
        for text in venn.subset_labels:
            if text is not None:
                text.set_fontsize(11)
                text.set_fontweight("bold")

    ax.set_title(
        "高价值客户 × 中高风险客户 × 负面反馈客户交集分析韦恩图",
        fontsize=16,
        fontweight="bold",
        pad=18
    )

    ax.text(
        0.5,
        -0.08,
        f"中心交集 = {len(center_set)} 人，代表同时具备高价值、高风险和负面反馈的重点挽留客户。",
        transform=ax.transAxes,
        ha="center",
        fontsize=10,
        color="#555555"
    )

    return fig, center_set


# =========================
# UpSet Plot
# =========================
def plot_customer_risk_upset(df, selected_signals, top_n=15):
    plot_df = df.copy()

    # 只保留至少命中一个信号的客户，避免“全 False”组合占据主要位置
    plot_df = plot_df[plot_df[selected_signals].any(axis=1)].copy()

    if plot_df.empty:
        return None

    upset_series = (
        plot_df
        .groupby(selected_signals)
        .size()
        .sort_values(ascending=False)
    )

    fig = plt.figure(figsize=(13, 7.5))

    upset = UpSet(
        upset_series,
        subset_size="auto",
        show_counts=True,
        sort_by="cardinality",
        max_subset_rank=top_n,
        facecolor="#4C78A8",
        element_size=42
    )

    upset.plot(fig=fig)

    fig.suptitle(
        "客户流失风险信号组合 UpSet 分析",
        fontsize=17,
        fontweight="bold",
        y=1.02
    )

    return fig


# =========================
# 风险组合统计表
# =========================
def make_risk_combination_summary(df, selected_signals, top_n=20):
    temp_df = df.copy()

    def get_combo_name(row):
        active = [col for col in selected_signals if row[col]]
        if len(active) == 0:
            return "无明显风险信号"
        return " ∩ ".join(active)

    temp_df["风险信号组合"] = temp_df.apply(get_combo_name, axis=1)
    temp_df["信号数量"] = temp_df[selected_signals].sum(axis=1)

    summary_df = (
        temp_df[temp_df["信号数量"] > 0]
        .groupby("风险信号组合")
        .agg(
            客户数=("customer_id", "count"),
            平均信号数量=("信号数量", "mean"),
            实际流失率=("churn_int", "mean"),
            平均CLV=("estimated_clv", "mean"),
            平均月收入=("monthly_revenue", "mean"),
            平均预期流失损失=("expected_loss_if_churn", "mean"),
            平均留存净收益=("net_gain_if_retained", "mean"),
            营销触达率=("contacted", "mean"),
            营销响应率=("responded", "mean")
        )
        .reset_index()
    )

    summary_df["潜在价值规模"] = summary_df["客户数"] * summary_df["平均CLV"]

    summary_df["风险价值指数"] = (
        summary_df["客户数"]
        * summary_df["平均CLV"]
        * (summary_df["实际流失率"] + 0.1)
    )

    summary_df = summary_df.sort_values(
        ["风险价值指数", "客户数"],
        ascending=False
    ).head(top_n)

    return summary_df


# =========================
# Plotly 高级组合价值图
# =========================
def plot_risk_combination_bubble(summary_df):
    plot_df = summary_df.copy()

    fig = px.scatter(
        plot_df,
        x="客户数",
        y="平均CLV",
        size="潜在价值规模",
        color="实际流失率",
        hover_name="风险信号组合",
        hover_data={
            "客户数": True,
            "平均CLV": ":.2f",
            "实际流失率": ":.2%",
            "平均预期流失损失": ":.2f",
            "营销触达率": ":.2%",
            "营销响应率": ":.2%",
            "潜在价值规模": ":.2f",
            "风险价值指数": ":.2f"
        },
        color_continuous_scale="RdYlBu_r",
        size_max=45,
        title="风险信号组合的客户规模、平均 CLV 与实际流失率"
    )

    fig.update_layout(
        height=620,
        xaxis_title="客户数量",
        yaxis_title="平均 CLV",
        coloraxis_colorbar_title="实际流失率",
        template="plotly_white"
    )

    fig.update_traces(
        marker=dict(
            line=dict(width=1, color="white"),
            opacity=0.82
        )
    )

    return fig


def plot_risk_combination_bar(summary_df):
    plot_df = summary_df.copy().sort_values("风险价值指数", ascending=True)

    fig = px.bar(
        plot_df,
        x="风险价值指数",
        y="风险信号组合",
        orientation="h",
        color="实际流失率",
        text="客户数",
        hover_data={
            "客户数": True,
            "平均CLV": ":.2f",
            "实际流失率": ":.2%",
            "平均预期流失损失": ":.2f",
            "营销触达率": ":.2%",
            "营销响应率": ":.2%",
            "潜在价值规模": ":.2f",
            "风险价值指数": ":.2f"
        },
        color_continuous_scale="Reds",
        title="Top 风险信号组合价值排序"
    )

    fig.update_traces(
        texttemplate="%{text}人",
        textposition="outside"
    )

    fig.update_layout(
        height=max(580, len(plot_df) * 38),
        xaxis_title="风险价值指数",
        yaxis_title="风险信号组合",
        yaxis=dict(automargin=True),
        margin=dict(l=280, r=60, t=80, b=50),
        template="plotly_white",
        coloraxis_colorbar_title="实际流失率"
    )

    return fig


# =========================
# 页面主体
# =========================
st.title("🔗 多维客户挽留优先级交集分析")

st.markdown(
    """
本页面通过 **韦恩图** 和 **UpSet Plot** 分析客户在多个风险信号上的重叠关系，
用于识别既有业务价值、又存在流失风险、同时已经暴露负面行为或反馈的重点客户群。

核心思路：

- **韦恩图**：用于展示 3 个关键客户集合的交集；
- **UpSet Plot**：用于展示多个风险信号之间的复杂组合关系；
- **组合价值图**：结合 CLV、流失率、触达率等指标，对重点组合进行业务优先级排序。
"""
)

with st.expander("📌 图表解释说明", expanded=False):
    st.markdown(
        """
### 为什么这里要用韦恩图和 UpSet Plot？

普通柱状图只能展示单个维度，例如高价值客户数量、负面反馈数量或流失客户数量。
但在真实客户挽留场景中，企业更关心的是：

> 哪些客户同时满足多个高风险条件？

例如：

- 既是高价值客户；
- 又属于中高流失风险；
- 同时还给出了负面反馈；
- 并且已经多次联系客服；
- 或者已经被营销触达但仍然存在流失风险。

这类客户才是最值得重点关注的对象。

### 注意事项

本数据集中的反馈、营销活动和业务成本字段包含合成生成成分，
因此交集分析主要用于学习和展示客户分析方法，不应直接解释为真实业务因果结论。
"""
    )


# =========================
# 侧边栏参数
# =========================
st.sidebar.header("⚙️ 交集分析参数")

risk_level_options = st.sidebar.multiselect(
    "选择中高风险等级",
    options=["low", "medium", "high"],
    default=["medium", "high"]
)

service_call_threshold = st.sidebar.slider(
    "高频客服阈值：客服呼叫次数 ≥",
    min_value=1,
    max_value=8,
    value=4,
    step=1
)

complaint_threshold = st.sidebar.slider(
    "高投诉强度阈值：投诉强度 ≥",
    min_value=1,
    max_value=5,
    value=4,
    step=1
)

top_n_upset = st.sidebar.slider(
    "UpSet Plot 展示 Top N 组合",
    min_value=5,
    max_value=30,
    value=15,
    step=1
)

top_n_summary = st.sidebar.slider(
    "组合价值图展示 Top N 组合",
    min_value=5,
    max_value=30,
    value=15,
    step=1
)


# =========================
# 数据加载
# =========================
df_raw = build_intersection_analysis_df()

df = add_risk_signal_columns(
    df_raw,
    risk_levels=risk_level_options,
    service_call_threshold=service_call_threshold,
    complaint_threshold=complaint_threshold
)


# =========================
# 顶部指标卡
# =========================
total_customers = df["customer_id"].nunique()
churn_customers = df.loc[df["已流失"], "customer_id"].nunique()
high_value_customers = df.loc[df["高价值"], "customer_id"].nunique()
high_risk_customers = df.loc[df["中高风险"], "customer_id"].nunique()
negative_customers = df.loc[df["负面反馈"], "customer_id"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("客户总数", f"{total_customers:,}")
col2.metric("流失客户数", f"{churn_customers:,}", f"{churn_customers / total_customers:.1%}")
col3.metric("高价值客户", f"{high_value_customers:,}", f"{high_value_customers / total_customers:.1%}")
col4.metric("中高风险客户", f"{high_risk_customers:,}", f"{high_risk_customers / total_customers:.1%}")
col5.metric("负面反馈客户", f"{negative_customers:,}", f"{negative_customers / total_customers:.1%}")

st.divider()


# =========================
# Tab 页面
# =========================
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "① 韦恩图：重点挽留客户池",
        "② UpSet Plot：多信号组合",
        "③ 组合价值排序",
        "④ 明细数据"
    ]
)


# =========================
# Tab 1：韦恩图
# =========================
with tab1:
    st.subheader("① 高价值 × 中高风险 × 负面反馈客户交集分析韦恩图")

    st.markdown(
        """
该韦恩图选取三个最关键的客户集合：

- **高价值客户**：`customer_value_segment == high_value`
- **中高风险客户**：风险等级属于所选风险等级，默认 `medium/high`
- **负面反馈客户**：`sentiment == negative`

三者中心交集代表：

> 同时具备高业务价值、高流失风险和负面反馈的重点挽留客户。
"""
    )

    fig_venn, center_set = plot_priority_customer_venn(df)

    left_col, right_col = st.columns([1.3, 1])

    with left_col:
        st.pyplot(fig_venn)
        plt.close(fig_venn)

    with right_col:
        center_df = df[df["customer_id"].isin(center_set)].copy()

        st.markdown("#### 🎯 中心交集客户概览")

        if len(center_df) > 0:
            c1, c2 = st.columns(2)
            c1.metric("中心交集客户数", f"{len(center_df):,}")
            c2.metric("中心交集流失率", f"{center_df['churn_int'].mean():.1%}")

            c3, c4 = st.columns(2)
            c3.metric("平均 CLV", f"{center_df['estimated_clv'].mean():.2f}")
            c4.metric("平均预期流失损失", f"{center_df['expected_loss_if_churn'].mean():.2f}")

            c5, c6 = st.columns(2)
            c5.metric("营销触达率", f"{center_df['contacted'].mean():.1%}")
            c6.metric("营销响应率", f"{center_df['responded'].mean():.1%}")

            st.markdown(
                """
**业务解释：**

中心交集客户数量通常不大，但业务优先级很高。
这部分客户既有价值，又已经暴露流失风险和负面情绪，
适合优先进行客服回访、套餐优化或个性化留存优惠。
"""
            )
        else:
            st.warning("当前筛选条件下，三个集合没有中心交集客户。可以放宽风险等级或阈值。")

# =========================
# Tab 2：UpSet Plot
# =========================
with tab2:
    st.subheader("② 多风险信号组合 UpSet Plot")

    st.markdown(
        """
UpSet Plot 用于展示多个客户风险信号之间的复杂交集关系。
相比传统韦恩图，UpSet Plot 更适合展示 4 个及以上集合。
"""
    )

    all_signal_options = [
        "已流失",
        "高价值",
        "中高风险",
        "高频客服",
        "负面反馈",
        "高投诉强度",
        "营销触达",
        "营销响应",
        "有国际套餐",
        "高使用强度"
    ]

    default_signals = [
        "已流失",
        "高价值",
        "中高风险",
        "高频客服",
        "负面反馈",
        "营销触达"
    ]

    selected_signals = st.multiselect(
        "选择参与 UpSet Plot 的风险信号",
        options=all_signal_options,
        default=default_signals
    )

    if len(selected_signals) < 2:
        st.warning("请至少选择 2 个风险信号。")
    else:
        fig_upset = plot_customer_risk_upset_plotly(
            df=df,
            selected_signals=selected_signals,
            top_n=top_n_upset
        )

        if fig_upset is not None:
            st.plotly_chart(fig_upset, use_container_width=True)

            st.info(
                """
读图方式：  
上方柱状图表示某个风险信号组合下的客户数量；  
下方深色圆点表示该组合命中的风险信号；  
同一列中被连线连接的圆点表示这些信号同时出现。
"""
            )
            st.markdown(
                """
            本图用于观察多个客户风险信号之间的重叠结构。  
            每一列代表一种风险信号组合，上方柱状图表示该组合覆盖的客户数量，
            下方点阵展示该组合具体包含哪些客户特征。

            通过该图可以快速识别客户群体中最常见的风险组合，
            例如“已流失 ∩ 中高风险 ∩ 高频客服”或“高价值 ∩ 负面反馈 ∩ 营销触达”等组合。
            """
            )

        else:
            st.warning("当前筛选条件下没有可展示的组合。")

# =========================
# Tab 3：组合价值排序
# =========================
with tab3:
    st.subheader("③ 风险信号组合的业务价值排序")

    st.markdown(
        """
为了让 UpSet Plot 不只是展示“人数”，这里进一步结合：

- 客户数量；
- 平均 CLV；
- 实际流失率；
- 预期流失损失；
- 营销触达率；
- 营销响应率；

构造组合层面的业务价值分析。
"""
    )

    if len(selected_signals) < 2:
        st.warning("请先在 UpSet Plot 页面至少选择 2 个风险信号。")
    else:
        summary_df = make_risk_combination_summary(
            df=df,
            selected_signals=selected_signals,
            top_n=top_n_summary
        )

        if summary_df.empty:
            st.warning("当前条件下没有可展示的风险组合。")
        else:
            fig_bubble = plot_risk_combination_bubble(summary_df)
            st.plotly_chart(fig_bubble, use_container_width=True)

            fig_bar = plot_risk_combination_bar(summary_df)
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("#### 风险组合统计表")

            show_df = summary_df.copy()

            percent_cols = [
                "实际流失率",
                "营销触达率",
                "营销响应率"
            ]

            for col in percent_cols:
                show_df[col] = show_df[col].map(lambda x: f"{x:.2%}")

            money_cols = [
                "平均CLV",
                "平均月收入",
                "平均预期流失损失",
                "平均留存净收益",
                "潜在价值规模",
                "风险价值指数"
            ]

            for col in money_cols:
                show_df[col] = show_df[col].map(lambda x: f"{x:,.2f}")

            st.dataframe(
                show_df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown(
                """
**业务解释：**

- 客户数越多，说明该组合覆盖面越大；
- 平均 CLV 越高，说明该组合客户价值越高；
- 实际流失率越高，说明该组合风险越强；
- 风险价值指数越高，说明该组合越值得优先干预。

因此，企业可以优先关注右上方高 CLV、高客户数、高流失率的客户组合。
"""
            )


# =========================
# Tab 4：明细数据
# =========================
with tab4:
    st.subheader("④ 客户交集分析明细数据")

    st.markdown(
        """
这里展示用于交集分析的客户级数据，可以用于检查每个客户命中了哪些风险信号。
"""
    )

    display_cols = [
        "customer_id",
        "churn_label",
        "state",
        "customer_value_segment",
        "usage_intensity",
        "rule_based_churn_risk_score",
        "rule_based_churn_risk_level",
        "customer_service_calls",
        "sentiment",
        "feedback_category",
        "complaint_intensity",
        "estimated_clv",
        "expected_loss_if_churn",
        "net_gain_if_retained",
        "contacted",
        "responded",
        "campaign_channel",
        "uplift_label",
        "已流失",
        "高价值",
        "中高风险",
        "高频客服",
        "负面反馈",
        "高投诉强度",
        "营销触达",
        "营销响应",
        "有国际套餐",
        "高使用强度"
    ]

    display_cols = [col for col in display_cols if col in df.columns]

    filter_signal = st.multiselect(
        "按风险信号筛选客户",
        options=[
            "已流失",
            "高价值",
            "中高风险",
            "高频客服",
            "负面反馈",
            "高投诉强度",
            "营销触达",
            "营销响应",
            "有国际套餐",
            "高使用强度"
        ],
        default=[]
    )

    detail_df = df.copy()

    for signal in filter_signal:
        detail_df = detail_df[detail_df[signal]]

    st.caption(f"当前筛选后客户数：{len(detail_df):,}")

    st.dataframe(
        detail_df[display_cols],
        use_container_width=True,
        hide_index=True
    )
