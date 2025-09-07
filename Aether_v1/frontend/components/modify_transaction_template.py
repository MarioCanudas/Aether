import streamlit as st
from utils import to_decimal
from controllers import CashTransactionController
from models.amounts import TransactionType
from models.templates import Template, TemplateType, TransactionDefaultValues

controller = CashTransactionController()

@st.dialog('Modify Template')
def modify_template_popup(template_id: int) -> None:
    with st.form(key= 'modify_template_form', border= False):
        template = controller.get_template(template_id)
        default_values = template.default_values
        
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
            
            transaction_date = st.date_input('Date', value= default_values.transaction_date, key= 'update_transaction_template_date')
            
            left, right = st.columns([4, 7])
            
            transaction_type = left.pills(
                'Type', 
                options= [tt.value for tt in TransactionType if tt != TransactionType.INITIAL_BALANCE], 
                selection_mode= 'single', 
                default= default_values.type, 
                key= 'update_transaction_template_type'
            )
            
            transaction_amount = right.number_input(
                label= 'Amount',
                min_value= 0.01,
                value= float(default_values.amount) if default_values.amount else None,
                key= 'update_transaction_template_amount'
            )
            
            categories = controller.get_categories()
            
            transaction_category = left.selectbox(
                label= 'Category',
                options= categories,
                index= categories.index(controller.get_category_name(default_values.category_id)),
                key= 'update_transaction_template_category'
            )
            
            transaction_description = right.text_input(
                label= 'Description',
                max_chars= 200,
                value= default_values.description,
                key= 'update_transaction_template_description'
            )
            
            if st.form_submit_button('Modify template', type= 'primary'):
                if transaction_category:
                    transaction_category_id = controller.get_category_id(transaction_category)
                    
                try:
                    # First verify that the transaction default values are valid
                    default_values = TransactionDefaultValues(
                        transaction_date= transaction_date,
                        type= TransactionType(transaction_type),
                        amount= to_decimal(transaction_amount) if transaction_amount else None,
                        category_id= transaction_category_id,
                        description= transaction_description
                    )
                    
                    # Then create the modified template
                    updated_template = Template(
                        user_id= controller.user_id,
                        template_name= template_name,
                        template_description= template_description,
                        template_type= TemplateType.TRANSACTION,
                        default_values= default_values
                    )
                    
                    controller.update_template(template_id, updated_template)
                    st.rerun()
                except ValueError as e:
                    st.warning(f'Some field is invalid, try again.')
                except Exception as e:
                    st.error(f'An error occurred: {e}')