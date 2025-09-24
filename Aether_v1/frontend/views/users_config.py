import streamlit as st
from controllers.user_configuration_controller import UserConfigurationController
from constants.views_icons import USERS_CONFIG_ICON

def show_users_config():
    # Page config
    st.set_page_config(
        page_title='Users Configuration', 
        page_icon=USERS_CONFIG_ICON, 
        layout='centered'
    )
    controller = UserConfigurationController()
    
    st.title('Users Configuration')
    
    st.subheader('All users')
    st.dataframe(controller.get_users_table(), hide_index= True, use_container_width= True)
    
    with st.expander('Modify User'):
        username = st.selectbox('User', controller.get_users(), index= None, key= 'modify_user_selectbox')
        
        if username:
            new_username = st.text_input('New name', value= username, key= 'modify_user_input')
            new_username = new_username.strip()
            
            if st.button('Confirm', key= 'modify_user_button', disabled= False if new_username != username and new_username != '' else True):
                try:
                    controller.modify_user(username, new_username)
                    
                    st.toast(f'User {username} modified successfully')
                except ValueError as e:
                    st.warning(f'User {username} already exists')
        else:
            st.write('Please, select a user')
    
    with st.expander('Add User'):
        username = st.text_input('Username', key= 'add_user_input')
        
        if st.button('Confirm', key= 'add_user_button'):
            if username not in controller.get_users():
                controller.add_user(username)
                st.toast(f'User {username} added successfully')
            else:
                st.warning(f'User {username} already exists')
            
    with st.expander('Delete User'):
        user_id = st.selectbox('User', controller.get_users(), index= None, key= 'delete_user_selectbox')
        
        if st.button('Confirm', key= 'delete_user_button'):
            controller.delete_user(user_id)
            st.toast(f'User {user_id} deleted successfully')
            