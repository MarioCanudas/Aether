import streamlit as st
from controllers import TransactionProcessorController
from components.confirm_upload import confirm_upload_popup
from constants.views_icons import UPLOAD_STATEMENTS_ICON

def show_upload_statements():
    # Page config
    st.set_page_config(
        page_title='Upload Statements', 
        page_icon=UPLOAD_STATEMENTS_ICON, 
        layout='centered'
    )
    controller = TransactionProcessorController()
    
    st.title("Upload Statements")
    
    with st.form(key= 'upload_statements_form', clear_on_submit= True):
        uploaded_files = st.file_uploader(
            "Please upload your Bank Statement PDF files", 
            accept_multiple_files=True, 
            type="pdf",
            disabled= False if st.session_state.logged_in else True,
            key= 'home_file_uploader'
        )
        
        if st.form_submit_button(label= 'Upload', icon= ':material/save:'):
            if uploaded_files:
                st.write("Processing Files...")
                try:
                    transactions = controller.process_uploaded_files(uploaded_files)
                    confirm_upload_popup(transactions)
                except Exception as e:
                    st.error(f"An unexpected error processing files: {e}")
            else:
                st.toast('No files uploaded', icon= ':material/info:')
                
            

