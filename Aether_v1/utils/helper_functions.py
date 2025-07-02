from typing import List, Literal
import re
import pandas as pd

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

def search_phrase_in_df(df: pd.DataFrame | pd.Series, phrase: List[str], type_return: Literal['idx', 'bool'] = 'idx') -> int | bool:
    """
    Search for a phrase in a DataFrame.
    The phrase must be in lower case.

    Args:
        df (pd.DataFrame): The DataFrame to search in.
        phrase (List[str]): The phrase to search for.
        type_return (Literal['idx', 'bool']): The type of return.

    Returns:
        int | bool: The index of the phrase if type_return is 'idx', True if the phrase is found, False otherwise.
    """
    
    # Iterate through the DataFrame, stopping before we run out of rows to compare
    # We subtract len(phrase) to ensure we don't go beyond the DataFrame bounds
    for i in range(len(df) - len(phrase)):
        # Extract a slice of text from the current position with the same length as the phrase
        # Convert all text to lowercase for case-insensitive comparison
        current_slice = list(df['text'].iloc[i : i + len(phrase)].str.lower()) if isinstance(df, pd.DataFrame) else list(df.iloc[i : i + len(phrase)].str.lower())
        
        # Check if the current slice exactly matches the target phrase
        if current_slice == phrase:
            # Return based on the requested return type
            if type_return == 'idx':
                return i  # Return the starting index where the phrase was found
            elif type_return == 'bool':
                return True  # Return True indicating the phrase was found
    
    # If no match was found, return appropriate default value based on return type
    if type_return == 'idx':
        return None  # Return None when no index is found
    elif type_return == 'bool':
        return False  # Return False when phrase is not found

