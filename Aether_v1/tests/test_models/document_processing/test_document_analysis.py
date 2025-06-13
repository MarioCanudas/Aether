import pytest
import pandas as pd
from unittest.mock import Mock, patch
from models import DefaultDocumentAnalyzer, PDFReader

SMALL_FILE = 'banorte_debit.pdf'
MEDIUM_FILE = 'bbva_debit.pdf'
OLD_CREDIT_FILE = 'banorte_credit_old.pdf'
NEW_CREDIT_FILE = 'banorte_credit_new.pdf'

TEST_BANKS = ['banorte', 'bbva']
TEST_BANK_CODES = {
    '072': 'banorte',
    '012': 'bbva',
}

class TestDefaultDocumentAnalyzerInitialization:
    """Test cases for DefaultDocumentAnalyzer initialization"""
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_init_with_reader(self, get_file_from_path):
        """Test DefaultDocumentAnalyzer initialization with PDFReader"""
        file_path = get_file_from_path
        reader = PDFReader(file_path)
        analyzer = DefaultDocumentAnalyzer(reader)
        
        assert analyzer.reader == reader, "Reader is not the same as the input file"
        assert hasattr(analyzer, 'reader'), "Reader is not a valid attribute"

class TestDocumentAnalyzerBankDetectionInFooter:
    """Test cases for bank detection in footer"""
    
    def test_detect_bank_in_footer_with_mock_data(self):
        """Test footer bank detection with mocked data"""
        # Create mock reader
        mock_reader = Mock()
        
        # Mock extracted words with footer data
        mock_df = pd.DataFrame({
            'text': ['some', 'text', 'bbva', 'bancomer', 'footer', 'info'],
            'bottom': [100, 200, 850, 860, 870, 880],  # Last items in footer
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0, 0],
            'top': [50, 150, 800, 810, 820, 830],
            'x1': [50, 50, 50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        mock_reader.get_height.return_value = 900  # Document height
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        # Change the BANKS list to the TEST_BANKS list during the test
        with patch('models.document_processing.document_analysis.BANKS', TEST_BANKS):
            result = analyzer.detect_bank_in_footer()
            assert result == 'bbva', "Bank is not detected correctly"
    
    def test_detect_bank_in_footer_no_bank_found(self):
        """Test footer bank detection when no bank is found"""
        mock_reader = Mock()
        
        # Mock extracted words without bank names in footer
        mock_df = pd.DataFrame({
            'text': ['some', 'random', 'text', 'without', 'bank', 'names'],
            'bottom': [100, 200, 300, 850, 860, 870],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0, 0],
            'top': [50, 150, 250, 800, 810, 820],
            'x1': [50, 50, 50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        mock_reader.get_height.return_value = 900
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        # Change the BANKS list to the TEST_BANKS list during the test
        with patch('models.document_processing.document_analysis.BANKS', TEST_BANKS):
            # Change the search_phrase_in_df function to return False during the test
            with patch('models.document_processing.document_analysis.search_phrase_in_df', return_value=False):
                result = analyzer.detect_bank_in_footer()
                assert result is None, "Bank is detected incorrectly"
    
    def test_detect_bank_in_footer_nu_special_case(self):
        """Test Nu bank special case detection"""
        mock_reader = Mock()
        
        # Mock extracted words without footer but with Nu special phrase
        mock_df = pd.DataFrame({
            'text': ['nu', 'méxico', 'financiera,', 'some', 'other', 'text'],
            'bottom': [100, 110, 120, 200, 300, 400],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0, 0],
            'top': [50, 60, 70, 150, 250, 350],
            'x1': [50, 50, 50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        mock_reader.get_height.return_value = 900
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        # Change the BANKS list to the TEST_BANKS list during the test
        with patch('models.document_processing.document_analysis.BANKS', TEST_BANKS):
            # Change the search_phrase_in_df function to return True during the test
            with patch('models.document_processing.document_analysis.search_phrase_in_df', return_value=True):
                result = analyzer.detect_bank_in_footer()
                assert result == 'nu', "Bank is not detected correctly"

class TestDocumentAnalyzerBankDetectionByCode:
    """Test cases for bank detection by CLABE code"""
    
    def test_detect_bank_by_code_found(self):
        """Test bank detection by CLABE code when found"""
        mock_reader = Mock()
        
        # Mock extracted words with CLABE information
        mock_df = pd.DataFrame({
            'text': ['some', 'text', 'clabe', '012180001234567890', 'more', 'text'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0, 0],
            'top': [50, 60, 70, 80, 90, 100],
            'bottom': [60, 70, 80, 90, 100, 110],
            'x1': [50, 50, 50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        # Change the BANKS_CODES dictionary to the TEST_BANK_CODES dictionary during the test
        with patch('models.document_processing.document_analysis.BANKS_CODES', TEST_BANK_CODES):
            result = analyzer.detect_bank_by_code()
            assert result == 'bbva', "Bank is not detected correctly"
    
    def test_detect_bank_by_code_not_found(self):
        """Test bank detection by CLABE code when not found"""
        mock_reader = Mock()
        
        # Mock extracted words without CLABE information
        mock_df = pd.DataFrame({
            'text': ['some', 'text', 'without', 'clabe', 'information'],
            'page': [1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0],
            'top': [50, 60, 70, 80, 90],
            'bottom': [60, 70, 80, 90, 100],
            'x1': [50, 50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        result = analyzer.detect_bank_by_code()
        assert result is None, "Bank is detected incorrectly"
    
    def test_detect_bank_by_code_invalid_code(self):
        """Test bank detection with invalid bank code"""
        mock_reader = Mock()
        
        # Mock extracted words with invalid CLABE code
        mock_df = pd.DataFrame({
            'text': ['some', 'text', 'clabe', '999180001234567890', 'more', 'text'],
            'page': [1, 1, 1, 1, 1, 1],
            'x0': [0, 0, 0, 0, 0, 0],
            'top': [50, 60, 70, 80, 90, 100],
            'bottom': [60, 70, 80, 90, 100, 110],
            'x1': [50, 50, 50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch('models.document_processing.document_analysis.BANKS_CODES', TEST_BANK_CODES):
            result = analyzer.detect_bank_by_code()
            assert result is None, "Bank is detected incorrectly"


class TestDocumentAnalyzerBankDetection:
    """Test cases for the main bank detection method"""
    
    def test_detect_bank_by_code_first(self):
        """Test that detect_bank tries code detection first"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        # Mock that code detection finds a bank
        with patch.object(analyzer, 'detect_bank_by_code', return_value= 'bbva') as mock_code:
            with patch.object(analyzer, 'detect_bank_in_footer', return_value= 'banorte') as mock_footer:
                result = analyzer.detect_bank()
                
                assert result == 'bbva', "Bank is not detected correctly"
                mock_code.assert_called_once()
                mock_footer.assert_not_called()
    
    def test_detect_bank_fallback_to_footer(self):
        """Test that detect_bank falls back to footer detection"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        # Mock that code detection fails but footer detection succeeds
        with patch.object(analyzer, 'detect_bank_by_code', return_value= None) as mock_code:
            with patch.object(analyzer, 'detect_bank_in_footer', return_value= 'banorte') as mock_footer:
                result = analyzer.detect_bank()
                
                assert result == 'banorte', "Bank is not detected correctly"
                mock_code.assert_called_once()
                mock_footer.assert_called_once()
    
    def test_detect_bank_caching(self):
        """Test that detect_bank method caches results"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch.object(analyzer, 'detect_bank_by_code', return_value='bbva') as mock_code:
            # First call
            result1 = analyzer.detect_bank()
            # Second call
            result2 = analyzer.detect_bank()
            
            assert result1 == result2 == 'bbva', "Bank is not cached correctly"
            # Should only be called once due to caching
            mock_code.assert_called_once()


class TestDocumentAnalyzerStatementType:
    """Test cases for statement type detection"""
    
    def test_detect_statement_type_credit(self):
        """Test credit statement type detection"""
        mock_reader = Mock()
        
        # Mock extracted words with credit phrase
        mock_df = pd.DataFrame({
            'text': ['límite', 'de', 'crédito:', '50000'],
            'page': [1, 1, 1, 1],
            'x0': [0, 0, 0, 0],
            'top': [50, 60, 70, 80],
            'bottom': [60, 70, 80, 90],
            'x1': [50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        result = analyzer.detect_statement_type()
        assert result == 'credit', "Statement type is not detected correctly"
    
    def test_detect_statement_type_debit(self):
        """Test debit statement type detection (default case)"""
        mock_reader = Mock()
        
        # Mock extracted words without credit phrase
        mock_df = pd.DataFrame({
            'text': ['saldo', 'anterior', '1000', 'movimientos'],
            'page': [1, 1, 1, 1],
            'x0': [0, 0, 0, 0],
            'top': [50, 60, 70, 80],
            'bottom': [60, 70, 80, 90],
            'x1': [50, 50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        result = analyzer.detect_statement_type()
        assert result == 'debit', "Statement type is not detected correctly"
    
    def test_detect_statement_type_caching(self):
        """Test that detect_statement_type method caches results"""
        mock_reader = Mock()
        mock_reader.extract_words.return_value = pd.DataFrame({
            'text': ['test'],
            'page': [1],
            'x0': [0],
            'top': [50],
            'bottom': [60],
            'x1': [50]
        })
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch('models.document_processing.document_analysis.search_phrase_in_df', return_value=False) as mock_search:
            # First call
            result1 = analyzer.detect_statement_type()
            # Second call
            result2 = analyzer.detect_statement_type()
            
            assert result1 == result2 == 'debit', "Statement type is not cached correctly"
            # Should only be called once due to caching
            mock_search.assert_called_once()


class TestDocumentAnalyzerNewCreditFormat:
    """Test cases for new credit format detection"""
    
    def test_is_new_credit_format_true(self):
        """Test new credit format detection when both phrases are found"""
        mock_reader = Mock()
        old_format_words = pd.DataFrame(
            {
                'text': ['cargos', 'abonos', 'compra', '500', 'pago', '200', 'total', 'gastos', 'extra1', 'extra2', 'extra3'],
                'page': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                'x0': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'top': [50, 60, 65, 66, 67, 68, 70, 80, 81, 82, 83],
                'bottom': [60, 70, 66, 67, 68, 69, 80, 90, 91, 92, 93],
                'x1': [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
            }
        )
        mock_reader.extract_words.return_value = old_format_words
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        # Mock statement properties
        mock_properties = {
            'start_phrase': ['cargos', 'abonos'],
            'end_phrase': ['total', 'gastos']
        }
        
        with patch.object(analyzer, 'detect_statement_type', return_value='credit'):
            result = analyzer.is_new_credit_format(mock_properties)
            assert result is False, "New credit format is not detected correctly"
    
    def test_is_new_credit_format_false_debit(self):
        """Test new credit format detection returns False for debit statements"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        mock_properties = {
            'start_phrase': ['cargos,', 'abonos'],
            'end_phrase': ['total', 'cargos']
        }
        
        with patch.object(analyzer, 'detect_statement_type', return_value='debit'):
            result = analyzer.is_new_credit_format(mock_properties)
            assert result is False
    
    def test_is_new_credit_format_false_missing_phrases(self):
        """Test new credit format detection when phrases are not found"""
        mock_reader = Mock()
        new_format_words = pd.DataFrame(
            {
                'text': ['X,', 'Y', 'compra', '500', 'pago', '200', 'Z', 'W'],
                'page': [1, 1, 1, 1, 1, 1, 1, 1],
                'x0': [0, 0, 0, 0, 0, 0, 0, 0],
                'top': [50, 60, 65, 66, 67, 68, 70, 80],
                'bottom': [60, 70, 66, 67, 68, 69, 80, 90],
                'x1': [50, 50, 50, 50, 50, 50, 50, 50]
            }
        )
        mock_reader.extract_words.return_value = new_format_words
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        mock_properties = {
            'start_phrase': ['cargos,', 'abonos'],
            'end_phrase': ['total', 'cargos']
        }
        
        with patch.object(analyzer, 'detect_statement_type', return_value='credit'):
            result = analyzer.is_new_credit_format(mock_properties)
            assert result is True

class TestDocumentAnalyzerStatementProperties:
    """Test cases for getting statement properties"""
    
    def test_get_statement_properties_nu_debit(self):
        """Test getting statement properties for Nu debit"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch.object(analyzer, 'detect_bank', return_value='nu'):
            with patch.object(analyzer, 'detect_statement_type', return_value='debit'):
                result = analyzer.get_statement_properties()
                
                try:
                    assert result['bank'] == 'nu', "Bank is not detected correctly"
                    assert result['statement_type'] == 'debit', "Statement type is not detected correctly"
                    assert result['new_format'] == None, "New format is not detected correctly"
                except KeyError:
                    pytest.fail("Bank is not detected correctly")
    
    def test_get_statement_properties_bbva_credit_old_format(self):
        """Test getting statement properties for BBVA credit old format"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch.object(analyzer, 'detect_bank', return_value='bbva'):
            with patch.object(analyzer, 'detect_statement_type', return_value='credit'):
                with patch.object(analyzer, 'is_new_credit_format', return_value=False):
                    result = analyzer.get_statement_properties()
                    
                    try:
                        assert result['bank'] == 'bbva', "Bank is not detected correctly"
                        assert result['statement_type'] == 'credit', "Statement type is not detected correctly"
                        assert result['new_format'] == False, "New format is not detected correctly"
                    except KeyError:
                        pytest.fail("Bank is not detected correctly")
    
    def test_get_statement_properties_bbva_credit_new_format(self):
        """Test getting statement properties for BBVA credit new format"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        mock_bbva_new_props = {'bank': 'bbva', 'format': 'new'}
        
        with patch.object(analyzer, 'detect_bank', return_value='bbva'):
            with patch.object(analyzer, 'detect_statement_type', return_value='credit'):
                with patch.object(analyzer, 'is_new_credit_format', return_value=True):
                    result = analyzer.get_statement_properties()
                    
                    try:
                        assert result['bank'] == 'bbva', "Bank is not detected correctly"
                        assert result['statement_type'] == 'credit', "Statement type is not detected correctly"
                        assert result['new_format'] == True, "New format is not detected correctly"
                    except KeyError:
                        pytest.fail("Bank is not detected correctly")
    
    def test_get_statement_properties_unknown_combination(self):
        """Test getting statement properties for unknown bank/type combination"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch.object(analyzer, 'detect_bank', return_value='unknown_bank'):
            with patch.object(analyzer, 'detect_statement_type', return_value='debit'):
                result = analyzer.get_statement_properties()
                assert result is None
    
    def test_get_statement_properties_caching(self):
        """Test that get_statement_properties method caches results"""
        mock_reader = Mock()
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch.object(analyzer, 'detect_bank', return_value='nu') as mock_bank:
            with patch.object(analyzer, 'detect_statement_type', return_value='debit') as mock_type:
                with patch('models.document_processing.document_analysis.NU_DEBIT_PROPERTIES', {'bank': 'nu'}):
                    # First call
                    result1 = analyzer.get_statement_properties()
                    # Second call
                    result2 = analyzer.get_statement_properties()
                    
                    assert result1 == result2
                    # Should only be called once due to caching
                    mock_bank.assert_called_once()
                    mock_type.assert_called_once()


class TestDocumentAnalyzerErrorHandling:
    """Test cases for error handling"""
    
    def test_detect_bank_in_footer_empty_dataframe(self):
        """Test footer detection with empty DataFrame"""
        mock_reader = Mock()
        mock_reader.extract_words.return_value = pd.DataFrame(columns= ['text', 'page', 'x0', 'top', 'x1', 'bottom'])
        mock_reader.get_height.return_value = 900
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch('models.document_processing.document_analysis.BANKS', TEST_BANKS):
            with patch('models.document_processing.document_analysis.search_phrase_in_df', return_value=False):
                result = analyzer.detect_bank_in_footer()
                assert result is None
    
    def test_detect_bank_by_code_malformed_data(self):
        """Test CLABE detection with malformed data"""
        mock_reader = Mock()
        
        # Mock extracted words with malformed CLABE
        mock_df = pd.DataFrame({
            'text': ['clabe', 'abc123xyz', 'invalid'],
            'page': [1, 1, 1],
            'x0': [0, 0, 0],
            'top': [50, 60, 70],
            'bottom': [60, 70, 80],
            'x1': [50, 50, 50]
        })
        
        mock_reader.extract_words.return_value = mock_df
        
        analyzer = DefaultDocumentAnalyzer(mock_reader)
        
        with patch('models.document_processing.document_analysis.BANKS_CODES', TEST_BANK_CODES):
            result = analyzer.detect_bank_by_code()
            assert result is None


class TestDocumentAnalyzerRealFileScenarios:
    """Test cases using real file scenarios"""
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_real_file_basic_functionality(self, get_file_from_path):
        """Test analyzer with real file - basic functionality"""
        file_path = get_file_from_path
        reader = PDFReader(file_path)
        analyzer = DefaultDocumentAnalyzer(reader)
        
        try:
            # Test basic methods
            bank = analyzer.detect_bank()
            statement_type = analyzer.detect_statement_type()
            properties = analyzer.get_statement_properties()
            
            # Verify results are reasonable
            if bank is not None:
                assert bank in TEST_BANKS
            
            assert statement_type in ['debit', 'credit']
            
            if properties is not None:
                assert isinstance(properties, dict)
                
        except Exception as e:
            pytest.fail(f"Failed to analyze {file_path}: {str(e)}")
    
    @pytest.mark.parametrize('get_file_from_path', [OLD_CREDIT_FILE, NEW_CREDIT_FILE], indirect=True)
    def test_real_file_credit_detection(self, get_file_from_path):
        """Test analyzer with real credit file"""
        file_path = get_file_from_path
        reader = PDFReader(file_path)
        analyzer = DefaultDocumentAnalyzer(reader)
        
        try:
            properties = analyzer.get_statement_properties()
            
            assert properties['bank'] == 'banorte', "Bank is not detected correctly"
            assert properties['statement_type'] == 'credit', "Statement type is not detected correctly"
            
            if 'old' in file_path:
                assert properties['new_format'] == False
            else:
                assert properties['new_format'] == True
                
        except Exception as e:
            pytest.fail(f"Failed to analyze credit file {file_path}: {str(e)}")
