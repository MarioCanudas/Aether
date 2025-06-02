import pytest
import pandas as pd
from typing import Tuple, List
from core import TableNormalizer
from models.table_normalizer import TransactionTableNormalizer
# Import patterns from properties_catalog for realistic testing
from models.properties_catalog import NUMERIC_MONTH_PATTERNS, inverted_numeric_month_patterns

dummy_df = pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type'])
dummy_normalizer = TransactionTableNormalizer(dummy_df, dummy_df, {})

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

@pytest.mark.parametrize('table_normalizer_instance', BANK_FILES, indirect=True)
def test_table_normalizer_init(table_normalizer_instance):
    """Tests if the TransactionTableNormalizer initializes with the correct path."""
    table_normalizer, pdf_file = table_normalizer_instance
    try:
        assert isinstance(table_normalizer, TableNormalizer), f"Expected TableNormalizer instance, got {type(table_normalizer)} for {pdf_file}"
    except Exception as e:
        pytest.fail(f"Failed to initialize TableNormalizer for {pdf_file}: {str(e)}")

@pytest.mark.parametrize('table_normalizer_instance', BANK_FILES, indirect=True)
def test_period_idx(table_normalizer_instance):
    """Tests the period_idx property."""
    table_normalizer, pdf_file = table_normalizer_instance

    try:
        need_period: bool = table_normalizer.statement_properties['period_phrase'] is not None

        if not need_period:
            assert table_normalizer.period_idx is None, f"Period index should be None for {pdf_file}"
        else:
            period_idx = table_normalizer.period_idx
            assert isinstance(period_idx, int), f"Expected int, got {type(period_idx)} for {pdf_file}"
            assert period_idx >= 0, f"Period index should be non-negative for {pdf_file}"

    except Exception as e:
        pytest.fail(f"Failed to get period index for {pdf_file}: {str(e)}")

@pytest.mark.parametrize('table_normalizer_instance', BANK_FILES, indirect=True)
def test_detect_years(table_normalizer_instance):
    """Tests the years property."""
    table_normalizer, pdf_file = table_normalizer_instance

    try:
        years = table_normalizer.years

        need_detect_year: bool = table_normalizer.statement_properties['period_phrase'] is not None

        if not need_detect_year:
            assert years == [], f"Years should be empty for {pdf_file}"
        else:

            assert isinstance(years, list), f"Expected list, got {type(years)} for {pdf_file}"
            assert all(isinstance(year, int) for year in years), f"All elements should be integers for {pdf_file}"
            assert len(years) <= 2, f"Too many years detected ({len(years)}) for {pdf_file}"

    except Exception as e:
        pytest.fail(f"Failed to detect years for {pdf_file}: {str(e)}")

# PENDING: Uncomment and implement the months property test when ready

#@pytest.mark.parametrize('table_normalizer_instance', BANK_FILES, indirect=True)
#def test_detect_months(table_normalizer_instance):
#    """Tests the months property."""
#    table_normalizer, pdf_file = table_normalizer_instance

@pytest.mark.parametrize(
    'date_pattern, groups_date, month_pattern, test_dates', # test_dates : dict[test_date : expected_date]
    [
        # BANORTE_DEBIT
        (r"(\d{2})-(\w{3})-(\d{2})", (3, 2, 1), inverted_numeric_month_patterns, {'01-ENE-24': '2024-01-01', '31-DIC-23': '2023-12-31'}),
        # BANORTE_NEW_CREDIT
        (r"(\d{2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(20\d{2})", (3, 2, 1), inverted_numeric_month_patterns, {'15-MAY-2024': '2024-05-15', '01-JUN-2023': '2023-06-01'}),
        # BBVA_CREDIT
        (r"(\d{2})/(\d{2})/(\d{2})", (3, 2, 1), NUMERIC_MONTH_PATTERNS, {'20/03/24': '2024-03-20', '05/11/23': '2023-11-05'}),
        # BBVA_NEW_CREDIT
        (r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})", (3, 2, 1), {m.lower(): n for n, m in NUMERIC_MONTH_PATTERNS.items()}, {'10-mar-2024': '2024-03-10', '25-dic-2023': '2023-12-25'}),
        # BANAMEX_NEW_CREDIT
        (r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})", (3, 2, 1), {m.lower(): n for n, m in NUMERIC_MONTH_PATTERNS.items()}, {'01-ene-2024': '2024-01-01', '30-jun-2023': '2023-06-30'}),
        # NU_DEBIT
        (r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (20\d{2})", (3, 2, 1), inverted_numeric_month_patterns, {'12 AGO 2024': '2024-08-12', '03 MAR 2023': '2023-03-03'}),
        # Invalid date
        (r"(\d{2})/(\d{2})/(\d{2})", (3, 2, 1), NUMERIC_MONTH_PATTERNS, {'invalid-date': ''}),
    ]
)
def test_normalize_date_with_year(date_pattern: str, groups_date: Tuple[int, int, int], month_pattern: dict, test_dates: dict):
    """Test if the date_with_year method normalizes dates correctly."""

    for test_date, expected_date in test_dates.items():
        normalized_date = dummy_normalizer.normalize_date_with_year(test_date, date_pattern, groups_date, month_pattern)
        assert normalized_date == expected_date, f"Expected {expected_date}, got {normalized_date} for {test_date}"

@pytest.mark.parametrize(
    'years, date_pattern, groups_date, month_pattern, test_dates', # test_dates : dict[test_date : expected_date]
    [
        # BANORTE_CREDIT (1 year)
        ([2024], r"(\d{2})/(\d{2})", (None, 1, 2), inverted_numeric_month_patterns, {'01/01': '2024-01-01', '12/31': '2024-12-31'}),
        # BANORTE_CREDIT (2 years - assuming logic uses year1 always)
        ([2023, 2024], r"(\d{2})/(\d{2})", (None, 1, 2), inverted_numeric_month_patterns, {'01/01': '2023-01-01', '12/31': '2023-12-31'}),
        # BBVA_DEBIT (1 year)
        ([2024], r"^(\d{2})/([A-Z]{3})\b", (None, 2, 1), inverted_numeric_month_patterns, {'01/ENE': '2024-01-01', '31/DIC': '2024-12-31'}),
        # BANAMEX_CREDIT (1 year)
        ([2024], r"(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic) (\d{2})", (None, 1, 2), {m.capitalize(): n for n, m in NUMERIC_MONTH_PATTERNS.items()}, {'Ene 01': '2024-01-01', 'Dic 31': '2024-12-31'}),
        # HSBC_CREDIT (1 year)
        ([2024], r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)", (None, 2, 1), inverted_numeric_month_patterns, {'01 ENE': '2024-01-01', '31 DIC': '2024-12-31'}),
        # INBURSA_DEBIT (1 year)
        ([2024], r"(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\d{2})", (None, 1, 2), inverted_numeric_month_patterns, {'ENE 01': '2024-01-01', 'DIC 31': '2024-12-31'}),
        # INBURSA_CREDIT (1 year - assuming dd/mm)
        ([2024], r"(\d{2})/(\d{2})", (None, 2, 1), NUMERIC_MONTH_PATTERNS, {'01/01': '2024-01-01', '31/12': '2024-12-31'}),
        # NU_CREDIT (1 year)
        ([2024], r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)", (None, 2, 1), inverted_numeric_month_patterns, {'01 ENE': '2024-01-01', '31 DIC': '2024-12-31'}),
        # Invalid date
        ([2024], r"(\d{2})/(\d{2})", (None, 2, 1), inverted_numeric_month_patterns, {'invalid-date': ''}),
        # No years provided
        ([], r"(\d{2})/(\d{2})", (None, 2, 1), inverted_numeric_month_patterns, {'01/01': ''}),
    ]
)
def test_normalize_date_without_year(years: List[int], date_pattern: str, groups_date: Tuple[None, int, int], month_pattern: dict, test_dates: dict):
    """Test if the date_without_year method normalizes dates correctly."""

    for test_date, expected_date in test_dates.items():
        normalized_date = dummy_normalizer.normalize_date_without_year(test_date, years, date_pattern, groups_date, month_pattern)
        assert normalized_date == expected_date, f"Expected {expected_date}, got {normalized_date} for {test_date}"

@pytest.mark.parametrize(
    'income_sign, expense_sign, test_amounts', # test_amounts : dict[test_amount : expected_result_series]
    [
        # BANORTE_CREDIT, BANAMEX_CREDIT, HSBC_CREDIT, INBURSA_CREDIT, NU_CREDIT (Income Sign Only)
        ('-', None, {'-1,234.56': pd.Series({'Amount': 1234.56, 'Type': 'Abono'}), 
                     '500.00': pd.Series({'Amount': -500.00, 'Type': 'Cargo'}), 
                     '$100.00': pd.Series({'Amount': -100.00, 'Type': 'Cargo'})}),
        # BANORTE_NEW_CREDIT, BBVA_NEW_CREDIT, BANAMEX_NEW_CREDIT (Both Signs)
        ('-', '+', {'-1,000.00': pd.Series({'Amount': 1000.00, 'Type': 'Abono'}), 
                     '+500.00': pd.Series({'Amount': -500.00, 'Type': 'Cargo'}), 
                     '200.00': pd.Series({'Amount': 0.0, 'Type': None})}), # No sign match
        # NU_DEBIT (Both Signs, reversed)
        ('+', '-', {'+1,000.00': pd.Series({'Amount': 1000.00, 'Type': 'Abono'}), 
                     '-500.00': pd.Series({'Amount': -500.00, 'Type': 'Cargo'}), 
                     '200.00': pd.Series({'Amount': 0.0, 'Type': None})}), # No sign match
        # Hypothetical: Expense Sign Only
        (None, '-', {'-1,234.56': pd.Series({'Amount': -1234.56, 'Type': 'Cargo'}), 
                     '500.00': pd.Series({'Amount': 500.00, 'Type': 'Abono'}), 
                     '$100.00': pd.Series({'Amount': 100.00, 'Type': 'Abono'})}),
        # Hypothetical: No Signs (Should ideally not happen with this function logic)
        (None, None, {'100.00': pd.Series({'Amount': 0.0, 'Type': None})}),
    ]
)
def test_normalize_amount_for_single_column(income_sign: str, expense_sign: str, test_amounts: dict):
    """Test if the normalize_amount_for_single_column method normalizes amounts correctly."""

    for test_amount, expected_result in test_amounts.items():
        normalized_result = dummy_normalizer.normalize_amount_for_single_column(test_amount, income_sign, expense_sign)
        pd.testing.assert_series_equal(normalized_result, expected_result, check_dtype=False, 
                                       check_names=False, rtol=1e-5, atol=1e-8, 
                                       obj=f"for input {test_amount}")

@pytest.mark.parametrize(
    'income_column, expense_column, balance_column, test_rows', # test_rows : dict[tuple_representing_row : expected_result_series]
    [
        # BANORTE_DEBIT, BBVA_DEBIT, INBURSA_DEBIT (Income, Expense, Balance)
        ('ABONOS', 'CARGOS', 'SALDO', {
            # Use tuples as keys instead of pd.Series
            ('1,000.00', '', ''): pd.Series({'Amount': 1000.00, 'Type': 'Abono'}), 
            ('', '500.00', ''): pd.Series({'Amount': -500.00, 'Type': 'Cargo'}), 
            ('', '', '2,000.00'): pd.Series({'Amount': 2000.00, 'Type': 'Saldo'}), 
            ('', '', ''): pd.Series({'Amount': 0.0, 'Type': None}),
            (pd.NA, '500.00', pd.NA): pd.Series({'Amount': -500.00, 'Type': 'Cargo'}), # Handle NA
            ('invalid', '', ''): pd.Series({'Amount': 0.0, 'Type': None}), # Handle invalid float
            (pd.NA, pd.NA, pd.NA): pd.Series({'Amount': 0.0, 'Type': None}), # All NA case
        }),
        # BBVA_CREDIT (Income, Expense, No Balance)
        ('IMPORTE ABONOS', 'IMPORTE CARGOS', None, {
            # Use tuples as keys instead of pd.Series
            ('1,000.00', ''): pd.Series({'Amount': 1000.00, 'Type': 'Abono'}), 
            ('', '500.00'): pd.Series({'Amount': -500.00, 'Type': 'Cargo'}), 
            ('', ''): pd.Series({'Amount': 0.0, 'Type': None}),
        }),
    ]
)
def test_normalize_amount_for_multiple_columns(income_column: str, expense_column: str, balance_column: str, test_rows: dict):
    """Test if the normalize_amount_for_multiple_columns method normalizes amounts correctly."""

    for test_row_tuple, expected_result in test_rows.items():
        # Convert tuple back to Series with correct index
        index = [income_column, expense_column, balance_column] if balance_column else [income_column, expense_column]
        # Ensure the tuple has the correct length for the index
        if len(test_row_tuple) != len(index):
             pytest.fail(f"Test row tuple {test_row_tuple} length does not match index length {len(index)}")
        test_row_series = pd.Series(test_row_tuple, index=index)

        normalized_result = dummy_normalizer.normalize_amount_for_multiple_columns(test_row_series, income_column, expense_column, balance_column)
        pd.testing.assert_series_equal(normalized_result, expected_result, check_dtype=False, 
                                       check_names=False, rtol=1e-5, atol=1e-8, 
                                       obj=f"for input row \n{test_row_series}")

@pytest.mark.parametrize('table_normalizer_instance', BANK_FILES, indirect=True)
def test_normalize_table(table_normalizer_instance):
    """Tests if the TransactionTableNormalizer normalizes the table correctly."""
    table_normalizer, pdf_file = table_normalizer_instance
    try:
        normalized_table = table_normalizer.normalize_table()
        assert isinstance(normalized_table, pd.DataFrame), f"Expected DataFrame, got {type(normalized_table)} for {pdf_file}"
        assert not normalized_table.empty, f"Normalized table is empty for {pdf_file}"

        expected_columns = {
            'Date': 'datetime64[ns]',
            'Description': 'object',
            'Amount': 'float64',
            'Type': 'object'
        }

        for col, dtype in expected_columns.items():
            assert col in normalized_table.columns, f"Missing column {col} in normalized table for {pdf_file}"
            assert normalized_table[col].dtype == dtype, f"Column {col} has incorrect dtype {normalized_table[col].dtype} for {pdf_file}"

        assert not pd.isna(normalized_table[['Date', 'Amount', 'Type']].values).any(), f"Normalized table contains NaN values for {pdf_file}"

    except Exception as e:
        pytest.fail(f"Failed to normalize table for {pdf_file}: {str(e)}")