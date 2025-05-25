import streamlit as st
from controllers import TransactionProcessorController

controller = TransactionProcessorController()

def show_transaction_processor():
    st.title("Transaction Processor")

    # Initialize session state for storing transactions
    controller.initialize_session_state()

    # Allow multiple file uploads
    uploaded_files = st.file_uploader("Upload Bank Statement PDF(s)", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        controller.process_uploaded_files(uploaded_files)

        if st.session_state.all_transactions:
            combined_df = controller.get_combined_df()
            cleaned_df = controller.get_cleaned_df()
            monthly_results = controller.get_monthly_results()
            
            controller.update_monthly_results()

            st.subheader("Extracted Transactions")
            st.dataframe(combined_df)

            st.subheader("Analyzed Transactions")
            st.dataframe(cleaned_df)

            st.subheader("Monthly Savings & Metrics")
            st.dataframe(monthly_results)

            total_savings = controller.get_total_savings()
            avg_income_per_month = controller.get_avg_income_per_month()
            avg_withdrawal_per_month = controller.get_avg_withdrawal_per_month()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Savings", value=f"${total_savings:,.2f}")
            with col2:
                st.metric(label="Avg Income/Month", value=f"${avg_income_per_month:,.2f}")
            with col3:
                st.metric(label="Avg Withdrawal/Month", value=f"${avg_withdrawal_per_month:,.2f}")

            fig, label = controller.get_plot_savings_donut_chart(total_savings, avg_income_per_month)
            st.pyplot(fig)
            st.markdown(f"<h2 style='text-align: center;'>Financial Health: {label}</h2>", unsafe_allow_html=True)

            tips = controller.get_financial_tips(label)
            st.subheader("Tips")
            for tip in tips:
                st.write(f"- {tip}")

    if st.button("Clear All Transactions"):
        controller.clear_all_transactions()
        st.rerun()
