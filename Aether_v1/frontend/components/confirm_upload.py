import streamlit as st
import pandas as pd
from controllers import TransactionProcessorController
from models.tables import AllTransactionsTable

controller = TransactionProcessorController()

@st.dialog('Confirm Upload')
def confirm_upload_popup(transactions: AllTransactionsTable) -> None:
    st.header('Transactions to be uploaded')
    st.dataframe(transactions.df)
    
    if st.button(label= 'Confirm', help= 'This will update the database with the new transactions. If you are not sure just close this popup'):
        controller.upload_transactions(transactions)
        st.toast('Transactions uploaded successfully')
        st.rerun()