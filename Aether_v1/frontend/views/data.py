from typing import cast

import streamlit as st
from constants.views_icons import TRANSACTIONS_ICON
from controllers import DataViewController
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.dates import Period


def show_data():
    # Page config
    st.set_page_config(page_title="Transactions", page_icon=TRANSACTIONS_ICON, layout="wide")
    controller = DataViewController()

    st.title("Transactions")

    # Check if data is available in session state
    if controller.user_have_transactions():
        # Get all variables to can filter the transactions
        transactions_period = controller.get_transactions_date_range()
        banks_in_transactions = controller.get_banks_in_transactions()

        col1, col2, col3, col4 = st.columns(4)

        statement_type = col1.segmented_control(
            label="Select statement type",
            options=[statement_type.value for statement_type in StatementType],
            key="statement_type",
        )

        amount_types = col2.multiselect(
            label="Select amount type",
            options=[tt.value for tt in TransactionType],
            key="amount_type",
        )

        date_range = col3.date_input(
            label="Select date range",
            value=transactions_period.to_tuple(),
            key="date_range",
        )

        banks = col4.multiselect(label="Select bank", options=banks_in_transactions, key="banks")

        if statement_type:
            statement_type = StatementType(statement_type)

        if amount_types:
            amount_types = [TransactionType(amount_type) for amount_type in amount_types]

        if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
            period = Period(start_date=date_range[0], end_date=date_range[1])
        else:
            period = transactions_period

        if banks:
            # banks is list[Any], need manual cast logic or trust list comprehension
            banks_enum: list[BankName] = [BankName(bank) for bank in banks]
        else:
            banks_enum = []

        # Ensure strict typing for arguments passed to get_filtered_transactions
        # Assuming get_filtered_transactions expects optional lists
        filtered_statement_type = StatementType(statement_type) if statement_type else None

        filtered_amount_types: list[TransactionType] | None = None
        if amount_types:
            filtered_amount_types = [TransactionType(t) for t in amount_types]

        try:
            filtered_transactions = controller.get_filtered_transactions(
                period, banks_enum, filtered_statement_type, filtered_amount_types
            )
        except Exception:
            filtered_transactions = controller.get_filtered_transactions(
                transactions_period,
                banks_enum,
                filtered_statement_type,
                filtered_amount_types,  # Fallback
            )
        finally:
            categories_list = cast(list[str], controller.get_categories())

            edited_transactions = st.data_editor(
                data=filtered_transactions.copy(),
                column_config={
                    "date": st.column_config.DateColumn(label="Date", format="YYYY/MM/DD"),
                    "category": st.column_config.SelectboxColumn(
                        label="Category",
                        options=categories_list,
                    ),
                    "description": st.column_config.TextColumn(
                        label="Description",
                        max_chars=200,
                    ),
                    "amount": st.column_config.NumberColumn(
                        label="Amount", format="$ %.2f", min_value=0.01, required=True
                    ),
                    "type": st.column_config.SelectboxColumn(
                        label="Type",
                        options=[tt.value for tt in TransactionType],
                        required=True,
                    ),
                    "bank": st.column_config.SelectboxColumn(
                        label="Bank",
                        options=[bn.value for bn in BankName],
                        required=True,
                    ),
                    "card_name": st.column_config.SelectboxColumn(
                        label="Card",
                        options=controller.get_cards(),
                        required=False,
                    ),
                    "statement_type": st.column_config.SelectboxColumn(
                        label="Statement Type",
                        options=[statement_type.value for statement_type in StatementType],
                        required=True,
                    ),
                    "filename": st.column_config.TextColumn(
                        label="Filename",
                        max_chars=50,
                    ),
                },
                column_order=[
                    "date",
                    "category",
                    "description",
                    "amount",
                    "type",
                    "bank",
                    "card_name",
                    "statement_type",
                    "filename",
                ],
                use_container_width=True,
                hide_index=True,
                width="stretch",
                num_rows="dynamic",
            )

        if st.button(label="", icon=":material/save:", help="Save transactions"):
            if not filtered_transactions.equals(edited_transactions):
                controller.modify_transactions(
                    original_transactions=filtered_transactions,
                    edited_transactions=edited_transactions,
                )
                st.toast("Transactions updated successfully", icon=":material/check:")
                st.rerun()
            else:
                st.toast("No changes to save", icon=":material/info:")

        if controller.user_have_potential_duplicates():
            potential_dupl_trans = controller.get_potential_duplicate_transactions()

            potential_dupl_trans_df = controller.transactions_to_df(potential_dupl_trans)

            st.dataframe(potential_dupl_trans_df)

    else:
        st.info("No transactions available. Please upload files or input transactions manually.")
