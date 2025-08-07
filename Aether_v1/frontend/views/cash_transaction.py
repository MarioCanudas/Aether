import streamlit as st
from controllers import TransactionProcessorController
import pandas as pd

controller = TransactionProcessorController()

def show_cash_transactions():
    with st.form(key= 'add_cash_transaction'):
        st.header('Add a cash transaction')
        
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
        
        user_id = controller.user_session_service.get_current_user_id()
        
        if st.form_submit_button(label= 'Sumbit'):
            transaction_record = {
                'user_id': user_id,
                'date': date,
                'description': description,
                'amount': transaction_amount if transaction_type == 'Abono' else -1 * transaction_amount,
                'type': transaction_type,
                'bank': 'cash',
                'statement_type': 'debit',
                'filename': None
            }
            
            controller.add_transaction(transaction_record)