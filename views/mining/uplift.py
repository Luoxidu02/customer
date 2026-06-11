import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.model_selection import train_test_split
# 换成了更强大的梯度提升树 (GBDT)
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score

# 引入你写好的数据加载模块
from utils.data_loader import load_campaign_with_customer_business

st.title("🎯 智能营销增效模型 (Uplift Modeling)")
st.markdown("""
> **商业痛点：** 传统的流失预测只告诉我们“谁会走”。如果给所有预测流失的人发代金券，不仅成本巨大，还可能唤醒“不应打扰型”客户（本来忘了退网，收到短信反而去退了）。
> **解决方案：** 通过增效模型，将客户精准分为 **5 大类**，找出真正的 **“可被说服型”**，实现营销 ROI 最大化！
""")

# ==========================================
# 0. 标签映射字典
# ==========================================
uplift_label_map = {
    'sure_thing': '自然留存型',
    'persuadable': '可被说服型',
    'do_not_disturb': '不应打扰型',
    'uncertain': '不确定型',
    'lost_cause': '挽回无望型'
}

color_map = {
    '自然留存型': '#3498db',  # 蓝色
    '可被说服型': '#2ecc71',  # 绿色
    '不应打扰型': '#e74c3c',  # 红色
    '不确定型': '#9b59b6',  # 紫色
    '挽回无望型': '#95a5a6'  # 灰色
}

# ==========================================
# 1. 使用 data_loader 加载数据
# ==========================================
with st.spinner("正在加载多维融合数据..."):
    df = load_campaign_with_customer_business()
    df['uplift_label_cn'] = df['uplift_label'].map(uplift_label_map)

if not df.empty:
    # ==========================================
    # 2. 营销人群画像分析
    # ==========================================
    st.header("📊 1. 客户营销敏感度画像")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        label_counts = df['uplift_label_cn'].value_counts().reset_index()
        label_counts.columns = ['人群类型', '数量']

        fig_pie = px.pie(label_counts, names='人群类型', values='数量',
                         color='人群类型', color_discrete_map=color_map,
                         hole=0.4, title="客户增效标签真实分布")
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("### 💡 营销动作指南")
        st.info("**🟢 可被说服型:** 重点营销对象！发券就能留住，不发就会流失。ROI 最高。")
        st.success("**🔵 自然留存型:** 铁粉。不发券也不会走。**策略：不发券，省下成本。**")
        st.error("**🔴 不应打扰型:** 沉睡的狗。本来不走，一发短信提醒反而走了。**策略：绝对避开！**")
        st.warning("**🟣 不确定型:** 行为模糊。**策略：可进行小规模 A/B 测试。**")
        st.markdown("""<div style="padding: 1rem; border-radius: 0.5rem; background-color: #f8f9fa; color: #6c757d;">
        <b>⚪ 挽回无望型:</b> 铁定要走。发券也救不回来。<b>策略：放弃挽留，节省资源。</b>
        </div>""", unsafe_allow_html=True)

    # ==========================================
    # 3. 训练增效预测模型 (GBDT) & 全面评估
    # ==========================================
    st.header("🧠 2. 训练 Uplift 预测模型 (GBDT) 与评估")
    st.markdown(
        "为了捕捉更复杂的非线性关系，我们采用 **梯度提升树 (GBDT)**。针对 5 分类问题，我们不仅关注准确率，更关注模型在各个类别上的 F1-Score 与混淆矩阵。")

    # 引入额外的评估指标库
    from sklearn.metrics import classification_report, confusion_matrix

    with st.spinner('正在训练 GBDT 模型并计算指标...'):
        features_to_use = ['customer_service_calls', 'rule_based_churn_risk_score',
                           'monthly_revenue', 'estimated_clv']

        X = df[features_to_use].fillna(0)
        y = df['uplift_label_cn']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 训练 GBDT 模型
        gb_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
        gb_model.fit(X_train, y_train)

        # 预测
        y_pred = gb_model.predict(X_test)

        # --- 核心指标计算 ---
        acc = accuracy_score(y_test, y_pred)
        report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        macro_f1 = report_dict['macro avg']['f1-score']
        weighted_f1 = report_dict['weighted avg']['f1-score']

        # 1. 顶部核心指标 KPI 卡片
        st.subheader("指标概览")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("🎯 整体准确率 (Accuracy)", f"{acc:.1%}", "所有样本中预测正确的比例")
        col_m2.metric("⚖️ 宏平均 F1 (Macro F1)", f"{macro_f1:.1%}", "各类别同等权重，衡量少数类表现")
        col_m3.metric("📊 加权平均 F1 (Weighted F1)", f"{weighted_f1:.1%}", "按样本量加权，衡量整体综合表现")

        st.divider()  # 分割线

        # 2. 混淆矩阵与特征重要性 并排展示
        col_v1, col_v2 = st.columns(2)

        with col_v1:
            # 绘制混淆矩阵热力图
            labels = sorted(list(set(y_test)))
            cm = confusion_matrix(y_test, y_pred, labels=labels)
            fig_cm = px.imshow(cm, text_auto=True, x=labels, y=labels,
                               labels=dict(x="模型预测类别", y="真实类别", color="样本数"),
                               color_continuous_scale='Blues',
                               title="🔍 混淆矩阵 (Confusion Matrix)")
            fig_cm.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_cm, use_container_width=True)

        with col_v2:
            # 特征重要性
            importances = gb_model.feature_importances_
            df_imp = pd.DataFrame({'特征': features_to_use, '重要性': importances}).sort_values(by='重要性',
                                                                                                ascending=True)
            feature_name_map = {
                'customer_service_calls': '客服呼叫次数',
                'rule_based_churn_risk_score': '规则流失风险分',
                'monthly_revenue': '月度营收',
                'estimated_clv': '预计终身价值(CLV)'
            }
            df_imp['特征中文'] = df_imp['特征'].map(feature_name_map)

            fig_imp = px.bar(df_imp, x='重要性', y='特征中文', orientation='h',
                             title="🌟 GBDT 特征重要性 (Feature Importance)")
            st.plotly_chart(fig_imp, use_container_width=True)

        # 3. 详细分类报告 (折叠面板，保持页面整洁)
        with st.expander("📄 查看详细分类报告 (Classification Report)"):
            st.markdown("展示每个细分类别的 **查准率 (Precision)**、**查全率 (Recall)** 和 **F1分数**：")
            # 过滤掉全局指标，只保留具体类别的指标
            df_report = pd.DataFrame(report_dict).transpose().iloc[:-3, :-1]
            df_report.columns = ['查准率 (Precision)', '查全率 (Recall)', 'F1-Score']
            # 格式化为百分比
            st.dataframe(df_report.style.format("{:.1%}"), use_container_width=True)

    # ==========================================
    # 4. 商业价值模拟 (基于真实业务数据的 ROI)
    # ==========================================
    st.header("💰 3. 商业价值模拟 (基于真实财务数据)")

    real_cost_per_offer = df[df['retention_cost'] > 0]['retention_cost'].mean()
    if pd.isna(real_cost_per_offer): real_cost_per_offer = 15.0

    real_value_per_retained = df['estimated_clv'].mean()

    st.markdown(
        f"假设我们对 **10,000 名** 预测有流失风险的客户进行营销干预。根据底层业务数据测算：\n* 平均单客挽留成本：**¥ {real_cost_per_offer:.2f}**\n* 挽留成功平均终身价值 (CLV)：**¥ {real_value_per_retained:.2f}**")

    label_probs = df['uplift_label_cn'].value_counts(normalize=True).to_dict()
    p_persuadable = label_probs.get('可被说服型', 0.15)
    p_do_not_disturb = label_probs.get('不应打扰型', 0.05)

    total_target_customers = 10000

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.subheader("❌ 策略 A：传统无差别发券")
        st.markdown("给所有人发券（不管他需不需要）。")

        cost_A = total_target_customers * real_cost_per_offer
        retained_A = (total_target_customers * p_persuadable) - (total_target_customers * p_do_not_disturb)
        revenue_A = retained_A * real_value_per_retained
        roi_A = revenue_A - cost_A

        st.metric("营销总成本", f"¥ {cost_A:,.0f}")
        st.metric("挽回净收益 (扣除成本前)", f"¥ {revenue_A:,.0f}")
        st.metric("最终净利润 (ROI)", f"¥ {roi_A:,.0f}", delta="成本高，且唤醒了沉睡客户", delta_color="inverse")

    with col_r2:
        st.subheader("✅ 策略 B：Uplift 精准发券")
        st.markdown("利用 GBDT 模型，**只给「可被说服型」发券**。")

        target_count = total_target_customers * p_persuadable
        cost_B = target_count * real_cost_per_offer
        retained_B = target_count
        revenue_B = retained_B * real_value_per_retained
        roi_B = revenue_B - cost_B

        st.metric("营销总成本", f"¥ {cost_B:,.0f}")
        st.metric("挽回净收益 (扣除成本前)", f"¥ {revenue_B:,.0f}")
        st.metric("最终净利润 (ROI)", f"¥ {roi_B:,.0f}", delta=f"比传统策略多赚 ¥{roi_B - roi_A:,.0f}！")

    st.success(
        f"**结论：** 引入 Uplift 模型后，我们不仅**节省了 {(cost_A - cost_B) / cost_A:.0%} 的营销成本**，还避免了打扰「不应打扰型」客户，最终净利润大幅提升！")
else:
    st.error("数据加载失败，请检查 data_loader.py 及其数据文件路径。")
