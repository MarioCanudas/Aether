import streamlit as st
from datetime import date, timedelta
from utils import to_decimal
from controllers import BudgetController
from models.dates import Period, PeriodRange
from models.financial import Budget

today = date.today()
controller = BudgetController()

@st.dialog('New Budget')
def new_budget_popup():
    left, right = st.columns([2, 3])
    
    category = left.selectbox('Category', controller.get_categories(), index= None, key= 'new_budget_category')

    name = right.text_input('Name', value= None, key= 'new_budget_name')
    
    amount = st.number_input('Amount', value= 0, key= 'new_budget_amount')
    
    period_range = st.selectbox('Period range', controller.get_period_ranges(), index= 0, key= 'new_budget_period_range')
    
    if period_range != PeriodRange.OTHER.value:
        left, right = st.columns(2)
        
        start_date = left.date_input('Start date', value= today, key= 'new_budget_start_date')
        end_date =  right.date_input('End date', value= controller.get_end_date(start_date, period_range), key= 'new_budget_end_date')
    else:
        default_date = (today, today + timedelta(days= 7))
        date_range = st.date_input('Period', value= default_date, key= 'new_budget_start_date')
        
        # Unpacking the date range with conditional unpacking to avoid type errors
        start_date, end_date = date_range if len(date_range) == 2 else default_date
        
    if name and category and amount > 0 and start_date and end_date and st.session_state.user_id:
        category_id = controller.get_category_id(category)
        
        new_budget = Budget(
            user_id= st.session_state.user_id,
            name= name, 
            category_id= category_id, 
            amount= to_decimal(amount), 
            period= Period(start_date= start_date, end_date= end_date),
        )
    else: new_budget = None
    
    if st.button('Add budget', type= 'primary', key= 'new_budget_add_button', disabled= new_budget is None) and new_budget is not None:
        controller.add_budget(new_budget)
        st.rerun()