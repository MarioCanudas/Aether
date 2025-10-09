import streamlit as st
import altair as alt
import asyncio
from datetime import datetime, timedelta
from controllers import HomeController
from constants.views_icons import HOME_ICON
from models.dates import Period
from models.financial import FinancialAmountsSums
from models.views_data import HomeViewData, HomePeriodsOptions

def _financial_sums(financial_sums: FinancialAmountsSums):
    income = float(financial_sums.income)
    withdrawal = float(financial_sums.withdrawal)
    savings = float(financial_sums.savings if financial_sums.savings else financial_sums.balance)

    left, center, right = st.columns(3)
    with left:
        st.metric(
            label="Income", 
            value=f"${income:,.2f}", 
            border= False,
            help= "Income by the selected period."
        )
    with center:
        st.metric(
            label="Withdrawal", 
            value=f"${withdrawal:,.2f}", 
            border= False,
            help= "Withdrawal by the selected period."
        )
    with right:
        st.metric(
            label="Savings", 
            value=f"${savings:,.2f}", 
            border= False,
            help= "Savings by the selected period."
        )
    
def _last_transactions(view_data: HomeViewData):
    last_transactions = view_data.last_transactions
    
    st.subheader("Last Transactions")
    
    st.dataframe(last_transactions, hide_index= True)
        
def _tips(view_data: HomeViewData):
    tips = view_data.tips
    
    st.write("<h2 style='text-align: center;'>Tips</h2>", unsafe_allow_html= True)
    for tip in tips:
        st.write(f"- {tip}")

def show_home():
    # Page config
    st.set_page_config(
        page_title='Home', 
        page_icon=HOME_ICON, 
        layout='wide'
    )
    controller = HomeController()
    
    st.title('Home')
 
    if controller.user_have_transactions():
        home_view_data = asyncio.run(controller.get_home_view_data())
        left, right = st.columns([3, 1.5])
        
        with left:
            balance = float(home_view_data.all_time_sums.balance)
            with st.container(border= True):
                st.metric(
                    label="Balance", 
                    value=f"${balance:,.2f}", 
                    border= False,
                    help= "General balance of the user. Total of income minus total of withdrawal."
                )
                
            with st.container(border= True):
                metrics_period = st.selectbox(
                    label= "",
                    options= HomePeriodsOptions.get_values(),
                    index= 0,
                    label_visibility= "collapsed",
                    key= "period_selectbox",
                )

                if metrics_period == HomePeriodsOptions.SPECIFIC_PERIOD:
                    today = datetime.now().date()
                    
                    specific_period = st.date_input(
                        label= "Specific Period",
                        value= (today - timedelta(days= 30), today),
                        key= "specific_period_date_input"
                    )
                    
                if metrics_period == HomePeriodsOptions.ALL_TIME:
                    financial_sums = home_view_data.all_time_sums
                elif metrics_period == HomePeriodsOptions.CURRENT_MONTH:
                    financial_sums = home_view_data.current_month_sums
                elif metrics_period == HomePeriodsOptions.LAST_MONTH:
                    financial_sums = home_view_data.last_month_sums
                elif metrics_period == HomePeriodsOptions.AVARAGE:
                    financial_sums = home_view_data.avarage_sums
                elif metrics_period == HomePeriodsOptions.SPECIFIC_PERIOD:
                    try:
                        period = Period(start_date= specific_period[0], end_date= specific_period[1])
                        financial_sums = controller.get_specific_period_sums(period)
                    except:
                        today = datetime.now().date()
                        financial_sums = controller.get_specific_period_sums(Period(start_date= today - timedelta(days= 30), end_date= today))
                    
                
                _financial_sums(financial_sums)
            
            with st.container(border= True):
                final_chart = alt.layer(home_view_data.income_vs_expenses_bar_chart, home_view_data.balance_line_chart).encode(
                    x= alt.X('month_label:O', sort= ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
                ).properties(
                    title='Income vs Expenses (last 6 months)'
                )
                st.altair_chart(final_chart, use_container_width= True)
            
        with right: 
            label = home_view_data.label
            
            with st.container(border= True):
                st.write(f"<h2 style='text-align: center;'>Financial Health</h2>", unsafe_allow_html= True)
                st.pyplot(home_view_data.donut_score_chart)
                st.write(f"<h4 style='text-align: center;'>{label.value}</h4>", unsafe_allow_html= True)
            
                st.divider()
                
                _tips(home_view_data) 
        
        with st.container(border= True):
            _last_transactions(home_view_data)
        
    else:
        st.info("No transactions available. Please upload files in the Upload Statements view.")
