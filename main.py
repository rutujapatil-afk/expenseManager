import streamlit as st
import pandas as pd
import hashlib
import os
import re
from datetime import date
from models.policy_suggestions import get_user_input, recommend_policy, visualize_policy_comparison, policy_data, model_spending, display_policy_suggestion
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
    try:
        user = users[(users["username"] == username) & (users["password"] == hashed_password)]
        return not user.empty
    except KeyError:
        st.error("CSV file is missing required columns 'username' or 'password'.")
        return False

def register_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False
    save_user(username, password)
    return True

# Dashboard Functionality
class UserAccount:
    def __init__(self, initial_balance=10000.0):
        self.balance = initial_balance
        self.transactions = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])

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

# Updated expense_dashboard function
def expense_dashboard():
    st.title("Expense Manager Dashboard")

    # Display current balance
    st.header(f"Current Balance: INR {user_account.balance:.2f}")
    
    # Welcome message
    st.header(f"Welcome, {st.session_state.username}!")

    # Expense Management Section
    with st.expander("Expense Management"):
        st.subheader("Add an Expense")

        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Entertainment", "Health", "Others"])
        expense_date = st.date_input("Date", value=date.today())
        description = st.text_input("Enter Description", "") if category == "Others" else ""

        if st.button("Add Expense"):
            expense_data = pd.DataFrame({"amount": [amount], "category": [category], "date": [str(expense_date)], "description": [description]})
            expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
            expenses = pd.concat([expenses, expense_data], ignore_index=True)
            expenses.to_csv("data/expenses.csv", index=False)
            st.success(f"Expense of {amount} in category {category} added.")
            user_account.debit(amount, description=description if description else category)  # Update balance

        st.subheader("Your Expenses")
        expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
        st.dataframe(expenses)

        # Deletion option for multiple transactions
        if not expenses.empty:
            st.subheader("Delete Multiple Transactions")
            delete_buttons = [st.checkbox(f"{row['category']} | {row['amount']} | {row['date']} | {row['description']}", key=f"checkbox_{index}") for index, row in expenses.iterrows()]
            if st.button("🗑️ Delete Selected Transactions"):
                selected_indices = [i for i, checked in enumerate(delete_buttons) if checked]
                if selected_indices:
                    expenses = expenses.drop(selected_indices)
                    expenses.to_csv("data/expenses.csv", index=False)
                    st.success("Selected transactions deleted.")
                    try:
                        st.experimental_rerun()
                    except AttributeError:
                        st.error("An error occurred while trying to rerun the app. Please try refreshing the page.")

    # Investment Policy Suggestions Section
    if st.session_state.get("is_profile_set", False):
        with st.expander("Investment Policy Suggestions (ML Models)"):
            st.subheader("Investment Suggestions")
            monthly_investment, investment_duration = get_user_input()
            if st.session_state.get("input_submitted", False) and st.button("Analyze"):
                recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
                if recommended_policy is not None and suitable_policies is not None:
                    visualize_policy_comparison(suitable_policies)
                display_policy_suggestion(monthly_investment, investment_duration)

    # SMS Classification Section
    with st.expander("SMS Classification"):
        st.subheader("SMS Classification")
        message = st.text_area("Paste your bank message here", key="sms_input")
        
        if st.button("Analyze"):
            label = classify_message(message)
            
            if label == 'spam':
                st.write("This message appears to be spam.")
            else:
                st.write("Non-spam message detected.")
                transaction_type, amount = extract_transaction_details(message)
                
                if transaction_type:
                    st.write(f"Transaction detected: {transaction_type.capitalize()} of INR {amount:.2f}")
                    
                    # Handle Debit or Credit transaction
                    if transaction_type == 'debit' and st.button(f"Add debit of INR {amount:.2f} to transaction history"):
                        user_account.debit(amount)  # Debit the amount and save it
                        st.success("Debit transaction added successfully.")
                    
                    elif transaction_type == 'credit' and st.button(f"Add credit of INR {amount:.2f} to transaction history"):
                        user_account.credit(amount)  # Credit the amount and save it
                        st.success("Credit transaction added successfully.")
                    
                    # Display updated transaction history
                    user_account.transactions = pd.read_csv("data/expenses.csv")  # Reload the saved transactions
                    st.write("Updated Transaction History:")
                    st.dataframe(user_account.transactions)


# Profile Setup for First-Time Login
def profile_setup():
    st.title("Setup Your Profile")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=0)
    profession = st.text_input("Profession")
    if st.button("Save Profile"):
        if first_name and last_name and age and profession:
            st.session_state.update({"first_name": first_name, "last_name": last_name, "gender": gender, "age": age, "profession": profession, "is_profile_set": True})
            profile_data = pd.DataFrame([{"username": st.session_state.username, "first_name": first_name, "last_name": last_name, "gender": gender, "age": age, "profession": profession}])
            if not os.path.exists("data/profiles.csv"):
                profile_data.to_csv("data/profiles.csv", index=False)
            else:
                profile_data.to_csv("data/profiles.csv", mode="a", header=False, index=False)
            st.success("Profile saved!")
            st.experimental_rerun()
        else:
            st.error("Please complete all fields.")

# Main Function
def login_signup():
    st.title("Expense Manager Login")
    
    # Define login and signup tabs
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
    
    # Login tab
    with tab_login:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state["username"] = username
                st.session_state["logged_in"] = True
                st.success("Login successful!")
                expense_dashboard()
            else:
                st.error("Invalid username or password")
    
    # Signup tab
    with tab_signup:
        st.subheader("Create a new account")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if register_user(username, password):
                st.success("Account created successfully! You can now log in.")
            else:
                st.error("Username already taken. Please choose a different one.")

# Handle user login and setup
if 'logged_in' in st.session_state and st.session_state.logged_in:
    if not st.session_state.get("is_profile_set", False):
        profile_setup()  # Allow profile setup if it's the user's first time logging in
    else:
        expense_dashboard()  # Show expense dashboard after profile setup
else:
    login_signup()
