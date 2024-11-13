import pandas as pd
import numpy as np
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
import os

def load_data():
    # Load policy and spending data
    policy_data = pd.read_csv("data/insurance_policies_dataset.csv")
    spending_data = pd.read_csv("data/transactions.csv")
    return policy_data, spending_data

def preprocess_data(df):
    # Fill missing values
    df.fillna(df.mean(), inplace=True)

    # Label encoding for categorical features
    label_encoders = {}
    for column in ['Policy Type', 'Risk Level', 'Investment Horizon', 'Liquidity', 
                   'Tax Efficiency', 'Fee Structure', 'Target Audience', 
                   'Investment Goals', 'Tax Advantages']:
        le = LabelEncoder()
        df[column] = le.fit_transform(df[column])
        label_encoders[column] = le

    # Scaling numerical features
    scaler = StandardScaler()
    numerical_columns = ['Expected ROI', 'Historical 1-Year Return', 'Historical 3-Year Return', 
                         'Historical 5-Year Return', 'Volatility', 'Sharpe Ratio', 
                         'Max Drawdown', 'Minimum Investment', 'Maximum Investment', 
                         'Lock-in Period', 'Exit Fees/Withdrawal Penalties']
    df[numerical_columns] = scaler.fit_transform(df[numerical_columns])
    
    return df, scaler, label_encoders

def train_model(X, y):
    # Split data and train the model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def display_investment_policy_recommendation():
    # Load and preprocess data
    df, _ = load_data()
    df, scaler, label_encoders = preprocess_data(df)

    # Separate features and target variable
    X = df.drop(columns=['Policy ID', 'Policy Name'])
    y = df['Expected ROI']

    # Train the model
    model = train_model(X, y)

    st.title('Investment Policy Recommendation System')

    # Get user inputs
    risk_level = st.selectbox("Risk Level", ["Low", "Medium", "High"])
    investment_horizon = st.selectbox("Investment Horizon", ["Short-term", "Medium-term", "Long-term"])
    expected_roi = st.slider("Expected ROI (%)", 5, 20, 10, step=1)
    min_investment = st.number_input("Minimum Investment (INR)", min_value=1000, max_value=10000000, value=50000, step=1000)

    def automate_assumptions(risk_level, investment_horizon, expected_roi, min_investment):
        # Set assumptions based on user inputs
        if risk_level == "Low":
            volatility, max_drawdown, sharpe_ratio = 5, 5, 1.5
        elif risk_level == "Medium":
            volatility, max_drawdown, sharpe_ratio = 10, 10, 1.0
        else:
            volatility, max_drawdown, sharpe_ratio = 15, 20, 0.5

        if investment_horizon == "Short-term":
            liquidity, lock_in_period, exit_fees = 0, 1, 3
        elif investment_horizon == "Medium-term":
            liquidity, lock_in_period, exit_fees = 1, 3, 2
        else:
            liquidity, lock_in_period, exit_fees = 2, 5, 1

        matching_roi = expected_roi
        min_investment_policy = df[df['Minimum Investment'] <= min_investment]
        return matching_roi, volatility, max_drawdown, sharpe_ratio, liquidity, lock_in_period, exit_fees, min_investment_policy

    # Apply assumptions to filter policies
    matching_roi, volatility, max_drawdown, sharpe_ratio, liquidity, lock_in_period, exit_fees, min_investment_policy = automate_assumptions(
        risk_level, investment_horizon, expected_roi, min_investment)

    # Filter policies based on user inputs
    filtered_df = min_investment_policy[(min_investment_policy['Expected ROI'] >= matching_roi - 1) & 
                                        (min_investment_policy['Expected ROI'] <= matching_roi + 1)]

    if st.button("Get Recommendation"):
        if len(filtered_df) > 0:
            # Prepare data for prediction
            X_filtered = filtered_df.drop(columns=['Policy ID', 'Policy Name'])
            X_filtered_scaled = scaler.transform(X_filtered)
            predicted_roi = model.predict(X_filtered_scaled)
            filtered_df['Predicted ROI'] = predicted_roi

            # Select and display top 5 policies
            top_policies = filtered_df[['Policy Name', 'Predicted ROI']].sort_values(by='Predicted ROI', ascending=False).head(5)

            st.subheader("Recommended Policy")
            st.write(f"Policy: {top_policies.iloc[0]['Policy Name']}")

            st.subheader("Top 5 Policies")
            st.write(top_policies)

            # Visualize top 5 policies
            visualize_policy_comparison(top_policies)
        else:
            st.warning("No policies match your criteria.")

def visualize_policy_comparison(top_policies):
    # Improved visualization for top 5 policies
    st.subheader("Top 5 Policy Comparison")

    if top_policies.empty:
        st.warning("No policies available for comparison.")
        return

    import matplotlib.pyplot as plt
    import seaborn as sns

    # Set up the figure for comparison
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Policy Name", y="Predicted ROI", data=top_policies, palette="viridis")
    plt.title("Top 5 Policies Comparison")
    plt.xlabel("Policy Name")
    plt.ylabel("Predicted ROI (%)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Display the chart on the Streamlit app
    st.pyplot(plt)
