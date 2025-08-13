import streamlit as st
from controllers import GoalsController
from components.new_goal import new_goal_popup

controller = GoalsController()

def show_goals():
    st.title('Goals')
    
    if st.button('New Goal', type= 'primary', key= 'new_goal_button'):
        new_goal_popup()
        
    st.subheader('Status')
    
    goal_to_view =st.selectbox('View', controller.get_current_goals_names(), key= 'view_goals_status')
    
    if goal_to_view:
        goal_info = controller.get_goal_info(goal_to_view)
        left, center, right = st.columns(3)
        
        left.metric('Goal', goal_info.amount + goal_info.added_amount)
        center.metric('Remaining', goal_info.remaining)
        right.metric('Expenses', goal_info.expenses)
    else:
        st.info('No goal selected')
    
    with st.expander('Current Goals'):
        df = controller.get_current_goals()
        
        if df.empty:
            st.write('No current goals')
        else:
            st.dataframe(df, hide_index= True, use_container_width= True)
    
    with st.expander('Past Goals'):
        df = controller.get_past_goals()
        
        if df.empty:
            st.write('No past goals')
        else:
            st.dataframe(df, hide_index= True, use_container_width= True)
        
    