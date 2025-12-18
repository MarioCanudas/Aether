import asyncio
from datetime import date, timedelta

import streamlit as st
from components import period_select_box
from constants.views_icons import EXPENSES_ANALYSIS_ICON
from controllers import AnalysisController
from models.dates import Period
from models.views_data import AnalysisAmounts, PeriodsOptions
from utils import give_amount_format


def show_expenses_analysis():
    # Page config
    st.set_page_config(
        page_title="Expenses Analysis", page_icon=EXPENSES_ANALYSIS_ICON, layout="wide"
    )
    controller = AnalysisController()

    st.title("Expenses Analysis")

    # Check if monthly results are available
    if controller.user_have_transactions():
        view_data = asyncio.run(controller.get_analysis_view_data("Cargo"))

        with st.container(border=True):
            selected_period = period_select_box(key="period_selectbox_expenses")

            if selected_period == PeriodsOptions.SPECIFIC_PERIOD:
                today = date.today()
                default_period = Period(start_date=today - timedelta(days=30), end_date=today)

                specific_period = st.date_input(
                    label="Specific Period",
                    value=default_period.to_tuple(),
                    key="specific_period_date_input",
                )

                if isinstance(specific_period, tuple) and len(specific_period) == 2:
                    period = Period(start_date=specific_period[0], end_date=specific_period[1])
                else:
                    period = default_period

            left_1, center_1, right_1 = st.columns(3)

            analysis_amounts: AnalysisAmounts

            if selected_period == PeriodsOptions.SPECIFIC_PERIOD:
                analysis_amounts = asyncio.run(
                    controller.get_amounts_in_specific_period("Cargo", period)
                )
            else:
                analysis_amounts = view_data.analysis_amounts[PeriodsOptions(selected_period)]

            left_1.metric(
                "Accumulated Expenses",
                value=give_amount_format(analysis_amounts.accumulated_amount),  # type: ignore
                help="Accumulated expenses by the selected period.",
            )

            center_1.metric(
                "Max Expenses",
                value=give_amount_format(analysis_amounts.max_amount),  # type: ignore
                help="Max expenses by the selected period.",
            )

            right_1.metric(
                "Expenses frecuency",
                value=analysis_amounts.frecuency,  # type: ignore
                help="Expenses frecuency by the selected period.",
            )

        with st.container(border=True):
            left_2, right_2 = st.columns(2)
            expenses_chart_type = left_2.segmented_control(
                label="Chart type",
                options=["Daily", "Monthly"],
                key="expenses_chart_type",
                default="Daily",
                help="Select the chart type to display.",
            )

            if expenses_chart_type == "Daily":
                with right_2:
                    year = st.selectbox(
                        label="Select year",
                        options=controller.get_years(),
                        key="expenses_year_selectbox",
                        index=0,
                    )

                st.subheader("Expenses per Day")
                st.subheader("Expenses per Day")
                if year:
                    daily_bar_chart = controller.get_daily_bar_chart("Cargo", year)
                    if daily_bar_chart:
                        st.altair_chart(daily_bar_chart)
                    else:
                        st.info("No transactions available. Please upload files in the Home view.")
                else:
                    st.info("Select year and month")
            else:
                year = right_2.selectbox(
                    label="Select year",
                    options=controller.get_years(),
                    key="expenses_month_selectbox",
                    index=0,
                )
                st.subheader("Total Expenses per Month")
                monthly_bar_chart = controller.get_monthly_bar_chart("Cargo", year)
                if monthly_bar_chart:
                    st.altair_chart(monthly_bar_chart)
                else:
                    st.info("No transactions available. Please upload files in the Home view.")

        with st.container(border=True):
            st.subheader("Sources of Expenses")
            amount_per_category_chart = view_data.amount_per_category_chart
            if amount_per_category_chart:
                st.altair_chart(amount_per_category_chart)
            else:
                st.info("No transactions available. Please upload files in the Home view.")

        with st.container(border=True):
            st.subheader("Average Expenses")

            left_4, right_4 = st.columns(2)
            with left_4:
                avg_monthly_bar_chart = view_data.avg_monthly_bar_chart
                if avg_monthly_bar_chart:
                    st.altair_chart(avg_monthly_bar_chart)
                else:
                    st.info("No transactions available. Please upload files in the Home view.")
            with right_4:
                avg_daily_bar_chart = view_data.avg_daily_bar_chart
                if avg_daily_bar_chart:
                    st.altair_chart(avg_daily_bar_chart)
                else:
                    st.info("No transactions available. Please upload files in the Home view.")

    else:
        st.info("No transactions available. Please upload files in the Home view.")
