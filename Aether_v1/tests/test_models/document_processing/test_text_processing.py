import pandas as pd
from models import DefaultTextProcessor

# Propiedades de prueba para diferentes patrones de fecha
TEST_STATEMENT_PROPERTIES_NUMERIC = {
    'date_pattern': r'(\d{2})/(\d{2})',  # DD/MM format
    'bank': 'test_bank',
    'statement_type': 'debit'
}

TEST_STATEMENT_PROPERTIES_MONTH = {
    'date_pattern': r'(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)',  # DD MMM format
    'bank': 'test_bank',
    'statement_type': 'credit'
}

TEST_STATEMENT_PROPERTIES_COMPLEX = {
    'date_pattern': r'(\d{2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic) (20\d{2})',  # DD-mmm-YYYY format
    'bank': 'test_bank',
    'statement_type': 'credit'
}


class TestDefaultTextProcessorInitialization:
    """Test cases for DefaultTextProcessor initialization"""
    
    def test_init_with_dataframe_and_properties(self):
        """Test DefaultTextProcessor initialization with DataFrame and properties"""
        mock_df = pd.DataFrame({
            'text': ['test', 'data'],
            'page': [1, 1],
            'x0': [0, 50],
            'top': [0, 0],
            'x1': [40, 90],
            'bottom': [10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        
        assert processor.extracted_words.equals(mock_df)
        assert processor.statement_properties == TEST_STATEMENT_PROPERTIES_NUMERIC
        assert hasattr(processor, 'extracted_words')
        assert hasattr(processor, 'statement_properties')


class TestDefaultTextProcessorDateCorrection:
    """Test cases for date correction functionality"""
    
    def test_date_with_extra_text_separation(self):
        """Test separation of date with extra text attached"""
        mock_df = pd.DataFrame({
            'text': ['12/05COMPRA', 'TIENDA', 'WALMART'],
            'page': [1, 1, 1],
            'x0': [0, 80, 150],
            'top': [0, 0, 0],
            'x1': [70, 140, 200],
            'bottom': [10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # The date should be separated from the extra text
        assert result.iloc[0]['text'] == '12/05'
        assert 'COMPRA' in result.iloc[1]['text']
        assert 'TIENDA' in result.iloc[1]['text']
    
    def test_date_split_across_two_cells(self):
        """Test combining date that is split across two cells"""
        mock_df = pd.DataFrame({
            'text': ['12', 'ENE', 'COMPRA', 'WALMART'],
            'page': [1, 1, 1, 1],
            'x0': [0, 30, 80, 150],
            'top': [0, 0, 0, 0],
            'x1': [25, 55, 140, 200],
            'bottom': [10, 10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_MONTH)
        result = processor.correct_text()
        
        # The date parts should be combined
        assert result.iloc[0]['text'] == '12 ENE'
        # One row should be dropped (the second part of the date)
        assert len(result) == len(mock_df) - 1
    
    def test_date_split_across_three_cells(self):
        """Test combining date that is split across three cells"""
        mock_df = pd.DataFrame({
            'text': ['12', 'ene', '2023', 'COMPRA', 'WALMART'],
            'page': [1, 1, 1, 1, 1],
            'x0': [0, 30, 60, 120, 180],
            'top': [0, 0, 0, 0, 0],
            'x1': [25, 55, 85, 170, 230],
            'bottom': [10, 10, 10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_COMPLEX)
        result = processor.correct_text()
        
        # The date parts should be combined
        assert result.iloc[0]['text'] == '12 ene 2023'
        # Two rows should be dropped
        assert len(result) == len(mock_df) - 2
    
    def test_no_date_modification_when_no_match(self):
        """Test that non-date text is not modified"""
        mock_df = pd.DataFrame({
            'text': ['COMPRA', 'TIENDA', 'WALMART'],
            'page': [1, 1, 1],
            'x0': [0, 80, 150],
            'top': [0, 0, 0],
            'x1': [70, 140, 200],
            'bottom': [10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # DataFrame should remain unchanged
        pd.testing.assert_frame_equal(result.reset_index(drop=True), mock_df.reset_index(drop=True))


class TestDefaultTextProcessorAmountCorrection:
    """Test cases for amount correction functionality"""
    
    def test_combine_separated_plus_sign_with_amount(self):
        """Test combining separated plus sign with amount"""
        mock_df = pd.DataFrame({
            'text': ['DEPOSITO', '+', '$1,234.56', 'TRANSFERENCIA'],
            'page': [1, 1, 1, 1],
            'x0': [0, 80, 90, 160],
            'top': [0, 0, 0, 0],
            'x1': [70, 85, 150, 250],
            'bottom': [10, 10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        
        # One row should be dropped (the standalone plus sign)
        assert len(result) == len(mock_df) - 1
        # The plus sign should be combined with the amount
        assert result.iloc[1]['text'] == '+$1,234.56'
    
    def test_combine_separated_minus_sign_with_amount(self):
        """Test combining separated minus sign with amount"""
        mock_df = pd.DataFrame({
            'text': ['CARGO', '-', '500.00', 'COMISION'],
            'page': [1, 1, 1, 1],
            'x0': [0, 60, 70, 120],
            'top': [0, 0, 0, 0],
            'x1': [50, 65, 110, 180],
            'bottom': [10, 10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # One row should be dropped (the standalone minus sign)
        assert len(result) == len(mock_df) - 1
        # The minus sign should be combined with the amount
        assert result.iloc[1]['text'] == '-500.00'
    
    def test_no_sign_combination_when_not_adjacent(self):
        """Test that signs are not combined when not adjacent to amounts"""
        mock_df = pd.DataFrame({
            'text': ['+', 'DEPOSITO', '1,234.56', 'CONCEPTO'],
            'page': [1, 1, 1, 1],
            'x0': [0, 20, 80, 150],
            'top': [0, 0, 0, 0],
            'x1': [15, 70, 140, 210],
            'bottom': [10, 10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Should remain unchanged since the + is not before an amount
        pd.testing.assert_frame_equal(result.reset_index(drop=True), mock_df.reset_index(drop=True))
    
    def test_amount_without_dollar_sign(self):
        """Test handling amounts without dollar sign"""
        mock_df = pd.DataFrame({
            'text': ['CARGO', '-', '1,500.00', 'RETIRO'],
            'page': [1, 1, 1, 1],
            'x0': [0, 60, 70, 140],
            'top': [0, 0, 0, 0],
            'x1': [50, 65, 130, 180],
            'bottom': [10, 10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        
        assert len(result) == len(mock_df) - 1
        # The minus sign should be combined with the amount
        assert result.iloc[1]['text'] == '-1,500.00'


class TestDefaultTextProcessorComplexScenarios:
    """Test cases for complex scenarios combining multiple corrections"""
    
    def test_date_and_amount_corrections_together(self):
        """Test document with both date and amount corrections needed"""
        mock_df = pd.DataFrame({
            'text': ['15/03COMPRA', 'WALMART', '+', '$2,500.50', 'DEPOSITO'],
            'page': [1, 1, 1, 1, 1],
            'x0': [0, 100, 200, 210, 280],
            'top': [0, 0, 0, 0, 0],
            'x1': [90, 190, 205, 270, 340],
            'bottom': [10, 10, 10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Check date correction
        assert result.iloc[0]['text'] == '15/03'
        assert 'COMPRA' in result.iloc[1]['text']
        
        # Check amount correction
        amount_found = False
        for _, row in result.iterrows():
            if '+$2,500.50' in row['text']:
                amount_found = True
                break
        assert amount_found
    
    def test_multiple_dates_and_amounts_in_document(self):
        """Test document with multiple dates and amounts"""
        mock_df = pd.DataFrame({
            'text': ['12/01PAGO', 'TARJETA', '-', '100.00', '15/01DEPOSITO', 'BANCO', '+', '500.00'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 80, 150, 160, 0, 80, 150, 160],
            'top': [0, 0, 0, 0, 20, 20, 20, 20],
            'x1': [70, 140, 155, 210, 70, 140, 155, 210],
            'bottom': [10, 10, 10, 10, 30, 30, 30, 30]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Check that both dates are corrected
        dates_found = 0
        amounts_found = 0
        for _, row in result.iterrows():
            if row['text'] in ['12/01', '15/01']:
                dates_found += 1
            elif row['text'] in ['-100.00', '+500.00']:
                amounts_found += 1
        
        assert dates_found == 2
        assert amounts_found == 2


class TestDefaultTextProcessorEdgeCases:
    """Test cases for edge cases and error handling"""
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame(columns=['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        
        processor = DefaultTextProcessor(empty_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        assert len(result) == 0
        assert list(result.columns) == list(empty_df.columns)
    
    def test_single_row_dataframe(self):
        """Test handling of single-row DataFrame"""
        single_row_df = pd.DataFrame({
            'text': ['12/05'],
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [40],
            'bottom': [10]
        })
        
        processor = DefaultTextProcessor(single_row_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Should remain unchanged
        pd.testing.assert_frame_equal(result.reset_index(drop=True), single_row_df.reset_index(drop=True))
    
    def test_malformed_date_pattern(self):
        """Test handling of malformed date patterns"""
        mock_df = pd.DataFrame({
            'text': ['12/05/2023EXTRA', 'COMPRA', 'WALMART'],
            'page': [1, 1, 1],
            'x0': [0, 100, 150],
            'top': [0, 0, 0],
            'x1': [90, 140, 200],
            'bottom': [10, 10, 10]
        })
        
        # Use a pattern that won't match the malformed date
        malformed_properties = {
            'date_pattern': r'(\d{2})/(\d{2})$',  # Strict end match
            'bank': 'test',
            'statement_type': 'debit'
        }
        
        processor = DefaultTextProcessor(mock_df, malformed_properties)
        result = processor.correct_text()
        
        # Should remain unchanged since pattern doesn't match
        pd.testing.assert_frame_equal(result.reset_index(drop=True), mock_df.reset_index(drop=True))
    
    def test_invalid_amount_pattern(self):
        """Test handling of invalid amount patterns"""
        mock_df = pd.DataFrame({
            'text': ['+', 'invalid_amount', 'CONCEPTO'],
            'page': [1, 1, 1],
            'x0': [0, 20, 80],
            'top': [0, 0, 0],
            'x1': [15, 70, 140],
            'bottom': [10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Should remain unchanged since 'invalid_amount' doesn't match amount pattern
        pd.testing.assert_frame_equal(result.reset_index(drop=True), mock_df.reset_index(drop=True))
    
    def test_missing_next_text_handling(self):
        """Test handling when next_text is None (last row)"""
        mock_df = pd.DataFrame({
            'text': ['COMPRA', 'WALMART', '12/05FINAL'],
            'page': [1, 1, 1],
            'x0': [0, 80, 150],
            'top': [0, 0, 0],
            'x1': [70, 140, 210],
            'bottom': [10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # The last row should be processed correctly even without next_text
        assert result.iloc[-1]['text'] == '12/05'
    
    def test_index_out_of_bounds_protection(self):
        """Test protection against index out of bounds errors"""
        mock_df = pd.DataFrame({
            'text': ['$1,234.56'],  # Amount at the very end
            'page': [1],
            'x0': [0],
            'top': [0],
            'x1': [80],
            'bottom': [10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Should not crash and should remain unchanged
        pd.testing.assert_frame_equal(result.reset_index(drop=True), mock_df.reset_index(drop=True))


class TestDefaultTextProcessorCaching:
    """Test cases for caching functionality"""
    
    def test_correct_text_caching(self):
        """Test that correct_text method caches results"""
        mock_df = pd.DataFrame({
            'text': ['12/05COMPRA', 'TIENDA'],
            'page': [1, 1],
            'x0': [0, 80],
            'top': [0, 0],
            'x1': [70, 140],
            'bottom': [10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        
        # First call
        result1 = processor.correct_text()
        # Second call
        result2 = processor.correct_text()
        
        # Should be the same object due to caching
        assert result1 is result2
        pd.testing.assert_frame_equal(result1, result2)


class TestDefaultTextProcessorCoordinateUpdates:
    """Test cases for coordinate updates when combining cells"""
    
    def test_coordinate_update_on_date_combination(self):
        """Test that coordinates are updated when combining date parts"""
        mock_df = pd.DataFrame({
            'text': ['12', 'ENE', 'COMPRA'],
            'page': [1, 1, 1],
            'x0': [0, 30, 80],
            'top': [0, 0, 0],
            'x1': [25, 55, 140],
            'bottom': [10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_MONTH)
        result = processor.correct_text()
        
        # The combined date should have updated x1 coordinate
        combined_date_row = result.iloc[0]
        assert combined_date_row['text'] == '12 ENE'
        assert combined_date_row['x1'] == 55  # Should be x1 of the second part
    
    def test_coordinate_preservation_on_amount_combination(self):
        """Test coordinate preservation when combining amounts with signs"""
        mock_df = pd.DataFrame({
            'text': ['DEPOSITO', '+', '$1,000.00'],
            'page': [1, 1, 1],
            'x0': [0, 80, 90],
            'top': [0, 0, 0],
            'x1': [70, 85, 160],
            'bottom': [10, 10, 10]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Find the combined amount
        amount_row = None
        for _, row in result.iterrows():
            if row['text'] == '+$1,000.00':
                amount_row = row
                break
        
        assert amount_row is not None
        # Coordinates should be from the original amount cell
        assert amount_row['x0'] == 90
        assert amount_row['x1'] == 160


class TestDefaultTextProcessorRealScenarios:
    """Test cases simulating real-world PDF extraction scenarios"""
    
    def test_bank_statement_row_simulation(self):
        """Test processing a typical bank statement row"""
        # Simulate a row from a real bank statement
        mock_df = pd.DataFrame({
            'text': ['15/03COMPRA', 'POS', 'WALMART', 'MEXICO', '+', '$2,547.89'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 100, 150, 220, 300, 310],
            'top': [0, 0, 0, 0, 0, 0],
            'x1': [90, 140, 210, 290, 305, 380],
            'bottom': [12, 12, 12, 12, 12, 12]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Verify date separation
        assert result.iloc[0]['text'] == '15/03'
        # Verify amount combination
        amount_combined = any('+$2,547.89' in row['text'] for _, row in result.iterrows())
        assert amount_combined
        # Verify description preservation
        description_words = ['COMPRA', 'POS', 'WALMART', 'MEXICO']
        for word in description_words:
            word_found = any(word in row['text'] for _, row in result.iterrows())
            assert word_found
    
    def test_multiple_transaction_rows(self):
        """Test processing multiple transaction rows"""
        mock_df = pd.DataFrame({
            'text': ['12/01PAGO', 'TARJETA', '-', '150.00', '13/01DEPOSITO', 'NOMINA', '+', '5,000.00'],
            'page': [1, 1, 1, 1, 1, 1, 1, 1],
            'x0': [0, 100, 200, 210, 0, 100, 200, 210],
            'top': [0, 0, 0, 0, 15, 15, 15, 15],
            'x1': [90, 190, 205, 270, 90, 190, 205, 280],
            'bottom': [12, 12, 12, 12, 27, 27, 27, 27]
        })
        
        processor = DefaultTextProcessor(mock_df, TEST_STATEMENT_PROPERTIES_NUMERIC)
        result = processor.correct_text()
        
        # Should have processed both transactions correctly
        dates_found = sum(1 for _, row in result.iterrows() if row['text'] in ['12/01', '13/01'])
        amounts_found = sum(1 for _, row in result.iterrows() if row['text'] in ['-150.00', '+5,000.00'])
        
        assert dates_found == 2
        assert amounts_found == 2
