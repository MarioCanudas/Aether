import matplotlib.pyplot as plt
from datetime import date
from pandas import DataFrame, Series
from models.configs import DonutChartConfig
from models.financial import FinancialStatus
from models.goals import GoalInfo, TransactionType, GoalStatus  

class PlottingService:
    @staticmethod
    def get_savings_donut_chart_config(label: FinancialStatus) -> DonutChartConfig:
        if label == FinancialStatus.EXCELLENT:
            return DonutChartConfig(completion_percentage= 100, label= label, color= '#1E90FF', points= '100 pts')
        elif label == FinancialStatus.GOOD:
            return DonutChartConfig(completion_percentage= 75, label= label, color= '#4CAF50', points= '75 pts')
        elif label == FinancialStatus.REGULAR:
            return DonutChartConfig(completion_percentage= 50, label= label, color= '#FF9800', points= '50 pts')
        elif label == FinancialStatus.POOR:
            return DonutChartConfig(completion_percentage= 25, label= label, color= '#F44336', points= '25 pts')
        else:
            raise ValueError(f"Invalid label: {label}")
        
    @staticmethod
    def get_plot_savings_donut_chart(donut_chart_config: DonutChartConfig) -> plt.Figure:
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
        fig, ax = plt.subplots()
        sizes = [completion_percentage, 100 - completion_percentage]
        colors = [color, '#E0E0E0']  # Color for the completed part and light gray for the remaining part
        ax.pie(sizes, labels=['', ''], colors=colors, startangle=90, counterclock=False,
            wedgeprops=dict(width=0.3))

        # Add the label in the center of the donut
        ax.text(0, 0, points, ha='center', va='center', fontsize=14, weight='bold', color ='white')

        # Make the plot background transparent
        fig.patch.set_alpha(0)  # Make the figure's background transparent
        ax.set_aspect('equal')

        return fig
    
    @staticmethod
    def bar_chart_monthly_total_expenses(monthly_results: DataFrame) -> plt.figure:
        expenses_bar_chart, ax_expenses = plt.subplots()

        # Plot the data
        ax_expenses.bar(monthly_results['year_month'], monthly_results['total_withdrawal'], color='orange')

        # Transparent background, Y-axis grid only, and white labels
        expenses_bar_chart.patch.set_alpha(0)  # Transparent background
        ax_expenses.set_facecolor('none')  # Transparent axes background
        ax_expenses.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
        ax_expenses.set_xticklabels(monthly_results['year_month'], rotation=90, color='white')
        ax_expenses.set_yticklabels(ax_expenses.get_yticks(), color='white')
        
        return expenses_bar_chart
    
    @staticmethod
    def bar_chart_monthly_total_income(monthly_results: DataFrame) -> plt.figure:
        income_bar_chart, ax_income = plt.subplots()

        # Plot the data
        ax_income.bar(monthly_results['year_month'], monthly_results['total_income'], color='blue')

        # Transparent background, white grid on Y-axis only, and white labels
        income_bar_chart.patch.set_alpha(0)
        ax_income.set_facecolor('none')
        ax_income.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
        ax_income.set_xticklabels(monthly_results['year_month'], rotation=90, color='white')
        ax_income.set_yticklabels(ax_income.get_yticks(), color='white')

        return income_bar_chart
    
    @staticmethod
    def bar_chart_daily_total_expenses(avg_expenses_per_day: Series) -> plt.figure:
        expenses_bar_chart, ax_avg_expenses_per_day = plt.subplots()
        ax_avg_expenses_per_day.bar(avg_expenses_per_day.index, avg_expenses_per_day, color='red')

        # Transparent background, Y-axis grid only, and white labels
        expenses_bar_chart.patch.set_alpha(0)
        ax_avg_expenses_per_day.set_facecolor('none')
        ax_avg_expenses_per_day.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
        ax_avg_expenses_per_day.set_xticks(range(1, 32))
        ax_avg_expenses_per_day.set_xticklabels(range(1, 32), rotation=90, color='white')
        ax_avg_expenses_per_day.set_yticklabels(ax_avg_expenses_per_day.get_yticks(), color='white')

        return expenses_bar_chart
    
    @staticmethod
    def bar_chart_daily_total_income(avg_income_per_day: Series) -> plt.figure:
        income_bar_chart, ax_avg_income_per_day = plt.subplots()
        ax_avg_income_per_day.bar(avg_income_per_day.index, avg_income_per_day, color='green')

        # Transparent background, Y-axis grid only, and white labels
        income_bar_chart.patch.set_alpha(0)
        ax_avg_income_per_day.set_facecolor('none')
        ax_avg_income_per_day.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
        ax_avg_income_per_day.set_xticks(range(1, 32))
        ax_avg_income_per_day.set_xticklabels(range(1, 32), rotation=90, color='white')
        ax_avg_income_per_day.set_yticklabels(ax_avg_income_per_day.get_yticks(), color='white')
        
        return income_bar_chart
        
    def donut_chart_goal_progress(self, goal_info: GoalInfo) -> plt.figure:
        completion_percentage = goal_info.progress_porcentage * 100
        porcentage_text = f'{int(completion_percentage)}%'
        
        fig, ax = plt.subplots()
        
        sizes = [completion_percentage, 100 - completion_percentage]
        colors = ['#275BF5', '#E0E0E0']  # Color for the completed part and light gray for the remaining part
        ax.pie(sizes, labels=['', ''], colors=colors, startangle=90, counterclock=False,
            wedgeprops=dict(width=0.3))

        # Add the label in the center of the donut
        ax.text(0, 0, porcentage_text, ha='center', va='center', fontsize=14, weight='bold', color ='white')

        # Make the plot background transparent
        fig.patch.set_alpha(0)  # Make the figure's background transparent
        ax.set_aspect('equal')

        return fig