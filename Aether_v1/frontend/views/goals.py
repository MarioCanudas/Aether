import streamlit as st
from controllers import GoalsController
from components.new_goal import new_goal_popup, add_amount_popup
from models.goals import GoalStatus

controller = GoalsController()

def show_goals():
    st.title('Goals')
    
    if st.button('New Goal', type= 'primary', key= 'new_goal_button'):
        new_goal_popup()
        
    st.subheader('Info')
    
    goal_to_view = st.selectbox('Choose a goal', controller.get_current_goals_names(), key= 'view_goals_status')
    
    if goal_to_view:
        goal_info = controller.get_goal_info(goal_to_view)
        
        left, right = st.columns(2)
        
        left.write(
            f"""
            **Name:** {goal_info.name} \n
            **Type:** {goal_info.type.value}
            """
        )
        
        right.write(
            f"""
            **Category:** {goal_info.category} \n
            **Period:** {goal_info.start_date} - {goal_info.end_date}
            """
        )
        
        st.badge(goal_info.status.value, icon= goal_info.status.icon, color= goal_info.status.color)
        
        left, center, right = st.columns(3)
        
        left.metric('Goal', goal_info.amount + goal_info.added_amount)
        center.metric('Remaining', goal_info.remaining)
        right.metric(
            goal_info.custom_current_amount_name, goal_info.current_amount,
            delta= f'{goal_info.progress_porcentage * 100:.2f}%',
            delta_color= 'normal' if goal_info.progress_porcentage < 1 else 'inverse'
            )
        
        if st.button('Add amount', type= 'primary', key= 'add_amount_button'):
            add_amount_popup(goal_info.goal_id)
        
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
        
    