import pytest
import pandas as pd
import re
from core import TableReconstructor
from models.table_reconstructor import is_amount

BANK_FILES = [
    #'amex_credit_new.pdf',
    #'amex_credit_old.pdf',
    'banamex_credit_new.pdf',
    'banamex_credit_old.pdf',
    #'banamex_debit.pdf',
    'banorte_credit_new.pdf',
    'banorte_credit_old.pdf',
    'banorte_debit.pdf',
    'bbva_credit_new.pdf',
    'bbva_credit_old.pdf', 
    'bbva_debit.pdf',
    #'hsbc_credit_new.pdf',
    'hsbc_credit_old.pdf',
    #'hsbc_debit.pdf',
    #'inbursa_credit_new.pdf',
    'inbursa_credit_old.pdf',
    'inbursa_debit.pdf',
    'nu_credit.pdf',
    'nu_debit.pdf',
]

@pytest.mark.parametrize('table_reconstructor_instance', BANK_FILES, indirect=True)
def test_table_reconstructor_init(table_reconstructor_instance):
    """Tests if the TransactionTableReconstructor initializes with the correct path."""
    table_reconstructor, pdf_file = table_reconstructor_instance
    try:
        assert isinstance(table_reconstructor, TableReconstructor), f"Expected TableReconstructor instance, got {type(table_reconstructor)} for {pdf_file}"
    except Exception as e:
        pytest.fail(f"Failed to initialize TableReconstructor for {pdf_file}: {str(e)}")

@pytest.mark.parametrize('table_reconstructor_instance', BANK_FILES, indirect=True)
def test_column_positions(table_reconstructor_instance):
    """Tests the column_positions property."""
    table_reconstructor, pdf_file = table_reconstructor_instance
    try:
        column_positions = table_reconstructor.column_positions
        assert isinstance(column_positions, dict), f"Expected dict, got {type(column_positions)} for {pdf_file}"

        columns = table_reconstructor.statement_propertys['columns']
        assert all(col in column_positions.keys() for col in columns), f"Not all columns found in column positions for {pdf_file}"
        assert all(isinstance(pos, tuple) and len(pos) == 2 for pos in column_positions.values()), f"Column positions should be tuples of length 2 for {pdf_file}"
        assert all(isinstance(x0, (float, int)) and isinstance(x1, (float, int)) for x0, x1 in column_positions.values()), f"Column positions should be floats for {pdf_file}"
    except Exception as e:
        pytest.fail(f"Failed to get column positions for {pdf_file}: {str(e)}")

def test_is_amount():
    """Tests the is_amount method."""

    test_amount_list = [
        "0.00",
        "1.23",
        "12.34",
        "123.45",
        "1,234.56",
        "12,345.67",
        "123,456.78",
        "1,234,567.89",
        "$1,234.56",
        "+123.45",
        "-0.50",
        "$+10.00", # Regex allows this
        "$-10.00", # Regex allows this
        "1,234.56-",
        "50.00+",
        " 100.00 ", # Test stripping
        "\t$1,000.00\n", # Test stripping
        "+$100.00",
        "-$50.00",
        "+1,000.00+", # Regex allows this
        "-1,000.00-", # Regex allows this
    ]

    test_not_amount_list = [
        "1234",          # No decimal part
        "1,234",         # No decimal part
        "12.3",          # Incorrect decimal digits
        "12.345",        # Incorrect decimal digits
        "1234,567.89",   # Incorrect comma placement
        "1,23.45",       # Incorrect comma placement
        "01.23",         # Leading zero (except for 0.xx)
        "abc",           # Non-numeric
        "12a.34",        # Non-numeric
        "12.34x",        # Non-numeric
        "$",             # Just symbols
        "-",
        "+",
        "12$3.45",       # Symbol in wrong place
        "12.34$",        # Symbol in wrong place (except trailing sign)
        "1.2.34",        # Multiple decimal points
        "1,2,3.45",      # Multiple commas incorrectly placed
        "1,234.",        # Decimal point without digits
        ".45",           # No digits before decimal
        "1 234.56",      # Space instead of comma
        "-$ 100.00",     # Space after sign
        "+ 100.00",      # Space after sign
    ]

    try:
        assert all(is_amount(value) for value in test_amount_list), f"Expected all values in test_amount_list to be amounts"
        assert all(not is_amount(value) for value in test_not_amount_list), f"Expected all values in test_not_amount_list to not be amounts"
    except Exception as e:
        pytest.fail(f"Failed to test is_amount: {str(e)}")

def is_date(date_pattern: str, value: str) -> bool:
    """
    Checks if a value matches a date pattern.
    """
    return bool(re.match(date_pattern, value.strip()))

@pytest.mark.parametrize('table_reconstructor_instance', BANK_FILES, indirect=True)
def test_get_structured_table(table_reconstructor_instance):
    """Tests the get_structured_table method."""
    table_reconstructor, pdf_file = table_reconstructor_instance
    columns = table_reconstructor.statement_propertys['columns']

    try:
        structured_table = table_reconstructor.get_structured_table()

        assert isinstance(structured_table, pd.DataFrame), f"Expected DataFrame, got {type(structured_table)} for {pdf_file}"
        assert not structured_table.empty, "DataFrame should not be empty"

        assert all(col in structured_table.columns for col in columns), f"Not all columns found in structured table for {pdf_file}"
    except Exception as e:
        pytest.fail(f"Failed to get structured table: {str(e)}")

@pytest.mark.parametrize('table_reconstructor_instance', BANK_FILES, indirect=True)
def test_reconstruct_table(table_reconstructor_instance):
    """Tests the reconstruct_table method."""
    table_reconstructor, pdf_file = table_reconstructor_instance
    columns  = table_reconstructor.statement_propertys['columns']

    date_column = table_reconstructor.statement_propertys['date_column']
    amounts_columns = table_reconstructor.statement_propertys['amount_column']

    date_pattern = table_reconstructor.statement_propertys['date_pattern']

    try:
        reconstructed_table = table_reconstructor.reconstruct_table()

        assert isinstance(reconstructed_table, pd.DataFrame), f"Expected DataFrame, got {type(reconstructed_table)} for {pdf_file}"
        assert not reconstructed_table.empty, "Reconstructed table should not be empty"

        assert not pd.isna(reconstructed_table.values).any(), "Reconstructed table should not contain NaN values"
        assert all(col in reconstructed_table.columns for col in columns), f"Not all columns found in reconstructed table for {pdf_file}"

        all_valid_dates = reconstructed_table[date_column].apply(lambda x: is_date(date_pattern, x)).all()
        assert all_valid_dates, f"Not all values in {date_column} are valid dates for {pdf_file}"

        for col in amounts_columns:
            assert reconstructed_table[col].apply(is_amount).all(), f"Not all values in {col} are valid amounts for {pdf_file}"
    except Exception as e:
        pytest.fail(f"Failed to reconstruct table: {str(e)}")