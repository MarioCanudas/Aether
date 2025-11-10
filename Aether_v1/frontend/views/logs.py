import streamlit as st
from components import add_user_popup
from controllers.logs_controller import LogsController
from constants.views_icons import LOGIN_ICON, LOGOUT_ICON


def show_login():
    # Page config
    st.set_page_config(
        page_title='Login', 
        page_icon=LOGIN_ICON, 
        layout='centered'
    )
    controller = LogsController()
    
    _, center, _ = st.columns([1, 3, 1])
    
    with center: 
        with st.form(key= 'access_form', clear_on_submit= True):
            username = st.text_input('Username', max_chars= 20, value= None, key= 'username_input')
            password = st.text_input('Password', type= 'password', value= '', placeholder= 'Enter your password', key= 'password_input')
            
            if st.form_submit_button('Login', key= 'login_button'):
                try:
                    if controller.verify_login(username, password):
                        user_id = controller.get_user_id(username)
                        controller.update_user_id(user_id)
                        st.session_state.user_id = user_id
                        
                        st.session_state.logged_in = True
                        st.toast(f'Logged in as {username} with id: {user_id}')
                        st.rerun()
                    else:
                        st.error('Invalid username or password')
                except ValueError as e:
                    st.error(f'Error verifying login: {e}')
                    
        if st.button('Add User', icon= ':material/add:', type= 'primary', key= 'add_user_button', help= 'Add a new user'):
            add_user_popup(controller)
        
def logout():
    # Page config
    st.set_page_config(
        page_title='Logout', 
        page_icon=LOGOUT_ICON, 
        layout='centered'
    )
    controller = LogsController()
    
    st.session_state.logged_in = False
    controller.clear_user_session()
    
    st.rerun()