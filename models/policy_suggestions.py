import pandas as pd
import numpy as np
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# Load Datasets
@st.cache_data
def load_data():
    # Load policy and spending data
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

    # Categorize 'Expected ROI' if column exists
    if 'Expected ROI' in policy_data.columns:
        policy_data['ROI Category'] = pd.cut(policy_data['Expected ROI'], bins=[0, 5, 10, 15, np.inf],
                                             labels=['Low', 'Medium', 'High', 'Very High'])
    else:
        st.error("Column 'Expected ROI' is missing from policy data.")
        return None, None

    # Check for required columns and return error if any are missing
    required_columns = ['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']
    missing_columns = [col for col in required_columns if col not in policy_data.columns]
    if missing_columns:
        st.error(f"Missing columns: {', '.join(missing_columns)}")
        return None, None

    return monthly_spending, policy_data

monthly_spending, policy_data = preprocess_data(spending_data, policy_data)

# Train Models
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

# User Input
def get_user_input():
    st.header("Enter Your Investment Details")
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

# Visualization
def visualize_policy_comparison(suitable_policies):
    if suitable_policies is not None and not suitable_policies.empty:
        top_policies = suitable_policies.nlargest(5, 'Potential Return ($)')
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        
        bar_plot = sns.barplot(
            data=top_policies,
            y='Policy Name',
            x='Potential Return ($)',
            palette='viridis',
            edgecolor='black'
        )
        
        plt.title("Top 5 Investment Policies by Potential Return", fontsize=16, weight='bold')
        plt.xlabel("Potential Return ($)", fontsize=14)
        plt.ylabel("Policy Name", fontsize=14)

        for index, value in enumerate(top_policies['Potential Return ($)']):
            bar_plot.text(value, index, f'${value:,.2f}', color='black', va="center")

        st.pyplot(plt)
    else:
        st.write("No suitable policies to visualize.")

def visualize_additional_charts(suitable_policies, policy_data):
    if suitable_policies is not None and not suitable_policies.empty:
        
        st.write("### Distribution of Expected ROI by Policy Type")
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=policy_data, x='Policy Type', y='Expected ROI', palette='coolwarm')
        plt.title("Expected ROI Distribution by Policy Type")
        plt.xlabel("Policy Type")
        plt.ylabel("Expected ROI (%)")
        st.pyplot(plt)

        st.write("### Investment Horizon vs. Potential Return")
        plt.figure(figsize=(10, 6))
        sns.scatterplot(
            data=suitable_policies,
            x='Investment Horizon',
            y='Potential Return ($)',
            hue='Policy Type',
            palette='Set1',
            s=100,
            edgecolor="black"
        )
        plt.title("Investment Horizon vs. Potential Return for Suitable Policies")
        plt.xlabel("Investment Horizon (months)")
        plt.ylabel("Potential Return ($)")
        plt.legend(title="Policy Type", loc="upper left")
        st.pyplot(plt)

        st.write("### Risk Level Distribution Among Top Recommended Policies")
        top_policies_risk = suitable_policies['Risk Level'].value_counts()
        plt.figure(figsize=(7, 7))
        plt.pie(
            top_policies_risk,
            labels=top_policies_risk.index,
            autopct='%1.1f%%',
            startangle=140,
            colors=sns.color_palette("Set2")
        )
        plt.title("Risk Level Distribution of Top Recommended Policies")
        st.pyplot(plt)
    
    else:
        st.write("No suitable policies to visualize additional charts.")

def display_dashboard():
    user_investment, investment_duration = get_user_input()
    
    if user_investment is not None and investment_duration is not None:
        recommended_policy, suitable_policies = recommend_policy(user_investment, investment_duration, policy_data, model_spending)
        
        if recommended_policy is not None:
            visualize_policy_comparison(suitable_policies)
            visualize_additional_charts(suitable_policies, policy_data)

# Run the dashboard
display_dashboard()

