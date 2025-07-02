import pytest
import pandas as pd
from unittest.mock import patch
from models import DefaultBoundaryDetector
from models.document_processing.banks_properties import BANORTE_DEBIT_PROPERTIES

# Test files to use for different scenarios
CORRECTED_WORDS_FILE = 'banorte_debit_corrected_words.csv'

# Test statement properties for different scenarios
TEST_STATEMENT_PROPERTIES_BASIC = {
    'start_phrase': ['fecha', 'descripción', 'cargos'],
    'end_phrase': ['total', 'cargos'],
    'bank': 'banorte',
    'statement_type': 'debit'
}

TEST_STATEMENT_PROPERTIES_COMPLEX = {
    'start_phrase': ['movimientos', 'del', 'periodo'],
    'end_phrase': ['saldo', 'final'],
    'bank': 'bbva',
    'statement_type': 'credit'
}

TEST_STATEMENT_PROPERTIES_MISSING = {
    'start_phrase': ['phrase', 'not', 'found'],
    'end_phrase': ['end', 'not', 'found'],
    'bank': 'test_bank',
    'statement_type': 'debit'
}


class TestDefaultBoundaryDetectorInitialization:
    """Test cases for DefaultBoundaryDetector initialization"""
    
    def test_init_with_dataframe_and_properties(self):
        """Test DefaultBoundaryDetector initialization with DataFrame and properties"""
        mock_df = pd.DataFrame({
            'text': ['test', 'data', 'here'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        assert detector.corrected_extracted_words.equals(mock_df)
        assert detector.statement_properties == TEST_STATEMENT_PROPERTIES_BASIC
        assert hasattr(detector, 'corrected_extracted_words')
        assert hasattr(detector, 'statement_properties')
        
    def test_inheritance_from_table_boundary_detector(self):
        """Test that DefaultBoundaryDetector inherits from TableBoundaryDetector"""
        mock_df = pd.DataFrame({'text': ['test'], 'page': [1], 'x0': [0], 'top': [0], 'x1': [40], 'bottom': [10]})
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        from models.core import TableBoundaryDetector
        assert isinstance(detector, TableBoundaryDetector)


class TestDefaultBoundaryDetectorStartIdx:
    """Test cases for get_start_idx functionality"""
    
    def test_get_start_idx_phrase_found(self):
        """Test get_start_idx when start phrase is found"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'fecha', 'descripción', 'cargos', 'data', 'after'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 290],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch('models.table_processing.boundary_detection.search_phrase_in_df', return_value=1):
            result = detector.get_start_idx()
            # Should return index after the phrase (1 + len(phrase) = 1 + 3 = 4)
            assert result == 4
    
    def test_get_start_idx_phrase_not_found(self):
        """Test get_start_idx when start phrase is not found"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'some', 'other', 'data'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 190],
            'bottom': [10, 10, 10, 10]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch('models.table_processing.boundary_detection.search_phrase_in_df', side_effect=Exception()):
            result = detector.get_start_idx()
            assert result is None
    
    def test_get_start_idx_caching(self):
        """Test that get_start_idx method caches results"""
        mock_df = pd.DataFrame({
            'text': ['fecha', 'descripción', 'cargos', 'data'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 190],
            'bottom': [10, 10, 10, 10]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch('models.table_processing.boundary_detection.search_phrase_in_df', return_value=0) as mock_search:
            # First call
            result1 = detector.get_start_idx()
            # Second call
            result2 = detector.get_start_idx()
            
            assert result1 == result2 == 3  # 0 + len(['fecha', 'descripción', 'cargos'])
            # Should only be called once due to caching
            mock_search.assert_called_once()


class TestDefaultBoundaryDetectorEndIdx:
    """Test cases for get_end_idx functionality"""
    
    def test_get_end_idx_phrase_found_with_valid_start(self):
        """Test get_end_idx when end phrase is found and start idx is valid"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'fecha', 'descripción', 'cargos', 'data', 'total', 'cargos', 'end'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250, 300, 350],
            'top': [0, 0, 0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 290, 340, 390],
            'bottom': [10, 10, 10, 10, 10, 10, 10, 10]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=4):
            with patch('models.table_processing.boundary_detection.search_phrase_in_df', return_value=5):
                result = detector.get_end_idx()
                # Should return index after the end phrase (5 + len(['total', 'cargos']) = 5 + 2 = 7)
                assert result == 7
    
    def test_get_end_idx_with_invalid_start(self):
        """Test get_end_idx when start idx is None"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'data', 'total', 'cargos'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 190],
            'bottom': [10, 10, 10, 10]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=None):
            result = detector.get_end_idx()
            assert result is None
    
    def test_get_end_idx_caching(self):
        """Test that get_end_idx method caches results"""
        mock_df = pd.DataFrame({
            'text': ['fecha', 'descripción', 'cargos', 'data', 'total', 'cargos'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 290],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=3):
            with patch('models.table_processing.boundary_detection.search_phrase_in_df', return_value=4) as mock_search:
                # First call
                result1 = detector.get_end_idx()
                # Second call
                result2 = detector.get_end_idx()
                
                assert result1 == result2 == 6  # 4 + len(['total', 'cargos'])
                # Should only be called once due to caching
                mock_search.assert_called_once()


class TestDefaultBoundaryDetectorFilteredWords:
    """Test cases for get_filtered_table_words functionality"""
    
    def test_get_filtered_table_words_valid_indices(self):
        """Test get_filtered_table_words with valid start and end indices"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'start', 'table', 'data', 'more', 'end', 'outro'],
            'page': [1, 1, 1, 1, 2, 2, 2],
            'x0': [0, 50, 100, 150, 200, 250, 300],
            'top': [0, 10, 20, 30, 40, 50, 60],
            'x1': [40, 90, 140, 190, 240, 290, 340],
            'bottom': [10, 20, 30, 40, 50, 60, 70]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=2):
            with patch.object(detector, 'get_end_idx', return_value=5):
                result = detector.get_filtered_table_words()
                
                # Should include rows 2, 3, 4 (indices 2 to 4 inclusive)
                assert len(result) == 3
                assert list(result['text']) == ['table', 'data', 'more']
                # Should be sorted by page and top
                assert result.iloc[0]['page'] == 1
                assert result.iloc[-1]['page'] == 2
    
    def test_get_filtered_table_words_invalid_start_idx(self):
        """Test get_filtered_table_words when start idx is None"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'data'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 10],
            'x1': [40, 90],
            'bottom': [10, 20]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=None):
            # End idx should be None because start idx is None
            result = detector.get_filtered_table_words()
            
            # Should return empty DataFrame with same columns
            assert result.empty is True
    
    def test_get_filtered_table_words_invalid_end_idx(self):
        """Test get_filtered_table_words when end idx is None"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'data'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 10],
            'x1': [40, 90],
            'bottom': [10, 20]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=1):
            with patch.object(detector, 'get_end_idx', return_value=None):
                result = detector.get_filtered_table_words()
                
                # Should return empty DataFrame with same columns
                assert result.empty is True
    
    def test_get_filtered_table_words_start_after_end(self):
        """Test get_filtered_table_words when start idx is after end idx"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'data'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 10],
            'x1': [40, 90],
            'bottom': [10, 20]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=5):
            with patch.object(detector, 'get_end_idx', return_value=2):
                result = detector.get_filtered_table_words()
                
                # Should return empty DataFrame with same columns
                assert result.empty is True
    
    def test_get_filtered_table_words_caching(self):
        """Test that get_filtered_table_words method caches results"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'table', 'data', 'end'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 10, 20, 30],
            'x1': [40, 90, 140, 190],
            'bottom': [10, 20, 30, 40]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch.object(detector, 'get_start_idx', return_value=1) as mock_start:
            with patch.object(detector, 'get_end_idx', return_value=3) as mock_end:
                # First call
                result1 = detector.get_filtered_table_words()
                # Second call
                result2 = detector.get_filtered_table_words()
                
                # Results should be the same
                pd.testing.assert_frame_equal(result1, result2)
                # Methods should only be called once due to caching
                mock_start.assert_called_once()
                mock_end.assert_called_once()


class TestDefaultBoundaryDetectorWithRealData:
    """Test cases using real CSV data files"""
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_with_real_corrected_words_data(self, get_input_data_from_path):
        """Test DefaultBoundaryDetector with real corrected words CSV data"""
        words_df, file_path = get_input_data_from_path
        
        detector = DefaultBoundaryDetector(words_df, BANORTE_DEBIT_PROPERTIES)
        
        # Test initialization
        assert detector.corrected_extracted_words.equals(words_df)
        assert detector.statement_properties == BANORTE_DEBIT_PROPERTIES
        
        # Test that all methods can be called without errors
        start_idx = detector.get_start_idx()
        end_idx = detector.get_end_idx()
        filtered_words = detector.get_filtered_table_words()
        
        # Basic sanity checks
        assert isinstance(start_idx, (int, type(None)))
        assert isinstance(end_idx, (int, type(None)))
        assert isinstance(filtered_words, pd.DataFrame)
        
        # If indices are found, they should be valid
        if start_idx is not None:
            assert start_idx >= 0
            assert start_idx <= len(words_df)
        
        if end_idx is not None:
            assert end_idx >= 0
            assert end_idx <= len(words_df)
            
        assert len(filtered_words) <= len(words_df)


class TestDefaultBoundaryDetectorEdgeCases:
    """Test cases for edge cases and error handling"""
    
    def test_empty_dataframe(self):
        """Test DefaultBoundaryDetector with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        detector = DefaultBoundaryDetector(empty_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        start_idx = detector.get_start_idx()
        end_idx = detector.get_end_idx()
        filtered_words = detector.get_filtered_table_words()
        
        assert start_idx is None
        assert end_idx is None
        assert len(filtered_words) == 0
    
    def test_single_row_dataframe(self):
        """Test DefaultBoundaryDetector with single row DataFrame"""
        single_row_df = pd.DataFrame({
            'text': ['test'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        detector = DefaultBoundaryDetector(single_row_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        # Since phrase length is 3 and we only have 1 row, search should fail
        start_idx = detector.get_start_idx()
        end_idx = detector.get_end_idx()
        filtered_words = detector.get_filtered_table_words()
        
        assert start_idx is None
        assert end_idx is None
        assert len(filtered_words) == 0
    
    def test_missing_required_columns(self):
        """Test behavior when DataFrame is missing required columns"""
        invalid_df = pd.DataFrame({
            'text': ['test', 'data'],
            'page': [1, 1]
            # Missing other required columns
        })
        
        detector = DefaultBoundaryDetector(invalid_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        # Should handle gracefully when filtering/sorting
        try:
            filtered_words = detector.get_filtered_table_words()
            # If it doesn't raise an exception, that's fine
        except KeyError:
            # Expected behavior for missing columns
            pass
    
    def test_special_characters_in_phrases(self):
        """Test with special characters in start and end phrases"""
        mock_df = pd.DataFrame({
            'text': ['$', 'special', 'phrase', '&', 'data', '@', 'end', 'phrase'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250, 300, 350],
            'top': [0, 0, 0, 0, 0, 0, 0, 0],
            'x1': [40, 90, 140, 190, 240, 290, 340, 390],
            'bottom': [10, 10, 10, 10, 10, 10, 10, 10]
        })
        
        special_properties = {
            'start_phrase': ['$', 'special', 'phrase'],
            'end_phrase': ['@', 'end', 'phrase'],
            'bank': 'test',
            'statement_type': 'debit'
        }
        
        detector = DefaultBoundaryDetector(mock_df, special_properties)
        
        with patch('models.table_processing.boundary_detection.search_phrase_in_df', side_effect=[0, 5]):
            start_idx = detector.get_start_idx()
            end_idx = detector.get_end_idx()
            
            assert start_idx == 3  # 0 + len(start_phrase)
            assert end_idx == 8   # 5 + len(end_phrase)


class TestDefaultBoundaryDetectorIntegration:
    """Integration test cases combining multiple methods"""
    
    def test_full_workflow_success(self):
        """Test complete workflow from initialization to filtered words"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'fecha', 'descripción', 'cargos', 'row1', 'row2', 'total', 'cargos', 'outro'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 250, 300, 350, 400],
            'top': [0, 10, 20, 30, 40, 50, 60, 70, 80],
            'x1': [40, 90, 140, 190, 240, 290, 340, 390, 440],
            'bottom': [10, 20, 30, 40, 50, 60, 70, 80, 90]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_BASIC)
        
        with patch('models.table_processing.boundary_detection.search_phrase_in_df', side_effect=[1, 6]):
            # Test complete workflow
            start_idx = detector.get_start_idx()
            assert start_idx == 4  # 1 + 3
            
            end_idx = detector.get_end_idx()
            assert end_idx == 8   # 6 + 2
            
            filtered_words = detector.get_filtered_table_words()
            assert len(filtered_words) == 4  # rows 4, 5, 6, 7
            assert list(filtered_words['text']) == ['row1', 'row2', 'total', 'cargos']
    
    def test_full_workflow_failure(self):
        """Test complete workflow when phrases are not found"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'some', 'random', 'data'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 10, 20, 30],
            'x1': [40, 90, 140, 190],
            'bottom': [10, 20, 30, 40]
        })
        
        detector = DefaultBoundaryDetector(mock_df, TEST_STATEMENT_PROPERTIES_MISSING)
        
        # Test complete workflow when phrases aren't found
        start_idx = detector.get_start_idx()
        assert start_idx is None
        
        end_idx = detector.get_end_idx()
        assert end_idx is None
        
        filtered_words = detector.get_filtered_table_words()
        assert filtered_words.empty is True
        
