import streamlit as st
from datetime import date
from utils import to_decimal
from controllers import CashTransactionController
from models.bank_properties import BankName, StatementType
from models.financial import TransactionRecord

controller = CashTransactionController()

def show_cash_transactions():
    # Initialize the transaction form counter to force the reset of the form once the user adds a transaction
    if not 'transaction_form' in st.session_state:
        st.session_state['transaction_form'] = 1
        
    with st.form(key= f'add_cash_transaction_{st.session_state["transaction_form"]}'):
        st.header('Add a cash transaction')
        
        transaction_date = st.date_input(
            label= 'Date',
            value= date.today(),
            key= 'transaction_date'
        )
        
        left, right = st.columns([4,7])
        
        transaction_type = left.pills(
            label= 'Type',
            options= ['Abono', 'Cargo'],
            selection_mode= 'single',
            default= None,
            key= 'transaction_type'
        )
        
        transaction_amount = right.number_input(
            label= 'Amount',
            min_value= 0.01,
            value= None,
            key= 'transaction_amount'
        )
        
        category = left.selectbox(
            label= 'Category',
            options= controller.get_categories(),
            index= None,
            key= 'transaction_category'
        )
        
        description = right.text_input(
            label= 'Description',
            max_chars= 200,
            value= '',
            key= 'transaction_description'
        )
        
        if st.form_submit_button(label= 'Sumbit'):
            try:
                transaction_record = TransactionRecord(
                    user_id= controller.user_id,
                    category_id= controller.get_category_id(category),
                    date= transaction_date,
                    description= description if description else '',
                    amount= to_decimal(transaction_amount if transaction_type == 'Abono' else -1 * transaction_amount),
                    type= transaction_type,
                    bank= BankName.CASH,
                    statement_type= StatementType.DEBIT,
                    filename= None
                )
                
                controller.add_transaction(transaction_record)
                
                st.toast('Transaction added successfully', icon= ':material/check:')
                st.session_state['transaction_form'] += 1 # Increment the transaction form counter to force the reset of the form
                st.rerun()
            except TypeError:
                st.warning('Please, fill all the fields')
            except Exception as e:
                raise e