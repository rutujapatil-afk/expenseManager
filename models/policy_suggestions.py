import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

# 1. Load Data
@st.cache_data
def load_data():
    try:
        expense_data = pd.read_csv("data/expenses.csv")
        policy_data = pd.read_csv("data/policies.csv")
    except FileNotFoundError as e:
        st.error(f"Error loading data: {e}")
        return None, None
    return expense_data, policy_data

expense_data, policy_data = load_data()

# 2. Data Preprocessing
def preprocess_data(expense_data, policy_data):
    if expense_data is None or policy_data is None:
        return None, None, None
    
    # Clean Expense Data
    expense_data['Date'] = pd.to_datetime(expense_data['Date'], errors='coerce')
    expense_data.dropna(subset=['Date', 'Amount'], inplace=True)
    expense_data['Amount'] = pd.to_numeric(expense_data['Amount'], errors='coerce')
    
    monthly_expenses = expense_data.groupby(expense_data['Date'].dt.to_period("M"))['Amount'].sum().reset_index()
    monthly_expenses.rename(columns={'Amount': 'Monthly Expense ($)', 'Date': 'Month'}, inplace=True)
    monthly_expenses['Spending Category'] = pd.cut(
        monthly_expenses['Monthly Expense ($)'],
        bins=[0, 500, 1500, np.inf],
        labels=['Low', 'Medium', 'High']
    )
    
    # Clean Policy Data
    le = LabelEncoder()
    policy_data['Policy Type'] = le.fit_transform(policy_data['Policy Type'])
    policy_data['ROI Category'] = pd.cut(
        policy_data['Expected ROI'], 
        bins=[0, 5, 10, 15, np.inf], 
        labels=['Low', 'Medium', 'High', 'Very High']
    )
    policy_data['Investment Horizon'] = policy_data['Investment Horizon'].str.extract(r'(\d+)').astype(float)

    return monthly_expenses, policy_data, le

monthly_expenses, policy_data, label_encoder = preprocess_data(expense_data, policy_data)

# 3. Train Models
def train_models(monthly_expenses, policy_data):
    if monthly_expenses is None or policy_data is None:
        return None, None, None
    
    # Spending Prediction Model
    X_spending = monthly_expenses[['Month']]
    y_spending = monthly_expenses['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)
    model_spending = RandomForestClassifier(random_state=42)
    model_spending.fit(X_train_s, y_train_s)
    spending_accuracy = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    # Policy Prediction Model
    X_policy = pd.get_dummies(policy_data[['Policy Type', 'Expected ROI', 'Investment Horizon']], drop_first=True)
    y_policy = policy_data['ROI Category']
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_policy, y_policy, test_size=0.2, random_state=42)
    model_policy = RandomForestClassifier(random_state=42)
    model_policy.fit(X_train_p, y_train_p)
    policy_accuracy = accuracy_score(y_test_p, model_policy.predict(X_test_p))

    efficiency_metrics = {
        "Spending Prediction Accuracy": spending_accuracy * 100,
        "Policy Prediction Accuracy": policy_accuracy * 100,
    }

    return model_spending, model_policy, efficiency_metrics

model_spending, model_policy, efficiency_metrics = train_models(monthly_expenses, policy_data)

# 4. Visualizations
def visualize_spending_trends(data):
    plt.figure(figsize=(10, 5))
    sns.barplot(data=data, x='Month', y='Monthly Expense ($)', palette='coolwarm')
    plt.title("Monthly Spending Trends", fontsize=14, weight='bold')
    plt.xticks(rotation=45)
    st.pyplot(plt)

def visualize_policy_roi(policy_data):
    plt.figure(figsize=(10, 5))
    avg_roi = policy_data.groupby('ROI Category')['Expected ROI'].mean().reset_index()
    sns.barplot(data=avg_roi, x='ROI Category', y='Expected ROI', palette='viridis')
    plt.title("Policy ROI by Category", fontsize=14, weight='bold')
    st.pyplot(plt)

# 5. Recommend Policies
def recommend_policy(user_investment, policy_data):
    if policy_data is not None:
        filtered_policies = policy_data[policy_data['Minimum Investment'] <= user_investment]
        top_policies = filtered_policies.nlargest(3, 'Expected ROI')
        st.write("Top 3 Policies for You:")
        st.table(top_policies)

# Main Application
def main():
    st.title("Expense and Policy Manager")
    
    if expense_data is not None:
        visualize_spending_trends(monthly_expenses)
    
    if policy_data is not None:
        visualize_policy_roi(policy_data)

    st.subheader("Get Policy Recommendations")
    investment = st.number_input("Enter your investment amount ($):", min_value=0.0, value=100.0)
    recommend_policy(investment, policy_data)

    if st.button("Show Efficiency Metrics"):
        st.write(efficiency_metrics)

main()
