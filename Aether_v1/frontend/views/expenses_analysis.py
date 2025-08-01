import streamlit as st
from controllers import AnalysisController

controller = AnalysisController()

def show_expenses_analysis(): 
    st.title('Expenses Analysis')

    # Check if monthly results are available
    if controller.user_have_monthly_results():
        st.write("Analysis based on monthly results")

        # Bar chart for Total Expenses
        st.subheader('Total Expenses by Month')
        monthly_expenses_chart = controller.get_bar_chart_monthly_total_by_category('Cargo')

        # Display the plot
        st.pyplot(monthly_expenses_chart)
    else:
        st.info("No monthly results available. Please upload files in the Home view.")

    if controller.user_have_transactions():
            st.subheader('Average Expenses by Day')
            
            daily_expenses_chart = controller.get_bar_chart_daily_total_by_category('Cargo')
            
            # Display the plot
            st.pyplot(daily_expenses_chart)
    else: 
        st.info("No transactions available. Please upload files in the Home view.")