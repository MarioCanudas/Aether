import streamlit as st
from datetime import date, timedelta
from utils import to_decimal
from controllers import GoalsController
from models.dates import Period, PeriodRange
from models.goals import Goal, GoalType

today = date.today()
controller = GoalsController()

@st.dialog('New Goal')
def new_goal_popup():
    templates_names = controller.get_goals_templates_names()
    
    template_name = st.pills('Template', options= list(templates_names.keys()), default= None, key= 'new_goal_template')
    
    with st.form(key= 'new_goal_form', border= False, clear_on_submit= True):
        if template_name is not None:
            template_id = templates_names[template_name]
            template = controller.get_goal_template(template_id)
            default_values = template.default_values
            
            name = st.text_input('Name', value= default_values.name if default_values.name else None, key= 'new_goal_name')
            
            left, right = st.columns(2)
            
            goal_types = controller.get_goal_types()
            goal_type = left.selectbox('Type', goal_types, index= goal_types.index(default_values.type.value) if default_values.type else None, key= 'new_goal_type')
            
            category = right.selectbox('Category', controller.get_categories(), index= None, key= 'new_goal_category')
            
            amount = st.number_input('Amount', value= float(default_values.amount) if default_values.amount else None, key= 'new_goal_amount')
            
            period_ranges = controller.get_period_ranges()
            period_range = st.selectbox('Period range', period_ranges, index= period_ranges.index(default_values.period_range.value) if default_values.period_range else 0, key= 'new_goal_period_range')
            
        else:
            name = st.text_input('Name', value= None, key= 'new_budget_name')
            
            left, right = st.columns(2)
            
            goal_type = left.selectbox('Type', controller.get_goal_types(), index= 0, key= 'new_goal_type')
            
            category = right.selectbox('Category', controller.get_categories(), index= None, key= 'new_budget_category')

            amount = st.number_input('Amount', value= 0, key= 'new_budget_amount')
            
            period_range = st.selectbox('Period range', controller.get_period_ranges(), index= 0, key= 'new_budget_period_range')
            
        if period_range != PeriodRange.OTHER.value:
            left, right = st.columns(2)
            
            start_date = left.date_input('Start date', value= today, key= 'new_budget_start_date')
            end_date =  right.date_input('End date', value= controller.get_end_date(start_date, PeriodRange(period_range)), key= 'new_budget_end_date')
        else:
            default_date = (today, today + timedelta(days= 7))
            date_range = st.date_input('Period', value= default_date, key= 'new_budget_start_date')
            
            # Unpacking the date range with conditional unpacking to avoid type errors
            start_date, end_date = date_range if len(date_range) == 2 else default_date
            
        if st.form_submit_button('Add budget', type= 'primary'):
            category_id = controller.get_category_id(category)
            goal_type = GoalType(goal_type)
            
            new_goal = Goal(
                user_id= st.session_state.user_id,
                name= name, 
                type= goal_type,
                category_id= category_id, 
                amount= to_decimal(amount), 
                period= Period(start_date= start_date, end_date= end_date),
                related_transaction_type= goal_type.transaction_type
            )
            
            controller.add_goal(new_goal)
            st.rerun()
        
@st.dialog('Add amount')
def add_amount_popup(goal_id: int) -> None:
    amount = st.number_input('Amount', value= 0, key= f'add_amount_amount_{goal_id}')
    
    if st.button('Add amount', type= 'primary', key= f'add_amount_add_button_{goal_id}', disabled= amount <= 0):
        amount = to_decimal(amount)
        controller.add_amount(goal_id, amount)
        st.rerun()