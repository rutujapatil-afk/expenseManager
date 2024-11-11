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
            st.session_state.first_name = first_name
            st.session_state.last_name = last_name
            st.session_state.gender = gender
            st.session_state.age = age
            st.session_state.profession = profession
            st.success("Profile successfully set up!")

            # Optionally, save these details to a CSV file for persistence
            profile_data = {
                "username": st.session_state.username,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "age": age,
                "profession": profession
            }

            # Append the profile data to a CSV file (or a more suitable database solution in production)
            profile_df = pd.DataFrame([profile_data])
            if not os.path.exists("data/profiles.csv"):
                profile_df.to_csv("data/profiles.csv", index=False)
            else:
                profile_df.to_csv("data/profiles.csv", mode="a", header=False, index=False)

            st.experimental_rerun()  # Reload to show the dashboard
        else:
            st.error("Please fill in all fields!")

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
