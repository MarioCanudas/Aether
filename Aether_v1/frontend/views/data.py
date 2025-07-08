import streamlit as st
from controllers.transaction_processor_controller import TransactionProcessorController

controller = TransactionProcessorController()

def show_data():
    st.title('Data')

    # Check if data is available in session state
    if controller.user_have_transactions() and controller.user_have_monthly_results():
        st.write("Data available in Data View")
        
        df_transactions = controller.get_transactions()
        df_monthly_results = controller.get_monthly_results()

        # Display the processed data table or use it for further analysis
        st.header("Transactions")
        st.dataframe(df_transactions)
        
        st.header("Monthly Results")
        st.dataframe(df_monthly_results)
    else:
        st.write("No data available. Please upload files in the Home view.")
