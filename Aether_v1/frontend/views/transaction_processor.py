import streamlit as st
from controllers import TransactionProcessorController
from components.confirm_upload import confirm_upload_popup

controller = TransactionProcessorController()

def show_transaction_processor():
    st.title("Transaction Processor")
    
    df_transactions = None

    # Allow multiple file uploads
    uploaded_files = st.file_uploader(
        "Upload Bank Statement PDF(s)", 
        accept_multiple_files=True,
        type="pdf", 
        disabled= controller.user_session_service.get_current_user_id() is None
    )
    if uploaded_files:
        
        try:
            df_transactions = controller.process_uploaded_files(uploaded_files)
            confirm_upload_popup(df_transactions)
        except Exception as e:
            st.error(f"An unexpected error processing {uploaded_files.name}: {e}")

        if df_transactions is not None:
            monthly_results = controller.get_monthly_results()

            st.subheader("Extracted Transactions")
            st.dataframe(df_transactions) if df_transactions is not None else st.info("No transactions uploaded")

            st.subheader("Monthly Savings & Metrics")
            st.dataframe(monthly_results)

            financial_analysis = controller.get_financial_analysis()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Savings", value=f"${financial_analysis['total_savings']:,.2f}")
            with col2:
                st.metric(label="Avg Income/Month", value=f"${financial_analysis['avg_income_per_month']:,.2f}")
            with col3:
                st.metric(label="Avg Withdrawal/Month", value=f"${financial_analysis['avg_withdrawal_per_month']:,.2f}")

            donut_score_chart = financial_analysis['donut_score_chart']
            label = financial_analysis['label']
            
            st.pyplot(donut_score_chart)
            st.markdown(f"<h2 style='text-align: center;'>Financial Health: {label}</h2>", unsafe_allow_html=True)

            tips = financial_analysis['tips']
            st.subheader("Tips")
            for tip in tips:
                st.write(f"- {tip}")

    # TODO: Uncomment and remove disabled= True when the clear all transactions function is implemented
    if st.button("Clear All Transactions", disabled= True):
        # controller.clear_all_transactions()
        st.rerun()
