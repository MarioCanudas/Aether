from datetime import date

import streamlit as st
from components import modify_template_popup, new_transaction_template_popup
from constants.views_icons import ADD_TRANSACTION_ICON
from controllers import AddTransactionController
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.templates import TransactionDefaultValues
from models.transactions import DuplicateResult, Transaction
from utils import to_decimal


@st.dialog("Potential Duplicate transactions")
def _confirm_potential_duplicate_upload(duplicate_result: DuplicateResult) -> None:
    controller = AddTransactionController()

    st.warning("This transaction is a potential duplicate. Do you want to upload it anyway?")

    st.subheader("Potential duplicates")
    potential_duplicates_df = controller.transactions_to_df(
        duplicate_result.potential_duplicates, to_view=True
    )
    st.dataframe(potential_duplicates_df)

    left, _, right = st.columns(3, gap="large")

    if left.button(label="Confirm", type="secondary", width="stretch"):
        duplicate_result.transaction.duplicate_potential_state = True
        controller.add_transaction(duplicate_result.transaction)

        controller.modify_potential_duplicate_transactions(duplicate_result.potential_duplicates)
        st.rerun()

    if right.button(label="Cancel", type="primary", width="stretch"):
        st.rerun()


def show_add_transaction():
    # Page config
    st.set_page_config(
        page_title="Add Transaction", page_icon=ADD_TRANSACTION_ICON, layout="centered"
    )
    controller = AddTransactionController()

    with st.container(key="add_transaction_container", border=True):
        st.header("Add transaction")

        templates_names = controller.get_templates_names()

        left, right = st.columns([8, 2])

        if templates_names:
            template_name = left.pills(
                label="Template",
                options=list(templates_names.keys()),
                selection_mode="single",
                default=None,
                key="transaction_template",
            )
            template_id = templates_names[template_name] if template_name else None
            template = controller.get_template(template_id) if template_id else None
        else:
            template_name = None
            template = None
            left.write("No templates found")

        with right:
            _left, _right = st.columns(2)

            if _left.button(
                "",
                type="primary",
                icon=":material/add:",
                help="Add a new template",
                key="add_template_button",
            ):
                new_transaction_template_popup()

            if _right.button(
                "",
                type="secondary",
                icon=":material/edit:",
                help="Modify a template",
                key="modify_template_button",
                disabled=not template_name,
            ):
                template_id = templates_names[template_name] if template_name else None
                modify_template_popup(template_id) if template_id else None

        with st.form(key="add_transaction_form", border=False, clear_on_submit=True):
            if template:
                default_values = template.default_values
                if not isinstance(default_values, TransactionDefaultValues):
                    raise TypeError(
                        "Template default values are not of type TransactionDefaultValues"
                    )

                transaction_date = st.date_input(
                    label="Date",
                    value=default_values.transaction_date,
                    key="transaction_date_template",
                )

                default_statement_type = (
                    default_values.statement_type.value if default_values.statement_type else None
                )

                transaction_statement_type = st.pills(
                    label="Statement Type",
                    options=StatementType.get_values(),
                    selection_mode="single",
                    default=default_statement_type,
                    key="transaction_statement_type_template",
                    width="stretch",
                )

                transaction_statement_type = (
                    StatementType(transaction_statement_type)
                    if transaction_statement_type
                    else None
                )

                left, right = st.columns([4, 7])

                default_bank_name = (
                    default_values.bank_name.value if default_values.bank_name else None
                )
                all_banks = BankName.get_values()

                transaction_bank = left.selectbox(
                    label="Bank",
                    options=all_banks,
                    index=all_banks.index(default_bank_name)
                    if default_bank_name and all_banks
                    else None,
                    placeholder="Select bank (optional)",
                    help="Chose the bank where the transacntion has been made",
                    key="transaction_bank_template",
                )

                transaction_bank = BankName(transaction_bank) if transaction_bank else None

                default_card = (
                    controller.get_card_by_id(default_values.card_id)
                    if default_values.card_id
                    else None
                )
                default_card_name = default_card.card_name if default_card else None
                all_cards = controller.get_cards()

                transaction_card = right.selectbox(
                    label="Card",
                    options=all_cards,
                    index=all_cards.index(default_card_name) if default_card_name else None,
                    placeholder="Select card (optional)",
                    help="Chose the card where the transaction has been made",
                    key="transaction_card_template",
                )

                transaction_card = (
                    controller.get_card_by_name(transaction_card) if transaction_card else None
                )

                transaction_type = left.pills(
                    label="Type",
                    options=["Abono", "Cargo"],
                    selection_mode="single",
                    default=default_values.type,
                    key="transaction_type_template",
                    width="stretch",
                )

                transaction_amount = right.number_input(
                    label="Amount",
                    min_value=0.01,
                    value=float(default_values.amount) if default_values.amount else None,
                    key="transaction_amount_template",
                )

                categories = controller.get_categories()

                if default_values.category_id is not None:
                    category_name = controller.get_category_name(default_values.category_id)
                    category_index = (
                        categories.index(category_name) if category_name in categories else None
                    )
                else:
                    category_index = None

                category = left.selectbox(
                    label="Category",
                    options=categories,
                    index=category_index,
                    key="transaction_category_template",
                )

                description = right.text_input(
                    label="Description",
                    max_chars=200,
                    value=default_values.description,
                    key="transaction_description_template",
                )
            else:
                transaction_date = st.date_input(
                    label="Date", value=date.today(), key="transaction_date"
                )

                transaction_statement_type = st.pills(
                    label="Statement Type",
                    options=StatementType.get_values(),
                    selection_mode="single",
                    default=StatementType.DEBIT.value,
                    key="transaction_statement_type",
                    width="stretch",
                )

                transaction_statement_type = (
                    StatementType(transaction_statement_type)
                    if transaction_statement_type
                    else None
                )

                left, right = st.columns([4, 7])

                transaction_bank = left.selectbox(
                    label="Bank",
                    options=[bank.value for bank in BankName],
                    index=None,
                    placeholder="Select bank (optional)",
                    help="Chose the bank where the transacntion has been made",
                    key="transaction_bank",
                )

                transaction_bank = BankName(transaction_bank) if transaction_bank else None

                transaction_card = right.selectbox(
                    label="Card",
                    options=controller.get_cards(bank=transaction_bank),
                    index=None,
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
                    default=None,
                    key="transaction_type",
                    width="stretch",
                )

                transaction_amount = right.number_input(
                    label="Amount", min_value=0.01, value=None, key="transaction_amount"
                )

                categories = controller.get_categories()

                category = left.selectbox(
                    label="Category", options=categories, index=None, key="transaction_category"
                )

                description = right.text_input(
                    label="Description", max_chars=200, value=None, key="transaction_description"
                )

            if st.form_submit_button(label="Sumbit", type="primary"):
                try:
                    if not isinstance(transaction_date, date):
                        raise TypeError("The transaction date is not valid")

                    if not isinstance(transaction_bank, BankName):
                        raise TypeError("The transaction bank is not valid")

                    if not isinstance(transaction_amount, float):
                        raise TypeError("The transaction amount is not valid")

                    if not isinstance(transaction_statement_type, StatementType):
                        raise TypeError("The transaction statement type is not valid")

                    transaction_record = Transaction(
                        user_id=controller.user_id,
                        category_id=controller.get_category_id(category) if category else None,
                        date=transaction_date,  # The verification is done above
                        description=description,
                        amount=to_decimal(transaction_amount)
                        if transaction_type == "Abono"
                        else to_decimal(-1 * transaction_amount),
                        type=TransactionType(transaction_type),
                        bank=transaction_bank,
                        card_id=transaction_card.card_id if transaction_card else None,
                        statement_type=transaction_statement_type,
                        filename=None,
                        duplicate_potential_state=False,
                    )

                    duplicate_result = controller.get_duplicate_result(transaction_record)

                    if duplicate_result.has_exact_duplicates:
                        st.toast(
                            "Transaction is an exact duplicate. Check the given values and try again",
                            icon=":material/warning:",
                        )
                    elif duplicate_result.has_potential_duplicates:
                        _confirm_potential_duplicate_upload(duplicate_result)
                    else:
                        controller.add_transaction(transaction_record)

                        st.toast("Transaction added successfully", icon=":material/check:")
                        st.rerun()
                except TypeError as type_err:
                    st.warning(
                        f"{type_err}, please, verify the given values to can add the transaction",
                        icon=":material/error:",
                    )
