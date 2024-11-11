import streamlit as st
import pandas as pd
import hashlib
import os
import src.auth as auth  # Import the authentication module

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# Main app logic
if not st.session_state.logged_in:
    # If the user is not logged in, show the login/signup form
    auth.login_signup()
else:
    # If logged in, show the dashboard
    st.title("Expense Manager Dashboard")

    # Display a welcome message with the logged-in user's username
    st.subheader(f"Welcome, {st.session_state.username}!")

    # Here you can add your dashboard functionality, such as showing expenses, adding expenses, etc.
    # For example, showing some mock expense data or a placeholder:
    
    st.write("This is your dashboard. You can now manage your expenses.")

    # Example placeholder for adding expenses (you can replace this with real functionality)
    expense = st.text_input("Enter an expense", "")
    if st.button("Add Expense"):
        if expense:
            st.write(f"Expense '{expense}' added!")
        else:
            st.error("Please enter a valid expense.")

    # Logout functionality
    if st.button("Logout"):
        # Clear session state to log out the user and rerun the app to show the login page
        st.session_state.clear()  # Clear the session state
        st.experimental_rerun()  # Rerun the app to redirect to login page
