import streamlit as st
import asyncio
from controllers import AnalysisController
from constants.views_icons import EXPENSES_ANALYSIS_ICON

def show_expenses_analysis(): 
    # Page config
    st.set_page_config(
        page_title='Expenses Analysis', 
        page_icon=EXPENSES_ANALYSIS_ICON, 
        layout='centered'
    )
    controller = AnalysisController()
    view_data = asyncio.run(controller.get_analysis_view_data('Cargo'))
    
    st.title('Expenses Analysis')

    # Check if monthly results are available
    if controller.user_have_transactions():
        st.write("Analysis based on monthly results")

        # Bar chart for Total Expenses
        st.subheader('Total Expenses by Month')

        # Display the plot
        st.altair_chart(view_data.monthly_chart)

        st.subheader('Average Expenses by Day')

        # Display the plot
        st.altair_chart(view_data.daily_chart)
    else: 
        st.info("No transactions available. Please upload files in the Home view.")