from datetime import date
from typing import Literal

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from constants.dates import MonthLabels
from constants.formats import AMOUNT_FORMAT
from matplotlib.figure import Figure
from models.amounts import TransactionType
from models.configs import DonutChartConfig
from models.financial import FinancialStatus
from models.goals import GoalInfo
from pandas import DataFrame


class PlottingService:
    INCOME_COLOR = "#63DF31"
    EXPENSES_COLOR = "#F52F31"
    BALANCE_COLOR = "purple"
    MONTH_LABELS = MonthLabels.get_values()

    @staticmethod
    def get_savings_donut_chart_config(label: FinancialStatus) -> DonutChartConfig:
        if label == FinancialStatus.EXCELLENT:
            return DonutChartConfig(
                completion_percentage=100, label=label, color="#1E90FF", points="100 pts"
            )
        elif label == FinancialStatus.GOOD:
            return DonutChartConfig(
                completion_percentage=75, label=label, color="#4CAF50", points="75 pts"
            )
        elif label == FinancialStatus.REGULAR:
            return DonutChartConfig(
                completion_percentage=50, label=label, color="#FF9800", points="50 pts"
            )
        elif label == FinancialStatus.POOR:
            return DonutChartConfig(
                completion_percentage=25, label=label, color="#F44336", points="25 pts"
            )
        else:
            raise ValueError(f"Invalid label: {label}")

    @staticmethod
    async def get_plot_savings_donut_chart(donut_chart_config: DonutChartConfig) -> Figure:
        """
        Plots a donut chart based on the savings compared to the average income.

        :param total_savings: The total savings value.
        :param avg_income_per_month: The average income per month.
        :return: A Matplotlib figure containing the donut chart and the corresponding label.
        """
        # Determine completion percentage, label, and color for the donut chart
        completion_percentage = donut_chart_config.completion_percentage
        color = donut_chart_config.color
        points = donut_chart_config.points

        # Plot the donut chart
        fig, ax = plt.subplots(figsize=(4, 4))
        sizes = [completion_percentage, 100 - completion_percentage]
        colors = [
            color,
            "#E0E0E0",
        ]  # Color for the completed part and light gray for the remaining part
        ax.pie(
            sizes,
            labels=["", ""],
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.2),
        )

        # Add the label in the center of the donut
        ax.text(0, 0, points, ha="center", va="center", fontsize=14, weight="bold", color="white")

        # Make the plot background transparent
        fig.patch.set_alpha(0)  # Make the figure's background transparent
        ax.set_aspect("equal")

        return fig

    async def get_income_vs_expenses_bar_chart(self, last_six_months: DataFrame) -> alt.Chart:
        bar_chart = (
            alt.Chart(last_six_months)
            .mark_bar()
            .encode(
                x=alt.X("month_label:O", title="Month", sort=self.MONTH_LABELS),
                y=alt.Y("amount:Q", title="Amount", axis=alt.Axis(format=AMOUNT_FORMAT)),
                xOffset=alt.XOffset(
                    "type:N",
                    scale=alt.Scale(
                        domain=[TransactionType.INCOME.value, TransactionType.EXPENSE.value]
                    ),
                ),
                color=alt.Color(
                    "type:N",
                    legend=None,
                    scale=alt.Scale(
                        domain=[TransactionType.INCOME.value, TransactionType.EXPENSE.value],
                        range=[PlottingService.INCOME_COLOR, PlottingService.EXPENSES_COLOR],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("month:O", title="Month"),
                    alt.Tooltip("amount:Q", title="Amount", format=AMOUNT_FORMAT),
                ],
            )
            .properties(title="Income vs Expenses (last 6 months)")
        )

        return bar_chart

    async def get_balance_line_chart(self, balance_six_months: DataFrame) -> alt.Chart:
        line_chart = (
            alt.Chart(balance_six_months)
            .mark_line(
                color=PlottingService.BALANCE_COLOR,
                point=alt.OverlayMarkDef(filled=True, color="purple", size=50),
            )
            .encode(
                x=alt.X("month_label:O", title="Month", sort=self.MONTH_LABELS),
                y=alt.Y("balance:Q", title="Balance", axis=alt.Axis(format=AMOUNT_FORMAT)),
                tooltip=[
                    alt.Tooltip("month_label:O", title="Month"),
                    alt.Tooltip("balance:Q", title="Balance", format=AMOUNT_FORMAT),
                ],
            )
            .properties(title="Balance (last 6 months)", height=500)
        )

        return line_chart

    def monthly_bar_chart(
        self, monthly_results: DataFrame, category: Literal["Abono", "Cargo"]
    ) -> alt.Chart:
        bar_chart = (
            alt.Chart(monthly_results)
            .mark_bar(
                color=PlottingService.INCOME_COLOR
                if category == "Abono"
                else PlottingService.EXPENSES_COLOR
            )
            .encode(
                x=alt.X("month_label:O", title="Month", sort=self.MONTH_LABELS),
                y=alt.Y(
                    "total_income:Q" if category == "Abono" else "total_withdrawal:Q",
                    title="Amount",
                    axis=alt.Axis(format=AMOUNT_FORMAT),
                ),
                tooltip=[
                    alt.Tooltip("month_label:O", title="Month"),
                    alt.Tooltip(
                        "total_income:Q" if category == "Abono" else "total_withdrawal:Q",
                        title="Amount",
                        format=AMOUNT_FORMAT,
                    ),
                ],
            )
        )

        return bar_chart

    def daily_bar_chart(
        self, amounts_per_day: DataFrame, category: Literal["Abono", "Cargo"]
    ) -> alt.Chart:
        bar_chart = (
            alt.Chart(amounts_per_day)
            .mark_bar(
                color=PlottingService.INCOME_COLOR
                if category == "Abono"
                else PlottingService.EXPENSES_COLOR,
                width=10,
            )
            .encode(
                x=alt.X(
                    "day:Q",
                    title="Day",
                    scale=alt.Scale(domain=[1, 31]),
                    axis=alt.Axis(tickCount=31, labelAngle=0),
                ),
                y=alt.Y("amount:Q", title="Amount", axis=alt.Axis(format=AMOUNT_FORMAT)),
                tooltip=[
                    alt.Tooltip("day:Q", title="Day"),
                    alt.Tooltip("amount:Q", title="Amount", format=AMOUNT_FORMAT),
                ],
            )
        )

        return bar_chart

    def category_amount_bar_chart(
        self, data: DataFrame, category: Literal["Abono", "Cargo"]
    ) -> alt.Chart | alt.LayerChart:
        base = alt.Chart(data).encode(
            x=alt.X(
                "amount:Q",
                title="Amount",
                axis=alt.Axis(format=AMOUNT_FORMAT),
            ),
            y=alt.Y(
                "category:N",
                title="Category",
                sort=alt.SortField(field="amount", order="descending"),
            ),
            text=alt.Text("amount:Q", format=AMOUNT_FORMAT),
            color=alt.Color(
                "category:N",
                legend=None,
                scale=alt.Scale(scheme="greens" if category == "Abono" else "reds"),
            ),
        )

        return base.mark_bar() + base.mark_text(align="left", dx=2)

    def donut_chart_goal_progress(self, goal_info: GoalInfo) -> Figure:
        completion_percentage = goal_info.progress_porcentage * 100
        porcentage_text = f"{int(completion_percentage)}%"

        fig, ax = plt.subplots()

        sizes = [completion_percentage, 100 - completion_percentage]
        colors = [
            "#275BF5",
            "#E0E0E0",
        ]  # Color for the completed part and light gray for the remaining part
        ax.pie(
            sizes,
            labels=["", ""],
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.3),
        )

        # Add the label in the center of the donut
        ax.text(
            0,
            0,
            porcentage_text,
            ha="center",
            va="center",
            fontsize=14,
            weight="bold",
            color="white",
        )

        # Make the plot background transparent
        fig.patch.set_alpha(0)  # Make the figure's background transparent
        ax.set_aspect("equal")

        return fig

    @staticmethod
    def goal_transactions_line_chart(goal_info: GoalInfo, transactions: DataFrame) -> alt.Chart:
        target_amount = float(goal_info.amount + goal_info.added_amount)

        days = (goal_info.end_date - goal_info.start_date).days
        tick_interval = days / 2 if days < 30 else days / 3

        relative_date_range = pd.date_range(start=goal_info.start_date, end=date.today(), freq="D")
        complete_dates_df = pd.DataFrame({"date": relative_date_range})

        if not transactions.empty:
            # Merge complete dates with transactions, filling missing amounts with 0
            complete_transactions = complete_dates_df.merge(
                transactions[["date", "amount"]], on="date", how="left"
            ).fillna({"amount": 0})

            # Sort by date and calculate cumulative amounts
            complete_transactions = complete_transactions.sort_values("date")
            complete_transactions["acumulated_amount"] = (
                complete_transactions["amount"].cumsum().astype(float)
            )
        else:
            # If no transactions, create DataFrame with all zeros
            complete_transactions = complete_dates_df.copy()
            complete_transactions["amount"] = 0
            complete_transactions["acumulated_amount"] = 0

        transactions_chart = (
            alt.Chart(complete_transactions)
            .mark_line(color="blue", point=True)
            .encode(
                x=alt.X(
                    "date:T",
                    title="Date",
                    scale=alt.Scale(domain=[goal_info.start_date, goal_info.end_date]),
                    axis=alt.Axis(format="%d/%m/%Y", tickCount=int(tick_interval)),
                ),
                y=alt.Y(
                    "acumulated_amount:Q",
                    title="Amount",
                    scale=alt.Scale(domain=[0, target_amount + target_amount * 0.2]),
                    axis=alt.Axis(format="$.2f"),
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Day", format="%d/%m/%Y"),
                    alt.Tooltip("acumulated_amount:Q", title="Amount", format="$.2f"),
                ],
            )
            .properties(
                title=f"Goal Progress: {goal_info.name}",
                height=500,
            )
        )

        return transactions_chart

    @staticmethod
    def goal_target_progress_line_chart(goal_info: GoalInfo) -> alt.Chart:
        target_amount = float(goal_info.amount + goal_info.added_amount)

        days = (goal_info.end_date - goal_info.start_date).days
        tick_interval = days / 2 if days < 30 else days / 3

        date_range = pd.date_range(start=goal_info.start_date, end=goal_info.end_date)
        target_progress = np.linspace(0, target_amount, len(date_range))
        target_progress_df = pd.DataFrame({"date": date_range, "amount": target_progress})

        target_progress_chart = (
            alt.Chart(target_progress_df)
            .mark_line(color="gray", strokeWidth=2, opacity=0.5, strokeDash=[5, 5])
            .encode(
                x=alt.X(
                    "date:T",
                    scale=alt.Scale(domain=[goal_info.start_date, goal_info.end_date]),
                    axis=alt.Axis(format="%d/%m/%Y", tickCount=int(tick_interval)),
                ),
                y=alt.Y(
                    "amount:Q",
                    scale=alt.Scale(domain=[0, target_amount + target_amount * 0.2]),
                    axis=alt.Axis(format="$.2f"),
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Day", format="%d/%m/%Y"),
                    alt.Tooltip("amount:Q", title="Expected Amount", format="$.2f"),
                ],
            )
        )

        return target_progress_chart

    @staticmethod
    def goal_target_amount_rule_chart(goal_info: GoalInfo) -> alt.Chart:
        target_amount = float(goal_info.amount + goal_info.added_amount)

        target_amount_df = pd.DataFrame(
            {
                "start_date": [goal_info.start_date],
                "end_date": [goal_info.end_date],
                "amount": [target_amount],
            }
        )

        target_amount_chart = (
            alt.Chart(target_amount_df)
            .mark_rule(color="red", strokeWidth=2)
            .encode(
                x="start_date:T",
                x2="end_date:T",
                y="amount:Q",
                tooltip=[alt.Tooltip("amount:Q", title="Target Amount", format="$.2f")],
            )
        )

        return target_amount_chart
