import streamlit as st
import pandas as pd
import hashlib
import os

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load or create users data
users_file = "data/users.csv"
if not os.path.exists(users_file):
    # Create an empty users file if it doesn't exist
    pd.DataFrame(columns=["username", "password"]).to_csv(users_file, index=False)

def load_users():
    return pd.read_csv(users_file)

# Save new user to file
def save_user(username, password):
    new_user = pd.DataFrame([[username, hash_password(password)]], columns=["username", "password"])
    new_user.to_csv(users_file, mode="a", header=False, index=False)

# Authentication Functions
def authenticate(username, password):
    users = load_users()
    user = users[(users["username"] == username) & (users["password"] == hash_password(password))]
    return not user.empty

# Registration Functions
def register_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False
    save_user(username, password)
    return True

# Login and Signup Interface
def login_signup():
    st.title("Expense Manager Login")

    # Tabs for login and signup
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    # Login tab
    with tab_login:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.button("Login")
        
        if login_button:
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

    # Signup tab
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

# Main Application
def main_app():
    st.title(f"Welcome, {st.session_state.username}!")
    # Here you can include the main dashboard, balance, transactions, etc.
    # Refer to the previous dashboard implementation here

# Check login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_signup()
else:
    main_app()
