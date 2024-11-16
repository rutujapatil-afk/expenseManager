import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import date
from models.policy_suggestions import get_user_input, recommend_policy, visualize_policy_comparison, policy_data, model_spending
from models.spam_classifier import classify_message, extract_transaction_details

print("Current Directory:", os.getcwd())
print("Available Files:", os.listdir())

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

# Sample placeholder data for policy and model (replace with actual data or model)
policy_data = pd.DataFrame({
    'policy_name': ['Policy A', 'Policy B', 'Policy C'],
    'investment_return': [7.5, 8.0, 6.5],  # Sample returns
    'risk_level': ['Low', 'Medium', 'High']
})

model_spending = {'Low': 1000, 'Medium': 5000, 'High': 10000}  # Sample spending model

def recommend_policy(monthly_investment, investment_duration, policy_data, model_spending):
    # Implement logic to recommend policies based on investment details
    suitable_policies = policy_data[policy_data['investment_return'] > (monthly_investment / investment_duration)]
    recommended_policy = suitable_policies.iloc[0]  # Select the top policy
    return recommended_policy, suitable_policies

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
    if st.session_state.get("is_profile_set", False):
        with st.expander("Investment Policy Suggestions (ML Models)"):

            st.subheader("Investment Suggestions")
            # Collect user input for investment details
            monthly_investment, investment_duration = get_user_input()

            if st.button("Analyze Investment", key="analyze_investment"):
                st.session_state.input_submitted = True
                # Pass the correct arguments to the recommend_policy function
                recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)

                if recommended_policy is not None and suitable_policies is not None:
                    st.write(f"Recommended Policy: {recommended_policy['policy_name']}")
                    st.write(f"Expected Return: {recommended_policy['investment_return']}%")
                    st.write("Other Suitable Policies:")
                    st.write(suitable_policies[['policy_name', 'investment_return']])

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

# Main function to handle login, profile setup, and dashboard display
def main():
    st.title("Expense Manager")

    if "username" not in st.session_state:
        st.subheader("Login or Register")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        action = st.selectbox("Select action", ["Login", "Register"])

        if action == "Login" and st.button("Login"):
            if authenticate(username, password):
                st.session_state.is_logged_in = True
                st.session_state.username = username
                expense_dashboard()
            else:
                st.error("Invalid username or password!")

        elif action == "Register" and st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! You can now log in.")
            else:
                st.error("Username already exists. Please try a different one.")

    elif st.session_state.get("is_logged_in", False):
        if not st.session_state.get("is_profile_set", False):
            setup_profile()
        else:
            expense_dashboard()

if __name__ == "__main__":
    main()
