import streamlit as st
from controllers import DataViewController
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.dates import Period

controller = DataViewController()

def show_data():
    st.title('Transactions')

    # Check if data is available in session state
    if controller.user_have_transactions():
        # Get all variables to can filter the transactions
        transactions_period = controller.get_transactions_date_range()
        banks_in_transactions = controller.get_banks_in_transactions()
        
        col1, col2, col3, col4 = st.columns(4)
        

        statement_type = col1.segmented_control(
            label= "Select statement type",
            options= [statement_type.value for statement_type in StatementType],
            key= "statement_type",
        )
        
        amount_types = col2.multiselect(
            label= "Select amount type",
            options= [tt.value for tt in TransactionType],
            key= "amount_type"
        )

        date_range = col3.date_input(
            label= "Select date range",
            value= transactions_period.to_tuple(),
            key= "date_range",
        )
        
        banks = col4.multiselect(
            label= "Select bank",
            options= banks_in_transactions,
            key= "banks"
        )
        
        if statement_type:
            statement_type = StatementType(statement_type)
            
        if amount_types:
            amount_types = [TransactionType(amount_type) for amount_type in amount_types]
            
        if date_range:
            period = Period(start_date= date_range[0], end_date= date_range[1])
            
        if banks:
            banks = [BankName(bank) for bank in banks]

        try:
            filtered_transactions = controller.get_filtered_transactions(period, banks, statement_type, amount_types)
        except Exception:
            filtered_transactions = controller.get_filtered_transactions(transactions_period, banks, statement_type, amount_types)
        finally:
            edited_transactions = st.data_editor(
                data= filtered_transactions.copy(),
                column_config=  {
                    'date' : st.column_config.DateColumn(
                        label= 'Date',
                        format= 'YYYY/MM/DD'
                    ),
                    'category' : st.column_config.SelectboxColumn(
                        label= 'Category',
                        options= controller.get_categories() + [None]
                    ),
                    'description' : st.column_config.TextColumn(
                        label= 'Description',
                        max_chars= 200,
                    ),
                    'amount' : st.column_config.NumberColumn(
                        label='Amount',
                        format='$ %.2f',
                        min_value= 0.01,
                        required= True
                    ),
                    'type' : st.column_config.SelectboxColumn(
                        label= 'Type',
                        options= [tt.value for tt in TransactionType],
                        required= True
                    ),
                    'bank' : st.column_config.SelectboxColumn(
                        label= 'Bank',
                        options= [bn.value for bn in BankName],
                        required= True
                    ),
                    'statement_type' : st.column_config.SelectboxColumn(
                        label= 'Statement Type',
                        options= [statement_type.value for statement_type in StatementType],
                        required= True
                    ),
                    'filename' : st.column_config.TextColumn(
                        label= 'Filename',
                        max_chars= 50,
                    )
                },
                column_order= ['date', 'category', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'],
                use_container_width= True,
                hide_index= True,
                width = 'stretch',
                num_rows= 'dynamic',
            )
        
        if st.button(label= '', icon= ':material/save:', help= 'Save transactions'):
            if not filtered_transactions.equals(edited_transactions):
                
                controller.modify_transactions(
                    original_transactions= filtered_transactions, 
                    edited_transactions= edited_transactions
                )
                st.toast('Transactions updated successfully', icon= ':material/check:')
                st.rerun()
            else:
                st.toast('No changes to save', icon= ':material/info:')
            
    else:
        st.write("No transactions available. Please upload files or input transactions manually.")
        
