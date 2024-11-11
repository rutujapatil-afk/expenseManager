import streamlit as st
import pandas as pd
import joblib
from models.spam_classifier import UserAccount
from models import spam_classifier, policy_suggestions

# Load the spam model and vectorizer
spam_model_path = './models/spam_classifier_model.pkl'
vectorizer_path = './models/tfidf_vectorizer.pkl'
spam_model, vectorizer = None, None

if joblib.os.path.exists(spam_model_path) and joblib.os.path.exists(vectorizer_path):
    spam_model = joblib.load(spam_model_path)
    vectorizer = joblib.load(vectorizer_path)

# Load transaction data
transaction_data = pd.read_csv("data/transactions.csv")
balance = transaction_data["Amount"].sum()
user_account = UserAccount(initial_balance=balance)

# Dashboard Layout
st.title("Expense Manager Dashboard")

# Balance Container
with st.container():
    st.subheader("Total Balance")
    st.write(f"Available Balance: ₹{user_account.balance:,.2f}")

# Salary Container
with st.container():
    st.subheader("Salary")
    salary = 70000  # Default salary; you can make this editable if needed
    st.write(f"Monthly Salary: ₹{salary:,.2f}")

# Recent Transactions Container
with st.container():
    st.subheader("Recent Transactions")
    if not transaction_data.empty:
        for idx, row in transaction_data.tail(5).iterrows():
            transaction_type = row['Transaction Type']
            amount = row['Amount']
            st.write(f"{transaction_type.capitalize()}: ₹{amount:,.2f}")
            delete_button = st.button("❌", key=f"delete_{idx}")
            if delete_button:
                transaction_data = transaction_data.drop(idx)
                transaction_data.to_csv("data/transactions.csv", index=False)
                st.experimental_rerun()

# Add New Transaction Container
with st.container():
    st.subheader("Add New Transaction")
    with st.form(key="add_transaction_form"):
        transaction_type = st.selectbox("Transaction Type", ["Credit", "Debit"])
        amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        submit_button = st.form_submit_button(label="Add Transaction")
    if submit_button:
        new_transaction = pd.DataFrame(
            [{"Transaction Type": transaction_type, "Amount": amount}],
            index=[len(transaction_data)]
        )
        transaction_data = pd.concat([transaction_data, new_transaction], ignore_index=True)
        transaction_data.to_csv("data/transactions.csv", index=False)
        user_account.credit(amount) if transaction_type == "Credit" else user_account.debit(amount)
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
