import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import joblib

# Step 1: Data Collection
@st.cache_data
def load_data():
    """
    Load the policy and spending data from CSV files.
    """
    try:
        policy_data = pd.read_csv("data/insurance_policies_dataset.csv")
        spending_data = pd.read_csv("data/transactions.csv")
        return policy_data, spending_data
    except FileNotFoundError:
        st.error("Data files not found. Please ensure the data directory and files are correctly set up.")
        return None, None

policy_data, spending_data = load_data()

# Step 2: Data Preprocessing
def preprocess_data(spending_data, policy_data):
    if spending_data is None or policy_data is None:
        st.stop()

    # Clean and preprocess spending data
    spending_data.columns = spending_data.columns.str.strip()
    spending_data['Date'] = pd.to_datetime(spending_data['Date'], errors='coerce')
    spending_data.dropna(subset=['Date'], inplace=True)
    spending_data['Amount'].fillna(spending_data['Amount'].median(), inplace=True)
    spending_data = spending_data[spending_data['Amount'] > 0]

    monthly_spending = spending_data.groupby(spending_data['Date'].dt.to_period("M"))['Amount'].sum().reset_index()
    monthly_spending.rename(columns={'Amount': 'Monthly Expense ($)', 'Date': 'Month'}, inplace=True)
    monthly_spending['Month'] = monthly_spending['Month'].dt.to_timestamp()

    monthly_spending['Spending Category'] = pd.cut(monthly_spending['Monthly Expense ($)'],
                                                   bins=[0, 500, 1500, np.inf],
                                                   labels=['Low', 'Medium', 'High'])

    # Clean and preprocess policy data
    le = LabelEncoder()
    policy_data['Policy Type'] = le.fit_transform(policy_data['Policy Type'])

    if 'Expected ROI' in policy_data.columns:
        policy_data['ROI Category'] = pd.cut(policy_data['Expected ROI'],
                                             bins=[0, 5, 10, 15, np.inf],
                                             labels=['Low', 'Medium', 'High', 'Very High'])
    else:
        st.error("Column 'Expected ROI' is missing from policy data.")
        return None, None

    required_columns = ['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']
    missing_columns = [col for col in required_columns if col not in policy_data.columns]
    if missing_columns:
        st.error(f"Missing columns: {', '.join(missing_columns)}")
        return None, None

    return monthly_spending, policy_data

monthly_spending, policy_data = preprocess_data(spending_data, policy_data)

# Step 3 & 4: Model Selection, Training, and Hyperparameter Tuning
def train_models(monthly_spending, policy_data):
    # Spending Model
    X_spending = monthly_spending[['Month']].apply(lambda x: x.dt.month if x.dtype == 'datetime64[ns]' else x)
    y_spending = monthly_spending['Spending Category']
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_spending, y_spending, test_size=0.2, random_state=42)

    param_grid = {'n_estimators': [50, 100, 200], 'max_depth': [5, 10, 20, None]}
    grid_spending = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=5, scoring='accuracy')
    grid_spending.fit(X_train_s, y_train_s)
    model_spending = grid_spending.best_estimator_
    acc_spending = accuracy_score(y_test_s, model_spending.predict(X_test_s))

    # Policy Model
    X_policy = policy_data[['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']]
    X_policy = pd.get_dummies(X_policy, drop_first=True)
    y_policy = policy_data['ROI Category']
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_policy, y_policy, test_size=0.2, random_state=42)

    grid_policy = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=5, scoring='accuracy')
    grid_policy.fit(X_train_p, y_train_p)
    model_policy = grid_policy.best_estimator_
    acc_policy = accuracy_score(y_test_p, model_policy.predict(X_test_p))

    return model_spending, model_policy, acc_spending, acc_policy

model_spending, model_policy, acc_spending, acc_policy = train_models(monthly_spending, policy_data)

# Save models for deployment
joblib.dump(model_spending, 'models/spending_model.pkl')
joblib.dump(model_policy, 'models/policy_model.pkl')

# Step 5: Evaluation
def evaluate_model(model, X_test, y_test, name):
    st.write(f"### Evaluation Report for {name} Model")
    predictions = model.predict(X_test)
    st.text(f"Accuracy: {accuracy_score(y_test, predictions):.2f}")
    st.text("Classification Report:")
    st.text(classification_report(y_test, predictions))
    st.text("Confusion Matrix:")
    st.write(pd.DataFrame(confusion_matrix(y_test, predictions)))

# Evaluate models
evaluate_model(model_spending, monthly_spending[['Month']], monthly_spending['Spending Category'], "Spending")
evaluate_model(model_policy, policy_data[['Policy Type', 'Expected ROI', 'Investment Horizon', 'Minimum Investment']],
               policy_data['ROI Category'], "Policy")

# Step 6: Predictions & Deployment
def predict_and_recommend(user_investment, investment_duration):
    st.header("Investment Policy Recommendation")
    user_spending = np.array([[user_investment]])
    predicted_category = model_spending.predict(user_spending)[0]

    st.write(f"Predicted Spending Category: {predicted_category}")
    if predicted_category == 'Low':
        suitable_policies = policy_data[policy_data['ROI Category'] == 'Low']
    elif predicted_category == 'Medium':
        suitable_policies = policy_data[policy_data['ROI Category'] != 'Very High']
    else:
        suitable_policies = policy_data[policy_data['ROI Category'] == 'High']

    if not suitable_policies.empty:
        suitable_policies['Potential Return ($)'] = (
            user_investment * investment_duration * suitable_policies['Expected ROI'] / 100
        )
        top_policy = suitable_policies.sort_values('Potential Return ($)', ascending=False).iloc[0]
        st.write("### Recommended Policy:")
        st.write(top_policy)
    else:
        st.error("No suitable policies found for your predicted category.")
