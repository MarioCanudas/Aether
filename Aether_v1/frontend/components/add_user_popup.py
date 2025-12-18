import streamlit as st
from models.users import NewUser
from controllers import LogsController

@st.dialog('Add User')
def add_user_popup(controller: LogsController):
    with st.form(key= 'add_user_form', border= False, clear_on_submit= True):
        username = st.text_input('Username', value= None, key= 'add_user_username')
        password = st.text_input('Password', value= None, type= 'password', key= 'add_user_password')
        confirm_password = st.text_input('Confirm Password', value= None, type= 'password', key= 'add_user_confirm_password')
        
        if st.form_submit_button('Add User', type= 'primary'):
            if not username or not password or not confirm_password:
                st.warning('All fields are required', icon= ':material/warning:')
            elif password != confirm_password:
                st.warning('Passwords do not match', icon= ':material/warning:')
            else:
                password_hash = controller.hash_password(password)
                
                new_user = NewUser(username= username, password_hash= password_hash)
                controller.add_user(new_user)
                st.success('User added successfully', icon= ':material/check:')
                st.rerun()