import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import date
from models.policy_suggestions import get_user_input, recommend_policy, visualize_policy_comparison
from models.policy_suggestions import policy_data, model_spending

# from policy_suggestions import display_investment_policy_recommendation

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
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Entertainment", "Health", "Others"])
        expense_date = st.date_input("Date", value=date.today())
        description = ""

        if category == "Others":
            description = st.text_input("Enter Description for the Expense")
        
        if st.button("Add Expense"):
            # Save the expense to CSV
            expense_data = pd.DataFrame({"amount": [amount], "category": [category], "date": [str(expense_date)], "description": [description]})
            expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
            
            # Concatenate new expense data to the existing DataFrame
            expenses = pd.concat([expenses, expense_data], ignore_index=True)
            
            # Save the updated expenses to the CSV
            expenses.to_csv("data/expenses.csv", index=False)
            st.success(f"Expense of {amount} in category {category} added on {expense_date}.")
        
        # Show expenses table
        st.subheader("Your Expenses")
        expenses = pd.read_csv("data/expenses.csv") if os.path.exists("data/expenses.csv") else pd.DataFrame(columns=["amount", "category", "date", "description"])
        st.dataframe(expenses)

        # Option to delete multiple transactions with checkboxes and dustbin icon 🗑️
        st.subheader("Delete Multiple Transactions")
        
        if not expenses.empty:
            # Create checkboxes for each transaction
            delete_buttons = []
            for index, row in expenses.iterrows():
                checkbox_label = f"{row['category']} | {row['amount']} | {row['date']} | {row['description']}"
                delete_buttons.append(st.checkbox(checkbox_label, key=f"checkbox_{index}"))

            # Button to delete selected transactions
            if st.button("🗑️ Delete Selected Transactions"):
                selected_indices = [i for i, checked in enumerate(delete_buttons) if checked]
                if selected_indices:
                    # Remove the selected transactions
                    expenses = expenses.drop(selected_indices)
                    expenses.to_csv("data/expenses.csv", index=False)
                    st.success(f"Deleted {len(selected_indices)} transaction(s).")
                    st.experimental_rerun()  # Refresh the page to reflect changes
                else:
                    st.warning("No transactions selected for deletion.")
        else:
            st.write("No expenses to delete.")

    # Investment Policy Suggestions Section in expense_dashboard()
    with st.expander("Investment Policy Suggestions (ML Models)"):
        st.subheader("Investment Suggestions")
    
    # Call function to get user input within this expander
    monthly_investment, investment_duration = get_user_input()
    
    if st.session_state.get("input_submitted", False):
        if st.button("Analyze"):
            # Perform policy recommendation
            recommended_policy, suitable_policies = recommend_policy(monthly_investment, investment_duration, policy_data, model_spending)
            
            if recommended_policy is not None and suitable_policies is not None:
                visualize_policy_comparison(suitable_policies)
        else:
            st.write("Please click 'Analyze' after filling out your investment details.")

    # SMS Classification Section (Add your model code here)
    with st.expander("SMS Classification"):
        st.subheader("SMS Classification")
        st.write("Here we will classify SMS messages to identify financial transactions.")
        # Placeholder for the SMS classification model logic
        st.write("SMS model will categorize messages based on your financial activity.")

# Profile Setup for First-Time Login
def profile_setup():
    st.title("Setup Your Profile")

    # Profile fields
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=0)
    profession = st.text_input("Profession")

    # When the user presses Save Profile
    if st.button("Save Profile"):
        if first_name and last_name and age and profession:
            # Save profile data to session state
            st.session_state.first_name = first_name
            st.session_state.last_name = last_name
            st.session_state.gender = gender
            st.session_state.age = age
            st.session_state.profession = profession
            st.success("Profile successfully set up!")

            # Ensure the data folder exists
            if not os.path.exists("data"):
                os.makedirs("data")

            # Save profile data to a CSV file
            profile_data = {
                "username": st.session_state.username,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "age": age,
                "profession": profession
            }

            # Create a DataFrame for the profile and append it to the CSV
            profile_df = pd.DataFrame([profile_data])
            if not os.path.exists("data/profiles.csv"):
                profile_df.to_csv("data/profiles.csv", index=False)
            else:
                profile_df.to_csv("data/profiles.csv", mode="a", header=False, index=False)

            # Set profile as completed in session state
            st.session_state.is_profile_set = True

            # Refresh the page to show the dashboard
            st.experimental_rerun()  # This will reload the page and show the dashboard after profile is set
        else:
            st.error("Please fill in all fields!")  # Error if fields are not filled

# Main Function
def login_signup():
    st.title("Expense Manager Login")

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.button("Login")
        
        if login_button:
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username

                # Check if the profile is already set up
                if not os.path.exists("data/profiles.csv") or username not in pd.read_csv("data/profiles.csv")["username"].values:
                    st.session_state.is_profile_set = False
                else:
                    st.session_state.is_profile_set = True

                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")
                st.session_state.pop("logged_in", None)  # Only clear relevant session key
                st.session_state.pop("username", None)
                st.experimental_rerun()

    with tab_signup:
        st.subheader("Sign Up")
        new_username = st.text_input("New Username", key="signup_username")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        signup_button = st.button("Sign Up")
        
        if signup_button:
            if register_user(new_username, new_password):
                st.success("Registration successful! Please log in.")
            else:
                st.error("Username already taken. Please choose a different one.")

def main():
    if "logged_in" in st.session_state and st.session_state.logged_in:
        if not st.session_state.is_profile_set:
            profile_setup()  # If profile is not set, prompt the user to set it up
        else:
            expense_dashboard()  # Show the expense dashboard after profile is set
    else:
        login_signup()  # Show the login/signup page

if __name__ == "__main__":
    main()
