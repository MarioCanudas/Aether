import matplotlib.pyplot as plt
import pandas as pd
import locale

# Line Chart
def plot_income_withdrawal_by_month(processed_data):
    """
    Plots Income and Withdrawal over time, with separate plots for each month.

    :param processed_data: DataFrame containing the processed transaction data
    """
    # Set locale to Spanish (Linux/Mac users). For Windows, see comment below.
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # For Linux/Mac users
    # locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # For Windows users

    # Ensure the 'Date' column is in datetime format for proper plotting
    processed_data['Date'] = pd.to_datetime(processed_data['Date'], format='%d-%b-%y')

    # Add 'Year-Month' column to group by month
    processed_data['Year-Month'] = processed_data['Date'].dt.to_period('M')

    # Group the data by 'Year-Month'
    grouped_data = processed_data.groupby('Year-Month')

    # Iterate through each group and create a plot for each month
    for name, group in grouped_data:
        plt.figure(figsize=(10, 6))

        # Sort the group by date in case it's not sorted
        group.sort_values('Date', inplace=True)

        # Plot Income with a line
        plt.plot(group['Date'], group['Income'], label='Income', color='green', marker='x')

        # Plot Withdrawal with a line
        plt.plot(group['Date'], group['Withdrawal'], label='Withdrawal', color='red', marker='o', linestyle='--')

        # Add labels and title
        plt.xlabel('Date')
        plt.ylabel('Amount')
        plt.title(f'Income and Withdrawal Over Time for {name}')

        # Rotate X-axis labels for better readability
        plt.xticks(rotation=45)

        # Show the legend
        plt.legend()

        # Display the plot
        plt.tight_layout()
        plt.show()

# Bar Chart
def plot_income_vs_withdrawal_by_month(processed_data):
    """
    Plots a bar chart for each month with the sum of 'Income' and 'Withdrawal' columns
    from the DataFrame, with the amount displayed above each bar for improved readability.

    :param processed_data: DataFrame containing the processed transaction data
    """
    # Set locale to Spanish (Linux/Mac users). For Windows, see comment below.
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # For Linux/Mac users
    # locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # For Windows users

    # Ensure the 'Date' column is in datetime format
    processed_data['Date'] = pd.to_datetime(processed_data['Date'], format='%d-%b-%y')

    # Add 'Year-Month' column to group by month
    processed_data['Year-Month'] = processed_data['Date'].dt.to_period('M')

    # Group the data by 'Year-Month'
    grouped_data = processed_data.groupby('Year-Month')

    # Iterate through each group and create a bar chart for each month
    for name, group in grouped_data:
        # Calculate the total sum of 'Income' and 'Withdrawal' for the current group (month)
        total_income = group['Income'].sum()
        total_withdrawal = group['Withdrawal'].sum()

        # Labels for the bar chart
        labels = ['Income', 'Withdrawal']

        # Values for the bar chart
        values = [total_income, total_withdrawal]

        # Create the bar chart
        plt.figure(figsize=(8, 6))
        bars = plt.bar(labels, values, color=['green', 'red'])

        # Add title and labels
        plt.title(f'Total Income vs. Withdrawal for {name}')
        plt.ylabel('Amount')

        # Add the amount above each bar for readability
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:.2f}', ha='center', va='bottom', fontsize=12)

        # Show the plot
        plt.tight_layout()
        plt.show()
