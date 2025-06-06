import streamlit as st
from controllers import AnalysisController

controller = AnalysisController()

def show_expenses_analysis(): 
    st.title('Expenses Analysis')

    # Check if monthly results are available
    if 'all_monthly_results' in st.session_state and not st.session_state.all_monthly_results.empty:
        st.write("Analysis based on monthly results")

        # Bar chart for Total Expenses
        st.subheader('Total Expenses by Month')
        expenses_chart = controller.get_bar_chart_monthly_total_by_category('Cargo')

        # Display the plot
        st.pyplot(expenses_chart)

        # Check if processed data is available for daily analysis
        if 'all_processed_data' in st.session_state and not st.session_state.all_processed_data.empty:
            st.subheader('Average Expenses by Day')
            
            expenses_chart = controller.get_bar_chart_daily_total_by_category('Cargo')
            
            # Display the plot
            st.pyplot(expenses_chart)
    else:
        st.write("No monthly results available. Please upload files in the Home view.")
