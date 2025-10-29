import streamlit as st
from datetime import date
from utils import to_decimal
from controllers import CashTransactionController
from constants.views_icons import CASH_TRANSACTION_ICON
from components import new_template_popup, modify_template_popup
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.financial import TransactionRecord

def show_cash_transactions():
    # Page config
    st.set_page_config(
        page_title='Cash Transaction', 
        page_icon=CASH_TRANSACTION_ICON, 
        layout='centered'
    )
    controller = CashTransactionController()
    
    with st.container(key= f'add_cash_transaction_container', border= True):
        st.header('Add a cash transaction')
        
        templates_names = controller.get_templates_names()
        
        left, right = st.columns([8, 2])
        
        if templates_names:
            template_name = left.pills(
                label= 'Template',
                options= list(templates_names.keys()),
                selection_mode= 'single',
                default= None,
                key= 'transaction_template'
            )
            template_id = templates_names[template_name] if template_name else None
            template = controller.get_template(template_id) if template_id else None
        else:
            template_name = None
            template = None
            left.write('No templates found')
        
        with right:
            _left, _right = st.columns(2)
            
            if _left.button('', type= 'primary', icon= ':material/add:', help= 'Add a new template', key= 'add_template_button'):
                new_template_popup()
            
            if _right.button('', type= 'secondary', icon= ':material/edit:', help= 'Modify a template', key= 'modify_template_button', disabled= not template_name):
                template_id = templates_names[template_name]
                modify_template_popup(template_id)
                
        with st.form(key= f'add_cash_transaction', border= False, clear_on_submit= True):
            if template:
                default_values = template.default_values
                
                transaction_date = st.date_input(
                    label= 'Date',
                    value= default_values.transaction_date,
                    key= 'transaction_date_template'
                )
                
                left, right = st.columns([4,7])
                
                transaction_type = left.pills(
                    label= 'Type',
                    options= ['Abono', 'Cargo'],
                    selection_mode= 'single',
                    default= default_values.type,
                    key= 'transaction_type_template'
                )
                
                transaction_amount = right.number_input(
                    label= 'Amount',
                    min_value= 0.01,
                    value= float(default_values.amount) if default_values.amount else None,
                    key= 'transaction_amount_template'
                )
                
                categories = controller.get_categories()
                
                category = left.selectbox(
                    label= 'Category',
                    options= categories,
                    index= categories.index(controller.get_category_name(default_values.category_id)),
                    key= 'transaction_category_template'
                ) 
                
                description = right.text_input(
                    label= 'Description',
                    max_chars= 200,
                    value= default_values.description,
                    key= 'transaction_description_template'
                ) 
            else:
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
                
                categories = controller.get_categories()
                
                category = left.selectbox(
                    label= 'Category',
                    options= categories,
                    index= None,
                    key= 'transaction_category'
                ) 
                
                description = right.text_input(
                    label= 'Description',
                    max_chars= 200,
                    value= None,
                    key= 'transaction_description'
                )  
                
            if st.form_submit_button(label= 'Sumbit', type= 'primary'):
                try:
                    transaction_record = TransactionRecord(
                        user_id= controller.user_id,
                        category_id= controller.get_category_id(category) if category else None,
                        date= transaction_date,
                        description= description if description else '',
                        amount= to_decimal(transaction_amount if transaction_type == 'Abono' else -1 * transaction_amount),
                        type= TransactionType(transaction_type),
                        bank= BankName.CASH,
                        statement_type= StatementType.DEBIT,
                        filename= None
                    )
                    
                    controller.add_transaction(transaction_record)
                    
                    st.toast('Transaction added successfully', icon= ':material/check:')
                    st.rerun()
                except TypeError:
                    st.warning('Please, fill all the fields')
                except Exception as e:
                    raise e