import streamlit as st

st.set_page_config(page_title="电信客户分析系统", page_icon="📞", layout="wide")

# ======================================================
# 🎨 核心魔法：CSS 强行构建三级缩进结构
# ======================================================
st.markdown("""
<style>
    /* --- 一级目录样式 (📂 数据分析 / 🧠 数据挖掘) --- */
    .level-1-header {
        font-size: 1.2rem;
        font-weight: 800;
        color: #1E1E1E;
        padding: 1rem 0 0.5rem 0.8rem;
        background-color: #F0F2F6; /* 给一级目录加个浅色背景，区分感更强 */
        margin-top: 10px;
        border-radius: 5px;
    }

    /* --- 二级目录样式 (📊 全量客户分析 等) --- */
    /* 这里的 [data-testid="stSidebarNav"] h2 是 st.navigation 的字典键 */
    [data-testid="stSidebarNavItems"] div:has(> h2) {
        margin-top: 5px;
    }

    [data-testid="stSidebarNav"] h2 {
        font-size: 1.0rem !important;
        font-weight: 700 !important;
        color: #444 !important;
        padding-left: 1.5rem !important; /* 二级目录缩进 */
        margin-bottom: 0px !important;
    }

    /* --- 三级目录样式 (具体页面链接) --- */
    [data-testid="stSidebarNav"] a {
        padding-left: 3.5rem !important; /* 三级页面深度缩进 */
        font-size: 0.9rem !important;
        height: 30px !important; /* 缩小行高，让结构更紧凑 */
        line-height: 30px !important;
    }

    /* 选中状态的样式 */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #E1E4E8 !important;
        border-left: 5px solid #FF4B4B !important;
        padding-left: calc(3.5rem - 5px) !important;
    }
</style>
""", unsafe_allow_html=True)

# ======================================================
# 1. 定义所有页面对象
# ======================================================

# EDA 部分
# EDA 部分
eda_full_0 = st.Page("views/eda/full_customers/eda_audit.py", title="EDA 数据体检", icon="🔎")
eda_full_1 = st.Page("views/eda/full_customers/basic.py", title="基础画像概览", icon="👥")
eda_full_2 = st.Page("views/eda/full_customers/usage.py", title="行为习惯分析", icon="📈")
eda_full_3 = st.Page("views/eda/full_customers/geo.py", title="地域分析", icon="📈")
eda_full_4 = st.Page("views/eda/full_customers/risk.py", title="风险分析", icon="📈")
eda_full_5 = st.Page("views/eda/full_customers/revenue.py", title="客户贡献分析", icon="📈")

eda_feed_1 = st.Page("views/eda/customer_feedback/sentiment.py", title="情感倾向分析", icon="🎭")
# eda_feed_2 = st.Page("views/eda/customer_feedback/keywords.py", title="反馈关键词云", icon="☁️")
eda_biz_1 = st.Page("views/eda/business_costs/financial.py", title="财务损失评估", icon="💰")
eda_camp_1 = st.Page("views/eda/campaign_uplift/uplift_overview.py", title="营销增量概览", icon="🎯")

# Mining 部分
ml_1 = st.Page("views/mining/churn.py", title="流失预测模型", icon="🤖")
ml_2 = st.Page("views/mining/uplift.py", title="Uplift 增量建模", icon="🏹")
ml_3 = st.Page("views/mining/roi.py", title="策略 ROI 模拟", icon="📊")

# ======================================================
# 2. 构建导航 (关键：只能调用一次 st.navigation)
# ======================================================

# 我们手动在侧边栏插入一级标题
st.sidebar.markdown('<div class="level-1-header">📂 数据分析</div>', unsafe_allow_html=True)

# 定义导航树

# 重点：Streamlit 目前不支持在 navigation 中间插入 markdown
# 如果你需要“数据挖掘”出现在下面，我们需要把它们合并，并用 CSS 技巧或者特殊的 Section 命名
# 这里采用最稳妥的办法：将所有内容合并，通过 CSS 区分

pg = st.navigation({
    "📊 全量客户分析": [eda_full_0, eda_full_1, eda_full_2, eda_full_3, eda_full_4, eda_full_5],
    "💬 客户反馈分析": [eda_feed_1],
    "💵 财务价值分析": [eda_biz_1],
    "🚀 营销活动分析": [eda_camp_1],
    "────────────────": [],  # 分割线
    "🤖 模型：流失预测": [ml_1],
    "🏹 模型：Uplift 增量": [ml_2],
    "📊 模型：策略 ROI": [ml_3],
})

# 如果你想让“数据挖掘”看起来像一级标题，我们可以在 CSS 里针对第 5 个 h2 进行特殊处理
st.markdown("""
<style>
    /* 针对分割线后的第一个二级标题，把它伪装成一级标题 */
    [data-testid="stSidebarNavItems"] div:nth-child(6) h2 {
        background-color: #F0F2F6 !important;
        padding-left: 0.8rem !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        color: #1E1E1E !important;
        margin-top: 20px !important;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

pg.run()
