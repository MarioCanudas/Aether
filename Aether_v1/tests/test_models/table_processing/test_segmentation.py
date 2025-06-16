import pytest
import pandas as pd
from unittest.mock import patch
from models import DefaultColumnSegmenter, DefaultRowSegmenter, DefaultBoundaryDetector
from models.document_processing.banks_properties import BANORTE_DEBIT_PROPERTIES

# Test files to use for different scenarios
CORRECTED_WORDS_FILE = 'banorte_debit_corrected_words.csv'

# Test statement properties for different scenarios
TEST_COLUMN_PROPERTIES_SINGLE_WORD = {
    'columns': ['FECHA', 'MONTO', 'SALDO'],
    'amount_column': ['MONTO', 'SALDO'],
    'bank': 'test',
    'statement_type': 'debit'
}

TEST_COLUMN_PROPERTIES_MULTI_WORD = {
    'columns': ['FECHA OPERACION', 'MONTO DEL DEPOSITO', 'DESCRIPCION ESTABLECIMIENTO'],
    'amount_column': ['MONTO DEL DEPOSITO'],
    'bank': 'test',
    'statement_type': 'debit'
}

TEST_COLUMN_PROPERTIES_EMPTY = {
    'columns': [],
    'amount_column': [],
    'bank': 'test',
    'statement_type': 'debit'
}


class TestDefaultColumnSegmenterInitialization:
    """Test cases for DefaultColumnSegmenter initialization"""
    
    def test_init_with_dataframe_and_properties(self):
        """Test DefaultColumnSegmenter initialization with DataFrame and properties"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        segmenter = DefaultColumnSegmenter(mock_df, TEST_COLUMN_PROPERTIES_SINGLE_WORD)
        
        assert segmenter.filtered_table_words.equals(mock_df)
        assert segmenter.statement_properties == TEST_COLUMN_PROPERTIES_SINGLE_WORD
        assert hasattr(segmenter, 'filtered_table_words')
        assert hasattr(segmenter, 'statement_properties')
    
    def test_inheritance_from_column_segmenter(self):
        """Test that DefaultColumnSegmenter inherits from ColumnSegmenter"""
        mock_df = pd.DataFrame({'text': ['test'], 'page': [1], 'x0': [0], 'top': [0], 'x1': [40], 'bottom': [10]})
        segmenter = DefaultColumnSegmenter(mock_df, TEST_COLUMN_PROPERTIES_SINGLE_WORD)
        
        from models.core import ColumnSegmenter
        assert isinstance(segmenter, ColumnSegmenter)


class TestDefaultColumnSegmenterDelimitColumnPositions:
    """Test cases for delimit_column_positions functionality"""
    
    def test_delimit_single_word_columns(self):
        """Test delimiting positions for single-word column names"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCION', 'MONTO', 'data1', 'data2', 'data3'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [10, 60, 120, 10, 60, 120],
            'top': [0, 0, 0, 20, 20, 20],
            'x1': [50, 110, 160, 50, 110, 160],
            'bottom': [10, 10, 10, 30, 30, 30]
        })
        
        properties = {
            'columns': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'amount_column': ['MONTO']
        }
        
        segmenter = DefaultColumnSegmenter(mock_df, properties)
        result = segmenter.delimit_column_positions()
        
        # Verify structure
        assert isinstance(result, dict)
        assert 'column' in result
        assert 'x0' in result
        assert 'x1' in result
        
        # Verify content
        assert result['column'] == ['FECHA', 'DESCRIPCION', 'MONTO']
        assert result['x0'] == [10, 60, 120]
        assert result['x1'] == [50, 110, 160]
    
    def test_delimit_multi_word_columns(self):
        """Test delimiting positions for multi-word column names"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'OPERACION', 'MONTO', 'DEL', 'DEPOSITO', 'SALDO'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [10, 60, 120, 170, 200, 250],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [50, 110, 160, 190, 240, 290],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        properties = {
            'columns': ['FECHA OPERACION', 'MONTO DEL DEPOSITO', 'SALDO'],
            'amount_column': ['MONTO DEL DEPOSITO', 'SALDO']
        }
        
        segmenter = DefaultColumnSegmenter(mock_df, properties)
        result = segmenter.delimit_column_positions()
        
        # Verify structure
        assert result['column'] == ['FECHA OPERACION', 'MONTO DEL DEPOSITO', 'SALDO']
        # First column should span from 'FECHA' x0 to 'OPERACION' x1
        assert result['x0'][0] == 10  # FECHA x0
        assert result['x1'][0] == 110  # OPERACION x1
        # Second column should span from 'MONTO' x0 to 'DEPOSITO' x1
        assert result['x0'][1] == 120  # MONTO x0
        assert result['x1'][1] == 240  # DEPOSITO x1
        # Third column (single word)
        assert result['x0'][2] == 250  # SALDO x0
        assert result['x1'][2] == 290  # SALDO x1
    
    def test_delimit_columns_not_found(self):
        """Test delimiting when some columns are not found in the data"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCION', 'other', 'data'],
            'page': [1, 1, 1, 1],
            'x0': [10, 60, 120, 170],
            'top': [0, 0, 0, 0],
            'x1': [50, 110, 160, 210],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {
            'columns': ['FECHA', 'DESCRIPCION', 'MONTO'],  # MONTO not in data
            'amount_column': ['MONTO']
        }
        
        segmenter = DefaultColumnSegmenter(mock_df, properties)
        result = segmenter.delimit_column_positions()
        
        # Verify structure
        assert result['column'] == ['FECHA', 'DESCRIPCION', 'MONTO']
        assert result['x0'] == [10, 60, None]  # MONTO not found
        assert result['x1'] == [50, 110, None]  # MONTO not found
    
    def test_delimit_empty_columns(self):
        """Test delimiting with empty columns list"""
        mock_df = pd.DataFrame({
            'text': ['data1', 'data2'],
            'page': [1, 1],
            'x0': [10, 60],
            'top': [0, 0],
            'x1': [50, 110],
            'bottom': [10, 10]
        })
        
        segmenter = DefaultColumnSegmenter(mock_df, TEST_COLUMN_PROPERTIES_EMPTY)
        result = segmenter.delimit_column_positions()
        
        # Should return empty lists
        assert result['column'] == []
        assert result['x0'] == []
        assert result['x1'] == []
    
    def test_delimit_duplicate_words_in_column(self):
        """Test delimiting when column words appear multiple times"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'FECHA', 'DESCRIPCION', 'MONTO'],
            'page': [1, 1, 1, 1],
            'x0': [10, 60, 120, 170],
            'top': [0, 0, 0, 0],
            'x1': [50, 100, 160, 210],
            'bottom': [10, 10, 10, 10]
        })
        
        properties = {
            'columns': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'amount_column': ['MONTO']
        }
        
        segmenter = DefaultColumnSegmenter(mock_df, properties)
        result = segmenter.delimit_column_positions()
        
        # Should use the first occurrence
        assert result['x0'][0] == 10  # First FECHA
        assert result['x1'][0] == 50  # First FECHA


class TestDefaultRowSegmenterInitialization:
    """Test cases for DefaultRowSegmenter initialization"""
    
    def test_init_with_dataframe(self):
        """Test DefaultRowSegmenter initialization with DataFrame"""
        mock_df = pd.DataFrame({
            'text': ['row1', 'row2', 'row3'],
            'page': [1, 1, 1],
            'x0': [0, 0, 0],
            'top': [0, 15, 30],
            'x1': [40, 40, 40],
            'bottom': [10, 25, 40]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        
        assert segmenter.filtered_table_words.equals(mock_df)
        assert hasattr(segmenter, 'filtered_table_words')
    
    def test_inheritance_from_row_segmenter(self):
        """Test that DefaultRowSegmenter inherits from RowSegmenter"""
        mock_df = pd.DataFrame({'text': ['test'], 'page': [1], 'x0': [0], 'top': [0], 'x1': [40], 'bottom': [10]})
        segmenter = DefaultRowSegmenter(mock_df)
        
        from models.core import RowSegmenter
        assert isinstance(segmenter, RowSegmenter)


class TestDefaultRowSegmenterRowThreshold:
    """Test cases for get_row_threshold functionality"""
    
    def test_get_row_threshold_normal_distribution(self):
        """Test row threshold calculation with normal data distribution"""
        mock_df = pd.DataFrame({
            'text': ['row1', 'row2', 'row3', 'row4', 'row5'],
            'page': [1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0],
            'top': [0, 10, 20, 30, 40],  # Regular 10px differences
            'x1': [40, 40, 40, 40, 40],
            'bottom': [5, 15, 25, 35, 45]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        threshold = segmenter.get_row_threshold()
        
        # Should be between min_threshold (2) and max_threshold (7)
        assert isinstance(threshold, (float, int))
        assert 2 <= threshold <= 7
    
    def test_get_row_threshold_outliers(self):
        """Test row threshold calculation with outliers"""
        mock_df = pd.DataFrame({
            'text': ['row1', 'row2', 'row3', 'row4', 'row5'],
            'page': [1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0],
            'top': [0, 5, 10, 100, 105],  # Large gap at position 3
            'x1': [40, 40, 40, 40, 40],
            'bottom': [5, 10, 15, 105, 110]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        threshold = segmenter.get_row_threshold()
        
        # Should handle outliers and stay within bounds
        assert isinstance(threshold, (float, int))
        assert 2 <= threshold <= 7
    
    def test_get_row_threshold_multiple_pages(self):
        """Test row threshold calculation with multiple pages"""
        mock_df = pd.DataFrame({
            'text': ['row1', 'row2', 'row3', 'row4'],
            'page': [1, 1, 2, 2],
            'x0': [0, 0, 0, 0],
            'top': [0, 10, 0, 12],  # Different pages can have different starts
            'x1': [40, 40, 40, 40],
            'bottom': [5, 15, 8, 20]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        threshold = segmenter.get_row_threshold()
        
        assert isinstance(threshold, (float, int))
        assert 2 <= threshold <= 7
    
    def test_get_row_threshold_empty_dataframe(self):
        """Test row threshold calculation with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        segmenter = DefaultRowSegmenter(empty_df)
        
        # Should handle empty data gracefully
        threshold = segmenter.get_row_threshold()
        # With empty data, it should return nan because there are no differences
        assert pd.isna(threshold)
    
    def test_get_row_threshold_single_row(self):
        """Test row threshold calculation with single row"""
        single_row_df = pd.DataFrame({
            'text': ['row1'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        segmenter = DefaultRowSegmenter(single_row_df)
        threshold = segmenter.get_row_threshold()
        
        # Should return nan when no differences can be calculated
        assert pd.isna(threshold)


class TestDefaultRowSegmenterGroupRows:
    """Test cases for group_rows functionality"""
    
    def test_group_rows_normal_spacing(self):
        """Test grouping rows with normal spacing"""
        mock_df = pd.DataFrame({
            'text': ['word1', 'word2', 'word3', 'word4', 'word5', 'word6'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 0, 50, 100],
            'top': [0, 0, 0, 20, 20, 20],  # Two rows: top=0 and top=20
            'x1': [40, 90, 140, 40, 90, 140],
            'bottom': [10, 10, 10, 30, 30, 30]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        
        with patch.object(segmenter, 'get_row_threshold', return_value=5.0):
            result = segmenter.group_rows()
        
        # Should have 2 rows (groups)
        assert len(result) == 2
        
        # Check structure
        assert 'row_group' in result.columns
        assert 'text' in result.columns
        assert 'words' in result.columns
        assert 'top' in result.columns
        assert 'bottom' in result.columns
        assert 'page' in result.columns
        
        # Check content
        assert result.iloc[0]['text'] == 'word1 word2 word3'
        assert result.iloc[1]['text'] == 'word4 word5 word6'
        assert len(result.iloc[0]['words']) == 3
        assert len(result.iloc[1]['words']) == 3
    
    def test_group_rows_single_row(self):
        """Test grouping when all words are in one row"""
        mock_df = pd.DataFrame({
            'text': ['word1', 'word2', 'word3'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],  # All same top
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        
        with patch.object(segmenter, 'get_row_threshold', return_value=5.0):
            result = segmenter.group_rows()
        
        # Should have 1 row
        assert len(result) == 1
        assert result.iloc[0]['text'] == 'word1 word2 word3'
        assert len(result.iloc[0]['words']) == 3
    
    def test_group_rows_each_word_separate_row(self):
        """Test grouping when each word is in a separate row"""
        mock_df = pd.DataFrame({
            'text': ['word1', 'word2', 'word3'],
            'page': [1, 1, 1],
            'x0': [0, 0, 0],
            'top': [0, 20, 40],  # Large gaps
            'x1': [40, 40, 40],
            'bottom': [10, 30, 50]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        
        with patch.object(segmenter, 'get_row_threshold', return_value=5.0):
            result = segmenter.group_rows()
        
        # Should have 3 rows
        assert len(result) == 3
        assert result.iloc[0]['text'] == 'word1'
        assert result.iloc[1]['text'] == 'word2'
        assert result.iloc[2]['text'] == 'word3'
    
    def test_group_rows_multiple_pages(self):
        """Test grouping rows across multiple pages"""
        mock_df = pd.DataFrame({
            'text': ['word1', 'word2', 'word3', 'word4'],
            'page': [1, 1, 2, 2],
            'x0': [0, 50, 0, 50],
            'top': [0, 0, 0, 0],  # Same top positions on different pages
            'x1': [40, 90, 40, 90],
            'bottom': [10, 10, 10, 10]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        
        with patch.object(segmenter, 'get_row_threshold', return_value=5.0):
            result = segmenter.group_rows()
        
        # Should group properly considering page differences
        assert len(result) >= 1
        assert isinstance(result, pd.DataFrame)
    
    def test_group_rows_empty_dataframe(self):
        """Test grouping with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        segmenter = DefaultRowSegmenter(empty_df)
        
        result = segmenter.group_rows()
        
        # Should return empty DataFrame with expected columns
        assert len(result) == 0
        expected_columns = ['row_group', 'text', 'words', 'top', 'bottom', 'page']
        assert all(col in result.columns for col in expected_columns)


class TestDefaultSegmentersWithRealData:
    """Test cases using real CSV data files"""
    
    @pytest.fixture(scope='class')
    def get_filtered_words(self, get_input_data_from_path) -> pd.DataFrame:
        words_df, _ = get_input_data_from_path
        filtered_words = DefaultBoundaryDetector(words_df, BANORTE_DEBIT_PROPERTIES).get_filtered_table_words()
        
        return filtered_words
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_column_segmenter_with_real_data(self, get_filtered_words):
        """Test DefaultColumnSegmenter with real corrected words CSV data"""
        filtered_words = get_filtered_words
        segmenter = DefaultColumnSegmenter(filtered_words, BANORTE_DEBIT_PROPERTIES)
        
        # Test initialization
        assert segmenter.filtered_table_words.equals(filtered_words)
        assert segmenter.statement_properties == BANORTE_DEBIT_PROPERTIES
        
        # Test that method can be called without errors
        result = segmenter.delimit_column_positions()
        
        # Verify structure
        assert isinstance(result, dict)
        assert 'column' in result
        assert 'x0' in result
        assert 'x1' in result
        
        # Verify lengths match
        assert len(result['column']) == len(result['x0']) == len(result['x1'])
        assert len(result['column']) == len(BANORTE_DEBIT_PROPERTIES['columns'])
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_row_segmenter_with_real_data(self, get_filtered_words):
        """Test DefaultRowSegmenter with real corrected words CSV data"""
        filtered_words = get_filtered_words
        
        segmenter = DefaultRowSegmenter(filtered_words)
        
        # Test initialization
        assert segmenter.filtered_table_words.equals(filtered_words)
        
        # Test that methods can be called without errors
        threshold = segmenter.get_row_threshold()
        grouped_rows = segmenter.group_rows()
        
        # Verify types and ranges
        assert isinstance(threshold, (float, int))
        assert 2 <= threshold <= 7
        assert isinstance(grouped_rows, pd.DataFrame)
        assert len(grouped_rows) <= len(filtered_words)
        
        # Verify expected columns
        expected_columns = ['row_group', 'text', 'words', 'top', 'bottom', 'page']
        assert all(col in grouped_rows.columns for col in expected_columns)


class TestDefaultSegmentersEdgeCases:
    """Test cases for edge cases and error handling"""
    
    def test_column_segmenter_missing_columns_property(self):
        """Test DefaultColumnSegmenter when statement_properties is missing 'columns'"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'MONTO'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 0],
            'x1': [40, 90],
            'bottom': [10, 10]
        })
        
        properties = {'bank': 'test'}  # Missing 'columns'
        
        segmenter = DefaultColumnSegmenter(mock_df, properties)
        
        # Should handle missing key gracefully
        try:
            segmenter.delimit_column_positions()
        except KeyError:
            # Expected behavior when 'columns' key is missing
            pass
    
    def test_row_segmenter_missing_required_columns(self):
        """Test DefaultRowSegmenter when DataFrame is missing required columns"""
        invalid_df = pd.DataFrame({
            'text': ['test', 'data'],
            'page': [1, 1]
            # Missing 'top' column
        })
        
        segmenter = DefaultRowSegmenter(invalid_df)
        
        # Should handle missing columns gracefully
        try:
            segmenter.get_row_threshold()
            segmenter.group_rows()
        except KeyError:
            # Expected behavior for missing required columns
            pass
    
    def test_column_segmenter_with_special_characters(self):
        """Test DefaultColumnSegmenter with special characters in column names"""
        mock_df = pd.DataFrame({
            'text': ['FECHA/', 'DESCRIPCIÓN', 'MONTO($)'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        properties = {
            'columns': ['FECHA/', 'DESCRIPCIÓN', 'MONTO($)'],
            'amount_column': ['MONTO($)']
        }
        
        segmenter = DefaultColumnSegmenter(mock_df, properties)
        result = segmenter.delimit_column_positions()
        
        # Should handle special characters
        assert result['column'] == ['FECHA/', 'DESCRIPCIÓN', 'MONTO($)']
        assert all(x is not None for x in result['x0'])
        assert all(x is not None for x in result['x1'])
    
    def test_row_segmenter_identical_top_values(self):
        """Test DefaultRowSegmenter when all rows have identical top values"""
        mock_df = pd.DataFrame({
            'text': ['word1', 'word2', 'word3'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [10, 10, 10],  # All identical
            'x1': [40, 90, 140],
            'bottom': [20, 20, 20]
        })
        
        segmenter = DefaultRowSegmenter(mock_df)
        
        threshold = segmenter.get_row_threshold()
        grouped_rows = segmenter.group_rows()
        
        # Should group all words into one row
        assert threshold == 2  # Minimum threshold
        assert len(grouped_rows) == 1
        assert grouped_rows.iloc[0]['text'] == 'word1 word2 word3'


class TestDefaultSegmentersIntegration:
    """Integration test cases combining both segmenters"""
    
    def test_segmenters_workflow_integration(self):
        """Test complete workflow using both segmenters together"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCION', 'MONTO', '01/01', 'Compra', '100.00', '02/01', 'Retiro', '50.00'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 0, 50, 100, 0, 50, 100],
            'top': [0, 0, 0, 20, 20, 20, 40, 40, 40],  # Header + 2 data rows
            'x1': [40, 90, 140, 40, 90, 140, 40, 90, 140],
            'bottom': [10, 10, 10, 30, 30, 30, 50, 50, 50]
        })
        
        properties = {
            'columns': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'amount_column': ['MONTO']
        }
        
        # Test column segmenter
        col_segmenter = DefaultColumnSegmenter(mock_df, properties)
        column_positions = col_segmenter.delimit_column_positions()
        
        # Test row segmenter
        row_segmenter = DefaultRowSegmenter(mock_df)
        with patch.object(row_segmenter, 'get_row_threshold', return_value=5.0):
            grouped_rows = row_segmenter.group_rows()
        
        # Verify integration results
        assert len(column_positions['column']) == 3
        assert len(grouped_rows) == 3  # Header + 2 data rows
        
        # Verify that both segmenters work with the same data
        assert isinstance(column_positions, dict)
        assert isinstance(grouped_rows, pd.DataFrame)
    
    def test_segmenters_with_banorte_properties(self):
        """Test both segmenters using BANORTE_DEBIT_PROPERTIES"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCIÓN', 'ESTABLECIMIENTO', 'MONTO', 'DEL', 'DEPOSITO'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [10, 60, 150, 250, 300, 350],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [50, 140, 240, 290, 340, 400],
            'bottom': [10, 10, 10, 10, 10, 10]
        })
        
        # Test with real bank properties
        col_segmenter = DefaultColumnSegmenter(mock_df, BANORTE_DEBIT_PROPERTIES)
        row_segmenter = DefaultRowSegmenter(mock_df)
        
        # Should not raise exceptions
        column_positions = col_segmenter.delimit_column_positions()
        threshold = row_segmenter.get_row_threshold()
        grouped_rows = row_segmenter.group_rows()
        
        # Basic verification
        assert isinstance(column_positions, dict)
        assert isinstance(threshold, (float, int))
        assert isinstance(grouped_rows, pd.DataFrame)
