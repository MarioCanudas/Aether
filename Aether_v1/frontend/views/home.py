import streamlit as st
from controllers import TransactionProcessorController
from components.confirm_upload import confirm_upload_popup

controller = TransactionProcessorController()

def show_home():
    st.title('Home')
 
    if controller.user_have_transactions():
        financial_analysis = controller.get_financial_summary()
        
        # Convert Decimal to float for display in streamlit
        total_savings = float(financial_analysis.total_savings)
        avg_income_per_month = float(financial_analysis.avg_income_per_month)
        avg_withdrawal_per_month = float(financial_analysis.avg_withdrawal_per_month)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Savings", value=f"${total_savings:,.2f}")
        with col2:
            st.metric(label="AVG Income/Month", value=f"${avg_income_per_month:,.2f}")
        with col3:
            st.metric(label="AVG Withdrawal/Month", value=f"${avg_withdrawal_per_month:,.2f}")

        donut_score_chart = controller.get_donut_score_chart()
        label = financial_analysis.label
        
        st.pyplot(donut_score_chart)
        st.markdown(f"<h2 style='text-align: center;'>Financial Health: {label}</h2>", unsafe_allow_html=True)

        tips = financial_analysis.tips
        st.subheader("Tips")
        for tip in tips:
            st.write(f"- {tip}")
        
        # TODO: Uncomment and remove disabled= True when the clear all transactions function is implemented
        if st.button('Clear all transactions', disabled= True):
            # controller.clear_all_transactions()
            st.rerun()
