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
        policy_data['ROI Category'] = pd.cut(policy_data['Expected ROI'],bins=[0, 5, 10, 15, np.inf],labels=['Low', 'Medium', 'High', 'Very High'])
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
        return None, None

    return st.session_state.monthly_investment, st.session_state.investment_duration

# Policy Recommendation
def recommend_policy(user_investment, investment_duration, policy_data, spending_model, label_encoder):
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
        top_policies = suitable_policies.nlargest(3, 'Potential Return ($)')

        st.subheader("Top 3 Recommended Policies:")
        visualize_policy_comparison(top_policies)

        # Select one best policy and print its details
        best_policy = top_policies.iloc[0]

        # Use inverse_transform to get the policy name from encoded 'Policy Type'
        policy_name = label_encoder.inverse_transform([best_policy['Policy Type']])[0]

        st.subheader("Recommended Policy for You:")
        st.write(f"**Policy Type:** {policy_name}")
        st.write(f"**Expected ROI:** {best_policy['Expected ROI']:.2f}%")
        st.write(f"**Investment Horizon:** {best_policy['Investment Horizon']:.1f} years")
        st.write(f"**Minimum Investment:** ${best_policy['Minimum Investment']:.2f}")
        st.write(f"**Potential Return:** ${best_policy['Potential Return ($)']:.2f}")
    else:
        st.write("No suitable policies found for your spending category.")

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
            bar_plot.text(value, index, f'${value:,.2f}', color='black', va="center")

        # Display the plot in Streamlit
        st.pyplot(plt)
    else:
        st.write("No suitable policies to visualize.")

# Visualization Functions
def visualize_monthly_spending_trend(monthly_spending):
    if not monthly_spending.empty:
        monthly_spending['Readable Month'] = pd.to_datetime(monthly_spending['Month'].astype(str) + "01", format='%Y%m%d')
        plt.figure(figsize=(12, 6))
        sns.barplot(data=monthly_spending, x='Readable Month', y='Monthly Expense ($)', palette='coolwarm')
        plt.xticks(rotation=45)
        plt.title("Monthly Spending Trend", fontsize=16, weight='bold')
        plt.xlabel("Month", fontsize=14)
        plt.ylabel("Monthly Expense ($)", fontsize=14)
        st.pyplot(plt)
        
        # Simple Explanation
        st.write("""
            **What this graph shows:**
            This graph displays the total spending over time. The x-axis represents the months, 
            and the y-axis shows how much was spent in each month. The color gradient shows changes 
            in spending, with cooler tones representing lower spending and warmer tones showing higher spending. 
            
            **Key Takeaways:**
            - Look for trends in the graph: are expenses rising, falling, or staying constant?
            - Peaks may indicate months of higher-than-normal expenses, which could be useful to understand 
              and plan for future spending.
        """)

def visualize_spending_categories(monthly_spending):
    spending_category_counts = monthly_spending['Spending Category'].value_counts().sort_values()
    plt.figure(figsize=(10, 6))
    sns.barplot(y=spending_category_counts.index, x=spending_category_counts, palette='viridis')
    plt.title("Spending Category Distribution", fontsize=16, weight='bold')
    plt.xlabel("Count", fontsize=14)
    plt.ylabel("Spending Category", fontsize=14)
    st.pyplot(plt)

    # Simple Explanation
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

def visualize_roi_bar(policy_data):
    plt.figure(figsize=(10, 6))
    avg_roi = policy_data.groupby('ROI Category')['Expected ROI'].mean().reset_index()
    sns.barplot(data=avg_roi, x='ROI Category', y='Expected ROI', palette='Blues')
    plt.title("Average Expected ROI by Policy Category", fontsize=16, weight='bold')
    plt.xlabel("ROI Category", fontsize=14)
    plt.ylabel("Average Expected ROI (%)", fontsize=14)
    st.pyplot(plt)

    # Simple Explanation
    st.write("""
            **What this graph shows:**
            This bar chart displays the average expected ROI (Return on Investment) for each ROI category 
            of the policies. The categories are 'Low', 'Medium', 'High', and 'Very High'. The y-axis shows 
            the average ROI for each category. 

            **Key Takeaways:**
            - Higher categories, such as 'High' and 'Very High', indicate policies with better returns 
              on investment.
            - If you want a policy with a better ROI, look for options in the 'High' or 'Very High' categories. 
    """)


def display_policy_suggestion():
    """
    Display the policy suggestion based on the user input
    """
    st.title("Investment Policy Suggestion")

    # Get user input
    monthly_investment, investment_duration = get_user_input()

    # Wait until the input is submitted
    if st.session_state.get("input_submitted", False):
        if st.button('Analyze'):
            recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
            # Visualizations
            visualize_monthly_spending_trend(monthly_spending)
            visualize_spending_categories(monthly_spending)
            visualize_roi_bar(policy_data)
        else:
            st.write("Please click 'Analyze' after filling out your investment details.")
