import streamlit as st
import pandas as pd
import hashlib
import os
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

        if st.button("Add Expense", key="add_expense"):
            expense_data = pd.DataFrame({"amount": [amount], "category": [category], "date": [str(expense_date)], "description": [description]})
            expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
            expenses = pd.concat([expenses, expense_data], ignore_index=True)
            expenses.to_csv("data/expenses.csv", index=False)
            st.success(f"Expense of {amount} in category {category} added.")
            user_account.debit(amount, description=description if description else category)

        st.subheader("Your Expenses")
        expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
        st.dataframe(expenses)

    # Investment Policy Suggestions Section
    profile_loaded = st.session_state.get("is_profile_set", False)
    if profile_loaded:
        with st.expander("Investment Policy Suggestions (ML Models)"):
            st.subheader("Investment Suggestions")
            monthly_investment, investment_duration = get_user_input()
            if st.button("Analyze Investment", key="analyze_investment"):
                st.session_state.input_submitted = True
                recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
                if recommended_policy is not None and suitable_policies is not None:
                    visualize_policy_comparison(suitable_policies)
                display_policy_suggestion(monthly_investment, investment_duration)

    # SMS Classification Section
    with st.expander("SMS Classification"):
        st.subheader("SMS Classification")
        message = st.text_area("Paste your bank message here", key="sms_input_unique")
        if st.button("Analyze SMS", key="analyze_sms_button"):
            label = classify_message(message)
            if label == 'spam':
                st.write("This message appears to be spam.")
            else:
                st.write("Non-spam message detected.")
                transaction_type, amount = extract_transaction_details(message)
                if transaction_type and amount > 0:
                    st.write(f"Transaction detected: {transaction_type.capitalize()} of INR {amount:.2f}")
                    if transaction_type == 'debit':
                        user_account.debit(amount)
                        st.success("Transaction debited and balance updated!")
                    elif transaction_type == 'credit':
                        user_account.credit(amount)
                        st.success("Transaction credited and balance updated!")
                    st.experimental_rerun()

    # Bill Splitting Section
    with st.expander("Bill Splitting"):
        st.subheader("Create a Group")
        
        if "groups" not in st.session_state:
            st.session_state.groups = {}
        if "debts" not in st.session_state:
            st.session_state.debts = {}

        group_name = st.text_input("Enter Group Name")
        members = st.text_area("Enter group members (comma-separated)")
        members_list = [member.strip() for member in members.split(",") if member.strip()]
        
        if st.button("Create Group"):
            if group_name and members_list:
                st.success(f"Group '{group_name}' created with members: {', '.join(members_list)}")
                st.session_state.groups[group_name] = {"members": members_list, "transactions": []}
            else:
                st.error("Please provide a valid group name and at least one member.")
        
        if group_name in st.session_state.groups:
            st.subheader("Split a Bill")
            total_amount = st.number_input("Total Amount", min_value=0.0, step=0.01)
            transaction_type = st.selectbox("Transaction Type", ["Cash", "Online"])
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Entertainment", "Health", "Others"])
            description = st.text_input("Description") if category == "Others" else ""
            split_date = date.today()
            
            if st.button("Split"):
                if total_amount > 0 and members_list:
                    split_amount = total_amount / len(members_list)
                    st.write(f"Each member owes INR {split_amount:.2f}.")
                    
                    # Update debts
                    for member in members_list:
                        if member != st.session_state.username:  # Skip the user splitting the bill
                            st.session_state.debts[member] = st.session_state.debts.get(member, 0) + split_amount
                    
                    st.session_state.groups[group_name]["transactions"].append({
                        "amount": total_amount,
                        "type": transaction_type,
                        "category": category,
                        "description": description,
                        "date": str(split_date),
                        "split_amount": split_amount
                    })
                    st.success("Bill split successfully!")
                else:
                    st.error("Please enter a valid amount and group.")
        
        # Display debts
        if st.session_state.debts:
            st.subheader("Debts Summary")
            for member, debt in st.session_state.debts.items():
                if debt > 0:
                    st.write(f"You owe {member}: INR {debt:.2f}")
                elif debt < 0:
                    st.write(f"{member} owes you: INR {-debt:.2f}")

# Login/Signup Section
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Welcome to Expense Manager")
    st.write("Your personalized platform for managing finances and investments.")
    option = st.selectbox("Select an option", ["Login", "Signup"])

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.success("Logged in successfully!")
                st.session_state.authenticated = True
                st.session_state.username = username
            else:
                st.error("Invalid username or password. Please try again.")
    elif option == "Signup":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if st.button("Signup"):
            if password == confirm_password:
                if register_user(username, password):
                    st.success("Account created successfully! You can now log in.")
                else:
                    st.error("Username already exists. Please choose a different one.")
            else:
                st.error("Passwords do not match. Please try again.")
else:
    # Show Dashboard
    expense_dashboard()
