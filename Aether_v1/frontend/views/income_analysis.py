import streamlit as st
from controllers import AnalysisController

analysis_controller = AnalysisController()

def show_income_analysis():
    st.title('Income Analysis')

    # Check if monthly results are available
    if 'all_monthly_results' in st.session_state and not st.session_state.all_monthly_results.empty:
        st.write("Analysis based on monthly results")

        # Bar chart for Total Income
        st.subheader('Total Income by Month')
        income_chart = analysis_controller.get_bar_chart_monthly_total_by_category('Abono')

        st.pyplot(income_chart)

        # Check if processed data is available for daily income analysis
        if 'all_processed_data' in st.session_state and not st.session_state.all_processed_data.empty:
            st.subheader('Average Income by Day')
            
            income_chart = analysis_controller.get_bar_chart_daily_total_by_category('Abono')

            st.pyplot(income_chart)
    else:
        st.write("No monthly results available. Please upload files in the Home view.")
