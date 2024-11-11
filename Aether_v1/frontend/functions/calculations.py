import pandas as pd

def calculate_savings_and_credit_card_expenses_by_month(processed_data):
    """
    Calculates monthly savings by subtracting total withdrawals from total income for each month,
    updates the final balance based on the initial balance and savings, and also calculates the total
    and average credit card expenses for each month.

    :param processed_data: DataFrame containing the processed transaction data
    :return: A DataFrame with columns for initial_balance, total_income, total_withdrawal, savings,
             final_balance, total_credit_card_expenses, and avg_credit_card_expense for each month.
    """
    # Ensure the 'Date' column is in datetime format
    processed_data['Date'] = pd.to_datetime(processed_data['Date'], format='%d-%b-%y')

    # Add 'Year-Month' column to group by month
    processed_data['Year-Month'] = processed_data['Date'].dt.to_period('M')

    # List to hold results for each month
    results = []

    # Group by 'Year-Month'
    grouped_data = processed_data.groupby('Year-Month')

    # Loop through each month group
    for name, group in grouped_data:
        # Extract initial balance where the description is 'SALDO ANTERIOR' for the current month, if present
        initial_balance_rows = group[group['Description'] == 'SALDO ANTERIOR']
        initial_balance = initial_balance_rows['Balance'].values[0] if not initial_balance_rows.empty else 0

        # Calculate total income and total withdrawal for the current month
        total_income = group['Income'].sum()
        total_withdrawal = group['Withdrawal'].sum()

        # Calculate savings by subtracting withdrawals from income
        savings = total_income - total_withdrawal

        # Calculate final balance: if savings is negative, subtract it from initial_balance
        if savings < 0:
            final_balance = initial_balance + savings  # Since savings is negative, this will reduce the balance
        else:
            final_balance = initial_balance + savings  # Add positive savings to initial_balance

        # Calculate the total and average credit card expenses for the current month
        credit_card_expenses = group[group['Description'].str.contains(
            'PAGO CONCENTRACION MOV TARJETA DE CRED', case=False, na=False)]
        total_credit_card_expenses = credit_card_expenses['Withdrawal'].sum()
        avg_credit_card_expense = credit_card_expenses['Withdrawal'].mean() if not credit_card_expenses.empty else 0

        # Store the results for the current month
        results.append({
            'Month': name,
            'initial_balance': initial_balance,
            'total_income': total_income,
            'total_withdrawal': total_withdrawal,
            'savings': savings,
            'final_balance': final_balance,
            'total_credit_card_expenses': total_credit_card_expenses,
            'avg_credit_card_expense': avg_credit_card_expense
        })

    # Convert the results list to a DataFrame
    results_df = pd.DataFrame(results)

    return results_df
