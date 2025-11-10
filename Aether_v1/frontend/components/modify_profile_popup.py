import streamlit as st
from controllers import ProfileConfigController
from models.users import UserProfile

@st.dialog('Modify Profile', width= 'medium')
def modify_profile_popup(profile: UserProfile) -> None:
    controller = ProfileConfigController()
        
    col1, col2 = st.columns(2)
        
    with col1:
        st.metric(
            label="Username",
            value= profile.username,
            help="Username of the user"
        )
    
    with col2:
        # Account age metric
        st.metric(
            label="Created at",
            value=profile.created_at_formatted,
            help="Date and time of account creation"
        )
    
    with st.form(key= 'modify_profile_form', border= False):
        current_password = st.text_input('Current password', value= None, type= 'password', key= 'current_password')
        new_username = st.text_input('New username', value= None, key= 'new_username')
        new_password = st.text_input('New password', value= None, key= 'new_password')
        
        st.info("If you don't want to change one of the fields, leave it blank")
        
        if st.form_submit_button('Modify profile', type= 'primary'):
            if not current_password:
                st.warning('Current password is required', icon= ':material/warning:')
            else:
                try:
                    controller.modify_user(current_password, new_username, new_password)
                    st.rerun()
                except ValueError as e:
                    st.warning(f'{e}', icon= ':material/warning:')