import pytest
import pandas as pd
from unittest.mock import patch
from models import DateNormalizer, AmountNormalizer, DefaultTableNormalizer
from models.document_processing.banks_properties import BANORTE_DEBIT_PROPERTIES, BBVA_DEBIT_PROPERTIES, BANORTE_CREDIT_PROPERTIES

# Test files to use for different scenarios
RECONSTRUCTED_TABLE_FILE = 'banorte_debit_reconstructed_table.csv'
BBVA_RECONSTRUCTED_TABLE_FILE = 'bbva_debit_reconstructed_table.csv'
BANORTE_CREDIT_RECONSTRUCTED_FILE = 'banorte_credit_old_reconstructed_table.csv'

# Test statement properties for different scenarios
TEST_PROPERTIES_WITH_YEAR = {
    'date_pattern': r'(\d{2})-(\w{3})-(\d{2})',
    'date_groups': (3, 2, 1),  # (year, month, day)
    'month_pattern': {'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04'},
    'amount_column': ['MONTO'],
    'income_sign': '+',
    'expense_sign': '-',
    'statement_type': 'debit',
    'initial_balance_description': None
}

TEST_PROPERTIES_WITHOUT_YEAR = {
    'date_pattern': r'(\d{2})/(\w{3})',
    'date_groups': (None, 2, 1),  # (year, month, day)
    'month_pattern': {'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04'},
    'amount_column': ['MONTO'],
    'income_sign': None,
    'expense_sign': None,
    'statement_type': 'debit',
    'initial_balance_description': None
}

TEST_PROPERTIES_MULTI_AMOUNT = {
    'date_pattern': r'(\d{2})-(\w{3})-(\d{4})',
    'date_groups': (3, 2, 1),
    'month_pattern': {'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04'},
    'amount_column': ['DEPOSITO', 'RETIRO', 'SALDO'],
    'income_column': 'DEPOSITO',
    'expense_column': 'RETIRO',
    'balance_column': 'SALDO',
    'income_sign': None,
    'expense_sign': None,
    'statement_type': 'debit',
    'initial_balance_description': 'SALDO ANTERIOR'
}

TEST_PROPERTIES_CREDIT = {
    'date_pattern': r'(\d{2})/(\d{2})',
    'date_groups': (None, 1, 2),
    'month_pattern': {'01': '01', '02': '02', '03': '03'},
    'amount_column': ['IMPORTE'],
    'income_sign': '-',
    'expense_sign': None,
    'statement_type': 'credit',
    'initial_balance_description': None
}


class TestDateNormalizerStaticMethods:
    """Test cases for DateNormalizer static methods"""
    
    def test_normalize_date_with_year_full_year(self):
        """Test date normalization with full 4-digit year"""
        date = "15-MAR-2024"
        date_pattern = r'(\d{2})-(\w{3})-(\d{4})'
        groups_date = (3, 2, 1)  # (year, month, day)
        month_pattern = {'MAR': '03'}
        
        result = DateNormalizer.normalize_date_with_year(date, date_pattern, groups_date, month_pattern)
        
        assert result == "2024-03-15"
    
    def test_normalize_date_with_year_two_digit_year(self):
        """Test date normalization with 2-digit year"""
        date = "15-MAR-24"
        date_pattern = r'(\d{2})-(\w{3})-(\d{2})'
        groups_date = (3, 2, 1)
        month_pattern = {'MAR': '03'}
        
        result = DateNormalizer.normalize_date_with_year(date, date_pattern, groups_date, month_pattern)
        
        assert result == "2024-03-15"
    
    def test_normalize_date_with_year_numeric_month(self):
        """Test date normalization with numeric month"""
        date = "15-03-2024"
        date_pattern = r'(\d{2})-(\d{2})-(\d{4})'
        groups_date = (3, 2, 1)
        month_pattern = {}  # Not used for numeric months
        
        result = DateNormalizer.normalize_date_with_year(date, date_pattern, groups_date, month_pattern)
        
        assert result == "2024-03-15"
    
    def test_normalize_date_with_year_no_match(self):
        """Test date normalization when pattern doesn't match"""
        date = "invalid-date"
        date_pattern = r'(\d{2})-(\w{3})-(\d{4})'
        groups_date = (3, 2, 1)
        month_pattern = {'MAR': '03'}
        
        result = DateNormalizer.normalize_date_with_year(date, date_pattern, groups_date, month_pattern)
        
        assert result == ""
    
    def test_normalize_date_without_year_single_year(self):
        """Test date normalization without year using single year from period"""
        date = "15/MAR"
        years = [2024]
        date_pattern = r'(\d{2})/(\w{3})'
        groups_date = (None, 2, 1)
        month_pattern = {'MAR': '03'}
        
        result = DateNormalizer.normalize_date_without_year(date, years, date_pattern, groups_date, month_pattern)
        
        assert result == "2024-03-15"
    
    def test_normalize_date_without_year_cross_year_early_month(self):
        """Test date normalization for cross-year period with early month"""
        date = "15/MAR"
        years = [2023, 2024]
        date_pattern = r'(\d{2})/(\w{3})'
        groups_date = (None, 2, 1)
        month_pattern = {'MAR': '03'}
        
        result = DateNormalizer.normalize_date_without_year(date, years, date_pattern, groups_date, month_pattern)
        
        assert result == "2023-03-15"  # Early month assigned to first year
    
    def test_normalize_date_without_year_cross_year_late_month(self):
        """Test date normalization for cross-year period with late month"""
        date = "15/DIC"
        years = [2023, 2024]
        date_pattern = r'(\d{2})/(\w{3})'
        groups_date = (None, 2, 1)
        month_pattern = {'DIC': '12'}
        
        result = DateNormalizer.normalize_date_without_year(date, years, date_pattern, groups_date, month_pattern)
        
        assert result == "2023-12-15"  # Month <= 12, assigned to first year
    
    def test_normalize_date_without_year_no_years(self):
        """Test date normalization when no valid years are provided"""
        date = "15/MAR"
        years = []
        date_pattern = r'(\d{2})/(\w{3})'
        groups_date = (None, 2, 1)
        month_pattern = {'MAR': '03'}
        
        result = DateNormalizer.normalize_date_without_year(date, years, date_pattern, groups_date, month_pattern)
        
        assert result == ""
    
    def test_normalize_date_without_year_no_match(self):
        """Test date normalization when pattern doesn't match"""
        date = "invalid"
        years = [2024]
        date_pattern = r'(\d{2})/(\w{3})'
        groups_date = (None, 2, 1)
        month_pattern = {'MAR': '03'}
        
        result = DateNormalizer.normalize_date_without_year(date, years, date_pattern, groups_date, month_pattern)
        
        assert result == ""


class TestDateNormalizerNormalizeColumn:
    """Test cases for DateNormalizer normalize_column method"""
    
    def test_normalize_column_with_year(self):
        """Test column normalization when dates include year"""
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        
        date_series = pd.Series(['15-MAR-24', '20-ABR-24', '01-ENE-24'])
        years = [2024]
        
        result = date_normalizer.normalize_column(date_series, years)
        
        expected = pd.Series(['2024-03-15', '2024-04-20', '2024-01-01'])
        pd.testing.assert_series_equal(result, expected)
    
    def test_normalize_column_without_year(self):
        """Test column normalization when dates don't include year"""
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITHOUT_YEAR)
        
        date_series = pd.Series(['15/MAR', '20/ABR', '01/ENE'])
        years = [2024]
        
        result = date_normalizer.normalize_column(date_series, years)
        
        expected = pd.Series(['2024-03-15', '2024-04-20', '2024-01-01'])
        pd.testing.assert_series_equal(result, expected)
    
    def test_normalize_column_mixed_valid_invalid(self):
        """Test column normalization with mix of valid and invalid dates"""
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        
        date_series = pd.Series(['15-MAR-24', 'invalid', '01-ENE-24'])
        years = [2024]
        
        result = date_normalizer.normalize_column(date_series, years)
        
        expected = pd.Series(['2024-03-15', '', '2024-01-01'])
        pd.testing.assert_series_equal(result, expected)


class TestAmountNormalizerStaticMethods:
    """Test cases for AmountNormalizer static methods"""
    
    def test_normalize_amount_single_column_income_sign_only(self):
        """Test single column normalization with income sign only"""
        value = "+1500.00"
        income_sign = "+"
        expense_sign = None
        
        with patch('utils.clean_amount', return_value='1500.00'):
            result = AmountNormalizer.normalize_amount_for_single_column(value, income_sign, expense_sign)
        
        assert result['Amount'] == 1500.00
        assert result['Type'] == 'Abono'
    
    def test_normalize_amount_single_column_expense_sign_only(self):
        """Test single column normalization with expense sign only"""
        value = "-750.50"
        income_sign = None
        expense_sign = "-"
        
        with patch('utils.clean_amount', return_value='750.50'):
            result = AmountNormalizer.normalize_amount_for_single_column(value, income_sign, expense_sign)
        
        assert result['Amount'] == -750.50
        assert result['Type'] == 'Cargo'
    
    def test_normalize_amount_single_column_both_signs_income(self):
        """Test single column normalization with both signs present - income case"""
        value = "+2000.00"
        income_sign = "+"
        expense_sign = "-"
        
        with patch('utils.clean_amount', return_value='2000.00'):
            result = AmountNormalizer.normalize_amount_for_single_column(value, income_sign, expense_sign)
        
        assert result['Amount'] == 2000.00
        assert result['Type'] == 'Abono'
    
    def test_normalize_amount_single_column_both_signs_expense(self):
        """Test single column normalization with both signs present - expense case"""
        value = "-1000.00"
        income_sign = "+"
        expense_sign = "-"
        
        with patch('utils.clean_amount', return_value='1000.00'):
            result = AmountNormalizer.normalize_amount_for_single_column(value, income_sign, expense_sign)
        
        assert result['Amount'] == -1000.00
        assert result['Type'] == 'Cargo'
    
    def test_normalize_amount_single_column_no_expense_sign_default_expense(self):
        """Test single column normalization without expense sign - defaults to expense"""
        value = "500.00"
        income_sign = "+"
        expense_sign = None
        
        with patch('utils.clean_amount', return_value='500.00'):
            result = AmountNormalizer.normalize_amount_for_single_column(value, income_sign, expense_sign)
        
        assert result['Amount'] == -500.00  # Default to expense when no income sign
        assert result['Type'] == 'Cargo'
    
    def test_normalize_amount_multiple_columns_income_only(self):
        """Test multiple column normalization with income only"""
        row = pd.Series({
            'DEPOSITO': '1500.00',
            'RETIRO': '',
            'SALDO': '2500.00'
        })
        
        with patch('utils.clean_amount', return_value='1500.00'):
            result = AmountNormalizer.normalize_amount_for_multiple_columns(row, 'DEPOSITO', 'RETIRO', 'SALDO')
        
        assert result['Amount'] == 1500.00
        assert result['Type'] == 'Abono'
    
    def test_normalize_amount_multiple_columns_expense_only(self):
        """Test multiple column normalization with expense only"""
        row = pd.Series({
            'DEPOSITO': '',
            'RETIRO': '750.00',
            'SALDO': '1750.00'
        })
        
        with patch('utils.clean_amount', return_value='750.00'):
            result = AmountNormalizer.normalize_amount_for_multiple_columns(row, 'DEPOSITO', 'RETIRO', 'SALDO')
        
        assert result['Amount'] == -750.00
        assert result['Type'] == 'Cargo'
    
    def test_normalize_amount_multiple_columns_balance_only(self):
        """Test multiple column normalization with balance only"""
        row = pd.Series({
            'DEPOSITO': '',
            'RETIRO': '',
            'SALDO': '3000.00'
        })
        
        with patch('utils.clean_amount', return_value='3000.00'):
            result = AmountNormalizer.normalize_amount_for_multiple_columns(row, 'DEPOSITO', 'RETIRO', 'SALDO')
        
        assert result['Amount'] == 3000.00
        assert result['Type'] == 'Saldo'
    
    def test_normalize_amount_multiple_columns_conflict_income_wins(self):
        """Test multiple column normalization with conflicting amounts - income wins"""
        row = pd.Series({
            'DEPOSITO': '2000.00',
            'RETIRO': '500.00',
            'SALDO': '1500.00'
        })
        
        def mock_clean_amount(value):
            return {'2000.00': '2000.00', '500.00': '500.00'}[value]
        
        with patch('utils.clean_amount', side_effect=mock_clean_amount):
            result = AmountNormalizer.normalize_amount_for_multiple_columns(row, 'DEPOSITO', 'RETIRO', 'SALDO')
        
        assert result['Amount'] == 1500.00  # 2000 - 500
        assert result['Type'] == 'Abono'
    
    def test_normalize_amount_multiple_columns_conflict_expense_wins(self):
        """Test multiple column normalization with conflicting amounts - expense wins"""
        row = pd.Series({
            'DEPOSITO': '500.00',
            'RETIRO': '2000.00',
            'SALDO': '1500.00'
        })
        
        def mock_clean_amount(value):
            return {'2000.00': '2000.00', '500.00': '500.00'}[value]
        
        with patch('utils.clean_amount', side_effect=mock_clean_amount):
            result = AmountNormalizer.normalize_amount_for_multiple_columns(row, 'DEPOSITO', 'RETIRO', 'SALDO')
        
        assert result['Amount'] == 1500.00  # 2000 - 500
        assert result['Type'] == 'Cargo'
    
    def test_normalize_amount_multiple_columns_na_values(self):
        """Test multiple column normalization with NaN values"""
        row = pd.Series({
            'DEPOSITO': None,
            'RETIRO': pd.NA,
            'SALDO': '1000.00'
        })
        
        with patch('utils.clean_amount', return_value='1000.00'):
            result = AmountNormalizer.normalize_amount_for_multiple_columns(row, 'DEPOSITO', 'RETIRO', 'SALDO')
        
        assert result['Amount'] == 1000.00
        assert result['Type'] == 'Saldo'
    
    def test_normalize_amount_multiple_columns_invalid_values(self):
        """Test multiple column normalization with invalid numeric values"""
        row = pd.Series({
            'DEPOSITO': None,
            'RETIRO': '',
            'SALDO': '1000.00'
        })
        
        result = AmountNormalizer.normalize_amount_for_multiple_columns(row, 'DEPOSITO', 'RETIRO', 'SALDO')
        
        assert result['Amount'] == 1000.00
        assert result['Type'] == 'Saldo'


class TestAmountNormalizerNormalizeColumn:
    """Test cases for AmountNormalizer normalize_column method"""
    
    def test_normalize_column_single_series(self):
        """Test column normalization with single Series input"""
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        
        amount_series = pd.Series(['+1500.00', '-750.00', '+2000.00'])
        
        with patch('utils.clean_amount', side_effect=['1500.00', '750.00', '2000.00']):
            result = amount_normalizer.normalize_column(amount_series)
        
        expected = pd.DataFrame({
            'Amount': [1500.00, -750.00, 2000.00],
            'Type': ['Abono', 'Cargo', 'Abono']
        })
        
        pd.testing.assert_frame_equal(result.reset_index(drop=True), expected)
    
    def test_normalize_column_multiple_dataframe(self):
        """Test column normalization with DataFrame input (multiple columns)"""
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        
        amount_df = pd.DataFrame({
            'DEPOSITO': ['1500.00', '', '2000.00'],
            'RETIRO': ['', '750.00', ''],
            'SALDO': ['2500.00', '1750.00', '4000.00']
        })
        
        with patch('utils.clean_amount', side_effect=['1500.00', '750.00', '2000.00']):
            result = amount_normalizer.normalize_column(amount_df)
        
        expected = pd.DataFrame({
            'Amount': [1500.00, -750.00, 2000.00],
            'Type': ['Abono', 'Cargo', 'Abono']
        })
        
        pd.testing.assert_frame_equal(result.reset_index(drop=True), expected)


class TestDefaultTableNormalizerInitialization:
    """Test cases for DefaultTableNormalizer initialization"""
    
    def test_initialization_with_table_and_properties(self):
        """Test DefaultTableNormalizer initialization"""
        mock_table = pd.DataFrame({
            'Date': ['15-MAR-24', '20-ABR-24'],
            'Description': ['Test 1', 'Test 2'],
            'MONTO': ['1500.00', '750.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        assert normalizer.reconstructed_table.equals(mock_table)
        assert normalizer.statement_properties == TEST_PROPERTIES_WITH_YEAR
        assert isinstance(normalizer.date_normalizer, DateNormalizer)
        assert isinstance(normalizer.amount_normalizer, AmountNormalizer)


class TestDefaultTableNormalizerAddInitialBalance:
    """Test cases for add_initial_balance method"""
    
    def test_add_initial_balance_credit_statement(self):
        """Test that initial balance is skipped for credit statements"""
        mock_table = pd.DataFrame({
            'Date': pd.to_datetime(['2024-03-15', '2024-03-20']),
            'Description': ['Test 1', 'Test 2'],
            'Amount': [1500.00, 750.00],
            'Type': ['Abono', 'Cargo']
        })
        
        credit_properties = TEST_PROPERTIES_CREDIT.copy()
        date_normalizer = DateNormalizer(credit_properties)
        amount_normalizer = AmountNormalizer(credit_properties)
        normalizer = DefaultTableNormalizer(mock_table, credit_properties, date_normalizer, amount_normalizer)
        
        result = normalizer.add_initial_balance(mock_table, 1000.00)
        
        # Should return unchanged table for credit statements
        pd.testing.assert_frame_equal(result, mock_table)
    
    def test_add_initial_balance_existing_description_found(self):
        """Test marking existing initial balance entry"""
        mock_table = pd.DataFrame({
            'Date': pd.to_datetime(['2024-03-01', '2024-03-15']),
            'Description': ['SALDO ANTERIOR', 'Test Transaction'],
            'Amount': [157.39, 1500.00],
            'Type': ['Saldo', 'Abono']
        })
        
        properties = TEST_PROPERTIES_MULTI_AMOUNT.copy()
        date_normalizer = DateNormalizer(properties)
        amount_normalizer = AmountNormalizer(properties)
        normalizer = DefaultTableNormalizer(mock_table, properties, date_normalizer, amount_normalizer)
        
        result = normalizer.add_initial_balance(mock_table, 157.39)
        
        # Should mark existing entry as 'Saldo inicial'
        assert result.loc[0, 'Type'] == 'Saldo inicial'
        assert len(result) == 2  # No new row added
    
    def test_add_initial_balance_no_existing_description(self):
        """Test creating new initial balance entry when not found"""
        mock_table = pd.DataFrame({
            'Date': pd.to_datetime(['2024-03-15', '2024-03-20']),
            'Description': ['Test 1', 'Test 2'],
            'Amount': [1500.00, 750.00],
            'Type': ['Abono', 'Cargo']
        })
        
        properties = TEST_PROPERTIES_MULTI_AMOUNT.copy()
        date_normalizer = DateNormalizer(properties)
        amount_normalizer = AmountNormalizer(properties)
        normalizer = DefaultTableNormalizer(mock_table, properties, date_normalizer, amount_normalizer)
        
        result = normalizer.add_initial_balance(mock_table, 1000.00)
        
        # Should add new initial balance row
        assert len(result) == 3
        initial_balance_row = result[result['Type'] == 'Saldo inicial'].iloc[0]
        assert initial_balance_row['Description'] == 'Saldo inicial'
        assert initial_balance_row['Amount'] == 1000.00
        assert initial_balance_row['Date'] == pd.to_datetime('2024-03-15')  # Min date
    
    def test_add_initial_balance_no_description_configured(self):
        """Test creating new entry when no initial balance description is configured"""
        mock_table = pd.DataFrame({
            'Date': pd.to_datetime(['2024-03-15', '2024-03-20']),
            'Description': ['Test 1', 'Test 2'],
            'Amount': [1500.00, 750.00],
            'Type': ['Abono', 'Cargo']
        })
        
        properties = TEST_PROPERTIES_WITH_YEAR.copy()
        properties['initial_balance_description'] = None
        date_normalizer = DateNormalizer(properties)
        amount_normalizer = AmountNormalizer(properties)
        normalizer = DefaultTableNormalizer(mock_table, properties, date_normalizer, amount_normalizer)
        
        result = normalizer.add_initial_balance(mock_table, 500.00)
        
        # Should add new initial balance row
        assert len(result) == 3
        initial_balance_row = result[result['Type'] == 'Saldo inicial'].iloc[0]
        assert initial_balance_row['Description'] == 'Saldo inicial'
        assert initial_balance_row['Amount'] == 500.00


class TestDefaultTableNormalizerNormalizeTable:
    """Test cases for normalize_table method (main integration)"""
    
    def test_normalize_table_single_amount_column(self):
        """Test complete table normalization with single amount column"""
        mock_table = pd.DataFrame({
            'Date': ['15-MAR-24', '20-ABR-24'],
            'Description': ['Test Income', 'Test Expense'],
            'MONTO': ['+1500.00', '-750.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', side_effect=['1500.00', '750.00']):
            result = normalizer.normalize_table([2024], 1000.00)
        
        # Check structure
        assert 'Date' in result.columns
        assert 'Description' in result.columns
        assert 'Amount' in result.columns
        assert 'Type' in result.columns
        
        # Check date normalization
        assert result['Date'].dtype == 'datetime64[ns]'
        
        # Check sorting by date
        assert result['Date'].is_monotonic_increasing
        
        # Check initial balance addition
        assert 'Saldo inicial' in result['Type'].values
    
    def test_normalize_table_multiple_amount_columns(self):
        """Test complete table normalization with multiple amount columns"""
        mock_table = pd.DataFrame({
            'Date': ['01-MAR-2024', '15-MAR-2024'],
            'Description': ['SALDO ANTERIOR', 'Test Transaction'],
            'DEPOSITO': ['', '1500.00'],
            'RETIRO': ['', ''],
            'SALDO': ['157.39', '1657.39']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_MULTI_AMOUNT, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', side_effect=['157.39', '1500.00']):
            result = normalizer.normalize_table([2024], 157.39)
        
        # Check that existing initial balance is marked correctly
        saldo_inicial_rows = result[result['Type'] == 'Saldo inicial']
        assert len(saldo_inicial_rows) == 1
        assert saldo_inicial_rows.iloc[0]['Description'] == 'SALDO ANTERIOR'
        
        # Check amount processing
        assert len(result) == 2
        assert 'Abono' in result['Type'].values
    
    def test_normalize_table_empty_dataframe(self):
        """Test normalization with empty input DataFrame"""
        empty_table = pd.DataFrame(columns=['Date', 'Description', 'MONTO'])
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(empty_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        # Should raise ValueError for empty input
        with pytest.raises(ValueError):
            normalizer.normalize_table([2024], 1000.00)
    
    def test_normalize_table_date_sorting(self):
        """Test that final table is sorted by date"""
        mock_table = pd.DataFrame({
            'Date': ['20-MAR-24', '01-MAR-24', '15-MAR-24'],
            'Description': ['Late Transaction', 'Early Transaction', 'Mid Transaction'],
            'MONTO': ['+500.00', '+1000.00', '+750.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', side_effect=['500.00', '1000.00', '750.00']):
            result = normalizer.normalize_table([2024], 0.00)
        
        # Check that dates are sorted
        dates = result['Date'].tolist()
        assert dates == sorted(dates)
        
        # Check that first date corresponds to early transaction
        first_non_inicial = result[result['Type'] != 'Saldo inicial'].iloc[0]
        assert first_non_inicial['Description'] == 'Early Transaction'


class TestDefaultTableNormalizerWithRealData:
    """Test cases using real CSV data files"""
    
    @pytest.mark.parametrize('get_input_data_from_path', [RECONSTRUCTED_TABLE_FILE], indirect=True)
    def test_normalize_banorte_debit_real_data(self, get_input_data_from_path):
        """Test normalization with real Banorte debit data"""
        table_df, _ = get_input_data_from_path
        
        date_normalizer = DateNormalizer(BANORTE_DEBIT_PROPERTIES)
        amount_normalizer = AmountNormalizer(BANORTE_DEBIT_PROPERTIES)
        normalizer = DefaultTableNormalizer(table_df, BANORTE_DEBIT_PROPERTIES, date_normalizer, amount_normalizer)
        
        result = normalizer.normalize_table([2024], 157.39)
        
        # Verify basic structure
        expected_columns = ['Date', 'Description', 'Amount', 'Type']
        assert all(col in result.columns for col in expected_columns)
        
        # Verify date conversion
        assert result['Date'].dtype == 'datetime64[ns]'
        
        # Verify types are assigned
        valid_types = ['Abono', 'Cargo', 'Saldo', 'Saldo inicial']
        assert all(t in valid_types for t in result['Type'].dropna())
        
        # Verify initial balance handling
        assert 'Saldo inicial' in result['Type'].values
    
    @pytest.mark.parametrize('get_input_data_from_path', [BBVA_RECONSTRUCTED_TABLE_FILE], indirect=True)
    def test_normalize_bbva_debit_real_data(self, get_input_data_from_path):
        """Test normalization with real BBVA debit data"""
        table_df, _ = get_input_data_from_path
        
        date_normalizer = DateNormalizer(BBVA_DEBIT_PROPERTIES)
        amount_normalizer = AmountNormalizer(BBVA_DEBIT_PROPERTIES)
        normalizer = DefaultTableNormalizer(table_df, BBVA_DEBIT_PROPERTIES, date_normalizer, amount_normalizer)
        
        result = normalizer.normalize_table([2022], 266451.99)
        
        # Verify structure and processing
        assert 'Date' in result.columns
        assert 'Amount' in result.columns
        assert 'Type' in result.columns
        
        # Verify amounts are numeric
        assert pd.api.types.is_numeric_dtype(result['Amount'])
        
        # Should have initial balance
        assert 'Saldo inicial' in result['Type'].values
    
    @pytest.mark.parametrize('get_input_data_from_path', [BANORTE_CREDIT_RECONSTRUCTED_FILE], indirect=True)
    def test_normalize_banorte_credit_real_data(self, get_input_data_from_path):
        """Test normalization with real Banorte credit data"""
        table_df, _ = get_input_data_from_path
        
        date_normalizer = DateNormalizer(BANORTE_CREDIT_PROPERTIES)
        amount_normalizer = AmountNormalizer(BANORTE_CREDIT_PROPERTIES)
        normalizer = DefaultTableNormalizer(table_df, BANORTE_CREDIT_PROPERTIES, date_normalizer, amount_normalizer)
        
        result = normalizer.normalize_table([2022], 0.00)
        
        # Credit statements should not have initial balance added
        assert 'Saldo inicial' not in result['Type'].values or len(result[result['Type'] == 'Saldo inicial']) == 0
        
        # Verify basic structure
        assert 'Date' in result.columns
        assert 'Amount' in result.columns
        assert 'Type' in result.columns


class TestDefaultTableNormalizerEdgeCases:
    """Test cases for edge cases and error handling"""
    
    def test_normalize_table_invalid_dates(self):
        """Test handling of invalid dates in normalization"""
        mock_table = pd.DataFrame({
            'Date': ['invalid-date', '15-MAR-24', 'another-invalid'],
            'Description': ['Invalid 1', 'Valid', 'Invalid 2'],
            'MONTO': ['+500.00', '+1000.00', '+750.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', side_effect=['500.00', '1000.00', '750.00']):
            result = normalizer.normalize_table([2024], 0.00)
        
        # Should handle invalid dates gracefully
        assert len(result) >= 1  # At least the valid date + initial balance
        
        # Valid date should be processed correctly
        valid_rows = result[result['Description'] == 'Valid']
        assert len(valid_rows) == 1
        assert pd.notna(valid_rows.iloc[0]['Date'])
    
    def test_normalize_table_invalid_amounts(self):
        """Test handling of invalid amounts in normalization"""
        mock_table = pd.DataFrame({
            'Date': ['15-MAR-24', '20-MAR-24'],
            'Description': ['Valid Amount', 'Invalid Amount'],
            'DEPOSITO': ['1500.00', 'invalid'],
            'RETIRO': ['', ''],
            'SALDO': ['2000.00', '2000.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_MULTI_AMOUNT, date_normalizer, amount_normalizer)
        
        def mock_clean_amount(value):
            if value == 'invalid':
                raise ValueError("Invalid amount")
            return value
        
        with patch('utils.clean_amount', side_effect=mock_clean_amount):
            result = normalizer.normalize_table([2024], 500.00)
        
        # Should handle invalid amounts gracefully
        assert len(result) >= 2  # At least one valid transaction + initial balance
        
        # Check that valid amounts are processed
        valid_amounts = result[result['Description'] == 'Valid Amount']
        assert len(valid_amounts) == 1
        assert valid_amounts.iloc[0]['Amount'] == 1500.00
    
    def test_normalize_table_missing_columns(self):
        """Test behavior with missing expected columns"""
        mock_table = pd.DataFrame({
            'Date': ['15-MAR-24'],
            'Description': ['Test'],
            # Missing MONTO column
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        # Should raise KeyError when expected columns are missing
        with pytest.raises(KeyError):
            normalizer.normalize_table([2024], 0.00)
    
    def test_normalize_table_malformed_properties(self):
        """Test behavior with malformed statement properties"""
        mock_table = pd.DataFrame({
            'Date': ['15-MAR-24'],
            'Description': ['Test'],
            'MONTO': ['1000.00']
        })
        
        malformed_properties = {
            # Missing required keys
            'amount_column': ['MONTO']
        }
        
        date_normalizer = DateNormalizer(malformed_properties)
        amount_normalizer = AmountNormalizer(malformed_properties)
        normalizer = DefaultTableNormalizer(mock_table, malformed_properties, date_normalizer, amount_normalizer)
        
        # Should raise KeyError when required properties are missing
        with pytest.raises(KeyError):
            normalizer.normalize_table([2024], 0.00)
    
    def test_normalize_table_zero_initial_balance(self):
        """Test normalization with zero initial balance"""
        mock_table = pd.DataFrame({
            'Date': ['15-MAR-24'],
            'Description': ['Test Transaction'],
            'MONTO': ['+1000.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', return_value='1000.00'):
            result = normalizer.normalize_table([2024], 0.00)
        
        # Should handle zero initial balance correctly
        initial_balance_rows = result[result['Type'] == 'Saldo inicial']
        assert len(initial_balance_rows) == 1
        assert initial_balance_rows.iloc[0]['Amount'] == 0.00
    
    def test_normalize_table_negative_initial_balance(self):
        """Test normalization with negative initial balance"""
        mock_table = pd.DataFrame({
            'Date': ['15-MAR-24'],
            'Description': ['Test Transaction'],
            'MONTO': ['+1000.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_WITH_YEAR)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_WITH_YEAR)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_WITH_YEAR, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', return_value='1000.00'):
            result = normalizer.normalize_table([2024], -500.00)
        
        # Should handle negative initial balance correctly
        initial_balance_rows = result[result['Type'] == 'Saldo inicial']
        assert len(initial_balance_rows) == 1
        assert initial_balance_rows.iloc[0]['Amount'] == -500.00


class TestDefaultTableNormalizerIntegration:
    """Test cases for integration scenarios"""
    
    def test_complete_normalization_workflow(self):
        """Test complete normalization workflow with all components"""
        mock_table = pd.DataFrame({
            'Date': ['01-FEB-2024', '15-FEB-2024', '28-FEB-2024'],
            'Description': ['SALDO ANTERIOR', 'Deposito Efectivo', 'Transferencia SPEI'],
            'DEPOSITO': ['', '5000.00', ''],
            'RETIRO': ['', '', '1200.00'],
            'SALDO': ['157.39', '5157.39', '3957.39']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_MULTI_AMOUNT, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', side_effect=['157.39', '5000.00', '1200.00']):
            result = normalizer.normalize_table([2024], 157.39)
        
        # Verify complete workflow
        assert len(result) == 3
        
        # Check date normalization
        expected_dates = [pd.Timestamp('2024-02-01'), pd.Timestamp('2024-02-15'), pd.Timestamp('2024-02-28')]
        actual_dates = sorted(result['Date'].tolist())
        assert actual_dates == expected_dates
        
        # Check amount normalization
        saldo_inicial = result[result['Type'] == 'Saldo inicial'].iloc[0]
        assert saldo_inicial['Amount'] == 157.39
        
        deposito = result[result['Type'] == 'Abono'].iloc[0]
        assert deposito['Amount'] == 5000.00
        
        retiro = result[result['Type'] == 'Cargo'].iloc[0]
        assert retiro['Amount'] == -1200.00
        
        # Check sorting
        assert result['Date'].is_monotonic_increasing
    
    def test_cross_year_period_normalization(self):
        """Test normalization with cross-year period"""
        mock_table = pd.DataFrame({
            'Date': ['15/DIC', '01/ENE', '15/ENE'],
            'Description': ['Dec Transaction', 'Jan Transaction 1', 'Jan Transaction 2'],
            'MONTO': ['+1000.00', '+500.00', '+750.00']
        })
        
        cross_year_properties = TEST_PROPERTIES_WITHOUT_YEAR.copy()
        cross_year_properties['month_pattern'] = {'DIC': '12', 'ENE': '01'}
        cross_year_properties['initial_balance_description'] = None
        
        date_normalizer = DateNormalizer(cross_year_properties)
        amount_normalizer = AmountNormalizer(cross_year_properties)
        normalizer = DefaultTableNormalizer(mock_table, cross_year_properties, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', side_effect=['1000.00', '500.00', '750.00']):
            result = normalizer.normalize_table([2023, 2024], 0.00)
        
        # Check year assignment logic
        dec_row = result[result['Description'] == 'Dec Transaction'].iloc[0]
        jan_row = result[result['Description'] == 'Jan Transaction 1'].iloc[0]
        
        # December should be assigned to first year (2023)
        assert dec_row['Date'].year == 2023
        assert dec_row['Date'].month == 12
        
        # January should be assigned to first year (2023) since month <= 12
        assert jan_row['Date'].year == 2023
        assert jan_row['Date'].month == 1
    
    def test_normalization_with_mixed_transaction_types(self):
        """Test normalization with various transaction types"""
        mock_table = pd.DataFrame({
            'Date': ['01-MAR-2024', '05-MAR-2024', '10-MAR-2024', '15-MAR-2024'],
            'Description': ['SALDO ANTERIOR', 'Deposito', 'Retiro ATM', 'Transferencia'],
            'DEPOSITO': ['', '2000.00', '', '1500.00'],
            'RETIRO': ['', '', '500.00', '800.00'],
            'SALDO': ['1000.00', '3000.00', '2500.00', '2200.00']
        })
        
        date_normalizer = DateNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        amount_normalizer = AmountNormalizer(TEST_PROPERTIES_MULTI_AMOUNT)
        normalizer = DefaultTableNormalizer(mock_table, TEST_PROPERTIES_MULTI_AMOUNT, date_normalizer, amount_normalizer)
        
        with patch('utils.clean_amount', side_effect=['1000.00', '2000.00', '500.00', '1500.00', '800.00']):
            result = normalizer.normalize_table([2024], 1000.00)
        
        # Check transaction type assignment
        types = result['Type'].value_counts()
        
        assert 'Saldo inicial' in types
        assert 'Abono' in types
        assert 'Cargo' in types
        
        # Verify specific transactions
        deposito_row = result[result['Description'] == 'Deposito'].iloc[0]
        assert deposito_row['Type'] == 'Abono'
        assert deposito_row['Amount'] == 2000.00
        
        retiro_row = result[result['Description'] == 'Retiro ATM'].iloc[0]
        assert retiro_row['Type'] == 'Cargo'
        assert retiro_row['Amount'] == -500.00
        
        # Transaction with both deposit and withdrawal (conflict resolution)
        transferencia_row = result[result['Description'] == 'Transferencia'].iloc[0]
        assert transferencia_row['Type'] == 'Abono'  # 1500 > 800, so Abono
        assert transferencia_row['Amount'] == 700.00  # 1500 - 800
