import streamlit as st
import asyncio
from controllers import AnalysisController
from components import period_select_box
from constants.views_icons import EXPENSES_ANALYSIS_ICON

def show_expenses_analysis(): 
    # Page config
    st.set_page_config(
        page_title='Expenses Analysis', 
        page_icon=EXPENSES_ANALYSIS_ICON, 
        layout='wide'
    )
    controller = AnalysisController()
    view_data = asyncio.run(controller.get_analysis_view_data('Cargo'))
    
    st.title('Expenses Analysis')

    # Check if monthly results are available
    if controller.user_have_transactions():
        selected_period = period_select_box(key= "period_selectbox_expenses")

        left, right = st.columns([3, 1.5])
        
        with left:
            with st.container(border= True):
                left_1, center_1, right_1 = st.columns(3)
                
                left_1.metric(
                    'Accumulated Expenses', 
                    value= 0,
                    help= 'Accumulated expenses by the selected period.'
                )
                
                center_1.metric(
                    'Max Expenses',
                    value= 0,
                    help= 'Max expenses by the selected period.'
                )
                
                right_1.metric(
                    'Expenses frecuency',
                    value= 0,
                    help= 'Expenses frecuency by the selected period.'
                )
            
            with st.container(border= True):
                st.subheader('Average Expenses by Day')
                st.altair_chart(view_data.daily_chart)
        
        with right:
            with st.container(border= True):
                st.subheader('Expenses by Category')
            
        with st.container(border= True):
            st.subheader('Total Expenses by Month in the current year')
            st.altair_chart(view_data.monthly_chart)
            
    else: 
        st.info("No transactions available. Please upload files in the Home view.")