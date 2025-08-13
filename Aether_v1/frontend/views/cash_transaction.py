import streamlit as st
from decimal import Decimal
from controllers import TransactionProcessorController
from models.bank_properties import BankName, StatementType
from models.financial import TransactionRecord

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
            min_value= 0.01,
            value= None
        )
        
        category = left.selectbox(
            label= 'Category',
            options= controller.get_categories(),
            index= None,
        )
        
        description = right.text_input(
            label= 'Description',
            max_chars= 200
        )
        
        if st.form_submit_button(label= 'Sumbit'):
            try:
                transaction_record = TransactionRecord(
                    user_id= controller.user_id,
                    category_id= controller.get_category_id(category),
                    date= date,
                    description= description,
                    amount= Decimal(transaction_amount if transaction_type == 'Abono' else -1 * transaction_amount),
                    type= transaction_type,
                    bank= BankName.CASH,
                    statement_type= StatementType.DEBIT,
                    filename= None
                )
                
                controller.add_transaction(transaction_record)
            except TypeError:
                st.warning('Please, fill all the fields')
            except Exception as e:
                raise e