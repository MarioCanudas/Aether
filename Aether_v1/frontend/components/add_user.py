import streamlit as st 
from controllers.base_controller import BaseController

controller = BaseController()

@st.dialog('Add a user')
def add_user_popup():
    username = st.text_input('Username')
    # password = st.text_input('Password', type= 'password')
    
    if st.button('Add user'):
        controller.add_user(username)
        st.toast(f"User {username} added successfully")
        st.rerun()