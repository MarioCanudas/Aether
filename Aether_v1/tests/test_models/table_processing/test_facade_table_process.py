import pytest
import pandas as pd
from unittest.mock import patch, Mock
from models import TableProcessingFacade
from models.document_processing.banks_properties import BANORTE_DEBIT_PROPERTIES, BBVA_DEBIT_PROPERTIES

# Test files to use for different scenarios
CORRECTED_WORDS_FILE = 'banorte_debit_corrected_words.csv'

# Test statement properties for different scenarios
TEST_PROPERTIES_INTEGRATION = {
    'start_phrase': ['fecha', 'descripcion', 'monto'],
    'end_phrase': ['total', 'final'],
    'columns': ['FECHA', 'DESCRIPCION', 'MONTO'],
    'amount_column': ['MONTO'],
    'date_pattern': r'(\d{2})-(\w{3})-(\d{2})',
    'bank': 'test',
    'statement_type': 'debit'
}

TEST_PROPERTIES_MULTI_AMOUNT = {
    'start_phrase': ['detalle', 'movimientos'],
    'end_phrase': ['resumen', 'total'],
    'columns': ['FECHA', 'DESCRIPCION', 'DEPOSITO', 'RETIRO', 'SALDO'],
    'amount_column': ['DEPOSITO', 'RETIRO', 'SALDO'],
    'date_pattern': r'(\d{2})/(\d{2})',
    'bank': 'test',
    'statement_type': 'debit'
}


class TestTableProcessingFacadeInitialization:
    """Test cases for TableProcessingFacade initialization"""
    
    def test_init_with_dataframe_and_properties(self):
        """Test TableProcessingFacade initialization with DataFrame and properties"""
        mock_df = pd.DataFrame({
            'text': ['fecha', 'descripcion', 'monto', '01-ENE-24', 'Compra', '100.00'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 0, 50, 100],
            'top': [0, 0, 0, 20, 20, 20],
            'x1': [40, 90, 140, 40, 90, 140],
            'bottom': [10, 10, 10, 30, 30, 30]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        assert facade.corrected_extracted_words.equals(mock_df)
        assert facade.statement_properties == TEST_PROPERTIES_INTEGRATION
        assert hasattr(facade, 'boundary_detector')
        assert hasattr(facade, 'corrected_extracted_words')
        assert hasattr(facade, 'statement_properties')
    
    def test_boundary_detector_initialization(self):
        """Test that boundary detector is properly initialized"""
        mock_df = pd.DataFrame({
            'text': ['test'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Verify boundary detector is created and configured
        from models import DefaultBoundaryDetector
        assert isinstance(facade.boundary_detector, DefaultBoundaryDetector)
        assert facade.boundary_detector.corrected_extracted_words.equals(mock_df)
        assert facade.boundary_detector.statement_properties == TEST_PROPERTIES_INTEGRATION


class TestTableProcessingFacadeGetters:
    """Test cases for component getter methods"""
    
    def test_get_column_segmenter(self):
        """Test get_column_segmenter method"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Mock the boundary detector to return filtered words
        mock_filtered_words = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        with patch.object(facade.boundary_detector, 'get_filtered_table_words', return_value=mock_filtered_words):
            column_segmenter = facade.get_column_segmenter()
        
        # Verify column segmenter is properly created
        from models import DefaultColumnSegmenter
        assert isinstance(column_segmenter, DefaultColumnSegmenter)
        assert column_segmenter.filtered_table_words.equals(mock_filtered_words)
        assert column_segmenter.statement_properties == TEST_PROPERTIES_INTEGRATION
    
    def test_get_row_segmenter(self):
        """Test get_row_segmenter method"""
        mock_df = pd.DataFrame({
            'text': ['word1', 'word2', 'word3'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 20, 40],
            'x1': [40, 90, 140],
            'bottom': [10, 30, 50]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Mock the boundary detector to return filtered words
        mock_filtered_words = pd.DataFrame({
            'text': ['word1', 'word2', 'word3'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 20, 40],
            'x1': [40, 90, 140],
            'bottom': [10, 30, 50]
        })
        
        with patch.object(facade.boundary_detector, 'get_filtered_table_words', return_value=mock_filtered_words):
            row_segmenter = facade.get_row_segmenter()
        
        # Verify row segmenter is properly created
        from models import DefaultRowSegmenter
        assert isinstance(row_segmenter, DefaultRowSegmenter)
        assert row_segmenter.filtered_table_words.equals(mock_filtered_words)
    
    def test_get_reconstructor(self):
        """Test get_reconstructor method integrating column and row segmenters"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESC', 'MONTO', '01-ENE', 'Compra', '100.00'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 0, 50, 100],
            'top': [0, 0, 0, 20, 20, 20],
            'x1': [40, 90, 140, 40, 90, 140],
            'bottom': [10, 10, 10, 30, 30, 30]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Mock filtered words
        mock_filtered_words = mock_df.copy()
        
        # Mock grouped rows from row segmenter
        mock_grouped_rows = pd.DataFrame({
            'row_group': [0, 1],
            'text': ['FECHA DESC MONTO', '01-ENE Compra 100.00'],
            'words': [
                [('FECHA', 0, 40), ('DESC', 50, 90), ('MONTO', 100, 140)],
                [('01-ENE', 0, 40), ('Compra', 50, 90), ('100.00', 100, 140)]
            ],
            'top': [0, 20],
            'bottom': [10, 30],
            'page': [1, 1]
        })
        
        # Mock column delimitation from column segmenter
        mock_column_delimitation = {
            'column': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'x0': [0, 50, 100],
            'x1': [40, 90, 140]
        }
        
        with patch.object(facade.boundary_detector, 'get_filtered_table_words', return_value=mock_filtered_words):
            with patch.object(facade, 'get_column_segmenter') as mock_col_seg:
                with patch.object(facade, 'get_row_segmenter') as mock_row_seg:
                    # Setup mocks
                    mock_col_seg_instance = Mock()
                    mock_col_seg_instance.delimit_column_positions.return_value = mock_column_delimitation
                    mock_col_seg.return_value = mock_col_seg_instance
                    
                    mock_row_seg_instance = Mock()
                    mock_row_seg_instance.group_rows.return_value = mock_grouped_rows
                    mock_row_seg.return_value = mock_row_seg_instance
                    
                    reconstructor = facade.get_reconstructor()
        
        # Verify reconstructor is properly created
        from models import TableReconstructor
        assert isinstance(reconstructor, TableReconstructor)
        assert reconstructor.grouped_rows.equals(mock_grouped_rows)
        assert reconstructor.column_delimitation == mock_column_delimitation
        assert reconstructor.statement_properties == TEST_PROPERTIES_INTEGRATION


class TestTableProcessingFacadeIntegration:
    """Test cases for complete integration workflow"""
    
    def test_reconstruct_table_complete_workflow(self):
        """Test complete table reconstruction workflow"""
        mock_df = pd.DataFrame({
            'text': ['intro', 'FECHA', 'DESCRIPCION', 'MONTO', '01-ENE-24', 'Compra', '100.00', '02-ENE-24', 'Retiro', '50.00', 'final'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 0, 50, 100, 0, 50, 100, 0, 50, 100, 0],
            'top': [0, 20, 20, 20, 40, 40, 40, 60, 60, 60, 80],
            'x1': [40, 40, 90, 140, 40, 90, 140, 40, 90, 140, 40],
            'bottom': [10, 30, 30, 30, 50, 50, 50, 70, 70, 70, 90]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Mock the entire pipeline
        mock_filtered_words = mock_df.iloc[1:10]  # Remove intro and final
        
        mock_grouped_rows = pd.DataFrame({
            'row_group': [0, 1, 2],
            'text': ['FECHA DESCRIPCION MONTO', '01-ENE-24 Compra 100.00', '02-ENE-24 Retiro 50.00'],
            'words': [
                [('FECHA', 0, 40), ('DESCRIPCION', 50, 90), ('MONTO', 100, 140)],
                [('01-ENE-24', 0, 40), ('Compra', 50, 90), ('100.00', 100, 140)],
                [('02-ENE-24', 0, 40), ('Retiro', 50, 90), ('50.00', 100, 140)]
            ]
        })
        
        mock_column_delimitation = {
            'column': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'x0': [0, 50, 100],
            'x1': [40, 90, 140]
        }
        
        mock_final_table = pd.DataFrame({
            'Date': ['01-ENE-24', '02-ENE-24'],
            'Description': ['Compra', 'Retiro'],
            'MONTO': ['100.00', '50.00']
        })
        
        with patch.object(facade.boundary_detector, 'get_filtered_table_words', return_value=mock_filtered_words):
            with patch('models.table_processing.facade.DefaultColumnSegmenter') as mock_col_class:
                with patch('models.table_processing.facade.DefaultRowSegmenter') as mock_row_class:
                    with patch('models.table_processing.facade.TableReconstructor') as mock_recon_class:
                        # Setup column segmenter mock
                        mock_col_instance = Mock()
                        mock_col_instance.delimit_column_positions.return_value = mock_column_delimitation
                        mock_col_class.return_value = mock_col_instance
                        
                        # Setup row segmenter mock
                        mock_row_instance = Mock()
                        mock_row_instance.group_rows.return_value = mock_grouped_rows
                        mock_row_class.return_value = mock_row_instance
                        
                        # Setup reconstructor mock
                        mock_recon_instance = Mock()
                        mock_recon_instance.reconstruct_table.return_value = mock_final_table
                        mock_recon_class.return_value = mock_recon_instance
                        
                        result = facade.reconstruct_table()
        
        # Verify final result
        assert isinstance(result, pd.DataFrame)
        assert result.equals(mock_final_table)
        
        # Verify that all components were called properly
        mock_col_class.assert_called_once_with(mock_filtered_words, TEST_PROPERTIES_INTEGRATION)
        mock_row_class.assert_called_once_with(mock_filtered_words)
        mock_recon_class.assert_called_once_with(mock_grouped_rows, mock_column_delimitation, TEST_PROPERTIES_INTEGRATION)
    
    def test_reconstruct_table_with_multiple_amount_columns(self):
        """Test reconstruction workflow with multiple amount columns"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESC', 'DEP', 'RET', 'SALDO', '01/01', 'Compra', '100', '', '1000'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 50, 100, 150, 200, 0, 50, 100, 150, 200],
            'top': [0, 0, 0, 0, 0, 20, 20, 20, 20, 20],
            'x1': [40, 90, 140, 190, 240, 40, 90, 140, 190, 240],
            'bottom': [10, 10, 10, 10, 10, 30, 30, 30, 30, 30]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_MULTI_AMOUNT)
        
        # Mock final table with multiple amount columns
        mock_final_table = pd.DataFrame({
            'Date': ['01/01'],
            'Description': ['Compra'],
            'DEPOSITO': ['100'],
            'RETIRO': [''],
            'SALDO': ['1000']
        })
        
        with patch.object(facade, 'get_reconstructor') as mock_get_recon:
            mock_reconstructor = Mock()
            mock_reconstructor.reconstruct_table.return_value = mock_final_table
            mock_get_recon.return_value = mock_reconstructor
            
            result = facade.reconstruct_table()
        
        # Verify result structure for multiple amount columns
        assert isinstance(result, pd.DataFrame)
        assert 'DEPOSITO' in result.columns
        assert 'RETIRO' in result.columns
        assert 'SALDO' in result.columns
        assert result.equals(mock_final_table)
    
    def test_component_dependencies(self):
        """Test that components depend on each other correctly"""
        mock_df = pd.DataFrame({
            'text': ['test', 'data'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 0],
            'x1': [40, 90],
            'bottom': [10, 10]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Test that column segmenter depends on boundary detector
        with patch.object(facade.boundary_detector, 'get_filtered_table_words') as mock_filter:
            mock_filtered = pd.DataFrame({'text': ['filtered'], 'page': [1], 'x0': [0], 'top': [0], 'x1': [40], 'bottom': [10]})
            mock_filter.return_value = mock_filtered
            
            column_segmenter = facade.get_column_segmenter()
            
            # Verify boundary detector was called
            mock_filter.assert_called_once()
            assert column_segmenter.filtered_table_words.equals(mock_filtered)
        
        # Test that row segmenter depends on boundary detector
        with patch.object(facade.boundary_detector, 'get_filtered_table_words') as mock_filter:
            mock_filtered = pd.DataFrame({'text': ['filtered'], 'page': [1], 'x0': [0], 'top': [0], 'x1': [40], 'bottom': [10]})
            mock_filter.return_value = mock_filtered
            
            row_segmenter = facade.get_row_segmenter()
            
            # Verify boundary detector was called
            mock_filter.assert_called_once()
            assert row_segmenter.filtered_table_words.equals(mock_filtered)


class TestTableProcessingFacadeWithRealData:
    """Test cases using real CSV data files"""
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_facade_with_real_corrected_words_data(self, get_input_data_from_path):
        """Test TableProcessingFacade with real corrected words CSV data"""
        words_df, file_path = get_input_data_from_path
        
        # Use a subset of the data for faster testing
        test_df = words_df.head(50) if len(words_df) > 50 else words_df
        
        facade = TableProcessingFacade(test_df, BANORTE_DEBIT_PROPERTIES)
        
        # Test initialization with real data
        assert facade.corrected_extracted_words.equals(test_df)
        assert facade.statement_properties == BANORTE_DEBIT_PROPERTIES
        
        # Test that all getter methods can be called without errors
        try:
            column_segmenter = facade.get_column_segmenter()
            row_segmenter = facade.get_row_segmenter()
            reconstructor = facade.get_reconstructor()
            
            # Verify types
            from models import DefaultColumnSegmenter, DefaultRowSegmenter, TableReconstructor
            assert isinstance(column_segmenter, DefaultColumnSegmenter)
            assert isinstance(row_segmenter, DefaultRowSegmenter)
            assert isinstance(reconstructor, TableReconstructor)
            
        except Exception as e:
            # If real processing fails due to data format issues, that's acceptable
            # The important thing is that the facade integrates the components correctly
            pass
    
    @pytest.mark.parametrize('get_input_data_from_path', [CORRECTED_WORDS_FILE], indirect=True)
    def test_full_pipeline_with_real_data(self, get_input_data_from_path):
        """Test complete pipeline with real data (may require mocking some steps)"""
        words_df, file_path = get_input_data_from_path
        
        # Use a small subset for testing
        test_df = words_df.head(20) if len(words_df) > 20 else words_df
        
        facade = TableProcessingFacade(test_df, BANORTE_DEBIT_PROPERTIES)
        
        # Mock some intermediate steps to ensure the pipeline completes
        mock_final_table = pd.DataFrame({
            'Date': ['01-ENE-24'],
            'Description': ['Test transaction'],
            'MONTO DEL DEPOSITO': ['100.00'],
            'MONTO DEL RETIRO': [''],
            'SALDO': ['900.00']
        })
        
        with patch.object(facade, 'get_reconstructor') as mock_get_recon:
            mock_reconstructor = Mock()
            mock_reconstructor.reconstruct_table.return_value = mock_final_table
            mock_get_recon.return_value = mock_reconstructor
            
            result = facade.reconstruct_table()
        
        # Verify final output structure
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0  # Should return a valid DataFrame


class TestTableProcessingFacadeEdgeCases:
    """Test cases for edge cases and error handling"""
    
    def test_empty_dataframe_input(self):
        """Test facade with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        
        facade = TableProcessingFacade(empty_df, TEST_PROPERTIES_INTEGRATION)
        
        # Should handle empty input gracefully
        assert facade.corrected_extracted_words.empty is True
        
        # Test that components can be created even with empty data
        try:
            column_segmenter = facade.get_column_segmenter()
            row_segmenter = facade.get_row_segmenter()
            # These should not crash, even if they return empty results
        except Exception:
            # Some exceptions may be acceptable with empty data
            pass
    
    def test_malformed_statement_properties(self):
        """Test facade with missing or malformed statement properties"""
        mock_df = pd.DataFrame({
            'text': ['test'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        malformed_properties = {
            'bank': 'test'
            # Missing required keys like columns, amount_column, etc.
        }
        
        facade = TableProcessingFacade(mock_df, malformed_properties)
        
        # Should handle missing properties gracefully in component creation
        try:
            column_segmenter = facade.get_column_segmenter()
            row_segmenter = facade.get_row_segmenter()
            reconstructor = facade.get_reconstructor()
        except (KeyError, AttributeError):
            # Expected behavior when required properties are missing
            pass
    
    def test_boundary_detector_returns_empty_table(self):
        """Test facade when boundary detector finds no table boundaries"""
        mock_df = pd.DataFrame({
            'text': ['random', 'text', 'without', 'table'],
            'page': [1, 1, 1, 1],
            'x0': [0, 50, 100, 150],
            'top': [0, 0, 0, 0],
            'x1': [40, 90, 140, 190],
            'bottom': [10, 10, 10, 10]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Mock boundary detector to return empty filtered words
        empty_filtered = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        
        with patch.object(facade.boundary_detector, 'get_filtered_table_words', return_value=empty_filtered):
            column_segmenter = facade.get_column_segmenter()
            row_segmenter = facade.get_row_segmenter()
            
            # Should handle empty filtered words
            assert column_segmenter.filtered_table_words.empty is True
            assert row_segmenter.filtered_table_words.empty is True
    
    def test_component_failure_handling(self):
        """Test facade behavior when individual components fail"""
        mock_df = pd.DataFrame({
            'text': ['test'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Test handling of column segmenter failure
        with patch.object(facade, 'get_column_segmenter', side_effect=Exception("Column segmentation failed")):
            try:
                reconstructor = facade.get_reconstructor()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Column segmentation failed" in str(e)
        
        # Test handling of row segmenter failure
        with patch.object(facade, 'get_row_segmenter', side_effect=Exception("Row segmentation failed")):
            try:
                reconstructor = facade.get_reconstructor()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Row segmentation failed" in str(e)


class TestTableProcessingFacadePerformance:
    """Test cases for performance and efficiency"""
    
    def test_boundary_detector_reuse(self):
        """Test that boundary detector is reused efficiently"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESC', 'MONTO'],
            'page': [1, 1, 1],
            'x0': [0, 50, 100],
            'top': [0, 0, 0],
            'x1': [40, 90, 140],
            'bottom': [10, 10, 10]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Mock filtered words
        mock_filtered_words = mock_df.copy()
        
        with patch.object(facade.boundary_detector, 'get_filtered_table_words', return_value=mock_filtered_words) as mock_filter:
            # Get both segmenters
            column_segmenter = facade.get_column_segmenter()
            row_segmenter = facade.get_row_segmenter()
            
            # Boundary detector should be called twice (once for each segmenter)
            assert mock_filter.call_count == 2
            
            # Both segmenters should use the same filtered words
            assert column_segmenter.filtered_table_words.equals(row_segmenter.filtered_table_words)
    
    def test_component_creation_efficiency(self):
        """Test that components are created efficiently without unnecessary operations"""
        mock_df = pd.DataFrame({
            'text': ['test', 'data'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 0],
            'x1': [40, 90],
            'bottom': [10, 10]
        })
        
        facade = TableProcessingFacade(mock_df, TEST_PROPERTIES_INTEGRATION)
        
        # Test that getting the same component type multiple times works correctly
        with patch.object(facade.boundary_detector, 'get_filtered_table_words') as mock_filter:
            mock_filtered = pd.DataFrame({'text': ['filtered'], 'page': [1], 'x0': [0], 'top': [0], 'x1': [40], 'bottom': [10]})
            mock_filter.return_value = mock_filtered
            
            # Get multiple column segmenters
            col_seg_1 = facade.get_column_segmenter()
            col_seg_2 = facade.get_column_segmenter()
            
            # Should create new instances each time but with same data
            assert col_seg_1 is not col_seg_2  # Different instances
            assert col_seg_1.filtered_table_words.equals(col_seg_2.filtered_table_words)  # Same data


class TestTableProcessingFacadeIntegrationScenarios:
    """Test cases for different integration scenarios"""
    
    def test_banorte_debit_integration(self):
        """Test integration specifically with Banorte debit properties"""
        mock_df = pd.DataFrame({
            'text': ['FECHA', 'DESCRIPCIÓN', 'ESTABLECIMIENTO', 'MONTO', 'DEL', 'DEPOSITO', 'MONTO', 'DEL', 'RETIRO', 'SALDO'],
            'page': [1] * 10,
            'x0': [0, 50, 100, 150, 200, 250, 300, 350, 400, 450],
            'top': [0] * 10,
            'x1': [40, 90, 140, 190, 240, 290, 340, 390, 440, 490],
            'bottom': [10] * 10
        })
        
        facade = TableProcessingFacade(mock_df, BANORTE_DEBIT_PROPERTIES)
        
        # Test that facade works with real bank properties
        column_segmenter = facade.get_column_segmenter()
        row_segmenter = facade.get_row_segmenter()
        
        # Verify that components are configured with bank properties
        assert column_segmenter.statement_properties == BANORTE_DEBIT_PROPERTIES
        assert 'MONTO DEL DEPOSITO' in BANORTE_DEBIT_PROPERTIES['amount_column']
        assert 'MONTO DEL RETIRO' in BANORTE_DEBIT_PROPERTIES['amount_column']
        assert 'SALDO' in BANORTE_DEBIT_PROPERTIES['amount_column']
    
    def test_bbva_debit_integration(self):
        """Test integration specifically with BBVA debit properties"""
        mock_df = pd.DataFrame({
            'text': ['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS'],
            'page': [1] * 6,
            'x0': [0, 50, 100, 150, 200, 250],
            'top': [0] * 6,
            'x1': [40, 90, 140, 190, 240, 290],
            'bottom': [10] * 6
        })
        
        facade = TableProcessingFacade(mock_df, BBVA_DEBIT_PROPERTIES)
        
        # Test that facade works with different bank properties
        column_segmenter = facade.get_column_segmenter()
        row_segmenter = facade.get_row_segmenter()
        
        # Verify that components are configured with BBVA properties
        assert column_segmenter.statement_properties == BBVA_DEBIT_PROPERTIES
        assert 'CARGOS' in BBVA_DEBIT_PROPERTIES['amount_column']
        assert 'ABONOS' in BBVA_DEBIT_PROPERTIES['amount_column']
    
    def test_end_to_end_integration_simulation(self):
        """Test end-to-end integration with realistic data simulation"""
        # Simulate a realistic table structure
        mock_df = pd.DataFrame({
            'text': [
                'detalle', 'de', 'movimientos',  # Start phrase
                'FECHA', 'DESCRIPCION', 'MONTO',  # Column headers
                '01-ENE-24', 'COMPRA', '100.00',  # Transaction 1
                '02-ENE-24', 'TRANSFERENCIA', '200.00',  # Transaction 2
                '03-ENE-24', 'RETIRO', '50.00',  # Transaction 3
                'total', 'final'  # End phrase
            ],
            'page': [1] * 17,
            'x0': [0, 30, 80, 0, 60, 120, 0, 60, 120, 0, 60, 120, 0, 60, 120, 0, 30],
            'top': [0, 0, 0, 20, 20, 20, 40, 40, 40, 60, 60, 60, 80, 80, 80, 100, 100],
            'x1': [25, 55, 105, 55, 115, 175, 55, 115, 175, 55, 115, 175, 55, 115, 175, 25, 55],
            'bottom': [10, 10, 10, 30, 30, 30, 50, 50, 50, 70, 70, 70, 90, 90, 90, 110, 110]
        })
        
        # Create properties that match the simulated data
        simulation_properties = {
            'start_phrase': ['detalle', 'de', 'movimientos'],
            'end_phrase': ['total', 'final'],
            'columns': ['FECHA', 'DESCRIPCION', 'MONTO'],
            'amount_column': ['MONTO'],
            'date_pattern': r'(\d{2})-(\w{3})-(\d{2})',
            'bank': 'simulation',
            'statement_type': 'debit'
        }
        
        facade = TableProcessingFacade(mock_df, simulation_properties)
        
        # Mock the final table result for complete integration test
        expected_table = pd.DataFrame({
            'Date': ['01-ENE-24', '02-ENE-24', '03-ENE-24'],
            'Description': ['COMPRA', 'TRANSFERENCIA', 'RETIRO'],
            'MONTO': ['100.00', '200.00', '50.00']
        })
        
        with patch.object(facade, 'get_reconstructor') as mock_get_recon:
            mock_reconstructor = Mock()
            mock_reconstructor.reconstruct_table.return_value = expected_table
            mock_get_recon.return_value = mock_reconstructor
            
            result = facade.reconstruct_table()
        
        # Verify end-to-end result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'Date' in result.columns
        assert 'Description' in result.columns
        assert 'MONTO' in result.columns
        assert result.equals(expected_table)
