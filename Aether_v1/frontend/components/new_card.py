import streamlit as st
from controllers import CardsViewController
from models.bank_properties import BankName, StatementType


@st.dialog("New Card")
def new_card_popup():
    controller = CardsViewController()

    with st.form(key="new_card_form", border=False, clear_on_submit=True):
        card_name = st.text_input("Name", value=None, key="new_card_name")

        left, right = st.columns(2)
        card_bank = left.selectbox(
            "Bank", options=BankName.get_values(), index=None, key="new_card_bank"
        )
        card_statement_type = right.selectbox(
            "Statement Type",
            options=StatementType.get_values(),
            index=None,
            key="new_card_statement_type",
        )

        card_expiration_date = st.date_input(
            "Expiration Date", value=None, key="new_card_expiration_date"
        )

        if st.form_submit_button("Add Card", type="primary"):
            if (
                not card_name
                or not card_bank
                or not card_statement_type
                or not card_expiration_date
            ):
                st.error("All fields are required")
            else:
                controller.add_card(
                    card_name,
                    BankName(card_bank),
                    StatementType(card_statement_type),
                    card_expiration_date,
                )
                st.rerun()
