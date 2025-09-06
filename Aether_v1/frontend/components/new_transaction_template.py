import streamlit as st
from datetime import date
from controllers import CashTransactionController
from models.amounts import TransactionType
from models.templates import TransactionTemplate

controller = CashTransactionController()

@st.dialog('New Template')
def new_template_popup() -> None:
    with st.form(key= 'new_template_form', border= False):
        left, right = st.columns([1, 3])
        
        template_name = left.text_input('Name', value= None, max_chars= 50, key= 'new_template_name')
        
        template_description = right.text_input(
            'Description', 
            value= None, 
            max_chars= 200, 
            key= 'new_template_description'
        )
        
        transaction_date = st.date_input('Date', value= date.today(), key= 'new_template_date')
        
        left, right = st.columns([4, 7])
        
        transaction_type = left.pills(
            'Type', 
            options= [tt.value for tt in TransactionType if tt != TransactionType.INITIAL_BALANCE], 
            selection_mode= 'single', 
            default= None, 
            key= 'new_transaction_template_type'
        )
        
        transaction_amount = right.number_input(
            label= 'Amount',
            min_value= 0.01,
            value= None,
            key= 'new_transaction_template_amount'
        )
        
        transaction_category = left.selectbox(
            label= 'Category',
            options= controller.get_categories(),
            index= None,
            key= 'new_transaction_template_category'
        )
        
        transaction_description = right.text_input(
            label= 'Description',
            max_chars= 200,
            value= None,
            key= 'new_transaction_template_description'
        )
        
        if st.form_submit_button('Add template', type= 'primary'):
            if transaction_category:
                transaction_category_id = controller.get_category_id(transaction_category)
                
            try:
                template = TransactionTemplate(
                    user_id= controller.user_id,
                    template_name= template_name,
                    template_description= template_description,
                    transaction_date= transaction_date,
                    transaction_type= TransactionType(transaction_type),
                    transaction_amount= transaction_amount,
                    transaction_category_id= transaction_category_id,
                    transaction_description= transaction_description
                )
                
                controller.add_template(template)
                st.rerun()
            except ValueError as e:
                st.warinig('Some field is invalid, try again.')
            except Exception as e:
                st.error(f'An error occurred: {e}')
        