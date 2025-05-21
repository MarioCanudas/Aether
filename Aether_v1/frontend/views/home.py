import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from functions.process import process_pdf_bytes
from functions.calculations import calculate_savings_and_credit_card_expenses_by_month
from functions.donut_chart import plot_savings_donut_chart
from functions.tips import get_financial_tips

def show_home():
    # Set the title
    st.title('Quick Financial Analysis')
    
    # Disable adding cash transaction pop up, because it's not implemented properly yet
    # adding_cash_transaction()

    # Initialize session state variables if they don't exist
    if 'all_processed_data' not in st.session_state:
        st.session_state.all_processed_data = pd.DataFrame()

    if 'all_monthly_results' not in st.session_state:
        st.session_state.all_monthly_results = pd.DataFrame()

    if 'files_uploaded' not in st.session_state:
        st.session_state.files_uploaded = False

    # File uploader
    uploaded_files = st.file_uploader("Please upload your Bank Statement PDF files", accept_multiple_files=True, type="pdf")
    if st.button('Add cash transaction', type= 'primary', disabled=True):
        st.rerun()

    if uploaded_files:
        st.session_state.all_processed_data = pd.DataFrame()
        st.session_state.all_monthly_results = pd.DataFrame()
        st.session_state.files_uploaded = False

        st.write("Processing Files...")
        all_processed_data_temp = pd.DataFrame()
        all_monthly_results_temp = pd.DataFrame()

        for uploaded_file in uploaded_files:
            processed_data = process_pdf_bytes(uploaded_file)
            all_processed_data_temp = pd.concat([all_processed_data_temp, processed_data], ignore_index=True)
            monthly_results = calculate_savings_and_credit_card_expenses_by_month(processed_data)
            all_monthly_results_temp = pd.concat([all_monthly_results_temp, monthly_results], ignore_index=True)

        all_processed_data_temp = all_processed_data_temp.sort_values(by='Date', ascending=True)
        all_monthly_results_temp = all_monthly_results_temp.sort_values(by='Month', ascending=True)

        st.session_state.all_processed_data = all_processed_data_temp
        st.session_state.all_monthly_results = all_monthly_results_temp
        st.session_state.files_uploaded = True

    if not st.session_state.all_processed_data.empty and not st.session_state.all_monthly_results.empty:
        total_savings = st.session_state.all_monthly_results['savings'].sum()
        avg_income_per_month = st.session_state.all_monthly_results['total_income'].mean()
        avg_withdrawal_per_month = st.session_state.all_monthly_results['total_withdrawal'].mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Savings", value=f"${total_savings:,.2f}")
        with col2:
            st.metric(label="AVG Income/Month", value=f"${avg_income_per_month:,.2f}")
        with col3:
            st.metric(label="AVG Withdrawal/Month", value=f"${avg_withdrawal_per_month:,.2f}")

        fig, label = plot_savings_donut_chart(total_savings, avg_income_per_month)
        st.pyplot(fig)
        st.markdown(f"<h2 style='text-align: center;'>Financial Health: {label}</h2>", unsafe_allow_html=True)

        tips = get_financial_tips(label)
        st.subheader("Tips")
        for tip in tips:
            st.write(f"- {tip}")
