import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import date
from models.policy_suggestions import (
    recommend_policy,
    visualize_policy_comparison,
    policy_data,
    model_spending,
    display_policy_suggestion,
)
from models.spam_classifier import classify_message, extract_transaction_details

# User Authentication Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Path to the users CSV file
users_file = "data/users.csv"

# Create the users CSV file if it doesn't exist
if not os.path.exists(users_file):
    pd.DataFrame(columns=["username", "password"]).to_csv(users_file, index=False)

def load_users():
    try:
        users = pd.read_csv(users_file)
        if "username" not in users.columns or "password" not in users.columns:
            st.error("CSV file must contain 'username' and 'password' columns.")
            return pd.DataFrame(columns=["username", "password"])
        return users
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    hashed_password = hash_password(password)
    new_user = pd.DataFrame([[username, hashed_password]], columns=["username", "password"])
    new_user.to_csv(users_file, mode="a", header=False, index=False)

def authenticate(username, password):
    users = load_users()
    hashed_password = hash_password(password)
    user = users[(users["username"] == username) & (users["password"] == hashed_password)]
    if not user.empty:
        st.session_state.username = username
        return True
    return False

def register_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False
    save_user(username, password)
    return True

# Profile Setup Function
def setup_profile():
    st.subheader("Complete Profile Setup")

    # User input fields
    name = st.text_input("Enter your name")
    phone_number = st.text_input("Enter your phone number")
    age = st.number_input("Enter your age", min_value=18, max_value=100, step=1)
    gender = st.selectbox("Select your gender", ["Male", "Female", "Prefer not to say"])
    profession = st.text_input("Enter your profession")
    investment_goal = st.selectbox("Select your primary investment goal", ["Wealth Growth", "Retirement", "Education", "Emergency Fund"])

    if st.button("Save Profile"):
        st.session_state.is_profile_set = True
        st.session_state.name = name
        st.session_state.phone_number = phone_number
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.profession = profession
        st.session_state.investment_goal = investment_goal

        st.success("Profile setup complete! Accessing your dashboard.")

# Dashboard Functionality
class UserAccount:
    def __init__(self, initial_balance=10000.0):
        self.balance = initial_balance
        self.transactions = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["type", "amount", "category", "date", "description"])

    def credit(self, amount, description="Credit"):
        self.balance += amount
        transaction = {"type": "credit", "amount": amount, "category": "Credit", "date": str(date.today()), "description": description}
        self.transactions = pd.concat([self.transactions, pd.DataFrame([transaction])], ignore_index=True)
        self.save_transactions()
        st.write(f"Credited: INR {amount:.2f}. New Balance: INR {self.balance:.2f}")

    def debit(self, amount, description="Debit"):
        if self.balance >= amount:
            self.balance -= amount
            transaction = {"type": "debit", "amount": amount, "category": "Debit", "date": str(date.today()), "description": description}
            self.transactions = pd.concat([self.transactions, pd.DataFrame([transaction])], ignore_index=True)
            self.save_transactions()
            st.write(f"Debited: INR {amount:.2f}. New Balance: INR {self.balance:.2f}")
        else:
            st.write("Insufficient balance!")

    def save_transactions(self):
        self.transactions.to_csv("data/expenses.csv", index=False)

# Initialize a user account instance
user_account = UserAccount()

@st.cache_data
def load_policy_data():
    return pd.read_csv("data/policies.csv")

policy_data = load_policy_data()

def expense_dashboard():
    st.title("Expense Manager Dashboard")
    st.header(f"Welcome, {st.session_state.username}!")

    # Profile Section
    if st.button("View Profile"):
        st.subheader("Your Profile")
        st.write(f"**Name**: {st.session_state.name}")
        st.write(f"**Phone Number**: {st.session_state.phone_number}")
        st.write(f"**Age**: {st.session_state.age}")
        st.write(f"**Gender**: {st.session_state.gender}")
        st.write(f"**Profession**: {st.session_state.profession}")
        st.write(f"**Investment Goal**: {st.session_state.investment_goal}")

        if st.button("Logout"):
            st.session_state.clear()

    # Policy Suggestions Section
    with st.expander("Investment Policy Suggestions"):
        st.subheader("Enter Investment Details")

        # User input for policy suggestions
        monthly_investment = st.number_input("Enter your monthly investment amount ($):", min_value=1.0, step=1.0)
        investment_duration = st.number_input("Enter your investment duration (in months):", min_value=1, step=1)

        if st.button("Submit Investment"):
            if monthly_investment <= 0 or investment_duration <= 0:
                st.error("Please enter valid positive values.")
            else:
                with st.spinner("Analyzing your investment options..."):
                    try:
                        recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
                        if recommended_policy is not None and not suitable_policies.empty:
                            visualize_policy_comparison(suitable_policies)
                            display_policy_suggestion(monthly_investment, investment_duration)
                        else:
                            st.warning("No suitable policies found for the entered investment details.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

# Main Application
def main():
    if "username" not in st.session_state:
        st.session_state.username = None

    st.set_page_config(page_title="Expense Manager", page_icon="💰")

    if st.session_state.username is None:
        st.title("Login to Expense Manager")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.username = username
                st.session_state.is_profile_set = False  # Reset profile setup state
                st.success("Login successful!")
            else:
                st.error("Invalid credentials.")

        if st.button("Register"):
            username = st.text_input("Create Username")
            password = st.text_input("Create Password", type="password")

            if register_user(username, password):
                st.success("Registration successful! Please login.")
            else:
                st.error("User already exists.")

    elif not st.session_state.get("is_profile_set", False):
        setup_profile()
    else:
        expense_dashboard()

if __name__ == "__main__":
    main()
