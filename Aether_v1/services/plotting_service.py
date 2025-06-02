import matplotlib.pyplot as plt

class PlottingService:
    def get_savings_donut_chart_config(self, total_savings, avg_income_per_month):
        if total_savings >= 0.10 * avg_income_per_month:
            return {'completion_percentage': 100, 'label': "Excellent!", "color": '#1E90FF', "points": '100 pts'}
        elif 0 <= total_savings < 0.10 * avg_income_per_month:
            return {'completion_percentage': 75, 'label': "Good", "color": '#4CAF50', "points": '75 pts'}
        elif -0.10 * avg_income_per_month <= total_savings < 0:
            return {'completion_percentage': 50, 'label': "Regular", "color": '#FF9800', "points": '50 pts'}
        else:
            return {'completion_percentage': 25, 'label': "Poor", "color": '#F44336', "points": '25 pts'}
            
    def get_plot_savings_donut_chart(self, total_savings, avg_income_per_month):
        """
        Plots a donut chart based on the savings compared to the average income.

        :param total_savings: The total savings value.
        :param avg_income_per_month: The average income per month.
        :return: A Matplotlib figure containing the donut chart and the corresponding label.
        """
        # Determine completion percentage, label, and color for the donut chart
        config = self.get_savings_donut_chart_config(total_savings, avg_income_per_month)
        completion_percentage = config['completion_percentage']
        label = config['label']
        color = config['color']
        points = config['points']

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

        return fig, label