import streamlit as st
from controllers import TransactionProcessorController

controller = TransactionProcessorController()

def show_transaction_processor():
    st.title("Transaction Processor")

    controller.initialize_session_state()

    # Allow multiple file uploads
    uploaded_files = st.file_uploader("Upload Bank Statement PDF(s)", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        
        for uploaded_file in uploaded_files:
            try:
                df_transactions = controller.process_uploaded_file(uploaded_file)
                controller.append_transactions(df_transactions)
            except ValueError as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
            except Exception as e:
                st.error(f"An unexpected error processing {uploaded_file.name}: {e}")
                
        controller.update_all_processed_data()
        controller.update_all_monthly_results()

        if st.session_state.all_transactions:
            combined_df = controller.get_combined_df()
            cleaned_df = controller.get_cleaned_df()
            monthly_results = controller.get_monthly_results()

            st.subheader("Extracted Transactions")
            st.dataframe(combined_df)

            st.subheader("Analyzed Transactions")
            st.dataframe(cleaned_df)

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

    if st.button("Clear All Transactions"):
        controller.clear_all_transactions()
        st.rerun()
