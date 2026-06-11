#utils.data_loader.py:
import pandas as pd
import streamlit as st
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@st.cache_data
def load_full_customers():
    df = pd.read_excel(os.path.join(DATA_DIR, "full_customers.xlsx"))
    df['churn'] = df['churn'].astype(str)
    return df


@st.cache_data
def load_train():
    return pd.read_excel(os.path.join(DATA_DIR, "train.xlsx"))


@st.cache_data
def load_test():
    return pd.read_excel(os.path.join(DATA_DIR, "test.xlsx"))


@st.cache_data
def load_feedback():
    return pd.read_excel(os.path.join(DATA_DIR, "customer_feedback.xlsx"))


@st.cache_data
def load_business():
    return pd.read_excel(os.path.join(DATA_DIR, "business_costs.xlsx"))


@st.cache_data
def load_campaign():
    return pd.read_excel(os.path.join(DATA_DIR, "campaign_uplift.xlsx"))
@st.cache_data
def load_feedback_with_customer():
    feedback_df = pd.read_excel(os.path.join(DATA_DIR, "customer_feedback.xlsx"))
    customer_df = pd.read_excel(os.path.join(DATA_DIR, "full_customers.xlsx"))

    # 只取反馈分析需要的客户字段
    customer_cols = [
        'customer_id',
        'churn',
        'total_charges',
        'customer_service_calls',
        'customer_value_segment',
        'usage_intensity',
        'rule_based_churn_risk_score',
        'rule_based_churn_risk_level'
    ]

    customer_df = customer_df[customer_cols].copy()

    merged_df = feedback_df.merge(
        customer_df,
        on='customer_id',
        how='left'
    )

    merged_df['churn_int'] = merged_df['churn'].astype(int)
    merged_df['churn_label'] = merged_df['churn_int'].map({0: '留存', 1: '流失'})

    return merged_df
@st.cache_data
def load_business_with_customer():
    business_df = pd.read_excel(os.path.join(DATA_DIR, "business_costs.xlsx"))
    customer_df = pd.read_excel(os.path.join(DATA_DIR, "full_customers.xlsx"))

    customer_cols = [
        'customer_id',
        'churn',
        'customer_value_segment',
        'usage_intensity',
        'rule_based_churn_risk_score',
        'rule_based_churn_risk_level',
        'customer_service_calls',
        'state'
    ]

    customer_df = customer_df[customer_cols].copy()

    merged_df = business_df.merge(
        customer_df,
        on='customer_id',
        how='left'
    )

    merged_df['churn_int'] = merged_df['churn'].astype(int)
    merged_df['churn_label'] = merged_df['churn_int'].map({0: '留存', 1: '流失'})

    return merged_df
@st.cache_data
def load_campaign_with_customer_business():
    campaign_df = pd.read_excel(os.path.join(DATA_DIR, "campaign_uplift.xlsx"))
    customer_df = pd.read_excel(os.path.join(DATA_DIR, "full_customers.xlsx"))
    business_df = pd.read_excel(os.path.join(DATA_DIR, "business_costs.xlsx"))

    customer_cols = [
        'customer_id',
        'churn',
        'customer_value_segment',
        'usage_intensity',
        'rule_based_churn_risk_score',
        'rule_based_churn_risk_level',
        'customer_service_calls',
        'state'
    ]

    business_cols = [
        'customer_id',
        'monthly_revenue',
        'estimated_remaining_months',
        'estimated_clv',
        'retention_cost',
        'expected_loss_if_churn',
        'net_gain_if_retained'
    ]

    customer_df = customer_df[customer_cols].copy()
    business_df = business_df[business_cols].copy()

    df = campaign_df.merge(customer_df, on='customer_id', how='left')
    df = df.merge(business_df, on='customer_id', how='left')

    df['churn_int'] = df['churn'].astype(int)
    df['churn_label'] = df['churn_int'].map({0: '留存', 1: '流失'})

    df['original_churn_int'] = df['original_churn'].astype(int)
    df['churn_after_campaign_int'] = df['churn_after_campaign'].astype(int)

    df['responded_int'] = df['responded'].astype(int)
    df['contacted_int'] = df['contacted'].astype(int)

    # 是否因为活动从流失变为留存
    df['saved_by_campaign'] = (
        (df['original_churn_int'] == 1) &
        (df['churn_after_campaign_int'] == 0)
    ).astype(int)

    # 是否活动后变差，原本不流失，后来流失
    df['worsened_after_campaign'] = (
        (df['original_churn_int'] == 0) &
        (df['churn_after_campaign_int'] == 1)
    ).astype(int)

    return df
