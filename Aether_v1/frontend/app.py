import sys
import os

# Add the project root directory (aether_v1) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from views.home import show_home
from views.data import show_data
from views.income_analysis import show_income_analysis
from views.expenses_analysis import show_expenses_analysis
from views.transaction_processor import show_transaction_processor  # Import the transaction processor


# -- Page Configuration --
st.set_page_config(page_title="Quick Analysis", page_icon=":lightbulb:")

# -- Sidebar Setup --
def load_sidebar():
    st.sidebar.image("assets/eli-logo.png", use_container_width=True)
    st.sidebar.text("Eli Alpha Version v0.0")

# -- Page Navigation --
PAGES = {
    "Overview": show_home,
    "Data Export": show_data,
    "Income Analysis": show_income_analysis,
    "Expenses Analysis": show_expenses_analysis,
    "Transaction Processor": show_transaction_processor,  # New view added here
}

def main():
    load_sidebar()
    st.title("Eli Financial Analysis")

    # Navigation
    page_selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[page_selection]
    page()  # Call the selected page function

if __name__ == "__main__":
    main()
