import streamlit as st
import datetime
from controllers import DataViewController

controller = DataViewController()

def show_data():
    st.title('Data')

    # Check if data is available in session state
    if controller.user_have_transactions() and controller.user_have_monthly_results():
        st.write("Data available in Data View")
        
        df_monthly_results = controller.get_monthly_results()

        # Display the processed data table or use it for further analysis
        st.header("Transactions")
        
        transactions_date_range = controller.get_transactions_date_range()
        
        date_range = st.date_input(
            label= "Select date range",
            value= transactions_date_range,
            min_value= transactions_date_range[0],
            max_value= transactions_date_range[1],
            key= "date_range"
        )
        
        try:
            filtered_transactions = controller.get_filtered_transactions(date_range)
        except:
            st.warning("Select a date range to view transactions")
        finally:
            if 'filtered_transactions' in locals():
                st.dataframe(filtered_transactions)
        
        st.header("Monthly Results")
        st.dataframe(df_monthly_results)
    else:
        st.write("No data available. Please upload files in the Home view.")
