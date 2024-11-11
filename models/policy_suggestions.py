# -- coding: utf-8 --
"""
policy_suggestions.py

Streamlit application for policy suggestion based on user spending patterns and investment preferences.
"""

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
    policy_data = pd.read_csv("data/insurance_policies_dataset.csv")
    spending_data = pd.read_csv("data/transactions.csv")
    return policy_data, spending_data

policy_data, spending_data = load_data()

# Data Preprocessing
def preprocess_data(spending_data, policy_data):
    """
    Preprocess the spending data and policy data to make them ready for analysis and model training.
    """
    # Clean and preprocess the spending data
    spending_data.columns = spending_data.columns.str.strip()  # Remove any trailing whitespaces from column names
    spending_data['Date'] = pd.to_datetime(spending_data['Date'])  # Convert 'Date' column to datetime
    monthly_spending = spending_data.groupby(spending_data['Date'].dt.to_period("M"))['Amount'].sum().reset_index()
    monthly_spending.rename(columns={'Amount': 'Monthly Expense ($)', 'Date': 'Month'}, inplace=True)
    monthly_spending['Month'] = monthly_spending['Month'].dt.to_timestamp().dt.year * 100 + monthly_spending['Month'].dt.month

    # Categorize spending into bins
    monthly_spending['Spending Category'] = pd.cut(monthly_spending['Monthly Expense ($)'],
                                                    bins=[0, 500, 1500, np.inf],
                                                    labels=['Low', 'Medium', 'High'])

    # Process the policy dataset for model training
    le = LabelEncoder()
    policy_data['Policy Type'] = le.fit_transform(policy_data['Policy Type'])
    policy_data['Interest Rate Category'] = pd.cut(policy_data['Interest Rate (%)'],
                                                   bins=[0, 5, 10, 15, np.inf],
                                                   labels=['Low', 'Medium', 'High', 'Very High'])
    
    return monthly_spending, policy_data

monthly_spending, policy_data = preprocess_data(spending_data, policy_data)

# Train the models
def train_models(monthly_spending, policy_data):
    """
    Train machine learning models for spending prediction and policy recommendation.
    """
    # Spending model
    X_spending = monthly_spending[['Month']]
    y_spending = monthly_spending['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)
    model_spending = RandomForestClassifier(random_state=42)
    model_spending.fit(X_train_s, y_train_s)
    acc_spending = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    # Policy model
    X_policy = policy_data[['Policy Type', 'Interest Rate (%)', 'Maturity Period (years)', 'Minimum Investment ($)']]
    X_policy = pd.get_dummies(X_policy, drop_first=True)  # Convert categorical data to dummy variables
    y_policy = policy_data['Interest Rate Category']
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_policy, y_policy, test_size=0.2, random_state=42)
    model_policy = RandomForestClassifier(random_state=42)
    model_policy.fit(X_train_p, y_train_p)
    acc_policy = accuracy_score(y_test_p, model_policy.predict(X_test_p))

    return model_spending, model_policy, acc_spending, acc_policy

model_spending, model_policy, acc_spending, acc_policy = train_models(monthly_spending, policy_data)

# User Input for investment
def get_user_input():
    """
    Get the user input for monthly investment and investment duration from the sidebar.
    """
    st.sidebar.header("User Investment Input")
    monthly_investment = st.sidebar.number_input("Enter your monthly investment amount ($):", min_value=0.0, value=100.0, step=10.0)
    investment_duration = st.sidebar.slider("Enter your investment duration (in months):", min_value=1, max_value=60, value=12)
    return monthly_investment, investment_duration

monthly_investment, investment_duration = get_user_input()

# Policy Recommendation
def recommend_policy(user_investment, investment_duration, policy_data, spending_model):
    """
    Recommend an insurance policy based on user spending and investment preferences.
    """
    user_spending = np.array([[user_investment]])
    predicted_category = spending_model.predict(user_spending)[0]
    st.write(f"Predicted Spending Category: {predicted_category}")

    # Filter policies based on spending category
    if predicted_category == 'Low':
        suitable_policies = policy_data[policy_data['Interest Rate Category'] == 'Low']
    elif predicted_category == 'Medium':
        suitable_policies = policy_data[policy_data['Interest Rate Category'] != 'Very High']
    else:
        suitable_policies = policy_data[policy_data['Interest Rate Category'] == 'High']

    if not suitable_policies.empty:
        suitable_policies = suitable_policies.copy()
        suitable_policies['Potential Return ($)'] = (user_investment * investment_duration) * (suitable_policies['Interest Rate (%)'] / 100)
        recommended_policy = suitable_policies.loc[suitable_policies['Potential Return ($)'].idxmax()]

        st.write("### Recommended Policy Based on Your Investment:")
        st.write(recommended_policy[['Policy Name', 'Policy Type', 'Interest Rate (%)', 'Maturity Period (years)', 'Minimum Investment ($)', 'Potential Return ($)']])

        st.write("### Reasons for Selection:")
        st.write(f"1. *Interest Rate*: The selected policy has an interest rate of {recommended_policy['Interest Rate (%)']}%, higher than the average.")
        st.write(f"2. *Potential Return*: Based on your investment of ${user_investment} over {investment_duration} months, the potential return is ${recommended_policy['Potential Return ($)']:.2f}.")
        st.write(f"3. *Investment Duration*: The maturity period aligns with your investment duration of {investment_duration // 12} years.")
        
        return recommended_policy, suitable_policies
    else:
        st.write("No suitable policies found for your spending category.")
        return None, None

# Visualization
def visualize_policy_comparison(suitable_policies):
    """
    Visualize the potential return of suitable policies as a bar chart.
    """
    if suitable_policies is not None and not suitable_policies.empty:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=suitable_policies, x='Policy Name', y='Potential Return ($)', palette='viridis')
        plt.xticks(rotation=45)
        plt.title("Potential Return Comparison of Suitable Policies")
        st.pyplot(plt)

# Main Function to run the app
if __name__ == "__main__":
    st.title("Policy Suggestion Dashboard")
    st.write("This application suggests investment policies based on your spending and investment preferences.")
    st.write(f"*Spending Model Accuracy*: {acc_spending * 100:.2f}%")
    st.write(f"*Policy Model Accuracy*: {acc_policy * 100:.2f}%")

    # Recommend Policy and Visualize
    recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
    
    if recommended_policy is not None and suitable_policies is not None:
        visualize_policy_comparison(suitable_policies)
