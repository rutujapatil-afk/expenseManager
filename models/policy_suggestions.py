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
        st.error(f"Error loading data: {e}")
        return None, None

policy_data, spending_data = load_data()

# Data Preprocessing with Debugging
def preprocess_data(spending_data, policy_data):
    if spending_data is None or policy_data is None:
        st.error("Spending or policy data is missing.")
        return None, None
    
    spending_data.columns = spending_data.columns.str.strip()
    spending_data['Date'] = pd.to_datetime(spending_data['Date'], errors='coerce')
    spending_data.dropna(subset=['Date', 'Amount'], inplace=True)

    monthly_spending = spending_data.groupby(spending_data['Date'].dt.to_period("M"))['Amount'].sum().reset_index()
    monthly_spending.rename(columns={'Amount': 'Monthly Expense ($)', 'Date': 'Month'}, inplace=True)
    monthly_spending['Month'] = monthly_spending['Month'].dt.to_timestamp().dt.year * 100 + monthly_spending['Month'].dt.month

    # Categorize monthly spending
    monthly_spending['Spending Category'] = pd.cut(monthly_spending['Monthly Expense ($)'],
                                                    bins=[0, 500, 1500, np.inf],
                                                    labels=['Low', 'Medium', 'High'])

    # Encoding policy types
    le = LabelEncoder()
    policy_data['Policy Type'] = le.fit_transform(policy_data['Policy Type'])

    # Check if 'Expected ROI' column exists and use it for categorization
    if 'Expected ROI' in policy_data.columns:
        policy_data['ROI Category'] = pd.cut(policy_data['Expected ROI'], bins=[0, 5, 10, 15, np.inf], labels=['Low', 'Medium', 'High', 'Very High'])
    else:
        st.error("Column 'Expected ROI' is missing from policy data.")
        return None, None

    # Check for required columns and adjust if needed
    required_columns = ['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']
    missing_columns = [col for col in required_columns if col not in policy_data.columns]
    if missing_columns:
        st.error(f"Missing columns: {', '.join(missing_columns)}")
        return None, None

    st.write(f"Monthly Spending Data Shape: {monthly_spending.shape}")
    st.write(f"Policy Data Shape: {policy_data.shape}")
    
    return monthly_spending, policy_data

monthly_spending, policy_data = preprocess_data(spending_data, policy_data)

# Train the models with Debugging
def train_models(monthly_spending, policy_data):
    # Train spending model
    X_spending = monthly_spending[['Month']]
    y_spending = monthly_spending['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)
    model_spending = RandomForestClassifier(random_state=42)
    model_spending.fit(X_train_s, y_train_s)
    acc_spending = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    # Train policy model
    X_policy = policy_data[['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']]
    X_policy = pd.get_dummies(X_policy, drop_first=True)
    y_policy = policy_data['ROI Category']
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_policy, y_policy, test_size=0.2, random_state=42)
    model_policy = RandomForestClassifier(random_state=42)
    model_policy.fit(X_train_p, y_train_p)
    acc_policy = accuracy_score(y_test_p, model_policy.predict(X_test_p))

    st.write(f"Spending Model Accuracy: {acc_spending * 100:.2f}%")
    st.write(f"Policy Model Accuracy: {acc_policy * 100:.2f}%")

    return model_spending, model_policy, acc_spending, acc_policy

model_spending, model_policy, acc_spending, acc_policy = train_models(monthly_spending, policy_data)

# User Input for investment with Debugging
def get_user_input():
    """
    Get the user input for monthly investment and investment duration.
    """
    st.header("Enter Your Investment Details")

    # Creating a form to input investment amount and duration
    with st.form(key='investment_form'):
        monthly_investment = st.number_input("Enter your monthly investment amount ($):", min_value=0.0, value=100.0, step=10.0)
        investment_duration = st.number_input("Enter your investment duration (in months):", min_value=1, max_value=600, value=12)

        submit_button = st.form_submit_button(label='Submit Investment')
        
        if submit_button:
            st.session_state.monthly_investment = monthly_investment
            st.session_state.investment_duration = investment_duration
            st.session_state.input_submitted = True
            st.success("Investment details submitted successfully!")

    if 'monthly_investment' not in st.session_state or 'investment_duration' not in st.session_state:
        st.write("Investment data not submitted yet.")
        return None, None

    st.write(f"User Input - Monthly Investment: ${st.session_state.monthly_investment}, Duration: {st.session_state.investment_duration} months")
    return st.session_state.monthly_investment, st.session_state.investment_duration

# Policy Recommendation
def recommend_policy(user_investment, investment_duration, policy_data, spending_model):
    if user_investment <= 0 or investment_duration <= 0:
        st.error("Please enter valid positive values for both monthly investment and investment duration.")
        return None, None
    
    user_spending = np.array([[user_investment]])
    predicted_category = spending_model.predict(user_spending)[0]
    st.write(f"Predicted Spending Category: {predicted_category}")

    if predicted_category == 'Low':
        suitable_policies = policy_data[policy_data['ROI Category'] == 'Low']
    elif predicted_category == 'Medium':
        suitable_policies = policy_data[policy_data['ROI Category'] != 'Very High']
    else:
        suitable_policies = policy_data[policy_data['ROI Category'] == 'High']

    if suitable_policies.empty:
        st.write("No suitable policies found for your spending category.")
    else:
        st.write(f"Found {len(suitable_policies)} suitable policies.")

    if not suitable_policies.empty:
        suitable_policies = suitable_policies.copy()
        suitable_policies['Potential Return ($)'] = (user_investment * investment_duration) * (suitable_policies['Expected ROI'] / 100)
        recommended_policy = suitable_policies.loc[suitable_policies['Potential Return ($)'].idxmax()]

        st.write("### Recommended Policy Based on Your Investment:")
        st.write(recommended_policy[['Policy Name', 'Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment', 'Potential Return ($)']])

        st.write("### Reasons for Selection:")
        st.write(f"1. *Expected ROI*: The selected policy has an expected ROI of {recommended_policy['Expected ROI']}%, which aligns with your goals.")
        st.write(f"2. *Potential Return*: Based on your investment of ${user_investment} over {investment_duration} months, the potential return is ${recommended_policy['Potential Return ($)']:.2f}.")
        st.write(f"3. *Investment Duration*: The maturity period aligns with your investment duration of {investment_duration // 12} years.")
        
        return recommended_policy, suitable_policies
    else:
        st.write("No suitable policies found for your spending category.")
        return None, None

# Visualization
def visualize_policy_comparison(suitable_policies):
    if suitable_policies is not None and not suitable_policies.empty:
        # Filter to show only the top 5 policies based on Potential Return
        top_policies = suitable_policies.nlargest(5, 'Potential Return ($)')

        # Set up the plot
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        
        # Plot horizontal bar chart for top 5 policies
        bar_plot = sns.barplot(
            data=top_policies,
            y='Policy Name',
            x='Potential Return ($)',
            palette='viridis',
            edgecolor='black'
        )
        
        # Adding labels and customizing the plot
        plt.title("Top 5 Investment Policies by Potential Return", fontsize=16, weight='bold')
        plt.xlabel("Potential Return ($)", fontsize=14)
        plt.ylabel("Policy Name", fontsize=14)

        # Add value labels to each bar
        for index, value in enumerate(top_policies['Potential Return ($)']):
            bar_plot.text(value, index, f'${value:,.2f}', color='black', ha="left", va="center")

        st.pyplot(plt)

# Main Function
def main():
    if policy_data is None or spending_data is None:
        st.error("Data could not be loaded. Please check the dataset.")
        return
    
    # Get user input for investment
    user_investment, investment_duration = get_user_input()
    if user_investment is None or investment_duration is None:
        return

    # Get recommendations based on user input
    recommended_policy, suitable_policies = recommend_policy(user_investment, investment_duration, policy_data, model_spending)

    # Visualize policy comparison
    visualize_policy_comparison(suitable_policies)

if __name__ == "__main__":
    main()
