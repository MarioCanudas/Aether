import streamlit as st
from utils import to_decimal
from controllers import CashTransactionController
from models.amounts import TransactionType
from models.templates import TransactionTemplate

controller = CashTransactionController()

@st.dialog('Modify Template')
def modify_template_popup(template_id: int) -> None:
    with st.form(key= 'modify_template_form', border= False):
        template = controller.get_template(template_id)
        
        if template is None:
            st.error('Template not found')
        else:
            left, right = st.columns([1, 3])
        
            template_name = left.text_input('Name', value= template.template_name, max_chars= 50, key= 'update_template_name')
            
            template_description = right.text_input(
                'Description', 
                value= template.template_description, 
                max_chars= 200, 
                key= 'update_template_description'
            )
            
            transaction_date = st.date_input('Date', value= template.transaction_date, key= 'update_transaction_template_date')
            
            left, right = st.columns([4, 7])
            
            transaction_type = left.pills(
                'Type', 
                options= [tt.value for tt in TransactionType if tt != TransactionType.INITIAL_BALANCE], 
                selection_mode= 'single', 
                default= template.transaction_type, 
                key= 'update_transaction_template_type'
            )
            
            transaction_amount = right.number_input(
                label= 'Amount',
                min_value= 0.01,
                value= float(template.transaction_amount),
                key= 'update_transaction_template_amount'
            )
            
            transaction_category = left.selectbox(
                label= 'Category',
                options= controller.get_categories(),
                index= template.transaction_category_id,
                key= 'update_transaction_template_category'
            )
            
            transaction_description = right.text_input(
                label= 'Description',
                max_chars= 200,
                value= template.transaction_description,
                key= 'update_transaction_template_description'
            )
            
            if st.form_submit_button('Modify template', type= 'primary'):
                if transaction_category:
                    transaction_category_id = controller.get_category_id(transaction_category)
                    
                try:
                    updated_template = TransactionTemplate(
                        user_id= controller.user_id,
                        template_name= template_name,
                        template_description= template_description,
                        transaction_date= transaction_date,
                        transaction_type= TransactionType(transaction_type),
                        transaction_amount= to_decimal(transaction_amount),
                        transaction_category_id= transaction_category_id,
                        transaction_description= transaction_description
                    )
                    
                    controller.update_template(template_id, updated_template)
                    st.rerun()
                except ValueError as e:
                    st.warinig('Some field is invalid, try again.')
                except Exception as e:
                    st.error(f'An error occurred: {e}')