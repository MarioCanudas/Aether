import asyncio

import streamlit as st
from controllers import UploadStatementsController
from models.transactions import Transaction

controller = UploadStatementsController()


@st.dialog("Confirm Upload", width="medium")
def confirm_upload_popup(transactions: list[Transaction]) -> None:
    st.header("Transactions to be uploaded")
    filtered_transactions_result = asyncio.run(controller.filter_transactions(transactions))

    if len(filtered_transactions_result.clean) > 0:
        st.subheader("Transactions to be uploaded")
        st.dataframe(
            controller.transactions_to_df(filtered_transactions_result.clean, to_view=True)
        )

    if len(filtered_transactions_result.potential_duplicates_to_upload) > 0:
        st.subheader("Potential duplicates to upload")
        st.dataframe(
            controller.transactions_to_df(
                filtered_transactions_result.potential_duplicates_to_upload, to_view=True
            )
        )

        st.info(
            "These transactions will be uploaded as potential duplicates. You can review them in the Transactions view."
        )

    if len(filtered_transactions_result.duplicated) > 0:
        st.subheader("Duplicated transactions")
        st.dataframe(
            controller.transactions_to_df(filtered_transactions_result.duplicated, to_view=True)
        )

        st.info("These transactions will not be uploaded because they are exact duplicates.")

    if st.button(
        label="Confirm",
        help="This will update the database with the new transactions. If you are not sure just close this popup",
    ):
        controller.upload_transactions(filtered_transactions_result)
        st.toast("Transactions uploaded successfully")
        st.rerun()
