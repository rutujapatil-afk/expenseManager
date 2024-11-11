import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import date

# User Authentication Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Path to the users CSV file
users_file = "data/users.csv"

# Create the users CSV file with comma-separated values if it doesn't exist
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
def expense_dashboard():
    st.title("Expense Manager Dashboard")
    
    # Welcome message
    st.header(f"Welcome, {st.session_state.username}!")
    st.write("This is your dashboard. You can now manage your expenses.")
    
    # Expense Management Section
    with st.expander("Expense Management"):
        st.subheader("Add an Expense")
        
        # Add Expense form
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        category = st.selectbox("Category", ["Food", "Transport", "Utilities", "Others"])
        expense_date = st.date_input("Date", value=date.today())
        
        if st.button("Add Expense"):
            # Save the expense to CSV
            expense_data = {"amount": amount, "category": category, "date": str(expense_date)}
            expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date"])
            expenses = expenses.append(expense_data, ignore_index=True)
            expenses.to_csv("data/expenses.csv", index=False)
            st.success(f"Expense of {amount} in category {category} added on {expense_date}.")

        # Show expenses table
        st.subheader("Your Expenses")
        expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date"])
        st.dataframe(expenses)

        # Option to delete an expense
        st.subheader("Delete a Transaction")
        if not expenses.empty:
            expense_to_delete = st.selectbox("Select an expense to delete", expenses["category"])
            if st.button("Delete Transaction"):
                expenses = expenses[expenses["category"] != expense_to_delete]
                expenses.to_csv("data/expenses.csv", index=False)
                st.success(f"Deleted expense in category: {expense_to_delete}")
        else:
            st.write("No expenses to delete.")

    # Machine Learning Models Section
    with st.expander("Machine Learning Models"):
        # Policy Suggestion Model
        st.subheader("Policy Suggestion")
        investment_amount = st.text_input("Investment Amount")
        investment_duration = st.text_input("Investment Duration (in months)")
        if st.button("Analyze"):
            # Placeholder for ML Model
            st.write(f"Analyzing investment policy for {investment_amount} over {investment_duration} months.")
        
        # SMS Classification Model
        st.subheader("SMS Classifier")
        sample_sms = st.text_area("Enter SMS")
        if st.button("Submit"):
            # Placeholder for SMS classification
            st.write(f"Classified SMS: {sample_sms}.")

    # User Profile Section
    with st.expander("Profile"):
        st.subheader("User Information")
        st.write(f"First Name: {st.session_state.first_name}")
        st.write(f"Last Name: {st.session_state.last_name}")
        st.write(f"Gender: {st.session_state.gender}")
        st.write(f"Age: {st.session_state.age}")
        st.write(f"Profession: {st.session_state.profession}")
        
        # Profile Picture Upload
        profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])
        if profile_pic is not None:
            st.image(profile_pic, width=100)

        if st.button("Logout"):
            st.session_state.clear()
            st.write("Logged out successfully.")

# Main Function
def main():
    if "logged_in" in st.session_state and st.session_state.logged_in:
        expense_dashboard()
    else:
        st.write("Please log in first.")
        # Show login/signup forms (your existing logic)

if __name__ == "__main__":
    main()
