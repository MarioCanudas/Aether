import streamlit as st
from controllers import TransactionProcessorController

controller = TransactionProcessorController()

def show_home():
    # Set the title
    st.title('Quick Financial Analysis')
    
    # Disable adding cash transaction pop up, because it's not implemented properly yet
    # adding_cash_transaction()

    controller.initialize_session_state()

    # File uploader
    uploaded_files = st.file_uploader("Please upload your Bank Statement PDF files", accept_multiple_files=True, type="pdf")
    if st.button('Add cash transaction', type= 'primary', disabled=True):
        st.rerun()

    if uploaded_files:

        st.write("Processing Files...")
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

    if not st.session_state.all_processed_data.empty and not st.session_state.all_monthly_results.empty:
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
