from datetime import datetime
from typing import List

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
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }

    # Convert the months to numeric values and find the minimum
    min_month = min(months, key=lambda m: month_order[m.upper()])

    return min_month
