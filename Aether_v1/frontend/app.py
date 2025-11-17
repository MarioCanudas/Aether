import streamlit as st
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Display in console
    ],
)

# Add the project root directory (aether_v1) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import viewr
from views.logs import show_login, logout
from views.home import show_home
from views.cash_transaction import show_cash_transactions
from views.income_analysis import show_income_analysis
from views.expenses_analysis import show_expenses_analysis
from views.goals import show_goals
from views.profile_config import show_profile
from views.data import show_data
from views.upload_files import show_upload_statements
from views.cards import show_cards
from constants.views_icons import (
    LOGIN_ICON,
    LOGOUT_ICON,
    HOME_ICON,
    CASH_TRANSACTION_ICON,
    INCOME_ANALYSIS_ICON,
    EXPENSES_ANALYSIS_ICON,
    GOALS_ICON,
    TRANSACTIONS_ICON,
    UPLOAD_STATEMENTS_ICON,
    PROFILE_ICON,
    CARDS_ICON,
)
from components import new_category_popup

# -- Page Configuration --
if not "logged_in" in st.session_state:
    st.session_state.logged_in = False

if not "user_id" in st.session_state:
    st.session_state.user_id = None

st.logo(
    "frontend/assets/eli-logo.png",
    size="large",
    icon_image="frontend/assets/eli-logo.png",
)

# -- Page Navigation --
PAGES = {
    "User": [
        st.Page(
            show_login,
            title="Login",
            icon=LOGIN_ICON,
            default=not st.session_state.logged_in,
        ),
    ]
}

if st.session_state.logged_in:
    PAGES.update(
        {
            "Overview": [
                st.Page(
                    show_home,
                    title="Home",
                    icon=HOME_ICON,
                    default=st.session_state.logged_in,
                ),
                st.Page(
                    show_cards, 
                    title="Cards", 
                    icon=CARDS_ICON,
                ),
                st.Page(
                    show_cash_transactions,
                    title="Cash Transaction",
                    icon=CASH_TRANSACTION_ICON,
                ),
                st.Page(show_goals, title="Goals", icon=GOALS_ICON),
            ],
            "Analytics": [
                st.Page(
                    show_income_analysis,
                    title="Income Analysis",
                    icon=INCOME_ANALYSIS_ICON,
                ),
                st.Page(
                    show_expenses_analysis,
                    title="Expenses Analysis",
                    icon=EXPENSES_ANALYSIS_ICON,
                ),
            ],
            "Data": [
                st.Page(show_data, title="Transactions", icon=TRANSACTIONS_ICON),
                st.Page(
                    show_upload_statements,
                    title="Upload Statements",
                    icon=UPLOAD_STATEMENTS_ICON,
                ),
            ],
            "Account": [
                st.Page(show_profile, title="Profile", icon=PROFILE_ICON),
                st.Page(logout, title="Log out", icon=LOGOUT_ICON),
            ],
        }
    )

    del PAGES["User"]

    with st.sidebar:
        if st.button(
            "Add Category",
            type="primary",
            help="Add a new category",
            key="add_category_button",
        ):
            new_category_popup()

page = st.navigation(
    PAGES, position="sidebar" if st.session_state.logged_in else "hidden"
)
page.run()
