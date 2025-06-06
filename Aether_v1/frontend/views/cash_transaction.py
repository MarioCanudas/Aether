import streamlit as st
from controllers import TransactionProcessorController
import pandas as pd

controller = TransactionProcessorController()

@st.dialog('Add a cash transaction')
def adding_cash_transaction():
    with st.form(key= 'adding a cash transaction', border=False):
        controller.initialize_session_state()
        
        date = st.date_input(
            label= 'Date',
        )
        
        left, right = st.columns([4,7])
        
        transaction_type = left.pills(
            label= 'Type',
            options= ['Abono', 'Cargo'],
            selection_mode= 'single',
        )
        
        transaction_amount = right.number_input(
            label= 'Amount',
            value= None
        )
        
        description = st.text_input(
            label= 'Description',
            max_chars= 200
        )
        
        if st.form_submit_button(label= 'Sumbit'):
            transaction_data = pd.DataFrame([{
                'Date': date,
                'Description': description,
                'Amount': transaction_amount if transaction_type == 'Abono' else -1 * transaction_amount,
                'Type': transaction_type,
                'bank': 'Cash',
                'statement_type': 'debit',
                'filename': None
            }])
            
            controller.append_transactions(transaction_data)
            controller.update_all_processed_data()
            controller.update_all_monthly_results()
            
            st.rerun()