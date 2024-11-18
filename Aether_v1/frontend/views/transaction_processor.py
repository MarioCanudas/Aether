import streamlit as st
import pandas as pd
from functions.bank_processor import get_bank_processor
from functions.process import identify_pdf
import os
from config import MONTH_PATTERNS, NUMERIC_MONTH_PATTERNS

def show_transaction_processor():
    st.title("Transaction Processor")

    # Initialize session state for storing transactions
    if 'all_transactions' not in st.session_state:
        st.session_state.all_transactions = []

    # Allow multiple file uploads
    uploaded_files = st.file_uploader("Upload Bank Statement PDF(s)", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Check if file was already processed (using name as identifier)
            if any(uploaded_file.name == df['filename'].iloc[0] for df in st.session_state.all_transactions if not df.empty):
                continue
            # Save uploaded file to a temporary path for processing
            temp_file_path = os.path.join("frontend", f"temp_uploaded_{uploaded_file.name}")
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                # Identify bank from PDF
                bank_info = identify_pdf(temp_file_path)
                bank_name = bank_info["bank"]
                statement_type = bank_info["account_type"]
                st.info(f"Detected bank for {uploaded_file.name}: {bank_name} - {statement_type}")

                month_patterns = NUMERIC_MONTH_PATTERNS if bank_name == 'BBVA' and statement_type == 'credit' else MONTH_PATTERNS
                processor = get_bank_processor(bank_name, statement_type, temp_file_path, month_patterns)
                transactions_df = processor.process_transactions()
                transactions_df['filename'] = uploaded_file.name
                st.session_state.all_transactions.append(transactions_df)

            except ValueError as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
            except Exception as e:
                st.error(f"An unexpected error processing {uploaded_file.name}: {e}")

            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        if st.session_state.all_transactions:
            # Combine all DataFrames
            combined_df = pd.concat(st.session_state.all_transactions, ignore_index=True)

            # Display the combined DataFrame
            st.subheader("Extracted Transactions")
            st.dataframe(combined_df)

    # Add a clear button
    if st.button("Clear All Transactions"):
        st.session_state.all_transactions = []
        st.rerun()
