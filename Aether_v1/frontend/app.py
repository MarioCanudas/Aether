import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO, # Set the logging level to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Display in console
    ]
)

# Add the project root directory (aether_v1) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from services.user_session_service import UserSessionService
from views.home import show_home
from views.data import show_data
from views.income_analysis import show_income_analysis
from views.expenses_analysis import show_expenses_analysis
from components.cash_transaction import adding_cash_transaction
from components.add_user import add_user_popup
from views.transaction_processor import show_transaction_processor  # Import the transaction processor

# -- Page Configuration --
st.logo("frontend/assets/eli-logo.png", size= 'large', icon_image= "frontend/assets/eli-logo.png")
if not 'all_transactions' in st.session_state:
    st.session_state.all_transactions = []
    
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

user_session_service = UserSessionService()
users = user_session_service.get_available_users()

# -- Sidebar configuration --
with st.sidebar:
    current_username = st.selectbox("Select User", users, index= None)
    
    if st.button('Add user'):
        add_user_popup(user_session_service)
    
    # Disable adding cash transaction button, because it's not implemented properly yet
    if st.button('Add cash transaction', type= 'primary'):
        adding_cash_transaction()

# -- User session management --
if current_username is None:
    user_session_service.clear_current_user()
    st.toast("No user selected")
elif current_username is not None and not user_session_service.current_user_id:
    user_id = user_session_service.get_user_id_by_username(current_username)
    user_session_service.set_current_user_by_id(user_id)
    st.toast(f"Logged in as {current_username} with id {user_session_service.current_user_id}")

        
page = st.navigation(PAGES)
page.run()
