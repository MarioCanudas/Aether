import streamlit as st 
from services import UserSessionService

@st.dialog('Add a user')
def add_user_popup(user_session_service: UserSessionService):
    username = st.text_input('Username')
    # password = st.text_input('Password', type= 'password')
    
    if st.button('Add user'):
        user_session_service.add_user(username)
        st.toast(f"User {username} added successfully")
        st.rerun()