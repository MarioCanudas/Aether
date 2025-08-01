import streamlit as st
import pandas as pd
from controllers import TransactionProcessorController

controller = TransactionProcessorController()

@st.dialog('Confirm Upload')
def confirm_upload_popup(transactions: pd.DataFrame) -> None:
    with st.form(key= 'confirm upload', border=False):
        st.header('Transactions to be uploaded')
        st.dataframe(transactions)
        
        if st.form_submit_button(label= 'Confirm', help= 'This will update the database with the new transactions. If you are not sure just close this popup'):
            controller.update_transactions(transactions)
            controller.update_monthly_results(transactions)
            st.toast('Transactions uploaded successfully')
            st.rerun()