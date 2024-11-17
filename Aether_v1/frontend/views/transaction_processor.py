import streamlit as st
import pandas as pd
from functions.bank_processor import get_bank_processor
import os

def show_transaction_processor():
    st.title("Transaction Processor")

    # User inputs for selecting bank and statement type
    bank_name = st.selectbox("Select Bank", ["Nu", "BBVA"])
    statement_type = st.selectbox("Select Statement Type", ["credit", "debit"])
    uploaded_file = st.file_uploader("Upload Bank Statement PDF", type="pdf")

    if uploaded_file is not None:
        # Save uploaded file to a temporary path for processing
        temp_file_path = os.path.join("frontend", "temp_uploaded.pdf")
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Define month patterns as required by your processors (customize as needed)
        month_patterns = {"january": "ENE", "february": "FEB", "march": "MAR", "april": "ABR"}  # Example patterns

        # Process the file
        try:
            processor = get_bank_processor(bank_name, statement_type, temp_file_path, month_patterns)
            transactions_df = processor.process_transactions()  # Get transactions as a DataFrame

            # Display the DataFrame in Streamlit
            st.subheader("Extracted Transactions")
            st.dataframe(transactions_df)

        except ValueError as e:
            st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

        # Optionally, delete the temporary file after processing (to avoid clutter)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    else:
        st.info("Please upload a PDF file to process transactions.")
