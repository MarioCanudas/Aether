import streamlit as st
from controllers import AnalysisController

analysis_controller = AnalysisController()

def show_income_analysis():
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