import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import date
from models.policy_suggestions import (
    get_user_input,
    recommend_policy,
    visualize_policy_comparison,
    policy_data,
    model_spending,
    display_policy_suggestion
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

# Updated login page function
def login_page():
    st.title("Log in to Expense Manager")
    st.write("You must log in to continue.")

    # Create a username and password input form
    username = st.text_input("Username", placeholder="Enter your username", label_visibility="collapsed")
    password = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="collapsed")

    # Login button
    if st.button("Log in"):
        if authenticate(username, password):
            st.session_state.username = username
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.experimental_rerun()  # Refresh the page to show the dashboard
        else:
            st.error("Invalid username or password")

    # Option to navigate to the signup process
    if st.button("Don't have an account?"):
        st.session_state.show_signup = True  # Trigger showing the signup form

# Signup page function
def signup_page():
    st.title("Sign Up for Expense Manager")
    st.write("Create an account to start managing your expenses.")

    new_username = st.text_input("Username (new user)", placeholder="Create a new username", label_visibility="collapsed")
    new_password = st.text_input("Password (new user)", type="password", placeholder="Create a new password", label_visibility="collapsed")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", label_visibility="collapsed")

    if st.button("Sign up"):
        if new_password == confirm_password:
            if register_user(new_username, new_password):
                st.success("Registration successful! You can now log in.")
                st.session_state.show_signup = False  # Reset the show_signup state
            else:
                st.error("Username already taken. Try another one.")
        else:
            st.error("Passwords do not match.")
    
    # Option to go back to the login page
    if st.button("Already have an account? Log in"):
        st.session_state.show_signup = False  # Hide the signup page and show login form

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

    # SMS Classification Section with improved error handling
    with st.expander("SMS Classification"):
        message = st.text_area("Enter bank SMS here:", key="sms_input")
        
        if st.button("Classify"):
            if message:  # Ensure that the message is not empty
                try:
                    # Classify the message (ensure classify_message function works correctly)
                    result, transaction_details = classify_message(message)
                    
                    if result == "spam":
                        st.write("This message appears to be spam.")
                    else:
                        st.write("This message contains a valid financial transaction.")
                        st.write(transaction_details)
                except Exception as e:
                    st.error(f"An error occurred during classification: {e}")
            else:
                st.warning("Please enter a valid SMS message.")

# Main Logic to control flow of pages
def main():
    if "logged_in" not in st.session_state or not st.session_state.get("logged_in", False):
        if "show_signup" not in st.session_state or not st.session_state["show_signup"]:
            login_page()  # If the user is not logged in, show the login page
        else:
            signup_page()  # If show_signup is true, show signup page
    else:
        expense_dashboard()  # Display the dashboard once the user is logged in

if __name__ == "__main__":
    main()
