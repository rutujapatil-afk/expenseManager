import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

# LabelEncoder for policy data
le = LabelEncoder()

# Load Datasets with @st.cache_data for better performance
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

    # Group spending data by month and calculate total expense
    monthly_spending = spending_data.groupby(spending_data['Date'].dt.to_period("M"))['Amount'].sum().reset_index()
    monthly_spending.rename(columns={'Amount': 'Monthly Expense ($)', 'Date': 'Month'}, inplace=True)

    monthly_spending['Month'] = monthly_spending['Month'].dt.year * 100 + monthly_spending['Month'].dt.month
    monthly_spending['Monthly Expense ($)'] = pd.to_numeric(monthly_spending['Monthly Expense ($)'], errors='coerce')
    monthly_spending = monthly_spending.dropna(subset=['Monthly Expense ($)'])

    # Categorize spending into low, medium, high categories
    monthly_spending['Spending Category'] = pd.cut(monthly_spending['Monthly Expense ($)'],
                                                    bins=[0, 500, 1500, np.inf],
                                                    labels=['Low', 'Medium', 'High'])

    # Preprocess policy data
    if 'Policy Type' in policy_data.columns:
        policy_data['Policy Type'] = le.fit_transform(policy_data['Policy Type'])
    else:
        st.error("Column 'Policy Type' is missing from policy data.")
        return None, None, None

    if 'Expected ROI' in policy_data.columns:
        policy_data['ROI Category'] = pd.cut(policy_data['Expected ROI'], bins=[0, 5, 10, 15, np.inf], labels=['Low', 'Medium', 'High', 'Very High'])
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
    # Spending Prediction Model
    X_spending = monthly_spending[['Month']]
    y_spending = monthly_spending['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)
    model_spending = RandomForestClassifier(random_state=42)
    model_spending.fit(X_train_s, y_train_s)
    acc_spending = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    # Policy Prediction Model
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

def visualize_policy_comparison(top_policies):
    if not top_policies.empty:
        plt.figure(figsize=(10, 6))
        categories = top_policies['Policy Type'].astype(str)
        x = np.arange(len(categories))
        width = 0.3

        plt.bar(x - width, top_policies['Expected ROI'], width, label='Expected ROI (%)', color='blue')
        plt.bar(x, top_policies['Investment Horizon'], width, label='Investment Horizon (years)', color='green')
        plt.bar(x + width, top_policies['Potential Return ($)'], width, label='Potential Return ($)', color='purple')

        plt.xticks(x, categories, rotation=45)
        plt.title("Top Policies Comparison", fontsize=16, weight='bold')
        plt.xlabel("Policy Type", fontsize=14)
        plt.ylabel("Values", fontsize=14)
        plt.legend()
        st.pyplot(plt)

        st.write(""" 
            **What this graph shows:**
            This bar chart compares the top 3 policies based on their Expected ROI, Investment Horizon, 
            and Potential Return. Each policy is represented by three bars: one for ROI, one for Horizon, 
            and one for Potential Return.

            **Key Takeaways:**
            - Policies with high ROI and low investment horizons are ideal for short-term goals.
            - Policies with high potential returns are attractive for long-term investments.
        """)

# Get User Input Function
def get_user_input():
    """
    Collects and returns user input from the Streamlit sidebar.
    """
    st.sidebar.header("User Input")
    policy_category = st.sidebar.selectbox("Select Policy Category", ["High", "Medium", "Low"])
    investment_horizon = st.sidebar.slider("Select Investment Horizon (years)", min_value=1, max_value=30, step=1, value=5)
    policy_type = st.sidebar.selectbox("Select Policy Type", policy_data['Policy Type'].unique())

    return policy_category, investment_horizon, policy_type

def recommend_policy(policy_category, investment_horizon, policy_type):
    """
    Recommends a policy based on user input.
    """
    filtered_policies = policy_data[(policy_data['ROI Category'] == policy_category) & 
                                    (policy_data['Investment Horizon'] <= investment_horizon) &
                                    (policy_data['Policy Type'] == le.transform([policy_type])[0])]
    top_policy = filtered_policies.nlargest(1, 'Expected ROI')
    return top_policy

# Streamlit User Interface
def main():
    st.title("Policy Recommendations and Spending Analysis")

    # Get user inputs
    policy_category, investment_horizon, policy_type = get_user_input()

    # Display visualizations
    visualize_monthly_spending_trend(monthly_spending)
    visualize_spending_categories(monthly_spending)
    visualize_roi_bar(policy_data)

    # Show top policies based on selected category and horizon
    top_policies = recommend_policy(policy_category, investment_horizon, policy_type)
    visualize_policy_comparison(top_policies)

    # Add the Model Efficiency button
    if st.button("Show Model Efficiency"):
        # Model Efficiency Metrics
        st.subheader("Model Efficiency")

        # Spending Prediction Accuracy
        st.write(f"**Spending Prediction Accuracy:** {efficiency_metrics['Spending Prediction Accuracy']:.2f}%")

        # Policy Prediction Accuracy
        st.write(f"**Policy Prediction Accuracy:** {efficiency_metrics['Policy Prediction Accuracy']:.2f}%")

        # Classification Report for Policies
        policy_classification_report = classification_report(y_test_p, model_policy.predict(X_test_p), output_dict=True)

        st.write("**Classification Report for Policies:**")
        # Convert classification report to DataFrame for better display
        report_df = pd.DataFrame(policy_classification_report).transpose()
        st.dataframe(report_df)

        # Optional: Display as raw text if desired
        st.text(classification_report(y_test_p, model_policy.predict(X_test_p)))

if __name__ == "__main__":
    main()
