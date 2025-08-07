import streamlit as st
from components.new_goal import new_goal_popup

def show_goals():    
    st.header('Goals')   
    
    if st.button('New Goal', type= 'primary', key= 'new_goal_button'):
        new_goal_popup()
    
    st.subheader('Goals')