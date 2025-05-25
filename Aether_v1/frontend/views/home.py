import streamlit as st
from controllers.transaction_processor_controller import TransactionProcessorController

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
        controller.reset_session_state()

        st.write("Processing Files...")
        
        controller.process_uploaded_files(uploaded_files)

        controller.update_all_processed_data()
        controller.update_all_monthly_results()

        st.session_state.files_uploaded = True

    if not st.session_state.all_processed_data.empty and not st.session_state.all_monthly_results.empty:
        total_savings = controller.get_total_savings()
        avg_income_per_month = controller.get_avg_income_per_month()
        avg_withdrawal_per_month = controller.get_avg_withdrawal_per_month()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Savings", value=f"${total_savings:,.2f}")
        with col2:
            st.metric(label="AVG Income/Month", value=f"${avg_income_per_month:,.2f}")
        with col3:
            st.metric(label="AVG Withdrawal/Month", value=f"${avg_withdrawal_per_month:,.2f}")

        fig, label = controller.get_plot_savings_donut_chart(total_savings, avg_income_per_month)
        st.pyplot(fig)
        st.markdown(f"<h2 style='text-align: center;'>Financial Health: {label}</h2>", unsafe_allow_html=True)

        tips = controller.get_financial_tips(label)
        st.subheader("Tips")
        for tip in tips:
            st.write(f"- {tip}")
