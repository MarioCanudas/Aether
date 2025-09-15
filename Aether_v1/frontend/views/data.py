import streamlit as st
from controllers import DataViewController

controller = DataViewController()

def show_data():
    st.title('Transactions')

    # Check if data is available in session state
    if controller.user_have_transactions():
        # Get all variables to can filter the transactions
        transactions_date_range = controller.get_transactions_date_range()
        banks_in_transactions = controller.get_banks_in_transactions()
        
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
        except Exception:
            filtered_transactions = controller.get_filtered_transactions(transactions_date_range, banks, statement_type, amount_type)
        finally:
            st.dataframe(filtered_transactions, hide_index=True)
    else:
        st.write("No transactions available. Please upload files or input transactions manually.")
        
