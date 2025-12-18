import streamlit as st
from typing import cast
from io import BytesIO
from controllers import UploadStatementsController
from components.confirm_upload import confirm_upload_popup
from constants.views_icons import UPLOAD_STATEMENTS_ICON

def show_upload_statements():
    # Page config
    st.set_page_config(
        page_title='Upload Statements', 
        page_icon=UPLOAD_STATEMENTS_ICON, 
        layout='centered'
    )
    controller = UploadStatementsController()
    
    st.title("Upload Statements")
    
    with st.form(key= 'upload_statements_form', clear_on_submit= True):
        card_name = st.selectbox('Card', options= controller.get_cards(), index= None, key= 'card_name', help= 'Select the card to upload the statements to')
        card = controller.get_card_by_name(card_name) if card_name else None
        
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
                
                # From streamlit documentation:
                # The UploadedFile class is a subclass of BytesIO, and therefore is "file-like". 
                # This means you can pass an instance of it anywhere a file is expected.
                uploaded_files = cast(list[BytesIO], uploaded_files)
                transactions = controller.process_uploaded_files(uploaded_files, card)
                confirm_upload_popup(transactions)
            else:
                st.toast('No files uploaded', icon= ':material/info:')
                
            

