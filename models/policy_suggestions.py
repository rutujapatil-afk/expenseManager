import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# Load Datasets
@st.cache_data
def load_data():
    """
    Load the policy and spending data from CSV files.
    """
    try:
        policy_data = pd.read_csv("data/insurance_policies_dataset.csv")
        spending_data = pd.read_csv("data/transactions.csv")
        return policy_data, spending_data
    except FileNotFoundError as e:
        st.error(f"Error loading data files: {e}")
        return None, None

# Data Preprocessing
def preprocess_data(spending_data, policy_data):
    if spending_data is None or policy_data is None:
        return None, None, None

    spending_data.columns = spending_data.columns.str.strip()
    spending_data['Date'] = pd.to_datetime(spending_data['Date'])
    monthly_spending = spending_data.groupby(spending_data['Date'].dt.to_period("M"))['Amount'].sum().reset_index()
    monthly_spending.rename(columns={'Amount': 'Monthly Expense ($)', 'Date': 'Month'}, inplace=True)
    monthly_spending['Month'] = monthly_spending['Month'].dt.to_timestamp()

    # Categorize monthly spending
    monthly_spending['Spending Category'] = pd.cut(
        monthly_spending['Monthly Expense ($)'],
        bins=[0, 500, 1500, np.inf],
        labels=['Low', 'Medium', 'High']
    )

    # Encoding policy types
    le = LabelEncoder()
    if 'Policy Type' in policy_data.columns:
        policy_data['Policy Type'] = le.fit_transform(policy_data['Policy Type'])
    else:
        st.error("Column 'Policy Type' is missing from policy data.")
        return None, None, None

    # Check if 'Expected ROI' column exists
    if 'Expected ROI' in policy_data.columns:
        policy_data['ROI Category'] = pd.cut(
            policy_data['Expected ROI'],
            bins=[0, 5, 10, 15, np.inf],
            labels=['Low', 'Medium', 'High', 'Very High']
        )
    else:
        st.error("Column 'Expected ROI' is missing from policy data.")
        return None, None, None

    # Check for required columns
    required_columns = ['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']
    missing_columns = [col for col in required_columns if col not in policy_data.columns]
    if missing_columns:
        st.error(f"Missing columns: {', '.join(missing_columns)}")
        return None, None, None

    return monthly_spending, policy_data, le

# Train the models
def train_models(monthly_spending, policy_data):
    if monthly_spending is None or policy_data is None:
        return None, None, None, None

    # Spending Prediction Model
    X_spending = monthly_spending[['Month']].apply(lambda x: x.astype('int64'))
    y_spending = monthly_spending['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)
    model_spending = RandomForestClassifier(random_state=42)
    model_spending.fit(X_train_s, y_train_s)
    acc_spending = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    # Policy Prediction Model
    X_policy = policy_data[['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']]
    y_policy = policy_data['ROI Category']
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_policy, y_policy, test_size=0.2, random_state=42)
    model_policy = RandomForestClassifier(random_state=42)
    model_policy.fit(X_train_p, y_train_p)
    acc_policy = accuracy_score(y_test_p, model_policy.predict(X_test_p))

    return model_spending, model_policy, acc_spending, acc_policy

# User Input for investment
def get_user_input():
    st.header("Enter Your Investment Details")
    with st.form(key='investment_form'):
        monthly_investment = st.number_input("Enter your monthly investment amount ($):", min_value=0.0, value=100.0, step=10.0)
        investment_duration = st.number_input("Enter your investment duration (in months):", min_value=1, max_value=600, value=12)
        submit_button = st.form_submit_button(label='Submit Investment')

    if submit_button:
        st.session_state['monthly_investment'] = monthly_investment
        st.session_state['investment_duration'] = investment_duration

    return st.session_state.get('monthly_investment'), st.session_state.get('investment_duration')

# Policy Recommendation
def recommend_policy(user_investment, investment_duration, policy_data, spending_model, le):
    if user_investment is None or investment_duration is None:
        st.error("Please provide valid investment details.")
        return None, None

    try:
        user_spending = np.array([[investment_duration]])
        predicted_category = spending_model.predict(user_spending)[0]
        st.write(f"Predicted Spending Category: {predicted_category}")
    except Exception as e:
        st.error(f"Error predicting spending category: {e}")
        return None, None

    if predicted_category == 'Low':
        suitable_policies = policy_data[policy_data['ROI Category'] == 'Low']
    elif predicted_category == 'Medium':
        suitable_policies = policy_data[policy_data['ROI Category'] != 'Very High']
    else:
        suitable_policies = policy_data[policy_data['ROI Category'] == 'High']

    if suitable_policies.empty:
        st.write("No suitable policies found.")
        return None, None

    suitable_policies['Potential Return ($)'] = (user_investment * investment_duration) * (suitable_policies['Expected ROI'] / 100)
    top_policies = suitable_policies.nlargest(3, 'Potential Return ($)')

    st.write("Recommended Policies:")
    st.write(top_policies)

    best_policy = top_policies.iloc[0]
    policy_name = le.inverse_transform([best_policy['Policy Type']])[0]
    st.write(f"Recommended Policy: {policy_name}")
    return best_policy, suitable_policies

# Visualization
def visualize_policy_comparison(suitable_policies):
    if suitable_policies.empty:
        return
    sns.barplot(data=suitable_policies, x='Policy Name', y='Potential Return ($)')
    st.pyplot()

# Main Display Function
def display_policy_suggestion():
    policy_data, spending_data = load_data()
    monthly_spending, policy_data, le = preprocess_data(spending_data, policy_data)
    model_spending, model_policy, _, _ = train_models(monthly_spending, policy_data)
    investment, duration = get_user_input()
    if st.button("Analyze"):
        recommend_policy(investment, duration, policy_data, model_spending, le)
