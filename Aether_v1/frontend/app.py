import streamlit as st
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

# Import views
from views.logs import show_login, logout
from views.home import show_home
from views.cash_transaction import show_cash_transactions
from views.income_analysis import show_income_analysis
from views.expenses_analysis import show_expenses_analysis
from views.goals import show_goals
from views.users_config import show_users_config
from views.data import show_data
from views.upload_files import show_upload_statements
from constants.views_icons import (
    LOGIN_ICON, LOGOUT_ICON, HOME_ICON, 
    CASH_TRANSACTION_ICON, INCOME_ANALYSIS_ICON, 
    EXPENSES_ANALYSIS_ICON, GOALS_ICON, TRANSACTIONS_ICON, 
    UPLOAD_STATEMENTS_ICON, USERS_CONFIG_ICON
)

# -- Page Configuration --
if not 'logged_in' in st.session_state:
    st.session_state.logged_in = False
    
if not 'user_id' in st.session_state:
    st.session_state.user_id = None
    
st.logo("frontend/assets/eli-logo.png", size= 'large', icon_image= "frontend/assets/eli-logo.png")
    
# -- Page Navigation --
PAGES = {
    'User': [
        st.Page(show_login, title= "Login", icon= LOGIN_ICON, default= not st.session_state.logged_in),
    ]
}

if st.session_state.logged_in:
    PAGES.update({
        'Overview': [
            st.Page(show_home, title= "Home", icon= HOME_ICON, default= st.session_state.logged_in),
            st.Page(show_cash_transactions, title= "Cash Transaction", icon= CASH_TRANSACTION_ICON),
            st.Page(show_goals, title= "Goals", icon= GOALS_ICON),
        ],
        'Analytics': [
            st.Page(show_income_analysis, title= "Income Analysis", icon= INCOME_ANALYSIS_ICON),
            st.Page(show_expenses_analysis, title= "Expenses Analysis", icon= EXPENSES_ANALYSIS_ICON),
        ],
        'Data': [
            st.Page(show_data, title= "Transactions", icon= TRANSACTIONS_ICON),
            st.Page(show_upload_statements, title= "Upload Statements", icon= UPLOAD_STATEMENTS_ICON)
        ],
        'Account': [
            st.Page(logout, title= "Log out", icon= LOGOUT_ICON),  
            # st.Page(show_profile_config, title= "Profile", icon= ':material/account_circle:'),
        ],
        'Dev Tools': [
            st.Page(show_users_config, title= "Users Configuration", icon= USERS_CONFIG_ICON),
        ],
    })
    
    del PAGES['User']
        
page = st.navigation(PAGES, position= 'sidebar' if st.session_state.logged_in else 'hidden')
page.run()
