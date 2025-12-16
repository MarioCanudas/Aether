import streamlit as st
import pandas as pd
import asyncio
from typing import List
from controllers import UploadStatementsController
from models.transactions import Transaction

controller = UploadStatementsController()

@st.dialog('Confirm Upload')
def confirm_upload_popup(transactions: List[Transaction]) -> None:
    st.header('Transactions to be uploaded')
    clean_transactions, potential_duplicates, duplicated_transactions = asyncio.run(controller.filter_transactions(transactions))
    
    if clean_transactions:
        clean_df = pd.DataFrame([t.model_dump() for t in clean_transactions])

        st.subheader('Transactions to be uploaded')
        st.dataframe(clean_df)
    
    if potential_duplicates:
        potential_dupl_df = pd.DataFrame([t.model_dump() for t in potential_duplicates])
        
        st.subheader('Potential duplicates')
        st.dataframe(potential_dupl_df)
        
        st.info('These transactions will be uploaded as potential duplicates. You can review them in the Transactions view.')
        
    if duplicated_transactions:
        duplicated_df = pd.DataFrame([t.model_dump() for t in duplicated_transactions])
        
        st.subheader('Duplicated transactions')
        st.dataframe(duplicated_df)
        
        st.info('These transactions will not be uploaded because they are exact duplicates.')
    
    if st.button(label= 'Confirm', help= 'This will update the database with the new transactions. If you are not sure just close this popup'):
        controller.upload_transactions(clean_transactions + potential_duplicates)
        st.toast('Transactions uploaded successfully')
        st.rerun()