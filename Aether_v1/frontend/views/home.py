import streamlit as st
from controllers import TransactionProcessorController
from .confirm_upload import confirm_upload_popup

controller = TransactionProcessorController()

def show_home():
    # Set the title
    st.title('Quick Financial Analysis')
    # File uploader
    uploaded_files = st.file_uploader(
        "Please upload your Bank Statement PDF files", 
        accept_multiple_files=True, 
        type="pdf",
        disabled= controller.user_session_service.get_current_user_id() is None,
        key= 'home_file_uploader'
    )

    if uploaded_files:

        st.write("Processing Files...")
        try:
            transactions = controller.process_uploaded_files(uploaded_files)
            confirm_upload_popup(transactions)
        except Exception as e:
            st.error(f"An unexpected error processing files: {e}")
            
    if controller.user_have_transactions() and controller.user_have_monthly_results():
        financial_analysis = controller.get_financial_analysis()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Savings", value=f"${financial_analysis['total_savings']:,.2f}")
        with col2:
            st.metric(label="AVG Income/Month", value=f"${financial_analysis['avg_income_per_month']:,.2f}")
        with col3:
            st.metric(label="AVG Withdrawal/Month", value=f"${financial_analysis['avg_withdrawal_per_month']:,.2f}")

        donut_score_chart = financial_analysis['donut_score_chart']
        label = financial_analysis['label']
        
        st.pyplot(donut_score_chart)
        st.markdown(f"<h2 style='text-align: center;'>Financial Health: {label}</h2>", unsafe_allow_html=True)

        tips = financial_analysis['tips']
        st.subheader("Tips")
        for tip in tips:
            st.write(f"- {tip}")
        
        # TODO: Uncomment and remove disabled= True when the clear all transactions function is implemented
        if st.button('Clear all transactions', disabled= True):
            # controller.clear_all_transactions()
            st.rerun()
