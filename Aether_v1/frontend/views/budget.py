import streamlit as st
from controllers import BudgetController
from components.new_budget import new_budget_popup

controller = BudgetController()

def show_budget():
    st.title('Budget')
    
    if st.button('New Budget', type= 'primary', key= 'new_budget_button'):
        new_budget_popup()
        
    st.subheader('Budget status')
    
    budget_to_view =st.selectbox('View', controller.get_current_budgets_names(), key= 'view_budgets_status')
    budget_info = controller.get_budget_info(budget_to_view)
    
    left, center, right = st.columns(3)
    
    left.metric('Budget', budget_info.amount + budget_info.added_amount)
    center.metric('Remaining', budget_info.remaining)
    right.metric('Expenses', budget_info.expenses)
    
    with st.expander('Current Budgets'):
        st.dataframe(controller.get_current_budgets(), hide_index= True, use_container_width= True)
    
    with st.expander('Past Budgets'):
        df = controller.get_past_budgets()
        
        if df.empty:
            st.write('No past budgets')
        else:
            st.dataframe(df, hide_index= True, use_container_width= True)
        
    