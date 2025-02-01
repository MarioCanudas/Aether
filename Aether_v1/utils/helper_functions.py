from datetime import datetime
from typing import List
import pandas as pd
import re

def get_min_month(months: List[str]) -> str:
    """
    Finds the earliest month from a list of month abbreviations.

    Parameters:
    - months (List[str]): A list of month abbreviations (e.g., ['NOV', 'OCT']).

    Returns:
    - str: The earliest month abbreviation.
    """
    # Define the mapping of month abbreviations to numeric values
    month_order = {
        'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }

    # Convert the months to numeric values and find the minimum
    min_month = min(months, key=lambda m: month_order[m.upper()])

    return min_month

def calculate_savings_and_validate_balances(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates monthly savings and validates balances by ensuring the running total matches the provided balances.

    :param data: DataFrame containing transaction data with 'Date', 'Description', 'Amount', 'Balance', and 'Type' columns.
    :return: A DataFrame with monthly savings and balance validation results.
    """
    # Ensure the 'Date' column is in datetime format
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')

    # Add 'Year-Month' column for grouping
    data['Year-Month'] = data['Date'].dt.to_period('M')

    # Initialize a list to store results
    results = []

    # Group data by 'Year-Month'
    grouped = data.groupby('Year-Month')

    for name, group in grouped:
        # Sort by date within the group for proper calculations
        group = group.sort_values(by='Date')

        # Extract the initial balance from "Saldo inicial"
        initial_balance_row = group[group['Description'].str.contains('Saldo inicial', case=False, na=False)]
        initial_balance = initial_balance_row['Balance'].values[0] if not initial_balance_row.empty else None

        # Calculate total income and withdrawals
        total_income = group[group['Type'] == 'Abono']['Amount'].sum()
        total_withdrawal = group[group['Type'] == 'Cargo']['Amount'].sum()

        # Calculate savings
        savings = total_income + total_withdrawal  # Withdrawals are negative, so adding them works here

        # Validate balances
        running_sum = initial_balance if initial_balance is not None else 0
        balance_valid = True
        for _, row in group.iterrows():
            running_sum += row['Amount']
            if pd.notnull(row['Balance']) and abs(running_sum - row['Balance']) > 1e-2:
                balance_valid = False
                break

        # Append results
        results.append({
            'Month': name,
            'initial_balance': initial_balance,
            'total_income': total_income,
            'total_withdrawal': total_withdrawal,
            'savings': savings,
            'balance_valid': balance_valid
        })

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    return results_df

def eliminate_ocr_errors_for_amounts(value: str) -> str:
    """
    Corrects common OCR errors in numerical strings representing monetary amounts.

    Args:
        value: A string containing a numerical value with potential OCR errors, such as misplaced spaces or commas.

    Returns:
        A corrected string representing the numerical value with the decimal point correctly positioned.
    """

    value = value.replace(' ', '')

    parts = re.split(r',', value)

    if len(parts) > 1:
        if len(parts[-1]) == 2:
            int_part = ''.join(parts[:-1])
            decimal_part = parts[-1]

            value = f'{int_part}.{decimal_part}'
        else:
            value = ''.join(parts)

    if value.count('.') > 1:
        *int_parts, decimal_part = value.split('.')
        value = f"{''.join(int_parts)}.{decimal_part}"

    return value

def delete_double_transactions(data: pd.DataFrame) -> pd.DataFrame:
    """
    Removes duplicate transactions from a financial dataset, specifically targeting credit card payments
    (abonos) and their corresponding debit transactions (cargos) to avoid double-counting.

    The function identifies:
    1. Credit transactions that are marked as "Abono" in the credit statement.
    2. Debit transactions that are marked as "Cargo" in the debit statement.
    3. Matches debit transactions to credit transactions based on:
       - Equal transaction amounts.
       - Debit transaction dates less than or equal to the corresponding credit transaction dates.
    4. Removes the credit transaction and the last matching debit transaction (based on the date).

    Parameters:
        data (pd.DataFrame): A DataFrame containing financial transaction data with the following expected columns:
            - 'statement_type': Type of statement ('credit' or 'debit').
            - 'Type': Type of transaction ('Abono' for payments, 'Cargo' for charges).
            - 'Amount': The transaction amount.
            - 'Date': The date of the transaction.

    Returns:
        pd.DataFrame: A cleaned DataFrame with duplicate transactions removed.

    Example:
        cleaned_data = delete_double_transactions(transaction_data)
    """
    data_cleaned = data.copy()

    credit_transactions = data_cleaned[
        (data_cleaned['statement_type'] == 'credit') &
        (data_cleaned['Type'] == 'Abono')
    ]
    debit_transactions = data_cleaned[
        (data_cleaned['statement_type'] == 'debit') &
        (data_cleaned['Type'] == 'Cargo')
    ]

    indices_to_remove = []

    for index, credit in credit_transactions.iterrows():
        matching_debit = debit_transactions[
            (debit_transactions['Amount'] == -credit['Amount']) &
            (debit_transactions['Date'] <= credit['Date'])
        ]

        if not matching_debit.empty:
            # Find the last matching debit based on date
            last_matching_debit = matching_debit.sort_values(by='Date').iloc[-1]
            # Add indices of credit and the last matching debit to the list
            indices_to_remove.extend([index, last_matching_debit.name])

    return data_cleaned.drop(indices_to_remove)
