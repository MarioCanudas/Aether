import streamlit as st
import asyncio
from controllers import AnalysisController
from components import period_select_box
from constants.views_icons import INCOME_ANALYSIS_ICON

def show_income_analysis():
    # Page config
    st.set_page_config(
        page_title='Income Analysis', 
        page_icon=INCOME_ANALYSIS_ICON, 
        layout='centered'
    )
    analysis_controller = AnalysisController()
    view_data = asyncio.run(analysis_controller.get_analysis_view_data('Abono'))
    
    st.title('Income Analysis')

    # Check if monthly results are available
    if analysis_controller.user_have_transactions():
        selected_period = period_select_box(key= "period_selectbox_income")

        # Bar chart for Total Income
        st.subheader('Total Income by Month')

        st.altair_chart(view_data.monthly_chart)
    
        st.subheader('Average Income by Day')

        st.altair_chart(view_data.daily_chart)
            
    else: 
        st.info("No transactions available. Please upload files in the Home view.")