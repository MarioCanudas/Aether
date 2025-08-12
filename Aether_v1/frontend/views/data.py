import streamlit as st
import datetime
from controllers import DataViewController

controller = DataViewController()

def show_data():
    st.title('Data')

    # Check if data is available in session state
    if controller.user_have_transactions() and controller.user_have_monthly_results():
        st.write("Data available in Data View")
        # Get all variables to can filter the transactions
        df_monthly_results = controller.get_monthly_results()
        transactions_date_range = controller.get_transactions_date_range()
        banks_in_transactions = controller.get_banks_in_transactions()
        
        # Display the transactions table
        st.header("Transactions")
        
        col1, col2, col3, col4 = st.columns(4)
        

        statement_type = col1.segmented_control(
            label= "Select statement type",
            options= ['debit', 'credit'],
            key= "statement_type",
        )
        
        amount_type = col2.multiselect(
            label= "Select amount type",
            options= ['Abono', 'Cargo', 'Saldo inicial'],
            key= "amount_type"
        )

        date_range = col3.date_input(
            label= "Select date range",
            value= transactions_date_range,
            min_value= transactions_date_range[0],
            max_value= transactions_date_range[1],
            key= "date_range"
        )
        
        banks = col4.multiselect(
            label= "Select bank",
            options= banks_in_transactions,
            key= "banks"
        )

        try:
            filtered_transactions = controller.get_filtered_transactions(date_range, banks, statement_type, amount_type)
        except Exception as e:
            filtered_transactions = controller.get_filtered_transactions(transactions_date_range, banks, statement_type, amount_type)
        finally:
            st.dataframe(filtered_transactions, hide_index=True)
        
        st.header("Monthly Results")
        st.dataframe(df_monthly_results, hide_index=True)
    else:
        st.write("No data available. Please upload files in the Home view.")
