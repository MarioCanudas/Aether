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
st.logo("assets/eli-logo.png", size= 'large', icon_image= "assets/eli-logo.png")

# -- Page Navigation --
PAGES = {
    'Eli Alpha Version v0.0': [
        st.Page(show_home, title= "Overview"),
        st.Page(show_data, title= "Data Export"),
        st.Page(show_income_analysis, title= "Income Analysis"),
        st.Page(show_expenses_analysis, title= "Expenses Analysis"),
        st.Page(show_transaction_processor, title= "Transaction Processor") # New view added here
    ],
}

page = st.navigation(PAGES)
page.run()
