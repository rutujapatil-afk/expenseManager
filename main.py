import os
import streamlit as st
import pandas as pd
import nltk
import joblib

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

# Your other imports (assuming these are correctly structured in the `models` directory)
from models import spam_classifier, policy_suggestion, budgeting_model

# Load data or mock data
transaction_data = pd.read_csv("data/transactions.csv")
balance = transaction_data["amount"].sum()

# Dashboard UI
st.title("Expense Manager Dashboard")

# Display Balance
st.header("Total Balance")
st.write(f"Available Balance: ${balance:.2f}")

# Display Recent Transactions
st.subheader("Recent Transactions")
st.table(transaction_data.tail(5))  # Show last 5 transactions

# Buttons for features
if st.button("Analyze Bank Messages"):
    spam_classifier.display_spam_detector()  # Ensure this method is properly imported from the spam_classifier module

if st.button("Investment Policy Suggestion"):
    policy_suggestion.display_policy_suggestion()  # Ensure this method is properly imported from the policy_suggestion module

if st.button("Budgeting Tool"):
    budgeting_model.display_budgeting_tool()  # Ensure this method is properly imported from the budgeting_model module
