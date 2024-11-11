import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from models.spam_classifier import UserAccount
from models import spam_classifier, policy_suggestions

# Load Data
transaction_data = pd.read_csv("data/transactions.csv")
balance = transaction_data["Amount"].sum()
default_salary = 70000  # Default salary in INR

# Dashboard UI Design with Containers
st.set_page_config(page_title="Expense Manager Dashboard", layout="wide")
st.title("Expense Manager Dashboard")

# Total Balance Container
with st.container():
    st.header("💰 Total Balance")
    st.write(f"Available Balance: ₹{balance:,.2f}")

# Salary Container
with st.container():
    st.header("💼 Monthly Salary")
    st.write(f"Current Salary: ₹{default_salary:,}")
    if st.button("Edit Salary"):
        new_salary = st.number_input("Enter your new salary", min_value=0.0, step=500.0)
        default_salary = new_salary

# Recent Transactions Container
with st.container():
    st.header("🧾 Recent Transactions")
    if not transaction_data.empty:
        for idx, row in transaction_data.iterrows():
            st.write(f"{row['Date']}: ₹{row['Amount']} - {row['Description']}")
            delete_btn = st.button(f"❌ Remove", key=f"delete_{idx}")
            if delete_btn:
                transaction_data = transaction_data.drop(idx)
                transaction_data.to_csv("data/transactions.csv", index=False)
                st.experimental_rerun()

# Add Transaction Button
with st.container():
    st.header("➕ Add a New Transaction")
    with st.form(key="add_transaction"):
        transaction_date = st.date_input("Transaction Date", value=datetime.now())
        transaction_amount = st.number_input("Amount (₹)", min_value=0.0)
        transaction_desc = st.text_input("Description")
        submit_btn = st.form_submit_button("Add Transaction")
        if submit_btn:
            new_transaction = pd.DataFrame({
                "Date": [transaction_date.strftime("%Y-%m-%d")],
                "Amount": [transaction_amount],
                "Description": [transaction_desc]
            })
            transaction_data = pd.concat([transaction_data, new_transaction], ignore_index=True)
            transaction_data.to_csv("data/transactions.csv", index=False)
            st.success("Transaction added successfully!")
            st.experimental_rerun()

# Analyze Bank Messages Container
with st.container():
    st.header("🔍 Analyze Bank Messages")
    if st.button("Analyze"):
        spam_classifier.display_spam_detector(UserAccount(balance))

# Investment Policy Suggestion Container
with st.container():
    st.header("📊 Investment Policy Suggestion")
    if st.button("Suggest Investment Policies"):
        policy_suggestions.display_policy_suggestion()

# CSS for Background Image and Styling
st.markdown("""
    <style>
        body {
            background: url('https://www.example.com/path/to/your/background.jpg') no-repeat center center fixed;
            background-size: cover;
            color: #333333;
        }
        .stContainer {
            background-color: rgba(255, 255, 255, 0.8);
            padding: 2rem;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Hide debugging text
if "spam_classifier" not in st.session_state:
    st.session_state["spam_classifier"] = True  # Load once
