import streamlit as st
from models import spam_classifier, policy_suggestion, budgeting_model
import pandas as pd

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
    spam_classifier.display_spam_detector()

if st.button("Investment Policy Suggestion"):
    policy_suggestion.display_policy_suggestion()

if st.button("Budgeting Assistance"):
    budgeting_model.display_budgeting_model()