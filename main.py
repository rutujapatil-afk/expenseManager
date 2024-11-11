import os
import streamlit as st
import pandas as pd
import nltk
import joblib
from models.spam_classifier import UserAccount  # Import UserAccount from spam_classifier
from models import spam_classifier, policy_suggestions  # Import spam_classifier and policy_suggestions

# Check if NLTK stopwords are available, and download if needed
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Display the current working directory for troubleshooting
st.write("Current working directory:", os.getcwd())

# Define paths for model files
spam_model_path = './models/spam_classifier_model.pkl'
vectorizer_path = './models/tfidf_vectorizer.pkl'

# Check if the model and vectorizer files exist before trying to load
if os.path.exists(spam_model_path) and os.path.exists(vectorizer_path):
    try:
        # Load the models
        spam_model = joblib.load(spam_model_path)
        vectorizer = joblib.load(vectorizer_path)
        st.write("Spam classifier and vectorizer loaded successfully!")
    except Exception as e:
        st.write(f"Error loading models: {e}")
else:
    st.write(f"Model or vectorizer files not found!")
    st.write(f"Spam model path: {spam_model_path}")
    st.write(f"Vectorizer path: {vectorizer_path}")

# Load data
transaction_data = pd.read_csv("data/transactions.csv")
balance = transaction_data["Amount"].sum()

# Dashboard UI
st.title("Expense Manager Dashboard")

# Display Balance
st.header("Total Balance")
st.write(f"Available Balance: ${balance:.2f}")

# Display Recent Transactions
st.subheader("Recent Transactions")
st.table(transaction_data.tail(5))  # Show last 5 transactions

# Create an instance of the UserAccount class
user_account = UserAccount()

# Buttons for features
if st.button("Analyze Bank Messages"):
    spam_classifier.display_spam_detector(user_account)  # Pass the user_account to the function

# Investment Policy Suggestion Button
if st.button("Investment Policy Suggestion"):
    # Request the user to input their monthly investment and investment duration
    st.sidebar.header("User Investment Input")
    monthly_investment = st.sidebar.number_input("Enter your monthly investment amount ($):", min_value=0.0, value=100.0, step=10.0)
    investment_duration = st.sidebar.slider("Enter your investment duration (in months):", min_value=1, max_value=60, value=12)

    # Call the policy suggestion display function with the user input
    policy_suggestions.display_policy_suggestion(monthly_investment, investment_duration)  # Pass the input to the suggestion function
