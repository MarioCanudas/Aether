import streamlit as st
from views.home import show_home
from views.data import show_data
from views.income_analysis import show_income_analysis  # Import the income analysis function
from views.expenses_analysis import show_expenses_analysis

# -- Page Configuration --
st.set_page_config(page_title="Quick Analysis", page_icon=":lightbulb:")

# -- Sidebar Setup --
def load_sidebar():
    st.sidebar.image("frontend/assets/eli-logo.png", use_container_width=True)
    st.sidebar.text("Eli Alpha Version v0.0")

# -- Page Navigation --
PAGES = {
    "Overview": show_home,
    "Data Export": show_data,
    "Income Analysis": show_income_analysis,
    "Expenses Analysis": show_expenses_analysis,
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
