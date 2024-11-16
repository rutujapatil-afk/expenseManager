import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib

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
        st.error(f"Error loading files: {e}")
        return None, None

policy_data, spending_data = load_data()

# Data Preprocessing
def preprocess_data(spending_data, policy_data):
    if spending_data is None or policy_data is None:
        return None, None, None
    
    # Clean spending data
    spending_data.columns = spending_data.columns.str.strip()
    spending_data['Date'] = pd.to_datetime(spending_data['Date'])
    
    # Aggregate spending by month
    monthly_spending = spending_data.groupby(spending_data['Date'].dt.to_period("M"))['Amount'].sum().reset_index()
    monthly_spending.rename(columns={'Amount': 'Monthly Expense ($)', 'Date': 'Month'}, inplace=True)
    
    # Convert month to numerical format and clean data
    monthly_spending['Month'] = monthly_spending['Month'].dt.year * 100 + monthly_spending['Month'].dt.month
    monthly_spending['Monthly Expense ($)'] = pd.to_numeric(monthly_spending['Monthly Expense ($)'], errors='coerce')
    monthly_spending = monthly_spending.dropna(subset=['Monthly Expense ($)'])
    
    # Categorize spending
    monthly_spending['Spending Category'] = pd.cut(
        monthly_spending['Monthly Expense ($)'],
        bins=[0, 500, 1500, np.inf],
        labels=['Low', 'Medium', 'High']
    )

    # Label encode policy types and categorize ROI
    le = LabelEncoder()
    policy_data['Policy Type'] = le.fit_transform(policy_data['Policy Type'])
    
    if 'Expected ROI' in policy_data.columns:
        policy_data['ROI Category'] = pd.cut(
            policy_data['Expected ROI'],
            bins=[0, 5, 10, 15, np.inf],
            labels=['Low', 'Medium', 'High', 'Very High']
        )
    else:
        st.error("Column 'Expected ROI' is missing from policy data.")
        return None, None, None

    if 'Investment Horizon' in policy_data.columns:
        policy_data['Investment Horizon'] = policy_data['Investment Horizon'].str.extract(r'(\d+)', expand=False).astype(float)
    else:
        st.error("Column 'Investment Horizon' is missing from policy data.")
        return None, None, None

    return monthly_spending, policy_data, le

monthly_spending, policy_data, le = preprocess_data(spending_data, policy_data)

# Train Models and Evaluate Efficiency
def train_models(monthly_spending, policy_data):
    if monthly_spending is None or policy_data is None:
        return None, None, None, None, None
    
    # Train spending prediction model
    X_spending = monthly_spending[['Month']]
    y_spending = monthly_spending['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)
    model_spending = RandomForestClassifier(random_state=42)
    model_spending.fit(X_train_s, y_train_s)
    acc_spending = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    # Train policy prediction model
    X_policy = policy_data[['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']]
    X_policy = pd.get_dummies(X_policy, drop_first=True)
    y_policy = policy_data['ROI Category']
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_policy, y_policy, test_size=0.2, random_state=42)
    model_policy = RandomForestClassifier(random_state=42)
    model_policy.fit(X_train_p, y_train_p)
    acc_policy = accuracy_score(y_test_p, model_policy.predict(X_test_p))

    efficiency_metrics = {
        "Spending Prediction Accuracy": acc_spending * 100,
        "Policy Prediction Accuracy": acc_policy * 100,
    }

    return model_spending, model_policy, efficiency_metrics, X_test_p, y_test_p

model_spending, model_policy, efficiency_metrics, X_test_p, y_test_p = train_models(monthly_spending, policy_data)

# User Login Page
def login():
    """
    Display login page.
    """
    st.title("Login to Expense Manager")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    # Check login credentials (This is just a sample; use proper authentication in production)
    if login_button:
        if username == "user" and password == "password":  # Replace with real authentication
            st.session_state.logged_in = True
            st.success("Login successful! Redirecting to dashboard...")
            return True
        else:
            st.error("Invalid username or password.")
    return False

# Main Dashboard
def dashboard():
    """
    Display the main dashboard with options like Profile, SMS Classifier, Policy Suggestions, etc.
    """
    st.title("Expense Manager Dashboard")
    option = st.selectbox("Choose an option", ["Profile", "SMS Classifier", "Policy Suggestions"])

    if option == "Profile":
        st.write("User Profile Page")
    elif option == "SMS Classifier":
        st.write("SMS Classifier Page")
    elif option == "Policy Suggestions":
        st.write("Running Policy Suggestions Model...")
        user_investment, investment_duration = get_user_input()
        if user_investment and investment_duration:
            recommend_policy(user_investment, investment_duration, policy_data, model_spending, le)

# User Input for Investment
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

# Policy Recommendations
def recommend_policy(user_investment, investment_duration, policy_data, model_spending, le):
    # Using the model to recommend a policy
    recommended_policies = policy_data[
        (policy_data['Expected ROI'] >= user_investment) &
        (policy_data['Investment Horizon'] >= investment_duration)
    ]
    if len(recommended_policies) > 0:
        st.write("Recommended Policies Based on Your Investment Preferences:")
        st.write(recommended_policies)
    else:
        st.write("No policies found matching your criteria.")

# Main Function
def main():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        if not login():
            return  # Don't continue to the dashboard if not logged in
    dashboard()

# Run the app
main()
