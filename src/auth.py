import streamlit as st
import pandas as pd
import hashlib
import os

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Path to the users CSV file
users_file = "data/users.csv"

# Create the users CSV file with comma-separated values if it doesn't exist
if not os.path.exists(users_file):
    pd.DataFrame(columns=["username", "password"]).to_csv(users_file, index=False)

def load_users():
    """
    Load the users from the CSV file into a pandas DataFrame.
    Ensure it is comma-separated.
    """
    try:
        users = pd.read_csv(users_file)
        # Ensure columns exist
        if "username" not in users.columns or "password" not in users.columns:
            st.error("CSV file must contain 'username' and 'password' columns.")
            return pd.DataFrame(columns=["username", "password"])
        return users
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    """
    Save the new user with a hashed password to the users CSV file.
    """
    hashed_password = hash_password(password)
    new_user = pd.DataFrame([[username, hashed_password]], columns=["username", "password"])
    new_user.to_csv(users_file, mode="a", header=False, index=False)

def authenticate(username, password):
    """
    Authenticate the user by comparing the entered password's hash with the stored hash.
    """
    users = load_users()
    hashed_password = hash_password(password)
    try:
        user = users[(users["username"] == username) & (users["password"] == hashed_password)]
        return not user.empty
    except KeyError:
        st.error("CSV file is missing required columns 'username' or 'password'.")
        return False

def register_user(username, password):
    """
    Register a new user by checking if the username exists. If not, save the user to the CSV file.
    """
    users = load_users()
    if username in users["username"].values:
        return False
    save_user(username, password)
    return True

def login_signup():
    """
    Display login and signup form, and handle authentication and registration.
    """
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

if __name__ == "__main__":
    login_signup()
