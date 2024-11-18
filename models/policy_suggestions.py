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
    spending_data.columns = spending_data.columns.str.strip()
    spending_data['Date'] = pd.to_datetime(spending_data['Date'])
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

    return monthly_spending, policy_data

monthly_spending, policy_data = preprocess_data(spending_data, policy_data)

# Train the models
def train_models(monthly_spending, policy_data):
    X_spending = monthly_spending[['Month']]
    y_spending = monthly_spending['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)
    model_spending = RandomForestClassifier(random_state=42)
    model_spending.fit(X_train_s, y_train_s)
    acc_spending = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    X_policy = policy_data[['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']]
    X_policy = pd.get_dummies(X_policy, drop_first=True)
    y_policy = policy_data['ROI Category']
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_policy, y_policy, test_size=0.2, random_state=42)
    model_policy = RandomForestClassifier(random_state=42)
    model_policy.fit(X_train_p, y_train_p)
    acc_policy = accuracy_score(y_test_p, model_policy.predict(X_test_p))

    return model_spending, model_policy, acc_spending, acc_policy

model_spending, model_policy, acc_spending, acc_policy = train_models(monthly_spending, policy_data)

# User Input for investment
def get_user_input(form_key="investment_form"):
    """
    Get the user input for monthly investment and investment duration.
    """
    st.header("Enter Your Investment Details")

    # Creating a form to input investment amount and duration with dynamic keys
    with st.form(key=form_key):
        monthly_investment = st.number_input("Enter your monthly investment amount ($):", min_value=0.0, value=100.0, step=10.0)
        investment_duration = st.number_input("Enter your investment duration (in months):", min_value=1, max_value=600, value=12)

        submit_button = st.form_submit_button(label='Submit Investment')
        
        if submit_button:
            st.session_state.monthly_investment = monthly_investment
            st.session_state.investment_duration = investment_duration
            st.session_state.input_submitted = True
            st.success("Investment details submitted successfully!")

    if 'monthly_investment' not in st.session_state or 'investment_duration' not in st.session_state:
        return None, None

    return st.session_state.monthly_investment, st.session_state.investment_duration

# Policy Recommendation
def recommend_policy(user_investment, investment_duration, policy_data, spending_model):
    user_spending = np.array([[user_investment]])
    predicted_category = spending_model.predict(user_spending)[0]
    st.write(f"Predicted Spending Category: {predicted_category}")

    if predicted_category == 'Low':
        suitable_policies = policy_data[policy_data['ROI Category'] == 'Low']
    elif predicted_category == 'Medium':
        suitable_policies = policy_data[policy_data['ROI Category'] != 'Very High']
    else:
        suitable_policies = policy_data[policy_data['ROI Category'] == 'High']

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

# Visualization for Top Policies
def visualize_policy_comparison(top_policies):
    if not top_policies.empty:
        top_policies = top_policies.nlargest(3, 'Potential Return ($)')
        plt.figure(figsize=(8, 6))
        categories = top_policies['Policy Name']
        x = np.arange(len(categories))
        width = 0.2

        bars1 = plt.bar(x - width, top_policies['Expected ROI'], width, label='Expected ROI (%)', color='#1f77b4', edgecolor='black')
        bars2 = plt.bar(x, top_policies['Investment Horizon'], width, label='Investment Horizon (years)', color='#2ca02c', edgecolor='black')
        bars3 = plt.bar(x + width, top_policies['Potential Return ($)'], width, label='Potential Return ($)', color='#d62728', edgecolor='black')

        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2, height + 0.05, f"{height:.1f}", ha='center', fontsize=9)

        plt.xticks(x, categories, rotation=20, ha='right', fontsize=10)
        plt.title("Top 3 Policies Comparison", fontsize=14, weight='bold')
        plt.xlabel("Policy Name", fontsize=12)
        plt.ylabel("Values", fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        plt.legend(loc='upper left', fontsize=10)
        plt.tight_layout()
        st.pyplot(plt)

# Visualization for Spending Categories
def visualize_spending_categories(monthly_spending):
    spending_category_counts = monthly_spending['Spending Category'].value_counts().sort_values()
    plt.figure(figsize=(10, 6))
    sns.barplot(y=spending_category_counts.index, x=spending_category_counts, palette='viridis')
    plt.title("Spending Category Distribution", fontsize=16, weight='bold')
    plt.xlabel("Count", fontsize=14)
    plt.ylabel("Spending Category", fontsize=14)
    st.pyplot(plt)

    st.write("""
            **What this graph shows:**
            This graph breaks down your monthly expenses into different categories: Low, Medium, and High. 
            Each bar represents how many months fall into each category, indicating the frequency of 
            that spending level. 
            
            **Key Takeaways:**
            - If most of your expenses fall into the 'Medium' category, this suggests that your spending 
              is generally moderate.
            - If you want to save, aim to bring down the frequency of 'High' spending months.
    """)

# Additional Visualizations
def visualize_monthly_spending_trend(monthly_spending):
    plt.figure(figsize=(10, 6))
    sns.barplot(x=monthly_spending['Month'].astype(str), y=monthly_spending['Monthly Expense ($)'], palette='coolwarm')
    plt.title("Monthly Spending Trend", fontsize=16, weight='bold')
    plt.xlabel("Month", fontsize=14)
    plt.ylabel("Total Spending ($)", fontsize=14)
    plt.xticks(rotation=45)
    st.pyplot(plt)

def visualize_avg_roi_by_policy_category(policy_data):
    avg_roi_by_category = policy_data.groupby('ROI Category')['Expected ROI'].mean().reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='ROI Category', y='Expected ROI', data=avg_roi_by_category, palette='muted')
    plt.title("Average Expected ROI by Policy Category", fontsize=16, weight='bold')
    plt.xlabel("Policy Category", fontsize=14)
    plt.ylabel("Average Expected ROI (%)", fontsize=14)
    st.pyplot(plt)

# Main Streamlit App Interface
def display_policy_suggestion():
    st.title("Investment Policy Suggestion")

    monthly_investment, investment_duration = get_user_input()

    if st.session_state.get("input_submitted", False):
        if st.button('Analyze'):
            recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
            if recommended_policy is not None and suitable_policies is not None:
                visualize_policy_comparison(suitable_policies)
                visualize_spending_categories(monthly_spending)
                visualize_monthly_spending_trend(monthly_spending)
                visualize_avg_roi_by_policy_category(policy_data)

if __name__ == "__main__":
    display_policy_suggestion()
