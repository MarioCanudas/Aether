import streamlit as st
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
    
    st.title('Expenses Analysis')

    # Check if monthly results are available
    if controller.user_have_transactions():
        st.write("Analysis based on monthly results")

        # Bar chart for Total Expenses
        st.subheader('Total Expenses by Month')
        monthly_expenses_chart = controller.get_bar_chart_monthly_total_by_category('Cargo')

        # Display the plot
        st.pyplot(monthly_expenses_chart)

        st.subheader('Average Expenses by Day')
        
        daily_expenses_chart = controller.get_bar_chart_daily_total_by_category('Cargo')
        
        # Display the plot
        st.pyplot(daily_expenses_chart)
    else: 
        st.info("No transactions available. Please upload files in the Home view.")