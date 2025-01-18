import streamlit as st
import pandas as pd
from functions.donut_chart import plot_savings_donut_chart
from functions.tips import get_financial_tips
from functions.bank_processor import get_bank_processor
from functions.process import identify_pdf
from utils.helper_functions import calculate_savings_and_validate_balances
import os
from config import MONTH_PATTERNS_ENG, NUMERIC_MONTH_PATTERNS

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

                month_patterns = NUMERIC_MONTH_PATTERNS if bank_name == 'BBVA' and statement_type == 'credit' else MONTH_PATTERNS_ENG
                processor = get_bank_processor(bank_name, statement_type, temp_file_path, month_patterns)
                transactions_df = processor.process_transactions()
                transactions_df['bank'] = bank_name
                transactions_df['statement_type'] = statement_type
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

            # Calculate monthly savings and metrics
            monthly_results = calculate_savings_and_validate_balances(combined_df)
            st.session_state.monthly_results = monthly_results

            # Display extracted transactions
            st.subheader("Extracted Transactions")
            st.dataframe(combined_df)

            # Display calculated monthly results
            st.subheader("Monthly Savings & Metrics")
            st.dataframe(monthly_results)

            # Show overall metrics
            total_savings = monthly_results['savings'].sum()
            avg_income_per_month = monthly_results['total_income'].mean()
            avg_withdrawal_per_month = monthly_results['total_withdrawal'].mean()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Savings", value=f"${total_savings:,.2f}")
            with col2:
                st.metric(label="Avg Income/Month", value=f"${avg_income_per_month:,.2f}")
            with col3:
                st.metric(label="Avg Withdrawal/Month", value=f"${avg_withdrawal_per_month:,.2f}")

            # Plot savings as a donut chart
            fig, label = plot_savings_donut_chart(total_savings, avg_income_per_month)
            st.pyplot(fig)
            st.markdown(f"<h2 style='text-align: center;'>Financial Health: {label}</h2>", unsafe_allow_html=True)

            # Display tips
            tips = get_financial_tips(label)
            st.subheader("Tips")
            for tip in tips:
                st.write(f"- {tip}")

    # Clear transactions and results
    if st.button("Clear All Transactions"):
        st.session_state.all_transactions = []
        st.session_state.monthly_results = pd.DataFrame()
        st.rerun()
