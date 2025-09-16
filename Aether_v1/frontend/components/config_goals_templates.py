import streamlit as st
from utils import to_decimal
from controllers import GoalsController
from models.dates import PeriodRange
from models.goals import GoalType
from models.templates import GoalDefaultValues, Template, TemplateType

controller = GoalsController()

@st.dialog('Goals Templates')
def config_goals_templates_popup():
    templates_names = controller.get_goals_templates_names()
    
    with st.expander('Add template', icon= ':material/add:', expanded= False):
        with st.form(key= 'add_goal_template_form', border= False, clear_on_submit= True):
            name = st.text_input('Name', value= None, key= 'add_goal_template_name')
            
            description = st.text_input('Description', value= None, max_chars= 200, key= 'add_goal_template_description')
            
            left, right = st.columns(2)
            
            goal_type = left.selectbox('Type', controller.get_goal_types(), index= 0, key= 'add_goal_template_type')
            
            category = right.selectbox('Category', controller.get_categories(), index= None, key= 'add_goal_template_category')
            
            amount = st.number_input('Amount', value= 0, key= 'add_goal_template_amount')
            
            period_range = st.selectbox('Period range', controller.get_period_ranges(), index= 0, key= 'add_goal_template_period_range')
            
            if st.form_submit_button('Add template', type= 'primary', disabled= not name and not goal_type):
                category_id = controller.get_category_id(category)
                goal_type = GoalType(goal_type)
                
                new_default_values = GoalDefaultValues(
                    name= name,
                    type= goal_type,
                    category_id= category_id,
                    amount= to_decimal(amount),
                    period_range= PeriodRange(period_range) if period_range else None
                )
                
                new_template = Template(
                    user_id= controller.user_id,
                    template_name= name,
                    template_description= description,
                    template_type= TemplateType.GOAL,
                    default_values= new_default_values
                )
                
                controller.add_goal_template(new_template)
        
    with st.expander('Modify template', icon= ':material/edit:', expanded= False):
        template_name = st.selectbox('Name', options= list(templates_names.keys()), index= None, key= 'choose_goal_template_name')
        
        with st.form(key= 'modify_goal_template_form', border= False, clear_on_submit= True):
            if template_name is not None:
                template_id = templates_names[template_name]
                template_to_modify = controller.get_goal_template(template_id)
                default_values: GoalDefaultValues = template_to_modify.default_values
                
                name = st.text_input('Modify Name', value= template_to_modify.template_name, key= 'modify_goal_template_name')
                
                description = st.text_input('Description', value= template_to_modify.template_description, max_chars= 200, key= 'modify_goal_template_description')
                
                left, right = st.columns(2)
                
                goal_types = controller.get_goal_types()
                goal_type = left.selectbox(
                    'Type', 
                    goal_types, 
                    index= goal_types.index(default_values.type) if default_values.type else None, 
                    key= 'modify_goal_template_type'
                )
                
                categories = controller.get_categories()
                category = right.selectbox(
                    'Category', 
                    categories, 
                    index= categories.index(controller.get_category_by_id(default_values.category_id)) if default_values.category_id else None, 
                    key= 'modify_goal_template_category'
                )

                amount = st.number_input(
                    'Amount', 
                    value= float(default_values.amount) if default_values.amount else None, 
                    min_value= 0.01, 
                    key= 'modify_goal_template_amount'
                )
                
                period_ranges = controller.get_period_ranges()
                period_range = st.selectbox(
                    'Period range', 
                    period_ranges, 
                    index= period_ranges.index(default_values.period_range.value) if default_values.period_range else None, 
                    key= 'modify_goal_template_period_range'
                )
                
            else:
                st.info('Select a template to modify')
                
            if st.form_submit_button('Modify template', type= 'primary', disabled= not template_name):
                category_id = controller.get_category_id(category)
                goal_type = GoalType(goal_type)
                
                updated_default_values = GoalDefaultValues(
                    name= name,
                    type= goal_type,
                    category_id= category_id,
                    amount= to_decimal(amount),
                    period_range= PeriodRange(period_range)
                )
                
                updated_template = Template(
                    user_id= controller.user_id,
                    template_name= template_name,
                    template_description= template_to_modify.template_description,
                    template_type= TemplateType.GOAL,
                    default_values= updated_default_values
                )
                
                controller.update_goal_template(template_id, updated_template)
            