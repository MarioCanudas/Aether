from typing import cast

import streamlit as st
from controllers import AddTransactionController
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.templates import Template, TemplateType, TransactionDefaultValues
from utils import to_decimal

controller = AddTransactionController()


@st.dialog("Modify Template", width="medium")
def modify_template_popup(template_id: int) -> None:
    with st.form(key="modify_template_form", border=False):
        template = controller.get_template(template_id)
        template = cast(Template, template)
        default_values = cast(TransactionDefaultValues, template.default_values)

        if template is None:
            st.error("Template not found")
        else:
            left, right = st.columns([1, 3])

            template_name = left.text_input(
                "Name", value=template.template_name, max_chars=50, key="update_template_name"
            )

            template_description = right.text_input(
                "Description",
                value=template.template_description,
                max_chars=200,
                key="update_template_description",
            )

            transaction_date = st.date_input(
                "Date",
                value=default_values.transaction_date,
                key="update_transaction_template_date",
            )

            transaction_statement_type = st.pills(
                label="Statement Type",
                options=StatementType.get_values(),
                selection_mode="single",
                default=default_values.statement_type.value
                if default_values.statement_type
                else None,
                key="update_transaction_template_statement_type",
                width="stretch",
            )
            transaction_statement_type = (
                StatementType(transaction_statement_type) if transaction_statement_type else None
            )

            left, right = st.columns([4, 7])

            default_bank_name = default_values.bank_name.value if default_values.bank_name else None
            all_banks = BankName.get_values()
            transaction_bank = left.selectbox(
                label="Bank",
                options=all_banks,
                index=all_banks.index(default_bank_name)
                if default_bank_name and all_banks
                else None,
                key="update_transaction_template_bank",
                width="stretch",
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
                key="update_transaction_template_card",
                width="stretch",
            )
            transaction_card = (
                controller.get_card_by_name(transaction_card) if transaction_card else None
            )

            transaction_type = left.pills(
                "Type",
                options=[
                    tt.value for tt in TransactionType if tt != TransactionType.INITIAL_BALANCE
                ],
                selection_mode="single",
                default=default_values.type,
                key="update_transaction_template_type",
            )

            transaction_amount = right.number_input(
                label="Amount",
                min_value=0.01,
                value=float(default_values.amount) if default_values.amount else None,
                key="update_transaction_template_amount",
            )

            categories = controller.get_categories()

            if default_values.category_id is not None:
                category_name = controller.get_category_name(default_values.category_id)
                category_index = (
                    categories.index(category_name) if category_name in categories else 0
                )
            else:
                category_index = None

            transaction_category = left.selectbox(
                label="Category",
                options=categories,
                index=category_index,
                key="update_transaction_template_category",
            )

            transaction_description = right.text_input(
                label="Description",
                max_chars=200,
                value=default_values.description,
                key="update_transaction_template_description",
            )

            if st.form_submit_button("Modify template", type="primary"):
                if transaction_category:
                    transaction_category_id = controller.get_category_id(transaction_category)

                try:
                    # First verify that the transaction default values are valid
                    default_values = TransactionDefaultValues(
                        transaction_date=transaction_date,
                        type=TransactionType(transaction_type),
                        amount=to_decimal(transaction_amount) if transaction_amount else None,
                        category_id=transaction_category_id,
                        description=transaction_description,
                        statement_type=transaction_statement_type,
                        bank_name=transaction_bank,
                        card_id=transaction_card.card_id if transaction_card else None,
                    )

                    # Then create the modified template
                    updated_template = Template(
                        user_id=controller.user_id,
                        template_name=template_name,
                        template_description=template_description,
                        template_type=TemplateType.TRANSACTION,
                        default_values=default_values,
                    )

                    controller.update_template(template_id, updated_template)
                    st.rerun()
                except ValueError:
                    st.warning("Some field is invalid, try again.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
