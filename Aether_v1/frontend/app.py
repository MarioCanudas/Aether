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
from controllers.base_controller import BaseController

# Import views
from views.home import show_home
from views.data import show_data
from views.income_analysis import show_income_analysis
from views.expenses_analysis import show_expenses_analysis
from views.transaction_processor import show_transaction_processor  # Import the transaction processor

# Import components
from components.cash_transaction import adding_cash_transaction
from components.add_user import add_user_popup

controller = BaseController()

# -- Page Configuration --
st.logo("frontend/assets/eli-logo.png", size= 'large', icon_image= "frontend/assets/eli-logo.png")
    
# -- Page Navigation --
PAGES = {
    'User': [
        # st.Page(show_login, title= "Login", icon= ':material/login:'),
        # st.Page(show_logout, title= "Logout", icon= ':material/logout:'),
        
    ],
    'Overview': [
        st.Page(show_home, title= "Home", icon= ':material/home:'),
        st.Page(show_income_analysis, title= "Income Analysis", icon= ':material/trending_up:'),
        st.Page(show_expenses_analysis, title= "Expenses Analysis", icon= ':material/trending_down:'),
    ],
    'Budget': [
        # st.Page(show_budget, title= "Budget", icon= ':material/budget:'),
        # st.Page(show_budget_analysis, title= "Budget Analysis", icon= ':material/budget_analysis:'),
        # st.Page(show_goals, title= "Goals", icon= ':material/goal:'),
        # st.Page(show_goals_tracker, title= "Goals Tracker", icon= ':material/goal_tracker:'),
    ],
    'Data': [
        st.Page(show_data, title= "Data Export", icon= ':material/table:'),
        st.Page(show_transaction_processor, title= "Transaction Processor", icon= ':material/flowsheet:'),
    ],
}

# -- Sidebar configuration --
with st.sidebar:
    current_username = st.selectbox("Select User", controller.get_users(), index= None)
    
    if st.button('Add user'):
        add_user_popup()
    
    # Disable adding cash transaction button, because it's not implemented properly yet
    if st.button('Add cash transaction', type= 'primary'):
        adding_cash_transaction()

# -- User session management --
if current_username is None:
    controller.clear_user_session()
    st.toast("No user selected")
    
elif current_username is not None:
    if not controller.user_id:
        user_id = controller.get_user_id(current_username)
        controller.update_user_id(user_id)
        
        st.toast(f"Logged in as {current_username} with id {controller.user_id}")
    else:
        st.toast(f"Already logged in as {current_username} with id {controller.user_id}")

        
page = st.navigation(PAGES)
page.run()
