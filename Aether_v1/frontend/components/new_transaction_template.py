import streamlit as st
from datetime import date
from utils import to_decimal
from controllers import AddTransactionController
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.templates import Template, TemplateType, TransactionDefaultValues

controller = AddTransactionController()

@st.dialog('New Transaction Template', width= 'medium')
def new_transaction_template_popup() -> None:
    with st.form(key= 'new_transaction_template_form', border= False):
        left, right = st.columns([1, 3])
        
        template_name = left.text_input('Name', value= None, max_chars= 50, key= 'new_transaction_template_name')
        
        template_description = right.text_input(
            'Description', 
            value= None, 
            max_chars= 200, 
            key= 'new_template_description'
        )
        
        transaction_date = st.date_input('Date', value= date.today(), key= 'new_transaction_template_date')
        
        transaction_statement_type = st.pills(
            'Statement Type', 
            options= StatementType.get_values(), 
            selection_mode= 'single', 
            default= None, 
            key= 'new_transaction_template_statement_type'
        )
        
        if transaction_statement_type in StatementType.get_values():
            transaction_statement_type = StatementType(transaction_statement_type)
        
        left, right = st.columns([4, 7])
        
        transaction_bank_name = left.selectbox(
            'Bank Name', 
            options= BankName.get_values(), 
            index= None, 
            key= 'new_transaction_template_bank_name'
        )
        
        if transaction_bank_name in BankName.get_values():
            transaction_bank_name = BankName(transaction_bank_name)
        
        transaction_card_name = right.selectbox(
            'Card Name', 
            options= controller.get_cards(), 
            index= None, 
            key= 'new_transaction_template_card_name'
        )
        
        if transaction_card_name:
            transaction_card_id = controller.get_card_by_name(transaction_card_name).card_id
        
        transaction_type = left.pills(
            'Type', 
            options= [tt.value for tt in TransactionType if tt != TransactionType.INITIAL_BALANCE], 
            selection_mode= 'single', 
            default= None, 
            key= 'new_transaction_template_transaction_type'
        )
        
        transaction_amount = right.number_input(
            label= 'Amount',
            min_value= 0.01,
            value= None,
            key= 'new_transaction_template_transaction_amount'
        )
        
        transaction_category = left.selectbox(
            label= 'Category',
            options= controller.get_categories(),
            index= None,
            key= 'new_transaction_template_transaction_category'
        )
        
        transaction_description = right.text_input(
            label= 'Description',
            max_chars= 200,
            value= None,
            key= 'new_transaction_template_transaction_description'
        )
        
        if st.form_submit_button('Add transaction template', type= 'primary'):
            if transaction_category:
                transaction_category_id = controller.get_category_id(transaction_category)
                
            try:
                # First verify that the transaction default values are valid
                default_values = TransactionDefaultValues(
                    transaction_date= transaction_date,
                    type= TransactionType(transaction_type),
                    amount= to_decimal(transaction_amount) if transaction_amount else None,
                    category_id= transaction_category_id,
                    description= transaction_description,
                    statement_type= StatementType(transaction_statement_type),
                    bank_name= transaction_bank_name,
                    card_id= transaction_card_id
                )
                
                # Then create the template
                template = Template(
                    user_id= controller.user_id,
                    template_name= template_name,
                    template_description= template_description,
                    template_type= TemplateType.TRANSACTION,
                    default_values= default_values
                )
                
                controller.add_template(template)
                st.rerun()
            except ValueError as e:
                st.warning(f'Some field is invalid, try again')
            except Exception as e:
                st.error(f'An error occurred: {e}')
        