import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import date
from models.policy_suggestions import (
    recommend_policy,
    visualize_policy_comparison,
    display_policy_suggestion,
    model_spending,
)
from models.spam_classifier import classify_message, extract_transaction_details

# User Authentication Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users_file = "data/users.csv"

# Create the users CSV file if it doesn't exist
if not os.path.exists(users_file):
    pd.DataFrame(columns=["username", "password"]).to_csv(users_file, index=False)

def load_users():
    try:
        return pd.read_csv(users_file)
    except Exception:
        return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    hashed_password = hash_password(password)
    new_user = pd.DataFrame([[username, hashed_password]], columns=["username", "password"])
    new_user.to_csv(users_file, mode="a", header=False, index=False)

def authenticate(username, password):
    users = load_users()
    hashed_password = hash_password(password)
    return not users[(users["username"] == username) & (users["password"] == hashed_password)].empty

def register_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False
    save_user(username, password)
    return True

# Profile Setup
def setup_profile():
    st.subheader("Complete Profile Setup")
    name = st.text_input("Name")
    phone_number = st.text_input("Phone Number")
    age = st.number_input("Age", min_value=18, max_value=100)
    gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])
    profession = st.text_input("Profession")
    investment_goal = st.selectbox("Investment Goal", ["Wealth Growth", "Retirement", "Education", "Emergency Fund"])
    
    if st.button("Save Profile"):
        st.session_state.is_profile_set = True
        st.session_state.name = name
        st.session_state.phone_number = phone_number
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.profession = profession
        st.session_state.investment_goal = investment_goal
        st.success("Profile saved! Accessing your dashboard.")

# Load datasets
@st.cache_data
def load_policy_data():
    return pd.read_csv("data/insurance_policies_dataset.csv")

@st.cache_data
def load_transactions():
    return pd.read_csv("data/transactions.csv") if os.path.exists("data/transactions.csv") else pd.DataFrame(columns=["type", "amount", "category", "date", "description"])

policy_data = load_policy_data()
transactions = load_transactions()

# Dashboard Features
class UserAccount:
    def __init__(self, initial_balance=10000.0):
        self.balance = initial_balance
        self.transactions = transactions

    def credit(self, amount, description="Credit"):
        self.balance += amount
        self.log_transaction("credit", amount, "Credit", description)

    def debit(self, amount, description="Debit"):
        if self.balance >= amount:
            self.balance -= amount
            self.log_transaction("debit", amount, "Debit", description)
        else:
            st.error("Insufficient balance!")

    def log_transaction(self, transaction_type, amount, category, description):
        transaction = {"type": transaction_type, "amount": amount, "category": category, "date": str(date.today()), "description": description}
        self.transactions = pd.concat([self.transactions, pd.DataFrame([transaction])], ignore_index=True)
        self.save_transactions()

    def save_transactions(self):
        self.transactions.to_csv("data/transactions.csv", index=False)

# Initialize a user account instance
user_account = UserAccount()

def expense_dashboard():
    st.title("Expense Manager Dashboard")
    st.header(f"Welcome, {st.session_state.username}!")

    if st.button("View Profile"):
        st.subheader("Your Profile")
        st.write(f"**Name**: {st.session_state.name}")
        st.write(f"**Phone**: {st.session_state.phone_number}")
        st.write(f"**Age**: {st.session_state.age}")
        st.write(f"**Gender**: {st.session_state.gender}")
        st.write(f"**Profession**: {st.session_state.profession}")
        st.write(f"**Goal**: {st.session_state.investment_goal}")
    
    # Expense Management
    with st.expander("Expense Management"):
        st.subheader("Add an Expense")
        amount = st.number_input("Amount", min_value=0.0)
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Entertainment", "Health", "Others"])
        expense_date = st.date_input("Date", value=date.today())
        description = st.text_input("Description")

        if st.button("Add Expense"):
            user_account.debit(amount, description)
            st.success(f"Expense of {amount} added.")

        st.subheader("Your Expenses")
        st.dataframe(user_account.transactions)

    # Policy Suggestions
    with st.expander("Investment Policy Suggestions"):
        st.subheader("Enter Investment Details")
        monthly_investment = st.number_input("Monthly Investment Amount ($)", min_value=0.0)
        investment_duration = st.number_input("Investment Duration (in months)", min_value=1)

        if st.button("Submit Investment"):
            try:
                recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending, user_account.transactions)
                if recommended_policy is not None:
                    visualize_policy_comparison(suitable_policies)
                    display_policy_suggestion(monthly_investment, investment_duration)
                else:
                    st.warning("No suitable policies found.")
            except Exception as e:
                st.error(f"Error: {e}")

    # SMS Classification
    with st.expander("SMS Classification"):
        st.subheader("Analyze SMS")
        message = st.text_area("Paste SMS here")
        if st.button("Classify SMS"):
            label = classify_message(message)
            if label == "spam":
                st.warning("This SMS is spam.")
            else:
                transaction_type, amount = extract_transaction_details(message)
                if transaction_type and amount > 0:
                    if transaction_type == "debit":
                        user_account.debit(amount)
                    else:
                        user_account.credit(amount)
                    st.success(f"Transaction processed: {transaction_type.capitalize()} of INR {amount}.")

    # Bill Splitting
    with st.expander("Bill Splitting"):
        st.subheader("Split a Bill")
        total_bill = st.number_input("Total Bill Amount", min_value=0.0)
        members = st.text_area("Enter names of members (comma-separated)")
        if st.button("Split Bill"):
            member_list = [name.strip() for name in members.split(",") if name.strip()]
            if member_list:
                share = total_bill / len(member_list)
                st.write(f"Each member owes: {share:.2f}")
            else:
                st.error("No members provided.")

# App Flow
def main():
    st.set_page_config(page_title="Investment Dashboard", layout="wide")
    if "username" not in st.session_state:
        st.session_state.username = None
        st.session_state.is_profile_set = False

    if st.session_state.username:
        if not st.session_state.is_profile_set:
            setup_profile()
        else:
            expense_dashboard()
    else:
        st.title("Welcome to the Investment Dashboard")
        option = st.radio("Choose an option", ["Login", "Register"])

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if option == "Login" and st.button("Login"):
            if authenticate(username, password):
                st.session_state.username = username
                st.success("Logged in!")
            else:
                st.error("Invalid credentials.")

        elif option == "Register" and st.button("Register"):
            if register_user(username, password):
                st.success("Account created! Please log in.")
            else:
                st.error("Username already exists.")

if __name__ == "__main__":
    main()
