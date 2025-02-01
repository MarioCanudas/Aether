import streamlit as st

@st.dialog('Add a cash transaction')
def adding_cash_transaction():
    with st.form(key= 'adding a cash transaction', border=False):
        date = st.date_input(
            label= 'Date',
        )
        
        left, right = st.columns([4,7])
        
        transaction_type = left.pills(
            label= 'Type',
            options= ['Income', 'Expense'],
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
        
        transaction_data = {
                'date': date,
                'description': description,
                'amount': transaction_amount,
                'type': transaction_type,
                'bank': 'Cash',
                'statement_type': 'Cash',
                'filename': None
            }
        
        if st.form_submit_button(label= 'Sumbit'):
            if not 'all_transactions' in st.session_state:
                st.session_state.all_transactions = []
                
            st.session_state.all_transactions.append(transaction_data)
            
            st.rerun()