import streamlit as st
import asyncio
from datetime import date, timedelta
from utils import give_amount_format
from controllers import AnalysisController
from components import period_select_box
from constants.dates import MonthLabels
from constants.views_icons import INCOME_ANALYSIS_ICON
from models.dates import Period
from models.views_data import PeriodsOptions

def show_income_analysis():
    # Page config
    st.set_page_config(
        page_title='Income Analysis', 
        page_icon=INCOME_ANALYSIS_ICON, 
        layout='wide'
    )
    controller = AnalysisController()
    view_data = asyncio.run(controller.get_analysis_view_data('Abono'))
    
    st.title('Income Analysis')

    # Check if monthly results are available
    if controller.user_have_transactions():
        with st.container(border= True):
            selected_period = period_select_box(key= "period_selectbox_income")
    
            if selected_period == PeriodsOptions.SPECIFIC_PERIOD:
                today = date.today()
                
                specific_period = st.date_input(
                    label= "Specific Period",
                    value= (today - timedelta(days= 30), today),
                    key= "specific_period_date_input"
                )
                period = Period(start_date= specific_period[0], end_date= specific_period[1])
                
            left_1, center_1, right_1 = st.columns(3)
            
            if selected_period == PeriodsOptions.SPECIFIC_PERIOD:
                analysis_amounts = asyncio.run(controller.get_amounts_in_specific_period('Abono', period))
            else:
                analysis_amounts = view_data.analysis_amounts[PeriodsOptions(selected_period)]
            
            left_1.metric(
                'Accumulated Income', 
                value= give_amount_format(analysis_amounts.accumulated_amount),
                help= 'Accumulated income by the selected period.',
            )
            
            center_1.metric(
                'Max Income',
                value= give_amount_format(analysis_amounts.max_amount),
                help= 'Max income by the selected period.'
            )
            
            right_1.metric(
                'Income frecuency',
                value= analysis_amounts.frecuency,
                help= 'Income frecuency by the selected period.'
            )
        
        left, right = st.columns([3, 1.5])
        
        with left:
            with st.container(border= True):
                left_2, right_2 = st.columns(2)
                income_chart_type = left_2.segmented_control(
                    label= 'Chart type',
                    options= ['Daily', 'Monthly'],
                    key= 'income_chart_type',
                    default= 'Daily',
                    help= 'Select the chart type to display.'
                )
                
                if income_chart_type == 'Daily':
                    with right_2:
                        left_3, right_3 = st.columns(2)
                        
                        year = left_3.selectbox(
                            label= 'Select year',
                            options= controller.get_years(),
                            key= 'income_year_selectbox',
                            index= 0,
                        )
                        month = right_3.selectbox(
                            label= 'Select month',
                            options= MonthLabels.get_values(),
                            key= 'income_month_selectbox',
                        )
                    
                    st.subheader('Income per Day')
                    st.altair_chart(controller.get_daily_bar_chart('Abono', MonthLabels(month), year))
                else:
                    year = right_2.selectbox(
                        label= 'Select year',
                        options= controller.get_years(),
                        key= 'income_month_selectbox',
                        index= 0,
                    )
                    st.subheader('Total Income per Month')
                    st.altair_chart(controller.get_monthly_bar_chart('Abono', year))
        
        with right:
            with st.container(border= True):
                st.subheader('Sources of Income')
                st.altair_chart(view_data.amount_per_category_chart)
                
        with st.container(border= True):
            st.subheader('Average Income')
            
            left_4, right_4 = st.columns(2)
            with left_4:
                st.altair_chart(view_data.avg_monthly_bar_chart)
            with right_4:
                st.altair_chart(view_data.avg_daily_bar_chart)
                  
    else: 
        st.info("No transactions available. Please upload files in the Home view.")