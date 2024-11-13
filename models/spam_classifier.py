import re
import joblib
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import streamlit as st
import os

# Download NLTK stopwords if not already present
nltk.download('stopwords')

# Define the paths to the model and vectorizer
model_path = './models/spam_classifier_model.pkl'
vectorizer_path = './models/tfidf_vectorizer.pkl'

# Check if the model files exist before trying to load them
if os.path.exists(model_path) and os.path.exists(vectorizer_path):
    try:
        model = joblib.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
    except Exception as e:
        st.write(f"Error loading model or vectorizer: {e}")
else:
    st.write("Model files not found in the expected paths!")

# Initialize stopwords and stemmer
stop_words = set(stopwords.words('english'))
ps = PorterStemmer()

# Improved regular expressions for transaction detection
credit_pattern = re.compile(r'credited|deposit|credited to your account|cr|credit', re.IGNORECASE)
debit_pattern = re.compile(r'debited|withdrawal|debited from your account|dr|debit', re.IGNORECASE)
amount_pattern = re.compile(r'INR\s?([\d,]+\.\d{1,2})')

# Preprocess message function
def preprocess_message(message):
    message = re.sub(r'http\S+|www.\S+', '', message)  # Remove URLs
    message = re.sub(r'\d+', '', message)               # Remove numbers
    message = re.sub(r'[^\w\s]', '', message)           # Remove punctuation
    message = message.lower()                           # Convert to lowercase
    tokens = message.split()
    tokens = [ps.stem(word) for word in tokens if word not in stop_words]
    return ' '.join(tokens)

# Classify message function
def classify_message(message):
    """
    Classify a message as 'spam' or 'ham' (not spam) based on the model prediction.
    """
    cleaned = preprocess_message(message)
    vector = vectorizer.transform([cleaned]).toarray()
    prediction = model.predict(vector)[0]
    return 'spam' if prediction == 1 else 'ham'

# Extract transaction details function
# Regular expression for detecting amounts in the message (including decimals)
amount_pattern = re.compile(r'\b(?:INR\s?)?([\d,]+\.\d{1,2})\b')

# Extract transaction details function
def extract_transaction_details(message):
    transaction_type = None
    # Check if it's a debit or credit
    if debit_pattern.search(message):  # more specifically checks for debit-related words
        transaction_type = 'debit'
    elif credit_pattern.search(message):  # more specifically checks for credit-related words
        transaction_type = 'credit'

    # Search for the amount in the message
    amount_match = amount_pattern.search(message)
    if amount_match:
        amount_str = amount_match.group(1)
        # Clean up the amount and ensure it's a float
        amount = float(amount_str.replace(',', '').strip())  # Remove commas and extra spaces
    else:
        amount = 0.0

    return transaction_type, amount


# UserAccount class for managing user balance and transactions
class UserAccount:
    def __init__(self, initial_balance=10000.0):
        self.balance = initial_balance
        self.transactions = []  # Store transaction details

    def credit(self, amount):
        self.balance += amount
        self.transactions.append({'type': 'credit', 'amount': amount})

    def debit(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.transactions.append({'type': 'debit', 'amount': amount})
        else:
            st.write("Insufficient balance!")

    def show_balance(self):
        return f"Current Balance: INR {self.balance:.2f}"

    def show_transactions(self):
        transaction_history = ""
        for txn in self.transactions:
            transaction_history += f"{txn['type'].capitalize()}: INR {txn['amount']:.2f}\n"
        return transaction_history


# Streamlit display function for the Expense Manager Dashboard
def display_expense_manager(user_account):
    st.header("Expense Manager Dashboard")
    
    # Display current balance
    st.subheader(user_account.show_balance())
    
    # Show transaction history
    st.subheader("Transaction History")
    st.text(user_account.show_transactions())
    
    # Allow the user to add a debit or credit manually
    with st.form("Add Transaction"):
        transaction_type = st.radio("Select Transaction Type", ["debit", "credit"])
        amount = st.number_input("Enter Amount", min_value=1.0)
        submit_button = st.form_submit_button("Add Transaction")

        if submit_button:
            if transaction_type == "debit":
                user_account.debit(amount)
            else:
                user_account.credit(amount)

            # Update the session state
            st.session_state.user_account = user_account


# Streamlit display function for SMS classification interface
def display_spam_detector(user_account):
    """
    Displays the SMS classification interface for classifying and analyzing bank messages.
    """
    st.header("SMS Classification")
    
    # Introductory message
    st.write("Here we will classify SMS messages to identify financial transactions.")
    st.write("The SMS model will categorize messages based on your financial activity.")

    # Get message input from user
    message = st.text_area("Paste your bank message here")
    
    # Analysis button
    if st.button("Analyze"):
        label = classify_message(message)
        
        if label == 'spam':
            st.write("This message appears to be spam and will not be processed further.")
        else:
            st.write("Message is classified as non-spam.")
            transaction_type, amount = extract_transaction_details(message)
            
            # Process credit and debit transactions
            if transaction_type == 'debit':
                if st.button(f"Add debit of INR {amount:.2f} to transaction history"):
                    user_account.debit(amount)
                    st.session_state.user_account = user_account  # Update user account in session state
                    st.write("Transaction added successfully!")
            elif transaction_type == 'credit':
                if st.button(f"Add credit of INR {amount:.2f} to transaction history"):
                    user_account.credit(amount)
                    st.session_state.user_account = user_account  # Update user account in session state
                    st.write("Transaction added successfully!")

    # Show balance and transaction history
    user_account.show_balance()
    user_account.show_transactions()


# Initialize user account and manage session state for persistence
if 'user_account' not in st.session_state:
    st.session_state.user_account = UserAccount()  # Initialize if not in session state

# Check if the user is logged in (for demonstration, we assume a basic login state)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    # User login interface (simple version)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        if username == "admin" and password == "password":
            st.session_state.logged_in = True
            st.success("Login successful!")
        else:
            st.error("Invalid credentials")
else:
    st.write("Welcome to the Expense Manager Dashboard!")
    # Show Expense Manager and SMS Classification after login
    display_expense_manager(st.session_state.user_account)
    display_spam_detector(st.session_state.user_account)
