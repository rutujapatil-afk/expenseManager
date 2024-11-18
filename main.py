import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import date
from models.policy_suggestions import get_user_input, recommend_policy, policy_data, model_spending, display_policy_suggestion,efficiency_metrics,y_test_p, model_policy,X_test_p
from models.spam_classifier import classify_message, extract_transaction_details
from sklearn.metrics import classification_report

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

import os
import pandas as pd
import streamlit as st
from datetime import date
from sklearn.metrics import classification_report

def expense_dashboard():
    st.title("Expense Manager Dashboard")
    st.header(f"Welcome, {st.session_state.username}!")

    # Profile Button
    if st.button("Profile"):
        st.subheader("Your Profile")
        st.write(f"**Name**: {st.session_state.name}")
        st.write(f"**Phone Number**: {st.session_state.phone_number}")
        st.write(f"**Age**: {st.session_state.age}")
        st.write(f"**Gender**: {st.session_state.gender}")
        st.write(f"**Profession**: {st.session_state.profession}")
        st.write(f"**Investment Goal**: {st.session_state.investment_goal}")

        # Logout Button
        if st.button("Logout"):
            st.session_state.clear()

    # Expense Management Section
    with st.expander("Expense Management"):
        st.subheader("Add an Expense")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Entertainment", "Health", "Others"])
        expense_date = st.date_input("Date", value=date.today())
        description = st.text_input("Enter Description", "") if category == "Others" else ""

        if st.button("Add Expense", key="add_expense"):
            expense_data = pd.DataFrame({
                "amount": [amount],
                "category": [category],
                "date": [str(expense_date)],
                "description": [description]
            })

            expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
            expenses = pd.concat([expenses, expense_data], ignore_index=True)
            expenses.to_csv("data/expenses.csv", index=False)
            st.success(f"Expense of {amount} in category {category} added.")

        st.subheader("Your Expenses")
        expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
        st.dataframe(expenses)

    # Bill Splitting Section
    manage_group_transactions()

    # Investment Policy Suggestions Section
    if st.session_state.get("is_profile_set", False):
        with st.expander("Investment Policy Suggestions (ML Models)"):
            st.subheader("Investment Suggestions")
            monthly_investment, investment_duration = get_user_input()
            if st.button("Analyze Investment", key="analyze_investment"):
                st.session_state.input_submitted = True
                recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
                display_policy_suggestion()

            if st.button("Show Model Efficiency"):
                st.subheader("Model Efficiency")
                st.write(f"Spending Prediction Accuracy: {efficiency_metrics['Spending Prediction Accuracy']:.2f}%")
                st.write(f"Policy Prediction Accuracy: {efficiency_metrics['Policy Prediction Accuracy']:.2f}%")

                # Parse and display the classification report
                st.write("Classification Report for Policies:")
                report_dict = classification_report(y_test_p, model_policy.predict(X_test_p), output_dict=True)
                report_df = pd.DataFrame(report_dict).transpose()
                st.table(report_df)

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

# New Group Management Section
# Group Management Section
def manage_group_transactions():
    # Initialize groups in session state if not present
    if "groups" not in st.session_state:
        st.session_state.groups = {}

    # Add a new group
    with st.expander("Split bill"):
        st.subheader("Split Bill")
        
        group_name = st.text_input("Enter Group Name", key="group_name_input")
        if "new_group_members" not in st.session_state:
            st.session_state.new_group_members = []
        
        # Display existing members for the new group
        st.write("### Members Added:")
        if st.session_state.new_group_members:
            for idx, member in enumerate(st.session_state.new_group_members):
                st.write(f"{idx + 1}. {member}")
        else:
            st.write("No members added yet.")

        # Input for adding a new member
        new_member = st.text_input("Add a Member", key="new_member_input")
        
        # Add member button
        if st.button("Add Member"):
            if new_member:
                if new_member in st.session_state.new_group_members:
                    st.warning(f"{new_member} is already in the group.")
                else:
                    st.session_state.new_group_members.append(new_member)
                    st.success(f"Added {new_member} to the group.")
            else:
                st.warning("Member name cannot be empty.")

        # Create Group button
        if st.button("Create Group"):
            if not group_name:
                st.warning("Group name is required.")
            elif group_name in st.session_state.groups:
                st.warning("A group with this name already exists.")
            elif not st.session_state.new_group_members:
                st.warning("At least one member is required to create a group.")
            else:
                st.session_state.groups[group_name] = {
                    "members": st.session_state.new_group_members.copy(),
                    "transactions": [],
                }
                st.session_state.new_group_members = []
                st.success(f"Group '{group_name}' created successfully!")

    # Display existing groups and manage their transactions
    for group_name, group_data in st.session_state.groups.items():
        with st.expander(f"Group: {group_name}"):
            st.subheader(f"Group: {group_name}")
            st.write(f"**Members:** {', '.join(group_data['members'])}")

            # Add Expense to Group
            st.subheader(f"Add Expense for {group_name}")
            expense_amount = st.number_input(f"Amount for {group_name}", min_value=0.0, step=0.01, key=f"amount_{group_name}")
            category = st.text_input(f"Category for {group_name}", key=f"category_{group_name}")
            expense_date = str(date.today())

            if st.button(f"Add Expense to {group_name}", key=f"add_expense_{group_name}"):
                n_members = len(group_data["members"])
                if n_members > 0:
                    split_amount = expense_amount / n_members
                    # Record the transaction
                    group_data["transactions"].append({
                        "payer": st.session_state.username,
                        "amount": expense_amount,
                        "category": category,
                        "date": expense_date,
                        "split_amount": split_amount,
                    })
                    st.success(f"Expense of INR {expense_amount:.2f} split among {n_members} members.")
                else:
                    st.warning(f"No members in group '{group_name}'. Cannot split expense.")

            # Display amount owed by group members
            if st.button(f"Owed by Members in {group_name}", key=f"owed_{group_name}"):
                owed_summary = calculate_owed_by_group_members(group_name)
                st.write("**Amount Owed by Group Members:**")
                for member, amount in owed_summary.items():
                    st.write(f"{member}: INR {amount:.2f}")

            # Display debts of the current user
            if st.button(f"Debts in {group_name}", key=f"debt_{group_name}"):
                debt_summary = calculate_user_debt(group_name)
                st.write("**Amount I Owe to Group Members:**")
                for member, amount in debt_summary.items():
                    st.write(f"{member}: INR {amount:.2f}")


# Helper functions for group debt and owed calculations
def calculate_owed_by_group_members(group_name):
    """Calculate how much each group member owes the current user."""
    group_data = st.session_state.groups[group_name]
    user = st.session_state.username
    owed = {member: 0 for member in group_data["members"] if member != user}

    for transaction in group_data["transactions"]:
        if transaction["payer"] == user:
            for member in owed:
                owed[member] += transaction["split_amount"]
        elif transaction["payer"] in owed:
            owed[transaction["payer"]] -= transaction["split_amount"]

    return {member: amount for member, amount in owed.items() if amount > 0}

def calculate_user_debt(group_name):
    """Calculate how much the current user owes to other group members."""
    group_data = st.session_state.groups[group_name]
    user = st.session_state.username
    debt = {member: 0 for member in group_data["members"] if member != user}

    for transaction in group_data["transactions"]:
        if transaction["payer"] != user and user in group_data["members"]:
            debt[transaction["payer"]] += transaction["split_amount"]

    return {member: amount for member, amount in debt.items() if amount > 0}

# Helper functions
def calculate_owed_by_group_members(group_name):
    group_data = st.session_state.groups[group_name]
    user = st.session_state.username
    owed = {member: 0 for member in group_data["members"] if member != user}

    for transaction in group_data["transactions"]:
        if transaction["payer"] == user:
            for member in owed:
                owed[member] += transaction["split_amount"]
        elif transaction["payer"] in owed:
            owed[transaction["payer"]] -= transaction["split_amount"]

    return {member: amount for member, amount in owed.items() if amount > 0}


def calculate_user_debt(group_name):
    group_data = st.session_state.groups[group_name]
    user = st.session_state.username
    debt = {member: 0 for member in group_data["members"] if member != user}

    for transaction in group_data["transactions"]:
        if transaction["payer"] != user and user in group_data["members"]:
            debt[transaction["payer"]] += transaction["split_amount"]

    return {member: amount for member, amount in debt.items() if amount > 0}

# Main Flow Logic
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_profile_set" not in st.session_state:
    st.session_state.is_profile_set = False
if "input_submitted" not in st.session_state:
    st.session_state.input_submitted = False
if "is_signing_up" not in st.session_state:
    st.session_state.is_signing_up = False

if "username" in st.session_state and st.session_state.username:
    if not st.session_state.is_profile_set:
        setup_profile()
    else:
        expense_dashboard()
else:
    st.header("Welcome to the Expense Manager!")
    st.subheader("Log in to continue")

    # Login Section
    username = st.text_input("Enter your username", key="username_login")
    password = st.text_input("Enter your password", type="password", key="password_login")
    
    login_col, new_user_col = st.columns(2)

    with login_col:
        if st.button("Login", key="login_button"):
            if authenticate(username, password):
                st.success(f"Logged in as {username}")
            else:
                st.error("Incorrect username or password.")

    with new_user_col:
        if st.button("New User", key="new_user_button"):
            st.session_state.is_signing_up = True

    st.markdown("[Forgotten account?](#)")

    # Signup Section
    if st.session_state.get("is_signing_up", False):
        st.subheader("Sign up for a new account")
        new_username = st.text_input("Enter a username", key="username_signup")
        new_password = st.text_input("Enter a password", type="password", key="password_signup")

        if st.button("Sign Up", key="signup_button"):
            if register_user(new_username, new_password):
                st.success(f"Account created for {new_username}. Please log in.")
                st.session_state.is_signing_up = False
            else:
                st.error("Username already exists.")
