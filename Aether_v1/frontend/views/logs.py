import streamlit as st
from controllers.logs_controller import LogsController

controller = LogsController()

def show_login():
    _, center, _ = st.columns([1, 3, 1])
    
    with center: 
        with st.form(key= 'access_form'):
            username = st.selectbox('User', controller.get_users(), index= None)
            password = st.text_input('Password', type= 'password', disabled= True)
            
            if st.form_submit_button('Login'):
                if username is not None:
                    st.session_state.logged_in = True
                    
                    user_id = controller.get_user_id(username)
                    controller.update_user_id(user_id)
                    st.session_state.user_id = user_id
                    
                    st.toast(f'Logged in as {username} with id: {user_id}')
                    st.rerun()
                else:
                    st.warning('Please select a username')
        
def logout():
    st.session_state.logged_in = False
    controller.clear_user_session()
    
    st.rerun()