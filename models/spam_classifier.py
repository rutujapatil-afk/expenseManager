import re
import joblib
import streamlit as st
from sklearn.naive_bayes import MultinomialNB
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
nltk.download('stopwords')
import os

model_path = 'spam_classifier_model.pkl'
if os.path.exists(model_path):
    model = joblib.load(model_path)
else:
    print(f"Model file {model_path} not found.")

vectorizer = joblib.load('models/tfidf_vectorizer.pkl')


# Initialize stopwords and stemmer
stop_words = set(stopwords.words('english'))
ps = PorterStemmer()

# Regular expressions for transaction detection
credit_pattern = re.compile(r'credited|deposit|credited to your account|cr', re.IGNORECASE)
debit_pattern = re.compile(r'debited|withdrawal|debited from your account|dr', re.IGNORECASE)
amount_pattern = re.compile(r'INR\s?([\d,]+\.\d{2})')

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
    cleaned = preprocess_message(message)
    vector = vectorizer.transform([cleaned]).toarray()
    prediction = model.predict(vector)[0]
    return 'spam' if prediction == 1 else 'ham'

# Extract transaction details function
def extract_transaction_details(message):
    if credit_pattern.search(message):
        transaction_type = 'credit'
    elif debit_pattern.search(message):
        transaction_type = 'debit'
    else:
        transaction_type = None

    amount_match = amount_pattern.search(message)
    amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0.0

    return transaction_type, amount

# Display function for Streamlit
def display_spam_detector(user_account):
    st.header("Bank Message Analysis")

    # Get message input from user
    message = st.text_area("Paste your bank message here")
    if st.button("Analyze"):
        label = classify_message(message)
        if label == 'spam':
            st.write("This message appears to be spam.")
        else:
            st.write("Message is classified as non-spam.")
            transaction_type, amount = extract_transaction_details(message)
            if transaction_type == 'debit':
                if st.button(f"Add debit of INR {amount:.2f} to transaction history"):
                    user_account.debit(amount)
                    st.write("Transaction added successfully!")
            elif transaction_type == 'credit':
                user_account.credit(amount)
                st.write("Transaction added successfully!")

class UserAccount:
    def _init_(self, initial_balance=10000.0):
        self.balance = initial_balance
        self.transactions = []  # Store transaction details

    def credit(self, amount):
        self.balance += amount
        self.transactions.append({'type': 'credit', 'amount': amount})
        st.write(f"Credited: INR {amount:.2f}. New Balance: INR {self.balance:.2f}")

    def debit(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.transactions.append({'type': 'debit', 'amount': amount})
            st.write(f"Debited: INR {amount:.2f}. New Balance: INR {self.balance:.2f}")
        else:
            st.write("Insufficient balance!")

    def show_balance(self):
        st.write(f"Current Balance: INR {self.balance:.2f}")

    def show_transactions(self):
        st.write("Transaction History:")
        for txn in self.transactions:
            st.write(f"{txn['type'].capitalize()}: INR {txn['amount']:.2f}")