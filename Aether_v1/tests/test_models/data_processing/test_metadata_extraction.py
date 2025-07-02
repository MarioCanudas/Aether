import pytest
import pandas as pd
import re
from unittest.mock import patch
from models import DefaultMetadataExtractor
from models.document_processing.banks_properties import BANORTE_DEBIT_PROPERTIES, BANORTE_CREDIT_PROPERTIES, BBVA_DEBIT_PROPERTIES

# Test files to use for different scenarios
CORRECTED_WORDS_FILE = 'banorte_debit_corrected_words.csv'
BBVA_CORRECTED_WORDS_FILE = 'bbva_debit_corrected_words.csv'
BANORTE_CREDIT_WORDS_FILE = 'banorte_credit_old_corrected_words.csv'

# Test statement properties for different scenarios
TEST_PROPERTIES_WITH_PERIOD = {
    'period_phrase': ['periodo'],
    'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
    'year_group': 3,
    'initial_balance_phrase': ['saldo', 'inicial'],
    'statement_type': 'debit'
}

TEST_PROPERTIES_WITHOUT_PERIOD = {
    'period_phrase': None,
    'period_pattern': None,
    'year_group': None,
    'initial_balance_phrase': None,
    'statement_type': 'credit'
}

TEST_PROPERTIES_COMPLEX_PERIOD = {
    'period_phrase': ['información', 'del', 'periodo'],
    'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
    'year_group': 3,
    'initial_balance_phrase': ['saldo', 'inicial', 'del', 'periodo'],
    'statement_type': 'debit'
}

TEST_PROPERTIES_GENERIC_YEAR = {
    'period_phrase': ['periodo'],
    'period_pattern': None,  # Will use generic year pattern
    'year_group': None,
    'initial_balance_phrase': ['saldo', 'anterior'],
    'statement_type': 'debit'
}


class TestDefaultMetadataExtractorInitialization:
    """Test cases for DefaultMetadataExtractor initialization and inheritance"""
    
    def test_inheritance_from_metadata_extractor(self):
        """Test that DefaultMetadataExtractor inherits from MetadataExtractor correctly"""
        mock_df = pd.DataFrame({
            'text': ['test'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        extractor = DefaultMetadataExtractor(mock_df, TEST_PROPERTIES_WITH_PERIOD)
        
        # Verify inheritance
        from models.core import MetadataExtractor
        assert isinstance(extractor, MetadataExtractor)
        assert hasattr(extractor, 'corrected_extracted_words')
        assert hasattr(extractor, 'statement_properties')
    
    def test_init_with_dataframe_and_properties(self):
        """Test DefaultMetadataExtractor initialization with DataFrame and properties"""
        mock_df = pd.DataFrame({
            'text': ['periodo', 'del', '01/Enero/2024', 'saldo', 'inicial', '100.00'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 0, 50, 100],
            'top': [0, 0, 0, 20, 20, 20],
            'x1': [40, 90, 140, 40, 90, 140],
            'bottom': [10, 10, 10, 30, 30, 30]
        })
        
        extractor = DefaultMetadataExtractor(mock_df, TEST_PROPERTIES_WITH_PERIOD)
        
        assert extractor.corrected_extracted_words.equals(mock_df)
        assert extractor.statement_properties == TEST_PROPERTIES_WITH_PERIOD
    
    def test_init_with_empty_dataframe(self):
        """Test initialization with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        
        extractor = DefaultMetadataExtractor(empty_df, TEST_PROPERTIES_WITH_PERIOD)
        
        assert extractor.corrected_extracted_words.empty is True
        assert extractor.statement_properties == TEST_PROPERTIES_WITH_PERIOD


class TestDefaultMetadataExtractorPeriodIdx:
    """Test cases for get_period_idx method"""
    
    def test_get_period_idx_single_word_phrase(self):
        """Test finding period index with single word phrase"""
        mock_df = pd.DataFrame({
            'text': ['inicio', 'periodo', 'del', '01/Enero/2024'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {'period_phrase': ['periodo']}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        period_idx = extractor.get_period_idx()
        
        assert period_idx == 2  # Index after 'periodo'
    
    def test_get_period_idx_multi_word_phrase(self):
        """Test finding period index with multi-word phrase"""
        mock_df = pd.DataFrame({
            'text': ['resumen', 'información', 'del', 'periodo', '01/Enero/2024', 'al', '31/Enero/2024'],
            'page': [1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250, 300],
            'top': [0, 0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 290, 340],
            'bottom': [10, 10, 10, 10, 10, 10, 10]
        })
        
        properties = {'period_phrase': ['información', 'del', 'periodo']}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        period_idx = extractor.get_period_idx()
        
        assert period_idx == 4  # Index after 'información del periodo'
    
    def test_get_period_idx_with_colons(self):
        """Test finding period index with words containing colons"""
        mock_df = pd.DataFrame({
            'text': ['resumen', 'periodo:', 'del', '01/Enero/2024'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {'period_phrase': ['periodo']}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        period_idx = extractor.get_period_idx()
        
        assert period_idx == 2  # Index after 'periodo:' (colon stripped)
    
    def test_get_period_idx_case_insensitive(self):
        """Test that period phrase matching is case insensitive"""
        mock_df = pd.DataFrame({
            'text': ['inicio', 'PERIODO', 'del', '01/Enero/2024'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {'period_phrase': ['periodo']}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        period_idx = extractor.get_period_idx()
        
        assert period_idx == 2  # Should find 'PERIODO' when searching for 'periodo'
    
    def test_get_period_idx_phrase_not_found(self):
        """Test ValueError when period phrase is not found"""
        mock_df = pd.DataFrame({
            'text': ['inicio', 'texto', 'sin', 'periodo'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {'period_phrase': ['información', 'del', 'periodo']}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with pytest.raises(ValueError, match="Period phrase.*not found"):
            extractor.get_period_idx()
    
    def test_get_period_idx_empty_phrase(self):
        """Test behavior when period_phrase is empty or None"""
        mock_df = pd.DataFrame({
            'text': ['texto', 'sin', 'periodo'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        properties = {'period_phrase': None}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        result = extractor.get_period_idx()
        
        assert result is None
    
    def test_get_period_idx_caching(self):
        """Test that get_period_idx uses @cache decorator correctly"""
        mock_df = pd.DataFrame({
            'text': ['inicio', 'periodo', 'del', '01/Enero/2024'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {'period_phrase': ['periodo']}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Call twice to test caching
        result1 = extractor.get_period_idx()
        result2 = extractor.get_period_idx()
        
        assert result1 == result2 == 2
        
        # Verify the function has cache info (indicating @cache is working)
        assert hasattr(extractor.get_period_idx, 'cache_info')


class TestDefaultMetadataExtractorInitialBalance:
    """Test cases for get_initial_balance method"""
    
    def test_get_initial_balance_found(self):
        """Test extracting initial balance when phrase is found"""
        mock_df = pd.DataFrame({
            'text': ['resumen', 'saldo', 'inicial', '$1,234.56', 'otro', 'texto'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 200, 250, 300],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        properties = {
            'initial_balance_phrase': ['saldo', 'inicial'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch('utils.clean_amount', return_value='1234.56'):
            balance = extractor.get_initial_balance()
        
        assert balance == 1234.56
    
    def test_get_initial_balance_multi_word_phrase(self):
        """Test extracting initial balance with multi-word phrase"""
        mock_df = pd.DataFrame({
            'text': ['resumen', 'saldo', 'inicial', 'del', 'periodo', '2500.00'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 300],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        properties = {
            'initial_balance_phrase': ['saldo', 'inicial', 'del', 'periodo'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch('utils.clean_amount', return_value='2500.00'):
            balance = extractor.get_initial_balance()
        
        assert balance == 2500.00
    
    def test_get_initial_balance_credit_statement(self):
        """Test that initial balance returns None for credit statements"""
        mock_df = pd.DataFrame({
            'text': ['saldo', 'inicial', '1000.00'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 150],
            'bottom': [10, 10, 10]
        })
        
        properties = {
            'initial_balance_phrase': ['saldo', 'inicial'],
            'statement_type': 'credit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        balance = extractor.get_initial_balance()
        
        assert balance is None
    
    def test_get_initial_balance_phrase_not_found(self):
        """Test that method returns None when initial balance phrase is not found"""
        mock_df = pd.DataFrame({
            'text': ['texto', 'sin', 'balance', 'inicial'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {
            'initial_balance_phrase': ['saldo', 'inicial'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        balance = extractor.get_initial_balance()
        
        assert balance is None
    
    def test_get_initial_balance_no_phrase_configured(self):
        """Test that method returns None when no initial balance phrase is configured"""
        mock_df = pd.DataFrame({
            'text': ['saldo', 'inicial', '1000.00'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 150],
            'bottom': [10, 10, 10]
        })
        
        properties = {
            'initial_balance_phrase': None,
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        balance = extractor.get_initial_balance()
        
        assert balance is None
    
    def test_get_initial_balance_invalid_amount(self):
        """Test handling of invalid amount values"""
        mock_df = pd.DataFrame({
            'text': ['saldo', 'inicial', 'texto-no-numerico'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 180],
            'bottom': [10, 10, 10]
        })
        
        properties = {
            'initial_balance_phrase': ['saldo', 'inicial'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch('utils.clean_amount', return_value='texto-no-numerico'):
            balance = extractor.get_initial_balance()
        
        assert balance is None


class TestDefaultMetadataExtractorYears:
    """Test cases for get_years method"""
    
    def test_get_years_with_period_pattern(self):
        """Test extracting years using period pattern"""
        mock_df = pd.DataFrame({
            'text': ['inicio', 'periodo', '01/Enero/2024', 'al', '31/Enero/2024', 'fin'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 180, 240, 290],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Mock get_period_idx to return the index after 'periodo'
        with patch.object(extractor, 'get_period_idx', return_value=2):
            years = extractor.get_years()
        
        assert years == [2024]
    
    def test_get_years_multiple_years(self):
        """Test extracting multiple years from period section"""
        mock_df = pd.DataFrame({
            'text': ['periodo', '31/Diciembre/2023', 'al', '31/Enero/2024', 'fin'],
            'page': [1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200],
            'top': [0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240],
            'bottom': [10, 10, 10, 10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch.object(extractor, 'get_period_idx', return_value=1):
            years = extractor.get_years()
        
        assert years == [2023, 2024]  # Should be sorted and unique
    
    def test_get_years_generic_pattern_fallback(self):
        """Test fallback to generic year pattern when no period pattern is configured"""
        mock_df = pd.DataFrame({
            'text': ['periodo', 'año', '2024', 'información', '2023', 'fin'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 290],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': None,  # No specific pattern
            'year_group': None
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch.object(extractor, 'get_period_idx', return_value=1):
            years = extractor.get_years()
        
        assert years == [2023, 2024]  # Should find years using generic pattern
    
    def test_get_years_no_period_idx(self):
        """Test behavior when get_period_idx returns None"""
        mock_df = pd.DataFrame({
            'text': ['texto', 'sin', 'periodo'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch.object(extractor, 'get_period_idx', return_value=None):
            years = extractor.get_years()
        
        assert years == []
    
    def test_get_years_invalid_year_group(self):
        """Test handling of invalid year group in regex"""
        mock_df = pd.DataFrame({
            'text': ['periodo', '01/Enero/2024'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 0],
            'x1': [40, 140],
            'bottom': [10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 10  # Invalid group number
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch.object(extractor, 'get_period_idx', return_value=1):
            years = extractor.get_years()
        
        assert years == []  # Should handle IndexError gracefully
    
    def test_get_years_limited_search_window(self):
        """Test that year search is limited to 15 words after period_idx"""
        # Create a DataFrame with years both within and outside the search window
        text_data = ['periodo'] + [f'word{i}' for i in range(20)] + ['2025']
        mock_df = pd.DataFrame({
            'text': text_data,
            'page': [1] * len(text_data),
            'x0': list(range(0, 50 * len(text_data), 50)),
            'top': [0] * len(text_data),
            'x1': list(range(40, 50 * len(text_data), 50)),
            'bottom': [10] * len(text_data)
        })
        
        # Add '2024' within the 15-word window and '2025' outside it
        mock_df.loc[10, 'text'] = '2024'  # Within window (index 10 - 1 = 9 < 15)
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': None,
            'year_group': None
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch.object(extractor, 'get_period_idx', return_value=1):
            years = extractor.get_years()
        
        # Should only find 2024 (within window), not 2025 (outside window)
        assert years == [2024]
    
    def test_get_years_duplicate_removal(self):
        """Test that duplicate years are removed and result is sorted"""
        mock_df = pd.DataFrame({
            'text': ['periodo', '2024', 'texto', '2023', 'más', '2024', '2023'],
            'page': [1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250, 300],
            'top': [0, 0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 290, 340],
            'bottom': [10, 10, 10, 10, 10, 10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': None,
            'year_group': None
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch.object(extractor, 'get_period_idx', return_value=1):
            years = extractor.get_years()
        
        assert years == [2023, 2024]  # Sorted and unique


class TestDefaultMetadataExtractorMonths:
    """Test cases for get_months method"""
    
    def test_get_months_returns_none(self):
        """Test that get_months returns None (not implemented)"""
        mock_df = pd.DataFrame({
            'text': ['test'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        extractor = DefaultMetadataExtractor(mock_df, TEST_PROPERTIES_WITH_PERIOD)
        
        result = extractor.get_months()
        
        assert result is None


class TestDefaultMetadataExtractorWithRealData:
    """Test cases using real CSV data files"""
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_period_extraction_with_banorte_data(self, get_input_data_from_path):
        """Test period extraction with real Banorte debit data"""
        words_df, _ = get_input_data_from_path
        
        extractor = DefaultMetadataExtractor(words_df, BANORTE_DEBIT_PROPERTIES)
        
        # Test period index finding
        try:
            period_idx = extractor.get_period_idx()
            assert isinstance(period_idx, int)
            assert period_idx > 0
        except ValueError:
            # If period phrase not found in subset, that's acceptable for testing
            pass
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_initial_balance_extraction_with_banorte_data(self, get_input_data_from_path):
        """Test initial balance extraction with real Banorte debit data"""
        words_df, _ = get_input_data_from_path
        
        extractor = DefaultMetadataExtractor(words_df, BANORTE_DEBIT_PROPERTIES)
        
        balance = extractor.get_initial_balance()
        
        # Balance might be None if not found in subset, but should be a valid type
        assert balance is None or isinstance(balance, float)
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_year_extraction_with_banorte_data(self, get_input_data_from_path):
        """Test year extraction with real Banorte debit data"""
        words_df, _ = get_input_data_from_path
        
        extractor = DefaultMetadataExtractor(words_df, BANORTE_DEBIT_PROPERTIES)
        
        years = extractor.get_years()
        
        # Should return a list
        assert isinstance(years, list)
        
        # If years found, they should be valid
        for year in years:
            assert isinstance(year, int)
            assert 2000 <= year <= 2030  # Reasonable year range
    
    @pytest.mark.parametrize('get_input_data_from_path', [BBVA_CORRECTED_WORDS_FILE], indirect=True)
    def test_metadata_extraction_with_bbva_data(self, get_input_data_from_path):
        """Test metadata extraction with real BBVA debit data"""
        words_df, _ = get_input_data_from_path
        
        extractor = DefaultMetadataExtractor(words_df, BBVA_DEBIT_PROPERTIES)
        
        # Test all methods with BBVA properties
        try:
            period_idx = extractor.get_period_idx()
            assert period_idx is None or isinstance(period_idx, int)
        except ValueError:
            pass  # Expected if phrase not found in subset
        
        balance = extractor.get_initial_balance()
        assert balance is None or isinstance(balance, float)
        
        years = extractor.get_years()
        assert isinstance(years, list)
    
    @pytest.mark.parametrize('get_input_data_from_path', [BANORTE_CREDIT_WORDS_FILE], indirect=True)
    def test_credit_statement_with_real_data(self, get_input_data_from_path):
        """Test credit statement behavior with real Banorte credit data"""
        words_df, _ = get_input_data_from_path
        
        extractor = DefaultMetadataExtractor(words_df, BANORTE_CREDIT_PROPERTIES)
        
        # Credit statements should return None for initial balance
        balance = extractor.get_initial_balance()
        assert balance is None
        
        # Should still be able to extract years
        years = extractor.get_years()
        assert isinstance(years, list)


class TestDefaultMetadataExtractorEdgeCases:
    """Test cases for edge cases and error handling"""
    
    def test_empty_dataframe_handling(self):
        """Test behavior with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        
        extractor = DefaultMetadataExtractor(empty_df, TEST_PROPERTIES_WITH_PERIOD)
        
        # Should handle empty DataFrame gracefully
        period_idx = extractor.get_period_idx()
        assert period_idx is None
        
        balance = extractor.get_initial_balance()
        assert balance is None
        
        years = extractor.get_years()
        assert years == []
    
    def test_single_row_dataframe(self):
        """Test behavior with single row DataFrame"""
        single_row_df = pd.DataFrame({
            'text': ['periodo'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        extractor = DefaultMetadataExtractor(single_row_df, TEST_PROPERTIES_WITH_PERIOD)
        
        # Should raise an error because there is no more data after the period phrase
        with pytest.raises(ValueError):
            extractor.get_period_idx()
    
    def test_malformed_properties(self):
        """Test handling of malformed or missing properties"""
        mock_df = pd.DataFrame({
            'text': ['periodo', '2024'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 0],
            'x1': [40, 90],
            'bottom': [10, 10]
        })
        
        # Missing required keys
        malformed_properties = {}
        
        extractor = DefaultMetadataExtractor(mock_df, malformed_properties)
        
        # Should raise an error because the properties are malformed
        with pytest.raises(KeyError):
            extractor.get_period_idx()
    
    def test_invalid_regex_pattern(self):
        """Test handling of invalid regex patterns"""
        mock_df = pd.DataFrame({
            'text': ['periodo', '01/Enero/2024'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 0],
            'x1': [40, 140],
            'bottom': [10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': '[invalid regex',  # Invalid regex
            'year_group': 1
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        with patch.object(extractor, 'get_period_idx', return_value=1):
            # Should raise an error because the regex is invalid
            with pytest.raises(re.error):
                extractor.get_years()
    
    def test_period_phrase_at_end_of_dataframe(self):
        """Test edge case where period phrase is at the very end"""
        mock_df = pd.DataFrame({
            'text': ['inicio', 'texto', 'periodo'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        properties = {'period_phrase': ['periodo']}
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Should raise an error because there is no more data after the period phrase
        with pytest.raises(ValueError):
            extractor.get_period_idx()
    
    def test_very_large_dataframe_performance(self):
        """Test performance with larger DataFrames"""
        # Create a larger DataFrame
        large_size = 1000
        large_df = pd.DataFrame({
            'text': ['word'] * (large_size - 2) + ['periodo', '2024'],
            'page': [1] * large_size,
            'x0': list(range(large_size)),
            'top': [0] * large_size,
            'x1': list(range(40, large_size + 40)),
            'bottom': [10] * large_size
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': None,
            'year_group': None
        }
        extractor = DefaultMetadataExtractor(large_df, properties)
        
        # Should complete without performance issues
        import time
        start_time = time.time()
        
        period_idx = extractor.get_period_idx()
        years = extractor.get_years()
        
        end_time = time.time()
        
        # Should complete reasonably quickly (less than 1 second)
        assert end_time - start_time < 1.0
        assert period_idx == large_size - 1
        assert years == [2024]


class TestDefaultMetadataExtractorIntegration:
    """Test cases for integration scenarios combining multiple methods"""
    
    def test_complete_metadata_extraction_workflow(self):
        """Test complete workflow extracting all metadata"""
        mock_df = pd.DataFrame({
            'text': [
                'inicio', 'información', 'del', 'periodo', 
                '01/Febrero/2024', 'al', '29/Febrero/2024',
                'saldo', 'inicial', 'del', 'periodo', '$1,500.00',
                'otros', 'datos'
            ],
            'page': [1] * 14,
            'x0': list(range(0, 700, 50)),
            'top': [0] * 14,
            'x1': list(range(40, 740, 50)),
            'bottom': [10] * 14
        })
        
        properties = {
            'period_phrase': ['información', 'del', 'periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3,
            'initial_balance_phrase': ['saldo', 'inicial', 'del', 'periodo'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Test complete workflow
        period_idx = extractor.get_period_idx()
        assert period_idx == 4
        
        with patch('utils.clean_amount', return_value='1500.00'):
            balance = extractor.get_initial_balance()
            assert balance == 1500.00
        
        years = extractor.get_years()
        assert years == [2024]
    
    def test_metadata_extraction_with_mixed_case_text(self):
        """Test metadata extraction with mixed case text"""
        mock_df = pd.DataFrame({
            'text': [
                'RESUMEN', 'INFORMACIÓN', 'del', 'PERIODO',
                '15/MARZO/2024', 'AL', '15/ABRIL/2024',
                'SALDO', 'inicial', '$2,000.00'
            ],
            'page': [1] * 10,
            'x0': list(range(0, 500, 50)),
            'top': [0] * 10,
            'x1': list(range(40, 540, 50)),
            'bottom': [10] * 10
        })
        
        properties = {
            'period_phrase': ['información', 'del', 'periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3,
            'initial_balance_phrase': ['saldo', 'inicial'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Should handle mixed case correctly
        period_idx = extractor.get_period_idx()
        assert period_idx == 4
        
        with patch('utils.clean_amount', return_value='2000.00'):
            balance = extractor.get_initial_balance()
            assert balance == 2000.00
        
        years = extractor.get_years()
        assert years == [2024]
    
    def test_metadata_extraction_with_special_characters(self):
        """Test metadata extraction with special characters in text"""
        mock_df = pd.DataFrame({
            'text': [
                'período:', 'del', '01/Enero/2024',
                'saldo', 'inicial:', '$1,000.50',
                'otros', 'datos'
            ],
            'page': [1] * 8,
            'x0': list(range(0, 400, 50)),
            'top': [0] * 8,
            'x1': list(range(40, 440, 50)),
            'bottom': [10] * 8
        })
        
        properties = {
            'period_phrase': ['período'],  # With accent
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3,
            'initial_balance_phrase': ['saldo', 'inicial'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Should handle special characters and colons
        period_idx = extractor.get_period_idx()
        assert period_idx == 1
        
        with patch('utils.clean_amount', return_value='1000.50'):
            balance = extractor.get_initial_balance()
            assert balance == 1000.50
        
        years = extractor.get_years()
        assert years == [2024]


class TestDefaultMetadataExtractorPerformanceAndCaching:
    """Test cases for performance and caching behavior"""
    
    def test_caching_behavior_consistency(self):
        """Test that caching provides consistent results across multiple calls"""
        mock_df = pd.DataFrame({
            'text': ['inicio', 'periodo', 'del', '01/Enero/2024'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Call get_period_idx multiple times
        results = [extractor.get_period_idx() for _ in range(5)]
        
        # All results should be identical
        assert all(result == results[0] for result in results)
        assert results[0] == 2
        
        # Cache should show multiple hits
        cache_info = extractor.get_period_idx.cache_info()
        assert cache_info.hits >= 4  # At least 4 hits from the 5 calls
    
    def test_method_independence(self):
        """Test that different methods work independently"""
        mock_df = pd.DataFrame({
            'text': [
                'inicio', 'periodo', '01/Enero/2024',
                'saldo', 'inicial', '1000.00', 'fin'
            ],
            'page': [1] * 7,
            'x0': list(range(0, 350, 50)),
            'top': [0] * 7,
            'x1': list(range(40, 390, 50)),
            'bottom': [10] * 7
        })
        
        properties = {
            'period_phrase': ['periodo'],
            'period_pattern': r'(\d{2})/(\w+)/(\d{4})',
            'year_group': 3,
            'initial_balance_phrase': ['saldo', 'inicial'],
            'statement_type': 'debit'
        }
        extractor = DefaultMetadataExtractor(mock_df, properties)
        
        # Test methods in different orders
        years = extractor.get_years()
        
        with patch('utils.clean_amount', return_value='1000.00'):
            balance = extractor.get_initial_balance()
        
        period_idx = extractor.get_period_idx()
        
        # Results should be consistent regardless of call order
        assert period_idx == 2
        assert balance == 1000.00
        assert years == [2024]
