from datetime import date

import streamlit as st
from controllers import AddTransactionController
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.transactions import Transaction
from utils import to_decimal


def show_edit_transaction(t: Transaction) -> None:
    controller = AddTransactionController()

    with st.form(key="edit_transaction_form", border=False):
        transaction_date = st.date_input(label="Date", value=t.date, key="transaction_date")

        transaction_statement_type = st.pills(
            label="Statement Type",
            options=StatementType.get_values(),
            selection_mode="single",
            default=t.statement_type.value if t.statement_type else None,
            key="transaction_statement_type",
            width="stretch",
        )

        transaction_statement_type = (
            StatementType(transaction_statement_type) if transaction_statement_type else None
        )

        left, right = st.columns([4, 7])

        transaction_bank = left.selectbox(
            label="Bank",
            options=BankName.get_values(),
            index=BankName.get_values().index(t.bank.value) if t.bank else None,
            placeholder="Select bank (optional)",
            help="Chose the bank where the transacntion has been made",
            key="transaction_bank",
        )

        transaction_bank = BankName(transaction_bank) if transaction_bank else None

        cards = controller.get_cards(bank=transaction_bank)
        if t.card_id is not None:
            card = controller.get_card_by_id(t.card_id)
            card_name = card.card_name if card else None
        else:
            card_name = None

        transaction_card = right.selectbox(
            label="Card",
            options=cards,
            index=cards.index(card_name) if card_name in cards else None,
            placeholder="Select card (optional)",
            help="Chose the card where the transaction has been made",
            key="transaction_card",
        )

        transaction_card = (
            controller.get_card_by_name(transaction_card) if transaction_card else None
        )

        transaction_type = left.pills(
            label="Type",
            options=["Abono", "Cargo"],
            selection_mode="single",
            default=t.type.value if t.type else None,
            key="transaction_type",
            width="stretch",
        )

        transaction_amount = right.number_input(
            label="Amount", min_value=0.01, value=float(t.amount), key="transaction_amount"
        )

        categories = controller.get_categories()
        if t.category_id is not None:
            category_name = controller.get_category_name(t.category_id)
        else:
            category_name = None

        category = left.selectbox(
            label="Category",
            options=categories,
            index=categories.index(category_name) if category_name else None,
            key="transaction_category",
        )

        description = right.text_input(
            label="Description", max_chars=200, value=t.description, key="transaction_description"
        )

        if st.form_submit_button("", icon=":material/save_as:", key="sumbit_edit_trans_button"):
            ready_to_save = True

            if not isinstance(transaction_date, date):
                st.warning(
                    "Please, verify the given date to can update the transaction",
                    icon=":material/warning:",
                )
                ready_to_save = False

            if not isinstance(transaction_bank, BankName):
                st.warning(
                    "Please, select a valid bank to can update the transaction",
                    icon=":material/warning:",
                )
                ready_to_save = False

            if not isinstance(transaction_amount, float):
                st.warning(
                    "Please, enter a valid amount to can update the transaction",
                    icon=":material/warning:",
                )
                ready_to_save = False

            if not isinstance(transaction_statement_type, StatementType):
                st.warning(
                    "Please, select a valid statement type to can update the transaction",
                    icon=":material/warning:",
                )
                ready_to_save = False

            if ready_to_save:
                edited_transaction = Transaction(
                    user_id=t.user_id,
                    transaction_id=t.transaction_id,
                    date=transaction_date,
                    description=description,
                    amount=to_decimal(transaction_amount),
                    type=TransactionType(transaction_type),
                    bank=transaction_bank if transaction_bank else t.bank,
                    statement_type=transaction_statement_type
                    if transaction_statement_type
                    else t.statement_type,
                    category_id=controller.get_category_id(category) if category else t.category_id,
                    card_id=transaction_card.card_id if transaction_card else None,
                    filename=t.filename,
                )

                duplicate_result = controller.get_duplicate_result(edited_transaction)

                if duplicate_result.has_exact_duplicates:
                    st.warning(
                        "The edited transaction is detected as an exact duplicate of an existing transaction. Please, review the changes.",
                        icon=":material/warning:",
                    )
                elif duplicate_result.has_potential_duplicates:
                    st.warning(
                        "The edited transaction is detected as a similar duplicate of an existing transaction. Please, review the changes.",
                        icon=":material/warning:",
                    )
                else:
                    edited_transaction.duplicate_potential_state = False
                    controller.update_transaction(edited_transaction)
                    st.success("Transaction updated successfully", icon=":material/check:")
                    st.rerun()
            else:
                st.warning(
                    "Please, verify the entered data to can update the transaction",
                    icon=":material/warning:",
                )
