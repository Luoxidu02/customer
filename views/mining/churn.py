import streamlit as st
from utils.data_loader import load_train, load_test
from sklearn.metrics import average_precision_score
from sklearn.decomposition import PCA
from sklearn.metrics import average_precision_score
from sklearn.decomposition import PCA, TruncatedSVD
from scipy import sparse
import plotly.express as px
from sklearn.base import clone
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

#这个代码里面虽然写的是2种测试集选择，但是我只用了真正的测试集作为测试集，不是从训练集划分的！！！！
st.title("🤖 流失预测模型")
st.warning("🔧 开发中：特征工程、模型训练、ROC曲线、混淆矩阵、SHAP解释")
st.markdown("**使用数据：** `train.xlsx` + `test.xlsx`")
import os
import pickle
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import log_loss, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except Exception:
    WORDCLOUD_AVAILABLE = False

import streamlit as st
from utils.data_loader import load_train, load_test
# 👇 新增：导入 feedback 数据（如果 data_loader 里没有，可以用 pd.read_excel 替代）
try:
    from utils.data_loader import load_feedback
except ImportError:
    def load_feedback():
        return pd.read_excel("data/customer_feedback.xlsx") # 根据你的实际路径修改

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
try:
    import shap
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

try:
    import torch
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False



from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    ConfusionMatrixDisplay,
    average_precision_score
)

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False
try:
    from lightgbm import LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except Exception:
    LIGHTGBM_AVAILABLE = False

try:
    import torch
    from pytorch_tabnet.tab_model import TabNetClassifier
    TABNET_AVAILABLE = True
except Exception:
    TABNET_AVAILABLE = False


# =========================
# 页面基础设置
# =========================

st.title("🤖 流失预测模型")
st.caption("基于多种二分类算法的电信客户流失预测与模型对比分析")

st.markdown("""
本页面使用多种二分类算法对客户是否流失进行预测，并比较不同模型的分类效果。  
目标变量为 `churn`，其中 `1` 表示流失，`0` 表示未流失。
""")

st.markdown("**使用数据：** `train.xlsx` + `test.xlsx`")

st.divider()


# =========================
# 初始化 session_state
# =========================

if "model_results" not in st.session_state:
    st.session_state.model_results = None

if "roc_data" not in st.session_state:
    st.session_state.roc_data = None

if "confusion_data" not in st.session_state:
    st.session_state.confusion_data = None

if "importance_data" not in st.session_state:
    st.session_state.importance_data = None

if "last_train_config" not in st.session_state:
    st.session_state.last_train_config = None
if "training_histories" not in st.session_state:
    st.session_state.training_histories = None
if "risk_space_data" not in st.session_state:
    st.session_state.risk_space_data = None
if "shap_pipes" not in st.session_state:
    st.session_state.shap_pipes = None
if "shap_X_test" not in st.session_state:
    st.session_state.shap_X_test = None

if "shap_y_test" not in st.session_state:
    st.session_state.shap_y_test = None
if "xgb_animation_data" not in st.session_state:
    st.session_state.xgb_animation_data = None
if "xgb_pipes" not in st.session_state:
    st.session_state.xgb_pipes = None
if "xgb_X_train" not in st.session_state:
    st.session_state.xgb_X_train = None

if "xgb_X_test" not in st.session_state:
    st.session_state.xgb_X_test = None

if "xgb_y_train" not in st.session_state:
    st.session_state.xgb_y_train = None

if "xgb_y_test" not in st.session_state:
    st.session_state.xgb_y_test = None




# =========================
# 训练结果本地缓存文件
# =========================

RESULT_CACHE_FILE = "model_training_cache.pkl"
DEFAULT_LOCAL_BERT_PATH = r"D:\1大三下的所有课程\可视化\大作业\句子bert"


# 如果页面刷新导致 session_state 清空，则尝试从本地缓存恢复训练结果
if st.session_state.model_results is None and os.path.exists(RESULT_CACHE_FILE):
    try:
        with open(RESULT_CACHE_FILE, "rb") as f:
            cached_results = pickle.load(f)

        st.session_state.model_results = cached_results.get("model_results")
        st.session_state.roc_data = cached_results.get("roc_data")
        st.session_state.confusion_data = cached_results.get("confusion_data")
        st.session_state.importance_data = cached_results.get("importance_data")
        st.session_state.training_histories = cached_results.get("training_histories")
        st.session_state.risk_space_data = cached_results.get("risk_space_data")
        st.session_state.shap_pipes = cached_results.get("shap_pipes")
        st.session_state.shap_X_test = cached_results.get("shap_X_test")
        st.session_state.shap_y_test = cached_results.get("shap_y_test")
        st.session_state.last_train_config = cached_results.get("last_train_config")
        st.session_state.xgb_animation_data = cached_results.get("xgb_animation_data")
        st.session_state.xgb_pipes = cached_results.get("xgb_pipes")
        st.session_state.xgb_X_train = cached_results.get("xgb_X_train")
        st.session_state.xgb_X_test = cached_results.get("xgb_X_test")
        st.session_state.xgb_y_train = cached_results.get("xgb_y_train")
        st.session_state.xgb_y_test = cached_results.get("xgb_y_test")

        st.info("已从本地缓存恢复上一次训练结果，刷新页面不会重新训练。")

    except Exception as e:
        st.warning("读取本地训练缓存失败，将在重新训练后生成新的缓存。")


# =========================
# 数据读取
# =========================

try:
    train_df = load_train()
    test_df = load_test()
except Exception as e:
    st.error("数据读取失败，请检查 data/train.xlsx 和 data/test.xlsx 是否存在。")
    st.exception(e)
    st.stop()





# =========================
# 数据预处理函数
# =========================

def get_onehot_encoder():
    """
    兼容不同版本 sklearn 的 OneHotEncoder 参数。
    """
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


# =========================
# 👇 新增：处理 Feedback 文本特征的函数
# =========================
def process_feedback_features(feedback_df):
    df = feedback_df.copy()

    # 1. 情感映射为数值
    sentiment_map = {
        "positive": 1,
        "neutral": 0,
        "negative": -1
    }

    df["sentiment_score"] = (
        df["sentiment"]
        .map(sentiment_map)
        .fillna(0)
        .astype(float)
    )

    # 2. 抱怨强度保持数值型
    df["complaint_intensity"] = (
        pd.to_numeric(df["complaint_intensity"], errors="coerce")
        .fillna(0)
        .astype(float)
    )

    # 3. 不再使用 feedback_category，不再生成 feedback_xxx 类别特征
    agg_dict = {
        "sentiment_score": "mean",
        "complaint_intensity": "max"
    }

    customer_feedback_features = (
        df.groupby("customer_id")
        .agg(agg_dict)
        .reset_index()
    )

    return customer_feedback_features

@st.cache_resource(show_spinner=False)
def load_local_sentence_bert_model(local_model_path):
    """
    从本地文件夹加载 Sentence-BERT 模型。
    本项目使用 sentence-transformers/all-MiniLM-L6-v2。
    """

    if not TRANSFORMERS_AVAILABLE:
        raise ImportError(
            "当前环境未安装 sentence-transformers 或 torch，请先执行：pip install sentence-transformers torch safetensors"
        )

    if not os.path.isdir(local_model_path):
        raise FileNotFoundError(f"本地 Sentence-BERT 路径不存在：{local_model_path}")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = SentenceTransformer(
        local_model_path,
        device=device
    )

    return model


@st.cache_data(show_spinner=False)
def process_feedback_bert_features(
    feedback_df,
    local_model_path,
    batch_size=16,
    bert_output_dim=None
):
    """
    使用本地 Sentence-BERT 将 feedback_text 转换为语义向量特征。
    如果 bert_output_dim 不为空，则使用 PCA 将 BERT 向量降维。
    输出字段：
    customer_id, bert_emb_000, bert_emb_001, ...
    """

    if not TRANSFORMERS_AVAILABLE:
        raise ImportError(
            "当前环境未安装 sentence-transformers 或 torch，请先执行：pip install sentence-transformers torch safetensors"
        )

    if not os.path.isdir(local_model_path):
        raise FileNotFoundError(f"本地 Sentence-BERT 路径不存在：{local_model_path}")

    df = feedback_df.copy()

    df["feedback_text"] = df["feedback_text"].fillna("").astype(str)

    # 一个客户可能有多条反馈，按 customer_id 拼接成一段文本
    customer_text_df = (
        df.groupby("customer_id")["feedback_text"]
        .apply(lambda texts: " ".join(texts))
        .reset_index()
        .rename(columns={"feedback_text": "feedback_text_merged_for_bert"})
    )

    texts = customer_text_df["feedback_text_merged_for_bert"].tolist()

    model = load_local_sentence_bert_model(local_model_path)

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    original_dim = embeddings.shape[1]

    # =========================
    # 可选：PCA 降维
    # =========================
    if bert_output_dim is not None:
        bert_output_dim = int(bert_output_dim)

        if bert_output_dim <= 0:
            raise ValueError("bert_output_dim 必须大于 0。")

        if bert_output_dim < original_dim:
            max_components = min(
                bert_output_dim,
                embeddings.shape[0],
                embeddings.shape[1]
            )

            pca = PCA(
                n_components=max_components,
                random_state=42
            )

            embeddings = pca.fit_transform(embeddings)

        elif bert_output_dim == original_dim:
            pass

        else:
            raise ValueError(
                f"bert_output_dim={bert_output_dim} 不能大于原始 BERT 维度 {original_dim}。"
            )

    bert_feature_cols = [
        f"bert_emb_{i:03d}" for i in range(embeddings.shape[1])
    ]

    bert_features_df = pd.DataFrame(
        embeddings,
        columns=bert_feature_cols
    )

    bert_features_df.insert(
        0,
        "customer_id",
        customer_text_df["customer_id"].values
    )

    return bert_features_df


def process_feedback_text_features(feedback_df):
    """
    将 feedback_text 原始文本按 customer_id 聚合。
    如果一个客户有多条反馈，就拼接成一段文本。
    """
    df = feedback_df.copy()

    df["feedback_text"] = df["feedback_text"].fillna("").astype(str)

    customer_text_features = (
        df.groupby("customer_id")["feedback_text"]
        .apply(lambda texts: " ".join(texts))
        .reset_index()
        .rename(columns={"feedback_text": "feedback_text_merged"})
    )

    return customer_text_features
def build_feedback_text_analysis_df(train_df, test_df):
    """
    构造用于文本可视化的数据：
    将 customer_feedback.xlsx 中的 feedback_text 与 train/test 中的 churn 标签合并。
    """
    feedback_df = load_feedback().copy()

    if "feedback_text" not in feedback_df.columns:
        raise ValueError("feedback 数据中找不到 feedback_text 字段。")

    if "customer_id" not in feedback_df.columns:
        raise ValueError("feedback 数据中找不到 customer_id 字段。")

    feedback_df["feedback_text"] = feedback_df["feedback_text"].fillna("").astype(str)

    label_cols = ["customer_id", "churn"]

    train_label_df = train_df[label_cols].copy() if all(col in train_df.columns for col in label_cols) else pd.DataFrame()
    test_label_df = test_df[label_cols].copy() if all(col in test_df.columns for col in label_cols) else pd.DataFrame()

    label_df = pd.concat(
        [train_label_df, test_label_df],
        ignore_index=True
    ).drop_duplicates(subset=["customer_id"])

    text_df = pd.merge(
        feedback_df,
        label_df,
        on="customer_id",
        how="left"
    )

    text_df["churn_label"] = text_df["churn"].map({
        0: "未流失客户",
        1: "流失客户"
    }).fillna("未知客户")

    return text_df

def get_tfidf_top_words(texts, max_features=200, top_n=30, ngram_range=(1, 2)):
    """
    根据一组文本计算 TF-IDF 平均权重最高的词或短语。
    保留 no / not / nor，避免否定语义被删除。
    """
    texts = pd.Series(texts).fillna("").astype(str)

    texts = texts[texts.str.strip() != ""]

    if len(texts) == 0:
        return pd.DataFrame(columns=["word", "tfidf_weight"])

    custom_stop_words = list(ENGLISH_STOP_WORDS - {"no", "not", "nor"})

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words=custom_stop_words,
        ngram_range=ngram_range,
        min_df=1,
        max_df=0.95,
        sublinear_tf=True
    )

    X_tfidf = vectorizer.fit_transform(texts)

    words = vectorizer.get_feature_names_out()

    weights = np.asarray(X_tfidf.mean(axis=0)).ravel()

    word_df = pd.DataFrame({
        "word": words,
        "tfidf_weight": weights
    }).sort_values("tfidf_weight", ascending=False)

    return word_df.head(top_n)



def plot_wordcloud_from_word_df(word_df, title="反馈文本词云"):
    """
    根据 TF-IDF 权重生成词云。
    """
    if not WORDCLOUD_AVAILABLE:
        raise ImportError("当前环境未安装 wordcloud，请先执行：pip install wordcloud")

    freq_dict = dict(zip(word_df["word"], word_df["tfidf_weight"]))

    wordcloud = WordCloud(
        width=900,
        height=500,
        background_color="white",
        colormap="RdYlBu_r",
        max_words=120,
        prefer_horizontal=0.9,
        random_state=42
    ).generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", pad=12)

    return fig

def prepare_data(train_df, test_df, test_source, test_size, random_seed, use_scaler, use_text_tfidf=False):

    target_col = "churn"

    drop_cols = [
        "customer_id",
        "churn",
        "split",
        "rule_based_churn_risk_score",
        "rule_based_churn_risk_level",

        # 当前不使用反馈结构化数值特征
        "sentiment_score",
        "complaint_intensity"
    ]

    existing_drop_cols_train = [col for col in drop_cols if col in train_df.columns]
    existing_drop_cols_test = [col for col in drop_cols if col in test_df.columns]

    # 兜底删除所有由 feedback_category One-Hot 得到的字段
    feedback_category_cols_train = [
        col for col in train_df.columns
        if col.startswith("feedback_") and col != "feedback_text_merged"
    ]

    feedback_category_cols_test = [
        col for col in test_df.columns
        if col.startswith("feedback_") and col != "feedback_text_merged"
    ]

    existing_drop_cols_train = list(set(existing_drop_cols_train + feedback_category_cols_train))
    existing_drop_cols_test = list(set(existing_drop_cols_test + feedback_category_cols_test))

    if target_col not in train_df.columns:
        raise ValueError("train.xlsx 中找不到 churn 字段。")

    if test_source == "使用 test.xlsx 作为测试集":
        if target_col not in test_df.columns:
            raise ValueError("test.xlsx 中找不到 churn 字段。")

        X_train = train_df.drop(columns=existing_drop_cols_train)
        y_train = train_df[target_col]

        X_test = test_df.drop(columns=existing_drop_cols_test)
        y_test = test_df[target_col]

    else:
        X = train_df.drop(columns=existing_drop_cols_train)
        y = train_df[target_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_seed,
            stratify=y
        )

    # 找出数值型和类别型字段
    # =========================
    # 文本特征处理：feedback_text_merged
    # =========================
    text_feature = "feedback_text_merged"

    if use_text_tfidf and text_feature in X_train.columns:
        X_train[text_feature] = X_train[text_feature].fillna("").astype(str)
        X_test[text_feature] = X_test[text_feature].fillna("").astype(str)
        text_features = [text_feature]
    else:
        text_features = []

        # 如果不启用 TF-IDF，但数据里存在文本列，则删除，避免被 One-Hot
        if text_feature in X_train.columns:
            X_train = X_train.drop(columns=[text_feature])
        if text_feature in X_test.columns:
            X_test = X_test.drop(columns=[text_feature])

    # 找出数值型和类别型字段
    numeric_features = X_train.select_dtypes(
        include=["int64", "float64", "int32", "float32"]
    ).columns.tolist()

    categorical_features = X_train.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    # 避免文本列被当作普通类别变量 One-Hot
    categorical_features = [
        col for col in categorical_features
        if col not in text_features
    ]

    if use_scaler:
        numeric_transformer = StandardScaler()
    else:
        numeric_transformer = "passthrough"

    categorical_transformer = get_onehot_encoder()

    transformers = [
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ]

    if use_text_tfidf and text_feature in X_train.columns:
        custom_stop_words = list(ENGLISH_STOP_WORDS - {"no", "not", "nor"})

        text_transformer = TfidfVectorizer(
            max_features=30,
            stop_words=custom_stop_words,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.9,
            sublinear_tf=True
        )

        transformers.append(
            ("text", text_transformer, text_feature)
        )

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )

    # return X_train, X_test, y_train, y_test, preprocessor, numeric_features, categorical_features
    return X_train, X_test, y_train, y_test, preprocessor, numeric_features, categorical_features, text_features


def get_feature_names(preprocessor, numeric_features, categorical_features, text_features=None):

    """
    获取 One-Hot 编码之后的特征名。
    """
    feature_names = []

    feature_names.extend(numeric_features)

    if len(categorical_features) > 0:
        try:
            ohe = preprocessor.named_transformers_["cat"]
            cat_names = ohe.get_feature_names_out(categorical_features).tolist()
            feature_names.extend(cat_names)
        except Exception:
            pass

    # TF-IDF 文本特征名
    if text_features is not None and len(text_features) > 0:
        try:
            tfidf = preprocessor.named_transformers_["text"]
            text_names = tfidf.get_feature_names_out().tolist()
            text_names = [f"tfidf_{name}" for name in text_names]
            feature_names.extend(text_names)
        except Exception:
            pass

    return feature_names
def get_fitted_transformed_feature_names(preprocessor):
    """
    从已经 fit 完成的 ColumnTransformer 中提取变换后的特征名。
    兼容数值特征、One-Hot 类别特征、TF-IDF 文本特征。
    """
    feature_names = []

    for name, transformer, cols in preprocessor.transformers_:
        if transformer == "drop":
            continue

        if name == "remainder":
            continue

        if isinstance(cols, str):
            input_cols = [cols]
        else:
            try:
                input_cols = list(cols)
            except Exception:
                input_cols = []

        if transformer == "passthrough":
            feature_names.extend(input_cols)

        elif name == "text":
            try:
                text_names = transformer.get_feature_names_out().tolist()
                text_names = [f"tfidf_{x}" for x in text_names]
                feature_names.extend(text_names)
            except Exception:
                feature_names.extend(input_cols)

        elif hasattr(transformer, "get_feature_names_out"):
            try:
                names = transformer.get_feature_names_out(input_cols).tolist()
            except Exception:
                try:
                    names = transformer.get_feature_names_out().tolist()
                except Exception:
                    names = input_cols

            feature_names.extend(names)

        else:
            feature_names.extend(input_cols)

    return feature_names


def get_tree_shap_values(pipe, X_sample):
    """
    针对 LightGBM / XGBoost Pipeline 计算 SHAP values。
    注意：这里 SHAP 值通常解释的是模型原始输出，二分类一般可理解为 log-odds 方向贡献。
    """
    if not SHAP_AVAILABLE:
        raise ImportError("当前环境未安装 shap，请先执行：pip install shap")

    preprocessor = pipe.named_steps["preprocessor"]
    model = pipe.named_steps["model"]

    X_transformed = preprocessor.transform(X_sample)

    if sparse.issparse(X_transformed):
        X_transformed = X_transformed.toarray()
    else:
        X_transformed = np.asarray(X_transformed)

    feature_names = get_fitted_transformed_feature_names(preprocessor)

    if len(feature_names) != X_transformed.shape[1]:
        feature_names = [f"feature_{i}" for i in range(X_transformed.shape[1])]

    X_transformed_df = pd.DataFrame(
        X_transformed,
        columns=feature_names
    )

    explainer = shap.TreeExplainer(model)

    # 为了避免 XGBoost 对 DataFrame 特征名中特殊字符报错，这里传 numpy array
    shap_values = explainer.shap_values(X_transformed)

    expected_value = explainer.expected_value

    # 二分类兼容：LightGBM 有时返回 list，取正类 class 1
    if isinstance(shap_values, list):
        shap_values_to_plot = shap_values[1]

        if isinstance(expected_value, list) or isinstance(expected_value, np.ndarray):
            base_value = expected_value[1]
        else:
            base_value = expected_value

    else:
        shap_values_arr = np.asarray(shap_values)

        # 有些版本返回 shape = (n_samples, n_features, n_classes)
        if shap_values_arr.ndim == 3:
            shap_values_to_plot = shap_values_arr[:, :, 1]

            if isinstance(expected_value, list) or isinstance(expected_value, np.ndarray):
                base_value = np.asarray(expected_value).ravel()[1]
            else:
                base_value = expected_value
        else:
            shap_values_to_plot = shap_values_arr

            if isinstance(expected_value, list) or isinstance(expected_value, np.ndarray):
                base_value = np.asarray(expected_value).ravel()[0]
            else:
                base_value = expected_value

    return X_transformed_df, shap_values_to_plot, base_value


def plot_tree_shap_summary(pipe, X_sample, max_display=20, title="SHAP Summary Plot"):
    """
    SHAP beeswarm summary plot。
    """
    X_shap_df, shap_values_to_plot, base_value = get_tree_shap_values(pipe, X_sample)

    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_values_to_plot,
        X_shap_df,
        max_display=max_display,
        show=False
    )

    fig = plt.gcf()
    fig.suptitle(title, fontsize=14, y=1.02)

    return fig


def plot_tree_shap_bar(pipe, X_sample, max_display=20, title="SHAP Feature Importance"):
    """
    SHAP bar plot，全局重要性。
    """
    X_shap_df, shap_values_to_plot, base_value = get_tree_shap_values(pipe, X_sample)

    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_values_to_plot,
        X_shap_df,
        plot_type="bar",
        max_display=max_display,
        show=False
    )

    fig = plt.gcf()
    fig.suptitle(title, fontsize=14, y=1.02)

    return fig


def plot_tree_shap_waterfall(pipe, X_sample, sample_pos=0, max_display=15, title="SHAP Waterfall Plot"):
    """
    单个样本 waterfall plot。
    """
    X_shap_df, shap_values_to_plot, base_value = get_tree_shap_values(pipe, X_sample)

    base_value_scalar = np.asarray(base_value).ravel()[0]

    explanation = shap.Explanation(
        values=shap_values_to_plot[sample_pos],
        base_values=base_value_scalar,
        data=X_shap_df.iloc[sample_pos].values,
        feature_names=X_shap_df.columns.tolist()
    )

    plt.figure(figsize=(10, 7))
    shap.plots.waterfall(
        explanation,
        max_display=max_display,
        show=False
    )

    fig = plt.gcf()
    fig.suptitle(title, fontsize=14, y=1.02)

    return fig

def make_2d_risk_space_df(pipe, X_test, y_test, y_pred, y_prob, random_state=42):
    """
    将测试集样本映射到二维特征空间，并叠加模型预测流失概率。
    用于观察同类样本是否在二维空间中相对聚集，以及高风险样本是否集中在相似区域。
    """

    # 1. 获取预处理后的测试集特征
    if hasattr(pipe, "named_steps") and "preprocessor" in pipe.named_steps:
        X_test_transformed = pipe.named_steps["preprocessor"].transform(X_test)
    else:
        X_test_transformed = X_test

    # 2. PCA / TruncatedSVD 降维到二维
    # 2. PCA / TruncatedSVD 降维到三维
    if sparse.issparse(X_test_transformed):
        reducer = TruncatedSVD(n_components=3, random_state=random_state)
        X_3d = reducer.fit_transform(X_test_transformed)
        reducer_name = "TruncatedSVD"
    else:
        reducer = PCA(n_components=3, random_state=random_state)
        X_3d = reducer.fit_transform(X_test_transformed)
        reducer_name = "PCA"

    # 3. 兼容 Series / ndarray
    y_test_arr = y_test.values if isinstance(y_test, pd.Series) else np.asarray(y_test)

    y_pred_arr = np.asarray(y_pred)
    y_prob_arr = np.asarray(y_prob)

    # 4. 生成二维可视化数据
    risk_df = pd.DataFrame({
        "Dim1": X_3d[:, 0],
        "Dim2": X_3d[:, 1],
        "Dim3": X_3d[:, 2],
        "真实标签": y_test_arr.astype(int),
        "预测标签": y_pred_arr.astype(int),
        "预测流失概率": y_prob_arr,
        "是否预测正确": np.where(y_test_arr == y_pred_arr, "预测正确", "预测错误"),
        "降维方法": reducer_name
    })

    risk_df["真实类别"] = risk_df["真实标签"].map({
        0: "真实未流失",
        1: "真实流失"
    })

    risk_df["预测类别"] = risk_df["预测标签"].map({
        0: "预测未流失",
        1: "预测流失"
    })

    return risk_df

def make_xgboost_boosting_animation_df(
    pipe,
    X_test,
    y_test,
    random_state=42,
    max_points=800,
    step=10
):
    """
    生成 XGBoost 逐轮 Boosting 动画数据。

    每一帧表示使用前 r 棵树时，测试集样本的预测流失概率。
    三维坐标由测试集预处理特征经过 PCA / TruncatedSVD 得到。
    """

    preprocessor = pipe.named_steps["preprocessor"]
    model = pipe.named_steps["model"]

    # 1. 为了动画不卡顿，最多抽样 max_points 个测试样本
    if len(X_test) > max_points:
        X_vis = X_test.sample(
            n=max_points,
            random_state=random_state
        )
        selected_index = X_vis.index
        if isinstance(y_test, pd.Series):
            y_vis = y_test.loc[selected_index]
        else:
            y_test_arr = np.asarray(y_test)
            y_vis = y_test_arr[X_test.index.get_indexer(selected_index)]
    else:
        X_vis = X_test.copy()
        y_vis = y_test.copy() if hasattr(y_test, "copy") else np.asarray(y_test)

    # 2. 预处理测试数据
    X_vis_transformed = preprocessor.transform(X_vis)

    # 3. 降到三维，用作固定空间坐标
    if sparse.issparse(X_vis_transformed):
        reducer = TruncatedSVD(n_components=3, random_state=random_state)
        X_3d = reducer.fit_transform(X_vis_transformed)
        reducer_name = "TruncatedSVD"
    else:
        reducer = PCA(n_components=3, random_state=random_state)
        X_3d = reducer.fit_transform(np.asarray(X_vis_transformed))
        reducer_name = "PCA"

    y_vis_arr = y_vis.values if isinstance(y_vis, pd.Series) else np.asarray(y_vis)

    # 4. XGBoost 总树数
    try:
        total_rounds = int(model.n_estimators)
    except Exception:
        total_rounds = 300

    rounds = list(range(1, total_rounds + 1, step))

    if total_rounds not in rounds:
        rounds.append(total_rounds)

    # 5. 每一轮预测一次
    frames = []

    for r in rounds:
        try:
            # 新版 xgboost 推荐 iteration_range
            y_prob_r = model.predict_proba(
                X_vis_transformed,
                iteration_range=(0, r)
            )[:, 1]
        except TypeError:
            # 老版本兼容
            y_prob_r = model.predict_proba(
                X_vis_transformed,
                ntree_limit=r
            )[:, 1]

        temp_df = pd.DataFrame({
            "Dim1": X_3d[:, 0],
            "Dim2": X_3d[:, 1],
            "Dim3": X_3d[:, 2],
            "真实标签": y_vis_arr.astype(int),
            "预测流失概率": y_prob_r,
            "Boosting轮数": r,
            "降维方法": reducer_name
        })
        # 👇👇👇 新增：计算残差与绝对误差 👇👇👇
        temp_df["残差"] = temp_df["真实标签"] - temp_df["预测流失概率"]
        temp_df["预测误差绝对值"] = temp_df["残差"].abs()
        temp_df["散点大小"] = temp_df["预测误差绝对值"]*2 + 0.2
        # 👆👆👆 新增结束 👆👆👆


        temp_df["真实类别"] = temp_df["真实标签"].map({
            0: "真实未流失",
            1: "真实流失"
        })

        temp_df["预测类别"] = np.where(
            temp_df["预测流失概率"] >= 0.5,
            "预测流失",
            "预测未流失"
        )

        frames.append(temp_df)

    animation_df = pd.concat(frames, ignore_index=True)

    return animation_df
def get_xgb_total_trees(pipe):
    """
    获取 XGBoost 模型中树的总数量。
    对于二分类 binary:logistic，通常 n_estimators=多少，就有多少棵树。
    """
    model = pipe.named_steps["model"]
    booster = model.get_booster()
    tree_dump = booster.get_dump()
    return len(tree_dump)


def get_xgb_tree_text(pipe, tree_index):
    """
    获取指定编号的 XGBoost 树的文本结构。
    tree_index 从 0 开始。
    """
    model = pipe.named_steps["model"]
    booster = model.get_booster()
    tree_dump = booster.get_dump(with_stats=True)

    if tree_index < 0 or tree_index >= len(tree_dump):
        raise ValueError("tree_index 超出树的数量范围。")

    return tree_dump[tree_index]


def get_xgb_tree_dataframe(pipe, tree_index):
    """
    获取指定树的节点表格信息。
    """
    model = pipe.named_steps["model"]
    booster = model.get_booster()

    tree_df = booster.trees_to_dataframe()

    if "Tree" in tree_df.columns:
        tree_df = tree_df[tree_df["Tree"] == tree_index].copy()

    return tree_df


def get_xgb_feature_mapping(pipe):
    """
    将 XGBoost 内部特征名 f0, f1, f2... 映射回真实特征名。
    因为当前 XGBoost 是在预处理后的矩阵上训练的，所以树结构中常显示 f0、f1 这种内部编号。
    """
    preprocessor = pipe.named_steps["preprocessor"]

    try:
        feature_names = get_fitted_transformed_feature_names(preprocessor)
    except Exception:
        feature_names = []

    mapping_df = pd.DataFrame({
        "XGBoost内部特征名": [f"f{i}" for i in range(len(feature_names))],
        "实际特征名": feature_names
    })

    return mapping_df

def get_xgb_tree_dot_source(pipe, tree_index, rankdir="LR"):
    """
    获取指定 XGBoost 树的 DOT 源码。
    完全采用单独测试成功的写法：
    xgb.to_graphviz(model, ...) + dot.source
    """
    import xgboost as xgb

    model = pipe.named_steps["model"]

    dot = xgb.to_graphviz(
        model,
        num_trees=tree_index,
        rankdir=rankdir,
        yes_color="#4CAF50",
        no_color="#F44336"
    )

    return dot.source

def predict_xgb_proba_with_rounds(pipe, X, tree_count):
    """
    使用 XGBoost Pipeline 的前 tree_count 棵树预测流失概率。
    """
    preprocessor = pipe.named_steps["preprocessor"]
    model = pipe.named_steps["model"]

    X_processed = preprocessor.transform(X)

    try:
        proba = model.predict_proba(
            X_processed,
            iteration_range=(0, tree_count)
        )[:, 1]
    except TypeError:
        proba = model.predict_proba(
            X_processed,
            ntree_limit=tree_count
        )[:, 1]

    return proba
def plot_xgb_logloss_curve_with_slider(pipe, X_train, y_train, X_test, y_test, current_round):
    """
    画 XGBoost 从第 1 棵树到 current_round 棵树的 Train/Test LogLoss 曲线。
    """
    train_losses = []
    test_losses = []

    y_train_arr = y_train.values if isinstance(y_train, pd.Series) else np.asarray(y_train)
    y_test_arr = y_test.values if isinstance(y_test, pd.Series) else np.asarray(y_test)

    for r in range(1, current_round + 1):
        train_prob = predict_xgb_proba_with_rounds(
            pipe=pipe,
            X=X_train,
            tree_count=r
        )

        test_prob = predict_xgb_proba_with_rounds(
            pipe=pipe,
            X=X_test,
            tree_count=r
        )

        train_losses.append(log_loss(y_train_arr, train_prob))
        test_losses.append(log_loss(y_test_arr, test_prob))

    fig, ax = plt.subplots(figsize=(6, 4))

    x_axis = np.arange(1, current_round + 1)

    ax.plot(
        x_axis,
        train_losses,
        marker="o",
        linewidth=2,
        label="Train LogLoss"
    )

    ax.plot(
        x_axis,
        test_losses,
        marker="o",
        linewidth=2,
        label="Test LogLoss"
    )

    ax.axvline(
        current_round,
        color="red",
        linestyle="--",
        alpha=0.7,
        label=f"当前第 {current_round} 棵树"
    )

    ax.set_title("前 k 棵树累加后的 LogLoss")
    ax.set_xlabel("已加入的树数量 k")
    ax.set_ylabel("LogLoss")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)

    return fig
def plot_xgb_2d_risk_space_with_slider(pipe, X_test, y_test, current_round, random_state=42):
    """
    使用前 current_round 棵树预测测试集流失概率，
    并将测试集预处理特征降到二维后可视化。
    """
    preprocessor = pipe.named_steps["preprocessor"]

    X_processed = preprocessor.transform(X_test)

    if sparse.issparse(X_processed):
        reducer = TruncatedSVD(n_components=2, random_state=random_state)
        X_2d = reducer.fit_transform(X_processed)
        reducer_name = "TruncatedSVD"
    else:
        reducer = PCA(n_components=2, random_state=random_state)
        X_2d = reducer.fit_transform(np.asarray(X_processed))
        reducer_name = "PCA"

    y_prob = predict_xgb_proba_with_rounds(
        pipe=pipe,
        X=X_test,
        tree_count=current_round
    )

    y_arr = y_test.values if isinstance(y_test, pd.Series) else np.asarray(y_test)

    plot_df = pd.DataFrame({
        "Dim1": X_2d[:, 0],
        "Dim2": X_2d[:, 1],
        "真实标签": y_arr.astype(int),
        "预测流失概率": y_prob
    })

    plot_df["真实类别"] = plot_df["真实标签"].map({
        0: "真实未流失",
        1: "真实流失"
    })

    fig = px.scatter(
        plot_df,
        x="Dim1",
        y="Dim2",
        color="预测流失概率",
        symbol="真实类别",
        range_color=[0, 1],
        color_continuous_scale="RdYlBu_r",
        hover_data=[
            "真实类别",
            "预测流失概率"
        ],
        title=f"前 {current_round} 棵树累加后的二维风险空间（{reducer_name}）"
    )

    fig.update_layout(
        height=460,
        xaxis_title=f"{reducer_name} 第一维",
        yaxis_title=f"{reducer_name} 第二维",
        coloraxis_colorbar_title="预测流失概率"
    )

    return fig


def check_graphviz_environment():
    """
    检查当前环境是否支持 Graphviz。
    """
    info = {
        "python_graphviz_installed": False,
        "dot_executable_available": False,
        "dot_path": None,
        "error": None
    }

    try:
        import graphviz
        info["python_graphviz_installed"] = True
    except Exception as e:
        info["error"] = f"Python graphviz 包未安装：{e}"
        return info

    try:
        import shutil
        dot_path = shutil.which("dot")
        if dot_path is not None:
            info["dot_executable_available"] = True
            info["dot_path"] = dot_path
    except Exception as e:
        info["error"] = f"检测 dot 可执行文件失败：{e}"

    return info

# =========================
# 模型构建函数
# =========================

def build_model(model_name, seed, use_class_weight, y_train=None):
    class_weight = "balanced" if use_class_weight else None

    if model_name == "Logistic Regression":
        model = LogisticRegression(
            max_iter=2000,
            random_state=seed,
            class_weight=class_weight
        )


    elif model_name == "LightGBM":

        if not LIGHTGBM_AVAILABLE:
            raise ImportError("当前环境未安装 lightgbm，请先执行：pip install lightgbm")

        if use_class_weight and y_train is not None:

            neg_count = np.sum(y_train == 0)

            pos_count = np.sum(y_train == 1)

            scale_pos_weight = neg_count / pos_count if pos_count != 0 else 1

        else:

            scale_pos_weight = 1

        model = LGBMClassifier(

            n_estimators=300,

            learning_rate=0.03,

            num_leaves=15,

            max_depth=4,

            subsample=0.9,

            colsample_bytree=0.9,

            reg_alpha=0.1,

            reg_lambda=0.1,

            random_state=seed,

            scale_pos_weight=scale_pos_weight,

            verbose=-1

        )


    elif model_name == "Decision Tree":
        model = DecisionTreeClassifier(
            random_state=seed,
            class_weight=class_weight,
            max_depth=None
        )

    elif model_name == "Random Forest":
        model = RandomForestClassifier(
            n_estimators=300,
            random_state=seed,
            class_weight=class_weight,
            n_jobs=-1
        )

    elif model_name == "XGBoost":
        if not XGBOOST_AVAILABLE:
            raise ImportError("当前环境未安装 xgboost，请先执行：pip install xgboost")

        if use_class_weight and y_train is not None:
            neg_count = np.sum(y_train == 0)
            pos_count = np.sum(y_train == 1)
            scale_pos_weight = neg_count / pos_count if pos_count != 0 else 1
        else:
            scale_pos_weight = 1

        model = XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric=["logloss", "auc"],
            random_state=seed,
            scale_pos_weight=scale_pos_weight,
            n_jobs=-1
        )




    elif model_name == "TabNet":

        if not TABNET_AVAILABLE:
            raise ImportError("当前环境未安装 pytorch-tabnet，请先执行：pip install pytorch-tabnet torch")

        model = TabNetClassifier(
            n_d=16,
            n_a=16,
            n_steps=3,
            gamma=1.2,
            n_independent=2,
            n_shared=2,
            lambda_sparse=1e-4,

            optimizer_fn=torch.optim.AdamW,
            optimizer_params=dict(
                lr=5e-3,
                weight_decay=1e-3
            ),

            scheduler_fn=torch.optim.lr_scheduler.StepLR,
            scheduler_params={
                "step_size": 30,
                "gamma": 0.85
            },

            mask_type="entmax",
            seed=seed,
            verbose=0
        )





    else:
        raise ValueError(f"未知模型：{model_name}")

    return model


# =========================
# 训练单个模型
# =========================

def train_one_model(
    model_name,
    seed,
    X_train,
    X_test,
    y_train,
    y_test,
    preprocessor,
    numeric_features,
    categorical_features,
    text_features,
    use_class_weight
):

    preprocessor = clone(preprocessor)

    base_model = build_model(
        model_name=model_name,
        seed=seed,
        use_class_weight=use_class_weight,
        y_train=y_train
    )


    pipe = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", base_model)
        ]
    )

    # =========================
    # 模型训练
    # =========================
    history = None  # 用于保存训练历史

    # 用于避免数据泄露：TabNet 的阈值选择只使用内部验证集，不使用测试集
    threshold_valid_prob = None
    threshold_valid_y = None

    # TabNet 测试集概率，避免 Pipeline 处理稀疏矩阵时出问题
    y_prob_test_override = None

    if model_name == "TabNet":

        # =========================
        # 防止数据泄露：
        # 不再使用 X_test/y_test 做 valid，而是从 X_train/y_train 中再划分内部验证集
        # =========================
        X_fit, X_valid, y_fit, y_valid = train_test_split(
            X_train,
            y_train,
            test_size=0.2,
            random_state=seed,
            stratify=y_train
        )

        # 预处理器只在 X_fit 上 fit，不能在测试集上 fit
        X_fit_processed = preprocessor.fit_transform(X_fit)
        X_valid_processed = preprocessor.transform(X_valid)
        X_test_processed = preprocessor.transform(X_test)

        # TabNet 严格要求输入是 numpy array，不能是 DataFrame 或稀疏矩阵
        import scipy.sparse

        def to_numpy_array(x):
            if scipy.sparse.issparse(x):
                return x.toarray()
            elif isinstance(x, pd.DataFrame):
                return x.values
            else:
                return np.asarray(x)

        X_fit_processed = to_numpy_array(X_fit_processed)
        X_valid_processed = to_numpy_array(X_valid_processed)
        X_test_processed = to_numpy_array(X_test_processed)

        y_fit_arr = y_fit.values if isinstance(y_fit, pd.Series) else np.asarray(y_fit)
        y_valid_arr = y_valid.values if isinstance(y_valid, pd.Series) else np.asarray(y_valid)

        # 注意：这里的 valid 是内部验证集，不是最终测试集
        base_model.fit(
            X_fit_processed,
            y_fit_arr,
            eval_set=[
                (X_fit_processed, y_fit_arr),
                (X_valid_processed, y_valid_arr)
            ],
            eval_name=["train", "valid"],
            eval_metric=["logloss", "auc"],
            max_epochs=30,#epoch
            patience=40,
            batch_size=128,
            virtual_batch_size=32,
            num_workers=0,
            drop_last=False,
            weights=1 if use_class_weight else 0
        )

        # 组装回 Pipeline，保证后续代码结构兼容
        pipe = Pipeline(steps=[("preprocessor", preprocessor), ("model", base_model)])

        # 用内部验证集来选择阈值，不能用测试集
        threshold_valid_prob = base_model.predict_proba(X_valid_processed)[:, 1]
        threshold_valid_y = y_valid_arr

        # 最终测试集概率只用于最后评估，不参与训练和阈值选择
        y_prob_test_override = base_model.predict_proba(X_test_processed)[:, 1]

        # 将 TabNet History 转成普通 dict，避免缓存和绘图报错
        tabnet_history = base_model.history
        history = {}

        for key in ["train_logloss", "valid_logloss", "train_auc", "valid_auc"]:
            try:
                value = tabnet_history[key]
                if value is not None:
                    history[key] = list(value)
            except Exception:
                pass




    else:

        pipe = Pipeline(

            steps=[

                ("preprocessor", preprocessor),

                ("model", base_model)

            ]

        )

        # =========================

        # XGBoost：单独处理，为了记录每一轮 eval_metric

        # =========================

        if model_name == "XGBoost":

            # 预处理器只在训练集 fit

            X_train_processed = preprocessor.fit_transform(X_train)

            X_test_processed = preprocessor.transform(X_test)

            y_train_arr = y_train.values if isinstance(y_train, pd.Series) else np.asarray(y_train)

            y_test_arr = y_test.values if isinstance(y_test, pd.Series) else np.asarray(y_test)

            base_model.fit(

                X_train_processed,

                y_train_arr,

                eval_set=[

                    (X_train_processed, y_train_arr),

                    (X_test_processed, y_test_arr)

                ],

                verbose=False

            )

            # 把已经 fit 好的 preprocessor 和 model 重新组装回 Pipeline

            pipe = Pipeline(

                steps=[

                    ("preprocessor", preprocessor),

                    ("model", base_model)

                ]

            )

            # 保存 XGBoost 每轮训练历史

            try:

                history = base_model.evals_result()

            except Exception:

                history = None


        else:

            pipe.fit(X_train, y_train)

    # =========================
    # 获取预测概率
    # =========================
    if y_prob_test_override is not None:
        # TabNet：这里已经提前算好了测试集概率
        y_prob = y_prob_test_override
    elif hasattr(pipe.named_steps["model"], "predict_proba"):
        y_prob = pipe.predict_proba(X_test)[:, 1]
    else:
        decision_score = pipe.decision_function(X_test)
        y_prob = (decision_score - decision_score.min()) / (decision_score.max() - decision_score.min())

    # =========================
    # 阈值调整
    # =========================
    if model_name == "TabNet":

        # TabNet 默认 0.5 阈值可能不合适
        # 注意：阈值只能在内部验证集上选择，不能用测试集 y_test
        best_threshold = 0.5
        best_f1 = -1

        if threshold_valid_prob is not None and threshold_valid_y is not None:
            for threshold in np.arange(0.20, 0.91, 0.01):
                temp_pred = (threshold_valid_prob >= threshold).astype(int)
                temp_f1 = f1_score(threshold_valid_y, temp_pred, zero_division=0)

                if temp_f1 > best_f1:
                    best_f1 = temp_f1
                    best_threshold = threshold

        # 最终测试集只用选好的阈值进行评估
        y_pred = (y_prob >= best_threshold).astype(int)
        used_threshold = best_threshold


    else:
        y_pred = (y_prob >= 0.5).astype(int)
        used_threshold = 0.5

    acc = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)

    # 特征重要性
    importance_df = None

    fitted_preprocessor = pipe.named_steps["preprocessor"]
    fitted_model = pipe.named_steps["model"]
    feature_names = get_feature_names(
        fitted_preprocessor,
        numeric_features,
        categorical_features,
        text_features
    )

    if hasattr(fitted_model, "feature_importances_"):
        importances = fitted_model.feature_importances_

        if len(feature_names) == len(importances):
            importance_df = pd.DataFrame({
                "feature": feature_names,
                "importance": importances
            }).sort_values("importance", ascending=False)

    elif hasattr(fitted_model, "coef_"):
        coef = fitted_model.coef_[0]

        if len(feature_names) == len(coef):
            importance_df = pd.DataFrame({
                "feature": feature_names,
                "importance": np.abs(coef),
                "coefficient": coef
            }).sort_values("importance", ascending=False)

    result = {
        "模型": model_name,
        "随机种子": seed,
        "阈值": round(used_threshold, 2),
        "Accuracy": round(acc, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1-score": round(f1, 4),
        "ROC-AUC": round(auc, 4),
        "PR-AUC": round(pr_auc, 4)
    }

    roc_result = {
        "fpr": fpr,
        "tpr": tpr,
        "auc": auc
    }
    risk_space_df = make_2d_risk_space_df(
        pipe=pipe,
        X_test=X_test,
        y_test=y_test,
        y_pred=y_pred,
        y_prob=y_prob,
        random_state=seed
    )
    xgb_animation_df = None

    if model_name == "XGBoost":
        try:
            xgb_animation_train_df = make_xgboost_boosting_animation_df(
                pipe=pipe,
                X_test=X_train,
                y_test=y_train,
                random_state=seed,
                max_points=800,
                step=1
            )

            xgb_animation_test_df = make_xgboost_boosting_animation_df(
                pipe=pipe,
                X_test=X_test,
                y_test=y_test,
                random_state=seed,
                max_points=800,
                step=1
            )

            xgb_animation_train_df["数据来源"] = "训练集"
            xgb_animation_test_df["数据来源"] = "测试集"

            xgb_animation_df = pd.concat(
                [xgb_animation_train_df, xgb_animation_test_df],
                ignore_index=True
            )

        except Exception:
            xgb_animation_df = None


    # return result, roc_result, cm, importance_df, history, risk_space_df
    return result, roc_result, cm, importance_df, history, risk_space_df, pipe, xgb_animation_df

def get_xgb_tree_dot_from_dataframe(pipe, tree_index, rankdir="LR"):
    """
    使用 booster.trees_to_dataframe() 手动生成 DOT 源码。
    不依赖系统 dot.exe，也不依赖 xgb.to_graphviz 的前端兼容性。
    """
    model = pipe.named_steps["model"]
    booster = model.get_booster()

    tree_df = booster.trees_to_dataframe()
    tree_df = tree_df[tree_df["Tree"] == tree_index].copy()

    if tree_df.empty:
        raise ValueError(f"没有找到 tree_index={tree_index} 对应的树。")

    lines = []
    lines.append("digraph G {")
    lines.append(f'    rankdir="{rankdir}";')
    lines.append('    graph [bgcolor="transparent"];')
    lines.append('    node [shape=box, style="rounded,filled", fontname="Microsoft YaHei", fontsize=10];')
    lines.append('    edge [fontname="Microsoft YaHei", fontsize=9];')

    def node_name(node_id):
        return f"node_{int(node_id)}"

    def parse_child_node_id(value):
        """
        trees_to_dataframe 中 Yes/No/Missing 可能是：
        '0-1', '0-2'
        也可能是数字。
        """
        if pd.isna(value):
            return None

        value = str(value)

        if value == "":
            return None

        if "-" in value:
            return int(value.split("-")[-1])

        return int(float(value))

    # 1. 生成节点
    for _, row in tree_df.iterrows():
        node_id = int(row["Node"])
        feature = row.get("Feature", "")

        if str(feature) == "Leaf":
            leaf_value = row.get("Gain", None)

            if pd.notna(leaf_value):
                label = f"leaf = {float(leaf_value):.4f}"
            else:
                label = "leaf"

            fillcolor = "#ffebee"

        else:
            split = row.get("Split", None)
            gain = row.get("Gain", None)
            cover = row.get("Cover", None)

            if pd.notna(split):
                label = f"{feature} < {float(split):.4f}"
            else:
                label = f"{feature}"

            if pd.notna(gain):
                label += f"\\ngain = {float(gain):.4f}"

            if pd.notna(cover):
                label += f"\\ncover = {float(cover):.2f}"

            fillcolor = "#e3f2fd"

        label = str(label).replace('"', '\\"')

        lines.append(
            f'    {node_name(node_id)} [label="{label}", fillcolor="{fillcolor}"];'
        )

    # 2. 生成边
    for _, row in tree_df.iterrows():
        feature = row.get("Feature", "")

        if str(feature) == "Leaf":
            continue

        node_id = int(row["Node"])

        yes_id = parse_child_node_id(row.get("Yes", None))
        no_id = parse_child_node_id(row.get("No", None))
        missing_id = parse_child_node_id(row.get("Missing", None))

        if yes_id is not None:
            yes_label = "yes"
            if missing_id == yes_id:
                yes_label += " / missing"

            lines.append(
                f'    {node_name(node_id)} -> {node_name(yes_id)} '
                f'[label="{yes_label}", color="#2e7d32", fontcolor="#2e7d32"];'
            )

        if no_id is not None:
            no_label = "no"
            if missing_id == no_id:
                no_label += " / missing"

            lines.append(
                f'    {node_name(node_id)} -> {node_name(no_id)} '
                f'[label="{no_label}", color="#c62828", fontcolor="#c62828"];'
            )

    lines.append("}")

    return "\n".join(lines)

# =========================
# 模型选项
# =========================

model_options = {
    "Logistic Regression": {
        "name_cn": "逻辑回归",
        "default_seed": 42,
        "desc": "线性分类模型，适合作为基准模型。"
    },
    "LightGBM": {
    "name_cn": "LightGBM",
    "default_seed": 43,
    "desc": "基于梯度提升的高效集成模型，适合表格数据分类任务。"
},

    "Decision Tree": {
        "name_cn": "决策树",
        "default_seed": 44,
        "desc": "可解释性强，可以展示分类规则。"
    },
    "Random Forest": {
        "name_cn": "随机森林",
        "default_seed": 45,
        "desc": "集成学习模型，适合表格数据。"
    },
    "XGBoost": {
        "name_cn": "XGBoost",
        "default_seed": 46,
        "desc": "梯度提升模型，通常在表格数据上表现较强。"
    },
        "TabNet": {
        "name_cn": "TabNet注意力神经网络",
        "default_seed": 47,
        "desc": "面向表格数据的深度学习模型，引入特征选择与注意力机制，比普通 MLP 更高级。"
    }

}


# =========================
# 数据概览
# =========================

st.subheader("一、数据概览")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("训练集样本数", train_df.shape[0])

with col2:
    st.metric("测试集样本数", test_df.shape[0])

with col3:
    st.metric("训练集字段数", train_df.shape[1])

with col4:
    if "churn" in train_df.columns:
        churn_rate = train_df["churn"].mean()
        st.metric("训练集流失率", f"{churn_rate:.2%}")
    else:
        st.metric("训练集流失率", "未知")


if not XGBOOST_AVAILABLE:
    st.warning("当前环境未检测到 xgboost。如果要使用 XGBoost，请先安装：`pip install xgboost`")
if not LIGHTGBM_AVAILABLE:
    st.warning("当前环境未检测到 lightgbm。如果要使用 LightGBM，请先安装：`pip install lightgbm`")

if not TABNET_AVAILABLE:
    st.warning("当前环境未检测到 pytorch-tabnet。如果要使用 TabNet 神经网络，请先安装：`pip install pytorch-tabnet torch`")

if not TRANSFORMERS_AVAILABLE:
    st.warning("当前环境未检测到 sentence-transformers 或 torch。如果要使用本地 Sentence-BERT 文本特征，请先安装：`pip install sentence-transformers torch safetensors`")

st.divider()


# =========================
# 模型训练配置
# =========================
# 在 col_d, col_e 旁边加上这个开关
# col_d, col_e, col_f = st.columns(3)  # 👇 把原来的 2 列改成 3 列
#
# with col_d:
#     use_scaler = st.checkbox("启用数值特征标准化", value=True)
#
# with col_e:
#     use_class_weight = st.checkbox("处理类别不平衡", value=True)
#
# with col_f:
#     # 👇 新增：特征融合开关
#     use_feedback = st.checkbox("🧩 融合客户反馈特征 (NLP)", value=True)

st.subheader("二、模型选择与训练配置")

with st.form("train_form"):
    selected_models = []
    model_seeds = {}

    cols = st.columns(2)

    for i, (model_key, model_info) in enumerate(model_options.items()):
        with cols[i % 2]:
            st.markdown(f"#### {model_info['name_cn']}")
            st.caption(model_info["desc"])

            default_checked = True
            if model_key == "TabNet":
                default_checked = False

            if model_key == "XGBoost" and not XGBOOST_AVAILABLE:
                default_checked = False
            if model_key == "LightGBM" and not LIGHTGBM_AVAILABLE:
                default_checked = False

            if model_key == "TabNet" and not TABNET_AVAILABLE:
                default_checked = False

            use_model = st.checkbox(
                f"启用 {model_info['name_cn']}",
                value=default_checked,
                key=f"use_{model_key.replace(' ', '_')}"
            )

            seed = st.number_input(
                f"{model_info['name_cn']} 随机种子",
                min_value=0,
                max_value=999999,
                value=model_info["default_seed"],
                step=1,
                key=f"seed_{model_key.replace(' ', '_')}"
            )

            if use_model:
                selected_models.append(model_key)
                model_seeds[model_key] = int(seed)

    st.divider()

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        test_source = st.selectbox(
            "测试集来源",
            ["使用 test.xlsx 作为测试集", "从 train.xlsx 中划分验证集"],
            index=0
        )

    with col_b:
        validation_size = st.slider(
            "验证集比例",
            min_value=0.1,
            max_value=0.5,
            value=0.2,
            step=0.05
        )

    with col_c:
        split_seed = st.number_input(
            "划分验证集随机种子",
            min_value=0,
            max_value=999999,
            value=2024,
            step=1
        )

    col_d, col_e, col_f, col_g = st.columns(4)

    with col_d:
        use_scaler = st.checkbox("启用数值特征标准化", value=True)

    with col_e:
        use_class_weight = st.checkbox("处理类别不平衡", value=True)

    with col_f:
        use_feedback_tfidf = st.checkbox("融合反馈原文 TF-IDF", value=False)

    with col_g:
        use_feedback_bert = st.checkbox("融合反馈原文 BERT", value=False)
    st.info(
        "说明：本项目不直接使用 sentiment_score、complaint_intensity 等结构化反馈字段，"
        "因为真实业务场景中客户通常只提供反馈原文。"
        "模型仅使用 feedback_text 原文，并通过 TF-IDF 或 BERT 自动提取文本特征。"
    )
    st.markdown("#### 客户反馈文本特征设置")

    st.info(
        "本项目仅使用客户反馈原文作为文本输入。"
        "对于 feedback 数据中的 sentiment、complaint_intensity 等结构化字段，"
        "由于它们更像是后期人工标注或规则加工结果，真实预测场景中未必可以直接获得，"
        "因此不会作为模型输入。"
        "若启用文本特征，系统会从 feedback_text 中自动提取 TF-IDF 或 BERT 语义向量特征。"
    )

    st.markdown("#### Sentence-BERT 本地模型设置")

    bert_model_path = st.text_input(
        "本地 Sentence-BERT 模型路径",
        value=DEFAULT_LOCAL_BERT_PATH,
        help="填写本地 all-MiniLM-L6-v2 文件夹路径，里面应包含 modules.json、model.safetensors、tokenizer.json、vocab.txt、1_Pooling/config.json 等文件。"
    )
    bert_output_dim = st.selectbox(
        "BERT 向量降维维度",
        options=[384, 256, 128, 64, 32, 16],
        index=3,
        help="all-MiniLM-L6-v2 原始维度是 384。选择更小的维度会使用 PCA 降维。"
    )

    submitted = st.form_submit_button("🚀 开始训练模型", use_container_width=True)


# =========================
# 执行训练
# =========================

if submitted:
    if len(selected_models) == 0:
        st.error("请至少选择一个模型。")
    else:
        try:
            # 👇 新增：特征融合逻辑开始
            train_df_model = train_df.copy()
            test_df_model = test_df.copy()

            if use_feedback_tfidf or use_feedback_bert:

                feedback_df = load_feedback()

                # 1. 融合原始文本 TF-IDF 特征：feedback_text
                if use_feedback_tfidf:
                    feedback_text_features = process_feedback_text_features(feedback_df)

                    train_df_model = pd.merge(
                        train_df_model,
                        feedback_text_features,
                        on="customer_id",
                        how="left"
                    )

                    test_df_model = pd.merge(
                        test_df_model,
                        feedback_text_features,
                        on="customer_id",
                        how="left"
                    )

                    train_df_model["feedback_text_merged"] = (
                        train_df_model["feedback_text_merged"]
                        .fillna("")
                        .astype(str)
                    )

                    test_df_model["feedback_text_merged"] = (
                        test_df_model["feedback_text_merged"]
                        .fillna("")
                        .astype(str)
                    )

                # 2. 融合本地 Sentence-BERT 语义向量特征：feedback_text -> dense embedding
                if use_feedback_bert:
                    if not TRANSFORMERS_AVAILABLE:
                        raise ImportError(
                            "当前环境未安装 sentence-transformers 或 torch，请先执行：pip install sentence-transformers torch safetensors"
                        )

                    if not os.path.isdir(bert_model_path):
                        raise FileNotFoundError(f"本地 Sentence-BERT 路径不存在：{bert_model_path}")

                    with st.spinner("正在使用本地 Sentence-BERT 提取反馈文本语义向量，首次运行可能较慢..."):
                        feedback_bert_features = process_feedback_bert_features(
                            feedback_df=feedback_df,
                            local_model_path=bert_model_path,
                            batch_size=16,
                            bert_output_dim=bert_output_dim
                        )

                    train_df_model = pd.merge(
                        train_df_model,
                        feedback_bert_features,
                        on="customer_id",
                        how="left"
                    )

                    test_df_model = pd.merge(
                        test_df_model,
                        feedback_bert_features,
                        on="customer_id",
                        how="left"
                    )

                # 数值型缺失填 0
                train_df_model.fillna(0.0, inplace=True)
                test_df_model.fillna(0.0, inplace=True)

                st.toast("✅ 已成功融合客户反馈文本特征！", icon="🧩")

            # 👆 新增：特征融合逻辑结束

            # 👇 修改：把原来的 train_df 换成 train_df_model
            X_train, X_test, y_train, y_test, preprocessor, numeric_features, categorical_features, text_features = prepare_data(
                train_df=train_df_model,
                test_df=test_df_model,
                test_source=test_source,
                test_size=validation_size,
                random_seed=int(split_seed),
                use_scaler=use_scaler,
                use_text_tfidf=use_feedback_tfidf
            )

            train_config = {
                "selected_models": selected_models,
                "model_seeds": model_seeds,
                "test_source": test_source,
                "validation_size": validation_size,
                "split_seed": int(split_seed),
                "use_scaler": use_scaler,
                "use_class_weight": use_class_weight,
                "use_feedback_tfidf": use_feedback_tfidf,
                "use_feedback_bert": use_feedback_bert,
                "bert_model_path": bert_model_path,
                "bert_output_dim": bert_output_dim
            }

            st.session_state.last_train_config = train_config

            all_results = []
            roc_data = {}
            confusion_data = {}
            importance_data = {}
            risk_space_data = {}
            shap_pipes = {}

            progress = st.progress(0)
            status = st.empty()
            training_histories = {}
            xgb_animation_data = {}
            xgb_pipes = {}

            for idx, model_name in enumerate(selected_models):
                status.write(f"正在训练：{model_options[model_name]['name_cn']} ...")

                # 👇 注意这里多加了一个 history
                result, roc_result, cm, importance_df, history, risk_space_df, fitted_pipe, xgb_animation_df = train_one_model(
                    model_name=model_name,
                    seed=model_seeds[model_name],
                    X_train=X_train,
                    X_test=X_test,
                    y_train=y_train,
                    y_test=y_test,
                    preprocessor=preprocessor,
                    numeric_features=numeric_features,
                    categorical_features=categorical_features,
                    text_features=text_features,
                    use_class_weight=use_class_weight
                )

                result["模型"] = model_options[model_name]["name_cn"]
                result["算法名称"] = model_name

                all_results.append(result)
                roc_data[model_options[model_name]["name_cn"]] = roc_result
                confusion_data[model_options[model_name]["name_cn"]] = cm
                risk_space_data[model_options[model_name]["name_cn"]] = risk_space_df

                if model_name in ["LightGBM", "XGBoost", "Random Forest", "Decision Tree"]:
                    shap_pipes[model_options[model_name]["name_cn"]] = fitted_pipe

                if importance_df is not None:
                    importance_data[model_options[model_name]["name_cn"]] = importance_df

                # 👇 新增：保存当前模型的训练历史
                if history is not None:
                    training_histories[model_options[model_name]["name_cn"]] = history
                if xgb_animation_df is not None:
                    xgb_animation_data[model_options[model_name]["name_cn"]] = xgb_animation_df
                if model_name == "XGBoost":
                    xgb_pipes[model_options[model_name]["name_cn"]] = fitted_pipe

                progress.progress((idx + 1) / len(selected_models))

            result_df = pd.DataFrame(all_results)

            st.session_state.model_results = result_df
            st.session_state.roc_data = roc_data
            st.session_state.confusion_data = confusion_data
            st.session_state.importance_data = importance_data
            st.session_state.training_histories = training_histories
            st.session_state.risk_space_data = risk_space_data
            st.session_state.xgb_animation_data = xgb_animation_data
            st.session_state.xgb_pipes = xgb_pipes

            st.session_state.xgb_X_train = X_train.copy()
            st.session_state.xgb_X_test = X_test.copy()
            st.session_state.xgb_y_train = y_train.copy() if hasattr(y_train, "copy") else np.asarray(y_train)
            st.session_state.xgb_y_test = y_test.copy() if hasattr(y_test, "copy") else np.asarray(y_test)

            st.session_state.shap_pipes = shap_pipes
            st.session_state.shap_X_test = X_test.copy()
            st.session_state.shap_y_test = y_test.copy() if hasattr(y_test, "copy") else np.asarray(y_test)

            #
            # 保存训练结果到本地缓存，避免刷新网页后丢失
            # 保存训练结果到本地缓存，避免刷新网页后丢失
            cached_results = {
                "model_results": st.session_state.model_results,
                "roc_data": st.session_state.roc_data,
                "confusion_data": st.session_state.confusion_data,
                "importance_data": st.session_state.importance_data,
                "training_histories": st.session_state.training_histories,
                "risk_space_data": st.session_state.risk_space_data,
                "shap_pipes": st.session_state.shap_pipes,
                "shap_X_test": st.session_state.shap_X_test,
                "shap_y_test": st.session_state.shap_y_test,
                "last_train_config": st.session_state.last_train_config,
                "xgb_animation_data": st.session_state.xgb_animation_data,
                "xgb_pipes": st.session_state.xgb_pipes,

                "xgb_X_train": st.session_state.xgb_X_train,
                "xgb_X_test": st.session_state.xgb_X_test,
                "xgb_y_train": st.session_state.xgb_y_train,
                "xgb_y_test": st.session_state.xgb_y_test
            }

            with open(RESULT_CACHE_FILE, "wb") as f:
                pickle.dump(cached_results, f)

            status.write("✅ 模型训练完成！")
            st.success("模型训练完成，结果已保存。刷新页面不会自动重新训练。")

        except Exception as e:
            st.error("模型训练失败。")
            st.exception(e)


st.divider()


# =========================
# 结果展示
# =========================

st.subheader("三、模型效果对比")

if st.session_state.model_results is None:
    st.warning("暂无训练结果，请先选择模型并点击“开始训练模型”。")
else:
    result_df = st.session_state.model_results.copy()

    show_cols = [
        "模型",
        "算法名称",
        "随机种子",
        "阈值",
        "Accuracy",
        "Precision",
        "Recall",
        "F1-score",
        "ROC-AUC",
        "PR-AUC"
    ]

    show_cols = [col for col in show_cols if col in result_df.columns]

    st.dataframe(
        result_df[show_cols],
        use_container_width=True,
        hide_index=True
    )

    best_auc = result_df.sort_values("ROC-AUC", ascending=False).iloc[0]
    best_f1 = result_df.sort_values("F1-score", ascending=False).iloc[0]
    best_recall = result_df.sort_values("Recall", ascending=False).iloc[0]

    if "PR-AUC" in result_df.columns:
        best_pr_auc = result_df.sort_values("PR-AUC", ascending=False).iloc[0]
    else:
        best_pr_auc = None

    col1, col2, col3, col4 = st.columns(4)
    with col4:
        if best_pr_auc is not None:
            st.metric("最佳 PR-AUC 模型", best_pr_auc["模型"], best_pr_auc["PR-AUC"])
        else:
            st.metric("最佳 PR-AUC 模型", "暂无", "-")

    with col1:
        st.metric("最佳 ROC-AUC 模型", best_auc["模型"], best_auc["ROC-AUC"])

    with col2:
        st.metric("最佳 F1-score 模型", best_f1["模型"], best_f1["F1-score"])

    with col3:
        st.metric("最佳 Recall 模型", best_recall["模型"], best_recall["Recall"])

    st.download_button(
        label="📥 下载模型评估结果 CSV",
        data=result_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="model_comparison_results.csv",
        mime="text/csv"
    )


st.divider()


# =========================
# 可视化
# =========================

st.subheader("四、模型可视化分析")

viz_tab = st.radio(
    "选择可视化模块",
    [
        "📊 指标对比",
        "📈 ROC曲线",
        "🔢 混淆矩阵",
        "⭐ 特征重要性",
        "☁️ 反馈文本词云",
        "📉 训练过程 (Loss曲线)",
        "🧭 三维风险空间",
        "🧬 SHAP解释",
        "🎬 XGBoost动画"
    ],
    index=0,
    horizontal=True,
    key="selected_visual_tab"
)








# 指标对比
if viz_tab == "📊 指标对比":
    if st.session_state.model_results is None:
        st.info("训练完成后将在这里展示各模型指标对比。")
    else:
        metric_cols = [
            "Accuracy",
            "Precision",
            "Recall",
            "F1-score",
            "ROC-AUC",
            "PR-AUC"
        ]

        metric_cols = [
            col for col in metric_cols
            if col in st.session_state.model_results.columns
        ]

        metric_result_df = st.session_state.model_results.copy()
        metric_result_df["模型"] = metric_result_df["模型"].replace({
            "TabNet注意力神经网络": "TabNet"
        })

        metric_df = metric_result_df.set_index("模型")[metric_cols]

        st.bar_chart(metric_df)

        # =========================
        # 多模型评价指标雷达图：优化版，小尺寸 + 外圈彩色指标环
        # =========================
        st.markdown("#### 多模型评价指标雷达图")

        radar_df = metric_df.copy()

        metrics = radar_df.columns.tolist()
        models = radar_df.index.tolist()

        num_metrics = len(metrics)

        # 每个指标对应的角度
        angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False)
        angles_closed = np.concatenate([angles, [angles[0]]])

        # 模型颜色
        model_colors = [
            "#0072B2",  # 蓝色：逻辑回归
            "#E69F00",  # 橙色：决策树
            "#009E73",  # 绿色：随机森林
            "#D55E00",  # 红橙色：XGBoost
            "#CC79A7",  # 紫红色：LightGBM
            "#56B4E9",  # 天蓝色
            "#F0E442",  # 黄色
            "#000000"  # 黑色
        ]

        # 外圈指标颜色
        metric_ring_colors = {
            "Accuracy": "#b7dce8",
            "Precision": "#c7dcef",
            "Recall": "#f4c4c4",
            "F1-score": "#f7cca3",
            "F1_Score": "#f7cca3",
            "F1 Score": "#f7cca3",
            "ROC-AUC": "#d9ead3",
            "AUC": "#d9ead3",
            "PR-AUC": "#f9e79f",
            "Kappa": "#f9e79f"
        }

        # 图调小
        fig_radar, ax = plt.subplots(
            figsize=(6.6, 6.6),
            subplot_kw={"projection": "polar"}
        )

        # 第一个指标放在正上方，顺时针排列
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # =========================
        # 外圈彩色指标环
        # =========================
        ring_bottom = 1.04
        ring_height = 0.11
        ring_width = 2 * np.pi / num_metrics

        for i, metric in enumerate(metrics):
            ax.bar(
                angles[i],
                ring_height,
                width=ring_width * 0.96,
                bottom=ring_bottom,
                color=metric_ring_colors.get(metric, "#dddddd"),
                edgecolor="white",
                linewidth=1.5,
                alpha=0.9,
                align="center",
                zorder=0
            )

        # 外圈边框
        circle_angles = np.linspace(0, 2 * np.pi, 500)

        ax.plot(
            circle_angles,
            np.full_like(circle_angles, ring_bottom),
            color="#333333",
            linewidth=1.0,
            zorder=1
        )

        ax.plot(
            circle_angles,
            np.full_like(circle_angles, ring_bottom + ring_height),
            color="#333333",
            linewidth=1.2,
            zorder=1
        )

        # =========================
        # 绘制雷达折线
        # =========================
        for idx, model in enumerate(models):
            values = radar_df.loc[model, metrics].astype(float).values
            values_closed = np.concatenate([values, [values[0]]])

            color = model_colors[idx % len(model_colors)]

            ax.plot(
                angles_closed,
                values_closed,
                color=color,
                linewidth=1.0,
                marker="o",
                markersize=4.5,
                label=model,
                zorder=4
            )

            ax.fill(
                angles_closed,
                values_closed,
                color=color,
                alpha=0.045,
                zorder=2
            )

        # =========================
        # 坐标轴设置
        # =========================
        ax.set_ylim(0, 1.17)

        ax.set_yticks([0.25, 0.50, 0.75, 1.00])
        ax.set_yticklabels(
            ["0.25", "0.50", "0.75", "1.00"],
            fontsize=8,
            color="#333333"
        )

        ax.yaxis.grid(True, linestyle="--", linewidth=0.9, alpha=0.35)
        ax.xaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.25)

        # 不显示默认角度标签
        ax.set_xticks(angles)
        ax.set_xticklabels([])

        # =========================
        # 外圈指标名称：修正旋转角度，不再乱竖着
        # =========================
        metric_display_names = {
            "Accuracy": "Accuracy",
            "Precision": "Precision",
            "Recall": "Recall",
            "F1-score": "F1-score",
            "F1_Score": "F1-score",
            "F1 Score": "F1-score",
            "ROC-AUC": "ROC-AUC",
            "AUC": "AUC",
            "PR-AUC": "PR-AUC",
            "Kappa": "Kappa"
        }

        for i, metric in enumerate(metrics):
            angle = angles[i]

            # 因为设置了 theta_offset=np.pi/2 和 theta_direction=-1，
            # 所以屏幕上的真实角度要这样算
            display_angle_deg = 90 - np.degrees(angle)

            # 文字沿圆环切线方向
            rotation = display_angle_deg - 90

            # 左半边翻转，避免倒着看
            if display_angle_deg < -90 or display_angle_deg > 90:
                rotation += 180
            # 单独把 F1-score 倒过来
            if metric in ["F1-score", "F1_Score", "F1 Score"]:
                rotation += 180

            ax.text(
                angle,
                ring_bottom + ring_height / 2,
                metric_display_names.get(metric, metric),
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                rotation=rotation,
                rotation_mode="anchor",
                color="black",
                zorder=5
            )

        # =========================
        # 标题和图例
        # =========================
        ax.set_title(
            "多模型评价指标雷达图",
            fontsize=14,
            fontweight="bold",
            pad=18
        )

        ax.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, -0.16),
            ncol=3,
            frameon=False,
            fontsize=9,
            handlelength=2.2,
            columnspacing=1.2
        )

        # 如果想让图居中且不要太宽，用 columns 包一下
        col_left, col_mid, col_right = st.columns([1, 2.4, 1])

        with col_mid:
            st.pyplot(fig_radar, use_container_width=False)

        plt.close(fig_radar)






        # =========================
        # 环形极坐标指标对比图：带数值标签 + 正常指标文字
        # =========================
        st.markdown("#### 环形指标对比图")

        radar_df = metric_df.copy()

        metrics = radar_df.columns.tolist()
        models = radar_df.index.tolist()

        values = []
        bar_labels = []
        bar_colors = []
        bar_metrics = []

        metric_colors = {
            "Accuracy": "#66c2a5",
            "Precision": "#fc8d62",
            "Recall": "#e78ac3",
            "F1-score": "#a6d854",
            "ROC-AUC": "#b3b3b3",
            "PR-AUC": "#ffd92f"
        }

        group_gap = 1
        angles = []
        current_pos = 0

        group_centers = {}
        group_bounds = {}

        for metric in metrics:
            start_pos = current_pos

            for model in models:
                values.append(float(radar_df.loc[model, metric]))
                bar_labels.append(model)
                bar_colors.append(metric_colors.get(metric, "#8da0cb"))
                bar_metrics.append(metric)
                angles.append(current_pos)
                current_pos += 1

            end_pos = current_pos - 1
            group_centers[metric] = (start_pos + end_pos) / 2
            group_bounds[metric] = (start_pos, end_pos)

            current_pos += group_gap

        angles = np.array(angles)
        values = np.array(values)

        total_slots = current_pos
        theta = 2 * np.pi * angles / total_slots
        width = 2 * np.pi / total_slots * 0.82

        fig_polar, ax = plt.subplots(
            figsize=(10, 10),
            subplot_kw={"projection": "polar"}
        )

        bars = ax.bar(
            theta,
            values,
            width=width,
            bottom=0.15,
            color=bar_colors,
            alpha=0.82,
            edgecolor="white",
            linewidth=1.5
        )

        # 半径范围，调大一点，给数值、模型名和外圈指标名留空间
        ax.set_ylim(0, 1.55)

        # 设置径向刻度
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels([" ", " ", " ", " ", " "], fontsize=0)
        ax.yaxis.grid(True, linestyle="--", alpha=0.45)
        ax.xaxis.grid(False)

        # =========================
        # 每个柱子顶端显示数值
        # =========================
        for t, v in zip(theta, values):
            angle_deg = np.degrees(t) % 360

            rotation = angle_deg
            if 90 < angle_deg < 270:
                rotation = angle_deg + 180


            ax.text(
                t,
                0.15 + v + 0.035,
                f"{v:.2f}",
                ha="center",
                va="center",
                fontsize=7,
                color="#333333",
                rotation=rotation,
                rotation_mode="anchor"
            )

        # =========================
        # 设置每个柱子外侧模型名：环绕文字
        # =========================
        ax.set_xticks([])
        ax.set_xticklabels([])

        reverse_model_metrics = ["Precision", "F1-score"]

        for t, model, metric in zip(theta, bar_labels, bar_metrics):
            angle_deg = np.degrees(t) % 360

            rotation = angle_deg + 90

            if 90 < angle_deg < 270:
                rotation -= 180

            # 指定这些指标组下面的模型名再反过来
            if metric in reverse_model_metrics:
                rotation += 180
            if metric in ["Precision", "Accuracy"] and model == "XGBoost":
                rotation += 180
            if metric in [ "Accuracy"] and model != "XGBoost":
                rotation += 180
            if metric == "Precision" and model == "TabNet":
                rotation += 180

            ax.text(
                t,
                1.27,
                model,
                ha="center",
                va="center",
                fontsize=7,
                rotation=rotation,
                rotation_mode="anchor",
                color="#333333"
            )

        # =========================
        # 添加每个指标名称：完整文字，不拆成字母
        # =========================
        metric_display_names = {
            "Accuracy": "Accuracy",
            "Precision": "Precision",
            "Recall": "Recall",
            "F1-score": "F1-score",
            "ROC-AUC": "ROC-AUC",
            "PR-AUC": "PR-AUC"
        }

        for metric, center in group_centers.items():
            center_theta = 2 * np.pi * center / total_slots
            angle_deg = np.degrees(center_theta) % 360

            # 让文字沿圆环切线方向摆放
            rotation = angle_deg - 90

            # 左半边翻转，避免倒着看
            if 90 < angle_deg < 270:
                rotation += 180
            if metric == "Recall":
                rotation += 180
            if metric == "PR-AUC":
                rotation += 180


            ax.text(
                center_theta,
                1.48,
                metric_display_names.get(metric, metric),
                ha="center",
                va="center",
                fontsize=15,
                fontweight="bold",
                rotation=rotation,
                rotation_mode="anchor",
                color="black",
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.75,
                    pad=1.8
                )
            )

        # =========================
        # 给每个指标组外圈加一段黑色弧线
        # =========================
        for metric, (start_pos, end_pos) in group_bounds.items():
            start_theta = 2 * np.pi * (start_pos - 0.45) / total_slots
            end_theta = 2 * np.pi * (end_pos + 0.45) / total_slots

            arc_thetas = np.linspace(start_theta, end_theta, 80)
            arc_radius = np.full_like(arc_thetas, 1.42)

            ax.plot(
                arc_thetas,
                arc_radius,
                color="black",
                linewidth=1.2,
                alpha=0.85
            )

            # 弧线两端的小短线
            for end_t in [start_theta, end_theta]:
                ax.plot(
                    [end_t, end_t],
                    [1.39, 1.45],
                    color="black",
                    linewidth=1.2,
                    alpha=0.85
                )

        # =========================
        # 中间挖空效果
        # =========================
        inner_circle = plt.Circle(
            (0, 0),
            0.14,
            transform=ax.transData._b,
            color="white",
            zorder=10
        )
        ax.add_artist(inner_circle)

        ax.set_title(
            "多模型多指标环形极坐标柱状对比图",
            fontsize=18,
            fontweight="bold",
            pad=35
        )

        st.pyplot(fig_polar)
        plt.close(fig_polar)

        st.markdown("#### 指标说明")
        st.markdown("""
        - **Accuracy**：整体预测正确率  
        - **Precision**：预测为流失的客户中，真实流失的比例  
        - **Recall**：真实流失客户中，被模型识别出来的比例  
        - **F1-score**：Precision 和 Recall 的综合指标  
        - **ROC-AUC**：模型区分流失与未流失客户的整体能力  
        - **PR-AUC**：Precision-Recall 曲线下面积，更适合观察类别不平衡场景下对流失客户的识别能力  
        """)

# ROC曲线
elif viz_tab == "📈 ROC曲线":
    if st.session_state.roc_data is None:
        st.info("训练完成后将在这里展示 ROC 曲线。")
    else:
        fig, ax = plt.subplots(figsize=(8, 6))

        for model_name, data in st.session_state.roc_data.items():
            ax.plot(
                data["fpr"],
                data["tpr"],
                linewidth=1.2,
                label=f"{model_name} AUC={data['auc']:.4f}"
            )

        ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("ROC Curve")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)


# 混淆矩阵
elif viz_tab == "🔢 混淆矩阵":
    if st.session_state.confusion_data is None:
        st.info("训练完成后将在这里展示混淆矩阵。")
    else:
        st.markdown("#### 所有模型混淆矩阵对比")

        model_names = list(st.session_state.confusion_data.keys())

        # 每行显示 3 个混淆矩阵
        n_cols = 3

        for i in range(0, len(model_names), n_cols):
            cols = st.columns(n_cols)

            for j, model_name in enumerate(model_names[i:i + n_cols]):
                cm = st.session_state.confusion_data[model_name]

                with cols[j]:
                    fig, ax = plt.subplots(figsize=(4, 3.5))

                    disp = ConfusionMatrixDisplay(
                        confusion_matrix=cm,
                        display_labels=["未流失", "流失"]
                    )

                    disp.plot(
                        cmap="Blues",
                        ax=ax,
                        values_format="d",
                        colorbar=False
                    )

                    ax.set_title(f"{model_name}", fontsize=11)
                    ax.set_xlabel("预测标签")
                    ax.set_ylabel("真实标签")

                    st.pyplot(fig)
                    plt.close(fig)

                    tn, fp, fn, tp = cm.ravel()

                    st.markdown(
                        f"""
                        <div style="color: #8a8f98; font-size: 14px; margin-left: 105px;">
                            TN={int(tn)} | FP={int(fp)} | FN={int(fn)} | TP={int(tp)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.markdown("#### 混淆矩阵数值汇总")

        cm_summary = []

        for model_name, cm in st.session_state.confusion_data.items():
            tn, fp, fn, tp = cm.ravel()

            cm_summary.append({
                "模型": model_name,
                "TN 真负例": int(tn),
                "FP 假正例": int(fp),
                "FN 假负例": int(fn),
                "TP 真正例": int(tp)
            })

        cm_summary_df = pd.DataFrame(cm_summary)

        st.dataframe(
            cm_summary_df,
            use_container_width=True,
            hide_index=True
        )


# 特征重要性
# 特征重要性
# 特征重要性
elif viz_tab == "⭐ 特征重要性":
    if st.session_state.importance_data is None or len(st.session_state.importance_data) == 0:
        st.info("当前暂无可展示的特征重要性。决策树、随机森林、XGBoost、逻辑回归通常可以展示。")
    else:
        st.markdown("#### 支持特征重要性的模型对比")

        st.caption(
            "说明：当前仅展示支持特征重要性提取的模型。"
            "树模型展示 feature_importances_；逻辑回归展示系数绝对值。"
            "KNN 和 MLP 当前不直接提供内置特征重要性。"
        )

        # 每个模型展示前 20 个重要特征
        top_n = 50

        for model_name, importance_df in st.session_state.importance_data.items():

            plot_df = importance_df.head(top_n).copy()

            # 为了让最重要的特征显示在最上面，需要倒序
            plot_df = plot_df.sort_values("importance", ascending=True)

            # 控制每张图的高度，数值越小，上下间距越紧凑
            fig_height = max(3.2, 0.22 * len(plot_df))

            fig, ax = plt.subplots(figsize=(11, fig_height))

            ax.barh(
                plot_df["feature"],
                plot_df["importance"],
                color="#1f77b4"
            )

            # 在每个柱子右侧标注特征重要性数值
            max_importance = plot_df["importance"].max()

            for y, value in enumerate(plot_df["importance"]):
                ax.text(
                    value + max_importance * 0.01,
                    y,
                    f"{value:.4f}",
                    va="center",
                    fontsize=8,
                    color="#333333"
                )

            # 给右侧留出空间，防止数值被截断
            ax.set_xlim(0, max_importance * 1.15)

            ax.set_title(f"{model_name} - 特征重要性 Top {top_n}", fontsize=12, pad=6)
            ax.set_xlabel("Importance", fontsize=10)
            ax.set_ylabel("")

            # 显示完整特征名，不旋转
            ax.tick_params(axis="y", labelsize=9)
            ax.tick_params(axis="x", labelsize=9)

            # 添加浅色网格线
            ax.grid(axis="x", linestyle="--", alpha=0.3)

            # 去掉多余边框，让图更清爽
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            # 给左边留更多空间，防止长特征名被截断
            plt.subplots_adjust(
                left=0.35,
                right=0.98,
                top=0.88,
                bottom=0.15
            )

            st.pyplot(fig)
            plt.close(fig)

elif viz_tab == "☁️ 反馈文本词云":

    st.markdown("#### 客户反馈文本词云与 TF-IDF 关键词分析")

    st.caption(
        "该模块基于 customer_feedback.xlsx 中的 feedback_text 原文进行文本可视化。"
        "词云和关键词柱状图使用 TF-IDF 权重生成，用于观察流失客户与未流失客户反馈内容的差异。"
    )

    if not WORDCLOUD_AVAILABLE:
        st.warning("当前环境未安装 wordcloud，无法绘制词云。请先执行：pip install wordcloud")

    try:
        feedback_text_df = build_feedback_text_analysis_df(
            train_df=train_df,
            test_df=test_df
        )

        if feedback_text_df.empty:
            st.info("暂无反馈文本数据。")
        else:
            col_text_a, col_text_b, col_text_c = st.columns(3)

            with col_text_a:
                text_group = st.selectbox(
                    "选择文本范围",
                    ["全部客户", "流失客户", "未流失客户"],
                    index=0
                )

            with col_text_b:
                top_n_words = st.slider(
                    "显示 Top N 关键词",
                    min_value=10,
                    max_value=80,
                    value=40,
                    step=5
                )

            with col_text_c:
                max_features_words = st.slider(
                    "TF-IDF 最大候选词数",
                    min_value=50,
                    max_value=1000,
                    value=300,
                    step=50
                )

            if text_group == "流失客户":
                selected_text_df = feedback_text_df[feedback_text_df["churn"] == 1].copy()
                group_title = "流失客户"
            elif text_group == "未流失客户":
                selected_text_df = feedback_text_df[feedback_text_df["churn"] == 0].copy()
                group_title = "未流失客户"
            else:
                selected_text_df = feedback_text_df.copy()
                group_title = "全部客户"

            selected_text_df = selected_text_df[
                selected_text_df["feedback_text"].fillna("").astype(str).str.strip() != ""
            ]

            st.metric(
                f"{group_title}反馈文本条数",
                len(selected_text_df)
            )

            if len(selected_text_df) == 0:
                st.info(f"{group_title}暂无可用于分析的反馈文本。")
            else:
                word_df = get_tfidf_top_words(
                    texts=selected_text_df["feedback_text"],
                    max_features=max_features_words,
                    top_n=top_n_words,
                    ngram_range=(2, 2)
                )

                if word_df.empty:
                    st.info("当前文本无法提取有效关键词。")
                else:
                    # =========================
                    # 第一行：当前选择范围的词云 + TF-IDF 柱状图
                    # =========================
                    col_wc, col_bar = st.columns([1.05, 1.15])

                    with col_wc:
                        st.markdown(f"##### {group_title}反馈词云")

                        if WORDCLOUD_AVAILABLE:
                            fig_wc = plot_wordcloud_from_word_df(
                                word_df=word_df,
                                title=f"{group_title}反馈文本词云"
                            )

                            st.pyplot(fig_wc, use_container_width=True)
                            plt.close(fig_wc)
                        else:
                            st.info("安装 wordcloud 后可显示词云。")

                    with col_bar:
                        st.markdown(f"##### {group_title} TF-IDF Top 关键词")

                        plot_word_df = word_df.sort_values("tfidf_weight", ascending=True)

                        fig_word_bar = px.bar(
                            plot_word_df,
                            x="tfidf_weight",
                            y="word",
                            orientation="h",
                            title=f"{group_title}反馈文本 TF-IDF Top {top_n_words}",
                            labels={
                                "tfidf_weight": "平均 TF-IDF 权重",
                                "word": "关键词"
                            },
                            color="tfidf_weight",
                            color_continuous_scale="RdYlBu_r"
                        )

                        fig_word_bar.update_layout(
                            height=max(420, top_n_words * 15),
                            yaxis=dict(title=""),
                            coloraxis_showscale=False,
                            margin=dict(l=80, r=20, t=60, b=40)
                        )

                        st.plotly_chart(fig_word_bar, use_container_width=True)

                    # =========================
                    # 第二行：流失客户 vs 未流失客户词云对比
                    # 注意：这里一定要放在 col_wc / col_bar 外面
                    # =========================
                    st.divider()

                    st.markdown("#### 流失客户与未流失客户反馈词云对比")

                    churn_text_df_wc = feedback_text_df[
                        feedback_text_df["churn"] == 1
                        ].copy()

                    non_churn_text_df_wc = feedback_text_df[
                        feedback_text_df["churn"] == 0
                        ].copy()

                    churn_word_df_wc = get_tfidf_top_words(
                        texts=churn_text_df_wc["feedback_text"],
                        max_features=max_features_words,
                        top_n=top_n_words,
                        ngram_range=(2, 2)
                    )

                    non_churn_word_df_wc = get_tfidf_top_words(
                        texts=non_churn_text_df_wc["feedback_text"],
                        max_features=max_features_words,
                        top_n=top_n_words,
                        ngram_range=(2, 2)
                    )

                    col_wc_churn, col_wc_non_churn = st.columns(2)

                    with col_wc_churn:
                        st.markdown("##### 流失客户反馈词云")

                        if WORDCLOUD_AVAILABLE and len(churn_word_df_wc) > 0:
                            fig_churn_wc = plot_wordcloud_from_word_df(
                                word_df=churn_word_df_wc,
                                title="流失客户反馈词云"
                            )

                            st.pyplot(fig_churn_wc, use_container_width=True)
                            plt.close(fig_churn_wc)
                        else:
                            st.info("暂无流失客户反馈文本，或未安装 wordcloud。")

                    with col_wc_non_churn:
                        st.markdown("##### 未流失客户反馈词云")

                        if WORDCLOUD_AVAILABLE and len(non_churn_word_df_wc) > 0:
                            fig_non_churn_wc = plot_wordcloud_from_word_df(
                                word_df=non_churn_word_df_wc,
                                title="未流失客户反馈词云"
                            )

                            st.pyplot(fig_non_churn_wc, use_container_width=True)
                            plt.close(fig_non_churn_wc)
                        else:
                            st.info("暂无未流失客户反馈文本，或未安装 wordcloud。")

                    with st.expander("查看关键词表格"):
                        st.dataframe(
                            word_df,
                            use_container_width=True,
                            hide_index=True
                        )

                    with st.expander("查看原始反馈文本样例"):
                        st.dataframe(
                            selected_text_df[
                                ["customer_id", "churn_label", "feedback_text"]
                            ].head(100),
                            use_container_width=True,
                            hide_index=True
                        )

            st.divider()

            st.markdown("#### 流失客户 vs 未流失客户关键词对比")

            churn_text_df = feedback_text_df[feedback_text_df["churn"] == 1].copy()
            non_churn_text_df = feedback_text_df[feedback_text_df["churn"] == 0].copy()

            churn_words = get_tfidf_top_words(
                texts=churn_text_df["feedback_text"],
                max_features=max_features_words,
                top_n=25,
                ngram_range=(2, 2)
            )

            non_churn_words = get_tfidf_top_words(
                texts=non_churn_text_df["feedback_text"],
                max_features=max_features_words,
                top_n=25,
                ngram_range=(2, 2)
            )

            compare_col1, compare_col2 = st.columns(2)

            with compare_col1:
                st.markdown("##### 流失客户 Top 关键词")
                st.dataframe(
                    churn_words,
                    use_container_width=True,
                    hide_index=True
                )

            with compare_col2:
                st.markdown("##### 未流失客户 Top 关键词")
                st.dataframe(
                    non_churn_words,
                    use_container_width=True,
                    hide_index=True
                )

            st.markdown("""
            **解读方式：**

            - 词越大，说明该词在当前客户群体反馈中 TF-IDF 权重越高；
            - 可以对比“流失客户”和“未流失客户”的高频关键词差异；
            - 如果流失客户词云中出现较多与价格、服务、故障、取消、投诉相关的词，说明这些可能是流失风险的重要文本信号；
            - 该图可以作为 TF-IDF / BERT 文本特征进入模型前的探索性解释。
            """)

    except Exception as e:
        st.error("反馈文本词云分析失败。")
        st.exception(e)

# st.divider()
# 训练过程 (Loss曲线)
# 训练过程 (Loss曲线)
# 训练过程 (Loss曲线)
elif viz_tab == "📉 训练过程 (Loss曲线)":
    histories = st.session_state.get("training_histories")

    if histories is None or len(histories) == 0:
        st.info("当前暂无训练曲线数据。请勾选并训练【TabNet注意力神经网络】以查看。")
    else:
        st.markdown("#### 模型训练过程曲线")

        st.caption(
            "💡 **如何看图：** 如果 Train Loss 一直降，但 Valid Loss 降到一半反弹上升，说明**过拟合**了；如果两者都很高降不下去，说明**欠拟合**（可能是学习率太大或模型太简单）。"
        )

        for model_name, raw_history in histories.items():

            # =========================
            # 关键修复：无论 raw_history 是 dict 还是 TabNet History，都转成普通 dict
            # =========================
            history = {}

            history = {}

            # =========================
            # 1. TabNet History 格式
            # =========================
            for key in ["train_logloss", "valid_logloss", "train_auc", "valid_auc"]:
                try:
                    value = raw_history[key]
                    if value is not None:
                        history[key] = list(value)
                except Exception:
                    pass

            # =========================
            # 2. XGBoost evals_result 格式
            # =========================
            try:
                if "validation_0" in raw_history and "validation_1" in raw_history:
                    if "logloss" in raw_history["validation_0"]:
                        history["train_logloss"] = list(raw_history["validation_0"]["logloss"])

                    if "logloss" in raw_history["validation_1"]:
                        history["valid_logloss"] = list(raw_history["validation_1"]["logloss"])

                    if "auc" in raw_history["validation_0"]:
                        history["train_auc"] = list(raw_history["validation_0"]["auc"])

                    if "auc" in raw_history["validation_1"]:
                        history["valid_auc"] = list(raw_history["validation_1"]["auc"])
            except Exception:
                pass

            if len(history) == 0:
                st.warning(f"{model_name} 没有可用的训练曲线数据。")
                continue

            st.markdown(f"#### {model_name}")

            col1, col2 = st.columns(2)

            # =========================
            # Loss 曲线
            # =========================
            with col1:
                train_loss = history.get("train_logloss")
                valid_loss = history.get("valid_logloss")

                if train_loss is not None and valid_loss is not None:
                    fig_loss, ax_loss = plt.subplots(figsize=(6, 4))
                    ax_loss.plot(train_loss, label="Train Loss", color="#1f77b4", linewidth=2)
                    ax_loss.plot(valid_loss, label="Valid Loss", color="#ff7f0e", linewidth=2)
                    ax_loss.set_title("Loss 曲线 (越低越好)")
                    ax_loss.set_xlabel("Epochs")
                    ax_loss.set_ylabel("LogLoss")
                    ax_loss.legend()
                    ax_loss.grid(True, linestyle="--", alpha=0.6)
                    st.pyplot(fig_loss)
                    plt.close(fig_loss)
                else:
                    st.info("暂无 Loss 曲线数据。")

            # =========================
            # AUC 曲线
            # =========================
            with col2:
                train_auc = history.get("train_auc")
                valid_auc = history.get("valid_auc")

                if train_auc is not None and valid_auc is not None:
                    fig_auc, ax_auc = plt.subplots(figsize=(6, 4))
                    ax_auc.plot(train_auc, label="Train AUC", color="#2ca02c", linewidth=2)
                    ax_auc.plot(valid_auc, label="Valid AUC", color="#d62728", linewidth=2)
                    ax_auc.set_title("AUC 曲线 (越高越好)")
                    ax_auc.set_xlabel("Epochs")
                    ax_auc.set_ylabel("AUC")
                    ax_auc.legend()
                    ax_auc.grid(True, linestyle="--", alpha=0.6)
                    st.pyplot(fig_auc)
                    plt.close(fig_auc)
                else:
                    st.info("暂无 AUC 曲线数据。")
elif viz_tab == "🧭 三维风险空间":
    if st.session_state.risk_space_data is None or len(st.session_state.risk_space_data) == 0:
        st.info("训练完成后将在这里展示测试集二维风险空间可视化。")
    else:
        st.markdown("#### 测试集二维特征空间与模型流失风险分布")

        st.caption(
            "说明：该图先将测试集样本经过与训练阶段一致的预处理，再使用 PCA 或 TruncatedSVD 降到二维。"
            "每个点代表一个测试集客户，颜色表示模型预测的流失概率，形状表示真实类别。"
            "如果同一真实类别样本在二维空间中相对聚集，并且高风险颜色区域与真实流失样本区域基本一致，"
            "说明模型学习到了一定的类别区分规律。"
        )

        model_names = list(st.session_state.risk_space_data.keys())

        for selected_risk_model in model_names:
            st.markdown("---")
            st.markdown(f"### {selected_risk_model}")

            risk_df = st.session_state.risk_space_data[selected_risk_model].copy()

            reducer_name = risk_df["降维方法"].iloc[0] if "降维方法" in risk_df.columns else "PCA/SVD"

            fig_risk = px.scatter_3d(
                risk_df,
                x="Dim1",
                y="Dim2",
                z="Dim3",
                color="预测流失概率",
                symbol="真实类别",
                hover_data=[
                    "真实类别",
                    "预测类别",
                    "预测流失概率",
                    "是否预测正确"
                ],
                color_continuous_scale="RdYlBu_r",
                title=f"{selected_risk_model} 测试集三维风险空间可视化（{reducer_name}）"
            )

            fig_risk.update_layout(
                scene=dict(
                    xaxis_title=f"{reducer_name} 第一维",
                    yaxis_title=f"{reducer_name} 第二维",
                    zaxis_title=f"{reducer_name} 第三维",
                ),
                coloraxis_colorbar_title="预测流失概率",
                height=700,
                legend=dict(
                    title="真实类别",
                    x=1.02,
                    y=1.0
                ),
                coloraxis_colorbar=dict(
                    title="预测流失概率",
                    x=1.12
                ),
                margin=dict(l=0, r=180, t=80, b=0)
            )

            st.plotly_chart(fig_risk, use_container_width=True)

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.metric(
                    f"{selected_risk_model} 测试样本数",
                    len(risk_df)
                )

            with col_b:
                error_count = (risk_df["是否预测正确"] == "预测错误").sum()
                st.metric(
                    f"{selected_risk_model} 预测错误样本数",
                    int(error_count)
                )

            with col_c:
                st.metric(
                    f"{selected_risk_model} 平均预测流失概率",
                    f"{risk_df['预测流失概率'].mean():.4f}"
                )

            with st.expander(f"查看 {selected_risk_model} 二维风险空间数据"):
                st.dataframe(
                    risk_df,
                    use_container_width=True,
                    hide_index=True
                )

elif viz_tab == "🧬 SHAP解释":
    st.markdown("#### LightGBM / XGBoost 的 SHAP 后验可解释性分析")

    shap_X_test = st.session_state.get("shap_X_test")
    shap_y_test = st.session_state.get("shap_y_test")


    if not SHAP_AVAILABLE:
        st.error("当前环境未安装 shap，请先执行：pip install shap")
    elif(
        st.session_state.shap_pipes is None
        or len(st.session_state.shap_pipes) == 0
        or shap_X_test is None
        or shap_y_test is None
    ):
        st.info("当前暂无可用于 SHAP 分析的数据或模型。请先勾选并训练 LightGBM 或 XGBoost。")

    else:
        st.caption(
            "说明：SHAP 用于解释树模型的预测依据。"
            "Summary 图展示全局特征影响，Bar 图展示平均绝对贡献，Waterfall 图解释单个客户的预测原因。"
        )

        shap_model_names = list(st.session_state.shap_pipes.keys())

        selected_shap_model = st.selectbox(
            "选择要解释的模型",
            shap_model_names,
            index=0
        )

        selected_pipe = st.session_state.shap_pipes[selected_shap_model]

        st.markdown("##### SHAP 参数设置")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            shap_sample_size = st.slider(
                "SHAP 抽样样本数",
                min_value=50,
                max_value=min(1000, len(shap_X_test)),
                value=min(300, len(shap_X_test)),

                step=50
            )

        with col_b:
            shap_top_n = st.slider(
                "显示 Top N 特征",
                min_value=5,
                max_value=50,
                value=20,
                step=5
            )

        with col_c:
            waterfall_type = st.selectbox(
                "Waterfall 样本类型",
                ["预测流失概率最高客户", "预测流失概率最低客户", "第一个测试样本", "自定义样本序号"],
                index=0
            )
        custom_sample_idx = 0

        if waterfall_type == "自定义样本序号":
            custom_sample_idx = st.number_input(
                "输入测试集样本序号",
                min_value=0,
                max_value=len(shap_X_test) - 1,
                value=0,
                step=1
            )

        X_shap_sample = shap_X_test.sample(
            n=min(shap_sample_size, len(shap_X_test)),
            random_state=42
        )

        st.divider()

        # =========================
        # SHAP Summary Beeswarm
        # =========================
        st.markdown("### 1. SHAP Summary Beeswarm 图")

        with st.spinner("正在计算 SHAP Summary 图..."):
            try:
                fig_summary = plot_tree_shap_summary(
                    pipe=selected_pipe,
                    X_sample=X_shap_sample,
                    max_display=shap_top_n,
                    title=f"{selected_shap_model} SHAP Summary Plot"
                )

                st.pyplot(fig_summary)
                plt.close(fig_summary)

                st.markdown("""
                **解读方式：**
                - 每一行是一个特征；
                - 横轴 SHAP 值越大，越推动模型预测为流失；
                - 横轴 SHAP 值越小，越推动模型预测为未流失；
                - 颜色表示特征值大小，红色通常代表特征值较高，蓝色代表特征值较低。
                """)

            except Exception as e:
                st.error("SHAP Summary 图绘制失败。")
                st.exception(e)

        st.divider()

        # =========================
        # SHAP Bar
        # =========================
        st.markdown("### 2. SHAP 全局重要性 Bar 图")

        with st.spinner("正在计算 SHAP Bar 图..."):
            try:
                fig_bar = plot_tree_shap_bar(
                    pipe=selected_pipe,
                    X_sample=X_shap_sample,
                    max_display=shap_top_n,
                    title=f"{selected_shap_model} SHAP Global Importance"
                )

                st.pyplot(fig_bar)
                plt.close(fig_bar)

                st.markdown("""
                **解读方式：**
                - 该图按平均绝对 SHAP 值排序；
                - 越靠上的特征，对模型整体预测影响越大；
                - 相比普通 `feature_importances_`，SHAP 同时考虑了特征对预测结果的边际贡献。
                """)

            except Exception as e:
                st.error("SHAP Bar 图绘制失败。")
                st.exception(e)

        st.divider()

        # =========================
        # SHAP Waterfall
        # =========================
        st.markdown("### 3. 单个客户 SHAP Waterfall 图")

        try:
            y_prob_for_shap = selected_pipe.predict_proba(shap_X_test)[:, 1]

            if waterfall_type == "预测流失概率最高客户":
                selected_idx = int(np.argmax(y_prob_for_shap))
            elif waterfall_type == "预测流失概率最低客户":
                selected_idx = int(np.argmin(y_prob_for_shap))
            elif waterfall_type == "自定义样本序号":
                selected_idx = int(custom_sample_idx)
            else:
                selected_idx = 0

            X_one = shap_X_test.iloc[[selected_idx]]

            selected_prob = y_prob_for_shap[selected_idx]

            # y_test_arr = y_test.values if isinstance(y_test, pd.Series) else np.asarray(y_test)
            y_test_arr = shap_y_test.values if isinstance(shap_y_test, pd.Series) else np.asarray(shap_y_test)

            selected_true_label = int(y_test_arr[selected_idx])

            st.info(
                f"当前解释样本序号：{selected_idx}；"
                f"真实标签：{selected_true_label}；"
                f"模型预测流失概率：{selected_prob:.4f}"
            )

            with st.spinner("正在计算 SHAP Waterfall 图..."):
                fig_waterfall = plot_tree_shap_waterfall(
                    pipe=selected_pipe,
                    X_sample=X_one,
                    sample_pos=0,
                    max_display=shap_top_n,
                    title=f"{selected_shap_model} Single Customer SHAP Explanation"
                )

                st.pyplot(fig_waterfall)
                plt.close(fig_waterfall)

            with st.expander("查看该客户原始特征"):
                st.dataframe(
                    X_one,
                    use_container_width=True
                )

            st.markdown("""
            **解读方式：**
            - 红色特征通常表示将预测推向“流失”；
            - 蓝色特征通常表示将预测推向“未流失”；
            - Waterfall 图可以解释单个客户为什么被模型判定为高风险或低风险。
            """)

        except Exception as e:
            st.error("SHAP Waterfall 图绘制失败。")
            st.exception(e)
        # 👇👇👇 从这里开始复制，新增第 4 个 SHAP 图 👇👇👇
        st.divider()

        st.markdown("### 4. SHAP 双变量依赖图 (Dependence Plot)")
        st.caption(
            "展示单个特征的具体取值如何影响预测结果（SHAP值），以及它与另一个特征的交互作用。"
            "如果颜色呈现明显的分层或渐变，说明这两个特征共同对流失率产生了非线性的叠加影响。"
        )

        try:
            # 获取预处理后的 DataFrame 和 SHAP 值
            X_shap_df, shap_values_to_plot, _ = get_tree_shap_values(selected_pipe, X_shap_sample)
            available_features = X_shap_df.columns.tolist()

            if len(available_features) > 0:
                col_dep1, col_dep2 = st.columns(2)
                with col_dep1:
                    dep_feature_x = st.selectbox(
                        "选择主特征 (X轴)",
                        available_features,
                        index=0,
                        key="shap_dep_x"
                    )
                with col_dep2:
                    dep_feature_color = st.selectbox(
                        "选择交互特征 (颜色)",
                        ["auto (自动寻找最强交互特征)"] + available_features,
                        index=0,
                        key="shap_dep_color"
                    )

                with st.spinner("正在计算 SHAP Dependence 图..."):

                    # 处理 auto 选项
                    interaction_index = "auto" if "auto" in dep_feature_color else dep_feature_color

                    # 依赖图通常不需要显式创建 subplots，shap.dependence_plot 会自动处理当前 figure
                    plt.figure(figsize=(8, 5))

                    shap.dependence_plot(
                        dep_feature_x,
                        shap_values_to_plot,
                        X_shap_df,
                        interaction_index=interaction_index,
                        show=False
                    )

                    fig_dep = plt.gcf()
                    st.pyplot(fig_dep)
                    plt.close(fig_dep)

                    st.markdown("""
                    **解读方式：**
                    - **横轴**：你选择的主特征的实际取值；
                    - **纵轴**：该特征对预测结果的 SHAP 值（>0 推动流失，<0 抑制流失）；
                    - **颜色**：交互特征的取值（红色代表该特征值大，蓝色代表值小）；
                    - **怎么看交互**：比如横轴是“在网时长”，颜色是“月租费”。如果发现同样是“在网时长=10个月”，红点（高月租）的 SHAP 值远高于蓝点（低月租），这就说明“高月租”放大了“短在网时长”的流失风险！
                    """)
            else:
                st.info("未能提取到有效的特征列表。")

        except Exception as e:
            st.error("SHAP Dependence 图绘制失败。")
            st.exception(e)
        # 👆👆👆 复制到此结束 👆👆👆

elif viz_tab == "🎬 XGBoost动画":

    st.markdown("#### XGBoost Boosting 动画演示")

    st.caption(
        "该动画展示 XGBoost 从第 1 棵树开始，随着 Boosting 轮数增加，"
        "测试集客户的预测流失概率如何逐步变化。"
        "三维坐标是测试集特征经过预处理后，再通过 PCA 或 TruncatedSVD 降维得到的固定空间。"
    )

    xgb_animation_data = st.session_state.get("xgb_animation_data")

    if xgb_animation_data is None or len(xgb_animation_data) == 0:
        st.info("暂无 XGBoost 动画数据。请先勾选并训练 XGBoost。")
    else:
        xgb_model_names = list(xgb_animation_data.keys())

        selected_xgb_anim_model = st.selectbox(
            "选择 XGBoost 模型",
            xgb_model_names,
            index=0
        )

        anim_df = xgb_animation_data[selected_xgb_anim_model].copy()

        if "数据来源" in anim_df.columns:
            source_options = anim_df["数据来源"].dropna().unique().tolist()

            selected_anim_source = st.selectbox(
                "选择动画数据来源",
                source_options,
                index=0
            )

            anim_df = anim_df[anim_df["数据来源"] == selected_anim_source].copy()
        remove_anim_outliers = st.checkbox(
            "隐藏三维空间极端离群点",
            value=True,
            help="仅用于改善动画显示效果，不影响模型训练和预测结果。"
        )

        if remove_anim_outliers and all(col in anim_df.columns for col in ["Dim1", "Dim2", "Dim3"]):
            q_low = 0.01
            q_high = 0.99

            dim_filter = (
                    anim_df["Dim1"].between(anim_df["Dim1"].quantile(q_low), anim_df["Dim1"].quantile(q_high)) &
                    anim_df["Dim2"].between(anim_df["Dim2"].quantile(q_low), anim_df["Dim2"].quantile(q_high)) &
                    anim_df["Dim3"].between(anim_df["Dim3"].quantile(q_low), anim_df["Dim3"].quantile(q_high))
            )

            before_n = len(anim_df)
            anim_df = anim_df[dim_filter].copy()
            after_n = len(anim_df)

            st.caption(
                f"已隐藏三维坐标极端离群点：{before_n - after_n} 行动画数据。"
                f"该操作只影响可视化，不影响模型训练。"
            )

        else:
            st.warning(
                "当前动画数据没有“数据来源”字段，说明你正在使用旧缓存。"
                "请点击页面底部的“清空训练结果”，然后重新训练 XGBoost。"
            )

        reducer_name = (
            anim_df["降维方法"].iloc[0]
            if "降维方法" in anim_df.columns
            else "PCA/SVD"
        )
        xgb_pipes = st.session_state.get("xgb_pipes")
        selected_xgb_pipe = None
        total_trees = int(anim_df["Boosting轮数"].max())
        selected_round = 1

        if xgb_pipes is not None and selected_xgb_anim_model in xgb_pipes:
            selected_xgb_pipe = xgb_pipes[selected_xgb_anim_model]

            try:
                total_trees = get_xgb_total_trees(selected_xgb_pipe)
            except Exception:
                total_trees = int(anim_df["Boosting轮数"].max())

        total_trees = max(1, int(total_trees))

        if "xgb_sync_selected_round" not in st.session_state:
            st.session_state["xgb_sync_selected_round"] = 1

        if st.session_state["xgb_sync_selected_round"] > total_trees:
            st.session_state["xgb_sync_selected_round"] = total_trees

        selected_round = int(st.session_state["xgb_sync_selected_round"])


        st.markdown("##### 1. 样本预测流失概率随 Boosting 轮数变化")
        st.markdown("""
                **解读方式：**

                - 每个点代表一个测试集客户；
                - 点的位置固定，表示该客户在降维后的特征空间中的位置；
                - 颜色表示当前 Boosting 轮数下模型预测的流失概率；
                - 颜色越偏红，表示模型认为该客户越可能流失；
                - 随着轮数增加，如果颜色逐渐稳定，说明模型预测趋于收敛；
                - 如果一些点颜色变化剧烈，说明这些样本在模型学习过程中比较难判断。
                """)
        current_anim_df = anim_df[anim_df["Boosting轮数"] == selected_round].copy()

        if current_anim_df.empty:
            available_rounds = sorted(anim_df["Boosting轮数"].unique().tolist())
            nearest_round = min(available_rounds, key=lambda x: abs(x - selected_round))
            current_anim_df = anim_df[anim_df["Boosting轮数"] == nearest_round].copy()
        else:
            nearest_round = selected_round

        fig_anim = px.scatter_3d(
            current_anim_df,
            x="Dim1",
            y="Dim2",
            z="Dim3",
            color="预测流失概率",
            symbol="真实类别",
            range_color=[0, 1],

            color_continuous_scale="RdYlBu_r",
            hover_data=[
                "真实类别",
                "预测类别",
                "预测流失概率",
                "Boosting轮数"
            ],
            title=f"{selected_xgb_anim_model} 第 {nearest_round} 轮 Boosting：预测流失概率分布"

        # title=f"{selected_xgb_anim_model} Boosting 过程动画：预测流失概率逐轮变化"
        )
        # ... 上面是 fig_anim = px.scatter_3d(...) 的内容
        fig_anim.update_traces(
            marker=dict(
                size=5,  # 👈 点的大小（可以自己微调，比如 6、7、8）
                opacity=0.85,  # 👈 透明度（0 到 1 之间，0.8 表示 80% 不透明）
                line=dict(width=0.3, color="white")  # 👈 边缘宽度和颜色（width=1 表示 1 像素的白边）
            )
        )

        # fig_anim.update_layout(
        #     scene=dict(
        #         xaxis_title=f"{reducer_name} 第一维",
        #         yaxis_title=f"{reducer_name} 第二维",
        #         zaxis_title=f"{reducer_name} 第三维",
        #     ),
        #     height=750,
        #     coloraxis_colorbar_title="预测流失概率",
        #     legend=dict(
        #         title="真实类别",
        #         x=1.02,
        #         y=1.0
        #     ),
        #     coloraxis_colorbar=dict(
        #         title="预测流失概率",
        #         x=1.15,  # 颜色条再往右移，避开图例
        #         y=0.45,  # 颜色条往下移，整体居中居下
        #         len=0.75  # 颜色条长度稍微缩短，更美观
        #     ),
        #     margin=dict(l=0, r=180, t=80, b=0)
        # )
        fig_anim.update_layout(
            scene=dict(
                xaxis_title=f"{reducer_name} 第一维",
                yaxis_title=f"{reducer_name} 第二维",
                zaxis_title=f"{reducer_name} 第三维",
            ),
            title_y=0.81,           # 👈 新增：标题高度与第二个图一致
            title_x=0.3,            # 👈 新增：标题水平位置与第二个图一致
            height=750,
            coloraxis_colorbar_title="预测流失概率",
            legend=dict(
                title="真实类别",
                x=0.83,             # 👈 修改：图例左移并向下，和第二个图对齐
                y=0.94
            ),
            coloraxis_colorbar=dict(
                title="预测流失概率",
                x=0.83,             # 👈 修改：颜色条左移，和第二个图对齐
                y=0.45,
                len=0.75
            ),
            margin=dict(l=0, r=180, t=80, b=0)
        )


        # 调整动画播放速度
        # if fig_anim.layout.updatemenus:
        #     fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
        #     fig_anim.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300

        # st.plotly_chart(fig_anim, use_container_width=True)
        # ！！！这是你原有的代码，保持不变！！！
        st.plotly_chart(fig_anim, use_container_width=True, key="original_3d_anim")


        # 👇👇👇 从这里开始复制，新建带大小变化的 3D图 和 残差直方图 👇👇👇
        st.divider()



        st.markdown("##### 2. Boosting 逐轮新增树结构与前 k 棵树累加效果")

        if selected_xgb_pipe is None:
            st.info("暂无可展示的 XGBoost 树结构。请先重新训练 XGBoost。")
        else:
            try:
                tree_index = selected_round - 1

                # =========================
                # 先显示树图：放在标题 2 正下方
                # =========================
                dot = None

                try:
                    import xgboost as xgb

                    model = selected_xgb_pipe.named_steps["model"]

                    dot = xgb.to_graphviz(
                        model,
                        num_trees=tree_index,
                        rankdir="LR",
                        yes_color="#4CAF50",
                        no_color="#F44336"
                    )

                    st.markdown("###### 当前 XGBoost 树")
                    st.graphviz_chart(dot.source)

                except Exception as e:
                    st.warning("当前环境无法渲染 Graphviz 树图，改为显示文本树。")
                    st.exception(e)

                    tree_text = get_xgb_tree_text(
                        pipe=selected_xgb_pipe,
                        tree_index=tree_index
                    )

                    st.code(tree_text, language="text")

                # =========================
                # 再显示说明和控制项
                # =========================
                st.caption(
                    "说明：XGBoost 并不是在训练过程中不断修改同一棵树，"
                    "而是在每一轮 Boosting 中新增一棵树。"
                    "因此，这里通过滑块选择不同轮次，展示该轮新增的决策树结构。"
                )

                col_tree_a, col_tree_b = st.columns([2, 1])

                with col_tree_a:
                    st.info(f"当前同步轮数：第 {selected_round} 轮")

                with col_tree_b:
                    tree_display_mode = st.selectbox(
                        "树结构展示方式",
                        ["图形结构", "文本结构", "节点表格"],
                        index=0
                    )

                st.info(
                    f"当前展示的是第 {selected_round} 轮 Boosting 新增的树，"
                    f"对应 XGBoost 内部树编号 tree_index={tree_index}。"
                )

                # =========================
                # 根据选择额外展示文本结构 / 节点表格
                # 图形结构已经在标题下方显示过了
                # =========================
                if tree_display_mode == "图形结构":
                    if dot is not None:
                        with st.expander("查看当前树的 DOT 源码"):
                            st.code(dot.source, language="dot")

                elif tree_display_mode == "文本结构":
                    tree_text = get_xgb_tree_text(
                        pipe=selected_xgb_pipe,
                        tree_index=tree_index
                    )

                    st.code(tree_text, language="text")

                else:
                    tree_df = get_xgb_tree_dataframe(
                        pipe=selected_xgb_pipe,
                        tree_index=tree_index
                    )

                    st.dataframe(
                        tree_df,
                        use_container_width=True,
                        hide_index=True
                    )

                with st.expander("查看 XGBoost 内部特征名与实际特征名对应关系"):
                    mapping_df = get_xgb_feature_mapping(selected_xgb_pipe)

                    if mapping_df is not None and len(mapping_df) > 0:
                        st.dataframe(
                            mapping_df,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("暂无特征名映射信息。")

                st.divider()


                show_xgb_round_effect = st.checkbox(
                    "显示前 k 棵树累加后的风险空间与 LogLoss 曲线",
                    value=False,
                    key="show_xgb_round_effect"
                )

                if show_xgb_round_effect:
                    st.divider()

                    st.markdown("##### 4. 前 k 棵树累加后的风险空间与 LogLoss 曲线")

                    st.caption(
                        "下面两个图会跟随上面的滑块同步变化。"
                        f"当前 k = {selected_round}，表示只使用前 {selected_round} 棵树进行预测。"
                    )

                    xgb_X_train = st.session_state.get("xgb_X_train")
                    xgb_X_test = st.session_state.get("xgb_X_test")
                    xgb_y_train = st.session_state.get("xgb_y_train")
                    xgb_y_test = st.session_state.get("xgb_y_test")

                    if (
                            xgb_X_train is None
                            or xgb_X_test is None
                            or xgb_y_train is None
                            or xgb_y_test is None
                    ):
                        st.warning("缺少 XGBoost 绘图所需的训练/测试数据。请重新训练 XGBoost。")
                    else:
                        col_round_plot1, col_round_plot2 = st.columns([1, 1])

                        with col_round_plot1:
                            fig_risk_2d = plot_xgb_2d_risk_space_with_slider(
                                pipe=selected_xgb_pipe,
                                X_test=xgb_X_test,
                                y_test=xgb_y_test,
                                current_round=selected_round,
                                random_state=42
                            )

                            st.plotly_chart(
                                fig_risk_2d,
                                use_container_width=True
                            )

                        with col_round_plot2:
                            fig_logloss = plot_xgb_logloss_curve_with_slider(
                                pipe=selected_xgb_pipe,
                                X_train=xgb_X_train,
                                y_train=xgb_y_train,
                                X_test=xgb_X_test,
                                y_test=xgb_y_test,
                                current_round=selected_round
                            )

                            st.pyplot(fig_logloss)
                            plt.close(fig_logloss)

                st.markdown("""
                **解读方式：**

                - 每一棵树表示 XGBoost 在某一轮 Boosting 中新增的弱学习器；
                - 树中的判断条件通常显示为 `f0`、`f1`、`f2` 等内部特征编号；
                - 可以在“特征名对应关系”中查看这些编号对应的实际变量；
                - 非叶子节点表示模型根据某个特征进行分裂；
                - 叶子节点表示该路径下样本对最终预测结果的贡献；
                - 随着 Boosting 轮数增加，模型会不断新增树，用于修正前面模型尚未拟合好的样本。
                """)

            except Exception as e:
                st.error("XGBoost 树结构可视化失败。")
                st.exception(e)

        with st.expander("查看 XGBoost 动画原始数据"):
            st.dataframe(
                anim_df,
                use_container_width=True,
                hide_index=True
            )

        st.markdown("##### 1.1 聚焦困难样本：预测误差动态 3D 图")
        st.caption(
            "该图中，点的大小代表当前的预测误差绝对值。随着树的增加，大部分点缩小消失，剩下的巨大散点即为难以攻克的困难样本。")

        # 新建一个带有 size 的 3D 图
        fig_anim_size = px.scatter_3d(
            current_anim_df,
            x="Dim1",
            y="Dim2",
            z="Dim3",
            color="预测流失概率",
            symbol="真实类别",
            size="散点大小",
            size_max=22,
            range_color=[0, 1],
            color_continuous_scale="RdYlBu_r",
            hover_data=[
                "真实类别",
                "预测类别",
                "预测流失概率",
                "残差",
                "预测误差绝对值",
                "Boosting轮数"
            ],
            title=f"第 {nearest_round} 轮 Boosting：困难样本追踪"
        )

        fig_anim_size.update_layout(
            scene=dict(
                xaxis_title=f"{reducer_name} 第一维",
                yaxis_title=f"{reducer_name} 第二维",
                zaxis_title=f"{reducer_name} 第三维",
            ),
            title_y=0.81,  # 👈 新增：控制主标题的垂直位置（调小往下
            title_x=0.3,
            height=750,
            coloraxis_colorbar=dict(
                title="预测流失概率",
                x=0.83,
                y=0.45,
                len=0.75
            ),
            coloraxis_colorbar_title="预测流失概率",
            legend=dict(title="真实类别", x=0.83, y=0.94),
            margin=dict(l=0, r=180, t=80, b=0)
        )

        st.plotly_chart(fig_anim_size, use_container_width=True, key="size_3d_anim")


        st.markdown("##### 1.2 回归 Boosting 本质：残差 (Residuals) 收缩分布")
        st.markdown("""
        **解读方式：**
        - 横轴是**残差**（真实标签减去预测概率），范围在 [-1, 1] 之间。
        - 随着滑块拖动（树的数量增加），你会看到两座山峰（流失与未流失客户的残差）被不断地**“挤向” 0 的位置**。
        - 这最直观地展示了 Gradient Boosting 算法中每一棵新树都在**“纠正上一轮残差”**的数学本质。
        """)

        # 新建残差直方图
        fig_hist = px.histogram(
            current_anim_df,
            x="残差",
            color="真实类别",
            nbins=50,
            range_x=[-1.1, 1.1],
            barmode="overlay",
            opacity=0.75,
            color_discrete_map={
                "真实流失": "#d62728",
                "真实未流失": "#1f77b4"
            },
            title=f"第 {nearest_round} 轮 Boosting：残差分布直方图"
        )

        fig_hist.update_layout(
            height=600,
            title_x=0.29,
            xaxis_title="残差 (真实标签 - 预测概率)",
            yaxis_title="样本数量",
            legend=dict(title="真实类别"),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        # 👇 把刚才那两行替换成下面这两行 👇
        fig_hist.update_xaxes(
            title_font_color="black",
            tickfont_color="black",
            showline=True,  # 显示轴线
            linewidth=1.5,  # 边框线宽（可根据喜好改大）
            linecolor="black",  # 边框颜色为黑色
            mirror=True  # 镜像到上方，形成闭合框
        )

        fig_hist.update_yaxes(
            title_font_color="black",
            tickfont_color="black",
            showline=True,  # 显示轴线
            linewidth=1.5,  # 边框线宽
            linecolor="black",  # 边框颜色为黑色
            mirror=True  # 镜像到右侧，形成闭合框
        )

        st.plotly_chart(fig_hist, use_container_width=True, key="residual_hist_anim")

        # 👆👆👆 复制到此结束 👆👆👆

        # st.divider()

        st.sidebar.markdown("### 🎬 动画参数控制")
        selected_round = st.sidebar.slider(
            "选择 Boosting 轮数 / 第几棵树",
            min_value=1,
            max_value=int(total_trees),
            step=1,
            key="xgb_sync_selected_round",
            help="右侧 PCA 风险空间和树结构会同步到该轮数。"
        )

        # st.divider()


        st.markdown("##### 3. 平均预测流失概率随 Boosting 轮数变化")

        mean_prob_df = (
            anim_df
            .groupby("Boosting轮数", as_index=False)["预测流失概率"]
            .mean()
            .rename(columns={"预测流失概率": "平均预测流失概率"})
        )

        fig_mean = px.line(
            mean_prob_df,
            x="Boosting轮数",
            y="平均预测流失概率",
            markers=True,
            title=f"{selected_xgb_anim_model} 平均预测流失概率变化"
        )

        fig_mean.update_layout(
            height=420,
            xaxis_title="Boosting 轮数 / 树的数量",
            yaxis_title="平均预测流失概率",
            yaxis=dict(range=[0, 1])
        )

        st.plotly_chart(fig_mean, use_container_width=True)

        st.divider()
        st.divider()

# =========================
# 清空结果
# =========================

col_clear, col_info = st.columns([1, 4])

with col_clear:
    if st.button("🗑️ 清空训练结果"):
        st.session_state.model_results = None
        st.session_state.roc_data = None
        st.session_state.confusion_data = None
        st.session_state.importance_data = None
        st.session_state.last_train_config = None
        st.session_state.importance_data = None
        st.session_state.training_histories = None # 👇 新增
        st.session_state.risk_space_data = None
        st.session_state.shap_pipes = None
        st.session_state.shap_X_test = None
        st.session_state.shap_y_test = None
        st.session_state.xgb_animation_data = None
        st.session_state.xgb_pipes = None
        st.session_state.xgb_X_train = None
        st.session_state.xgb_X_test = None
        st.session_state.xgb_y_train = None
        st.session_state.xgb_y_test = None

        # 同时删除本地缓存文件
        if os.path.exists(RESULT_CACHE_FILE):
            os.remove(RESULT_CACHE_FILE)

        st.success("训练结果已清空。")
        st.rerun()


with col_info:
    st.caption("说明：只有点击“开始训练模型”按钮时才会重新训练，刷新页面不会自动重新训练。")
