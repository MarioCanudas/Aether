import streamlit as st
from controllers import AnalysisController
from constants.views_icons import INCOME_ANALYSIS_ICON

def show_income_analysis():
    # Page config
    st.set_page_config(
        page_title='Income Analysis', 
        page_icon=INCOME_ANALYSIS_ICON, 
        layout='centered'
    )
    analysis_controller = AnalysisController()
    
    st.title('Income Analysis')

    # Check if monthly results are available
    if analysis_controller.user_have_transactions():
        st.write("Analysis based on monthly results")

        # Bar chart for Total Income
        st.subheader('Total Income by Month')
        monthly_income_chart = analysis_controller.get_bar_chart_monthly_total_by_category('Abono')

        st.pyplot(monthly_income_chart)
    
        st.subheader('Average Income by Day')
        
        daily_income_chart = analysis_controller.get_bar_chart_daily_total_by_category('Abono')

        st.pyplot(daily_income_chart)
            
    else: 
        st.info("No transactions available. Please upload files in the Home view.")