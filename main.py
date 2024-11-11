import streamlit as st
import pandas as pd
import joblib
from models.spam_classifier import UserAccount
from models import spam_classifier, policy_suggestions
import os
import src.auth as auth  # Importing the authentication module

# Authentication check: Ensure that login state is present
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# Show login/signup screen if not logged in
if not st.session_state.logged_in:
    auth.login_signup()  # Show the login/signup form from auth.py
else:
    # Load the spam model and vectorizer
    spam_model_path = './models/spam_classifier_model.pkl'
    vectorizer_path = './models/tfidf_vectorizer.pkl'
    spam_model, vectorizer = None, None

    if os.path.exists(spam_model_path) and os.path.exists(vectorizer_path):
        spam_model = joblib.load(spam_model_path)
        vectorizer = joblib.load(vectorizer_path)

    # Load transaction data and check for essential columns
    try:
        transaction_data = pd.read_csv("data/transactions.csv")
        if not {"Category", "Amount"}.issubset(transaction_data.columns):
            raise ValueError("CSV file must contain 'Category' and 'Amount' columns.")
    except Exception as e:
        st.error(f"Error loading transaction data: {e}")
        transaction_data = pd.DataFrame(columns=["Category", "Amount"])

    # Calculate balance
    balance = transaction_data["Amount"].sum() if not transaction_data.empty else 0
    user_account = UserAccount(initial_balance=balance)

    # Dashboard Layout
    st.title(f"Welcome, {st.session_state.username}!")  # Greeting the logged-in user

    # Salary Container
    with st.container():
        st.subheader("Salary")
        salary = st.number_input("Enter your monthly salary (₹):", min_value=0.0, step=1000.0)
        st.write(f"Monthly Salary: ₹{salary:,.2f}")

    # Balance Container
    with st.container():
        st.subheader("Total Balance")
        st.write(f"Available Balance: ₹{user_account.balance:,.2f}")

    # Recent Transactions Container
    with st.container():
        st.subheader("Recent Transactions")
        if not transaction_data.empty:
            for idx, row in transaction_data.tail(5).iterrows():
                category = row.get('Category', 'N/A')
                amount = row.get('Amount', 0.0)
                st.write(f"{category.capitalize()}: ₹{amount:,.2f}")
                delete_button = st.button("❌", key=f"delete_{idx}")
                if delete_button:
                    transaction_data = transaction_data.drop(idx)
                    transaction_data.to_csv("data/transactions.csv", index=False)
                    st.experimental_rerun()

    # Add New Transaction Container
    with st.container():
        st.subheader("Add New Transaction")
        with st.form(key="add_transaction_form"):
            category = st.selectbox("Category", ["Credit", "Debit"])
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            submit_button = st.form_submit_button(label="Add Transaction")
        if submit_button:
            new_transaction = pd.DataFrame(
                [{"Category": category, "Amount": amount}],
                index=[len(transaction_data)]
            )
            transaction_data = pd.concat([transaction_data, new_transaction], ignore_index=True)
            transaction_data.to_csv("data/transactions.csv", index=False)
            user_account.credit(amount) if category == "Credit" else user_account.debit(amount)
            st.experimental_rerun()

    # Analyze Bank Messages Container
    with st.container():
        st.subheader("Analyze Bank Messages")
        if st.button("Analyze Bank Messages"):
            spam_classifier.display_spam_detector(user_account)

    # Investment Policy Suggestion Container
    with st.container():
        st.subheader("Investment Policy Suggestion")
        if st.button("Get Investment Policy Suggestion"):
            policy_suggestions.display_policy_suggestion()

    # Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.experimental_rerun()  # Rerun the app to reset to the login page

    # Reset Session Button (Optional: Clears session and reruns app)
    if st.button("Reset Session"):
        st.session_state.clear()  # Clear all session state
        st.experimental_rerun()  # Rerun the app to reset the state
