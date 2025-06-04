from typing import List
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
