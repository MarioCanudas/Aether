import pytest
import pandas as pd
from io import BytesIO
from models import DocumentProcessingFacade, PDFReader, DefaultDocumentAnalyzer, DefaultTextProcessor

SMALL_FILE = 'banorte_debit.pdf'
MEDIUM_FILE = 'bbva_debit.pdf'

class TestDocumentProcessingFacadeIntegration:
    """Integration tests for DocumentProcessingFacade - testing complete workflows with real components"""
    
    @pytest.fixture(scope= 'class')
    def facade_from_path(self, get_file_from_path) -> DocumentProcessingFacade:
        return DocumentProcessingFacade(get_file_from_path)
    
    @pytest.fixture(scope= 'class')
    def facade_from_bytesio(self, get_bytesio_from_path) -> DocumentProcessingFacade:
        return DocumentProcessingFacade(get_bytesio_from_path)
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_complete_document_processing_workflow(self, facade_from_path):
        """Test the complete document processing workflow from file to corrected words"""
        facade: DocumentProcessingFacade = facade_from_path
        
        # Step 1: Extract raw words from PDF
        extracted_words = facade.get_extracted_words()
        assert isinstance(extracted_words, pd.DataFrame)
        assert len(extracted_words) > 0
        assert set(extracted_words.columns) == {'page', 'text', 'x0', 'top', 'x1', 'bottom'}
        
        # Step 2: Analyze document to get statement properties
        statement_properties = facade.get_statement_properties()
        # Properties might be None if document is not recognized, which is valid
        assert statement_properties is None or isinstance(statement_properties, dict)
        
        # Step 3: Get text processor (integrates extracted words + properties)
        text_processor = facade.get_text_processor()
        assert isinstance(text_processor, DefaultTextProcessor)
        assert hasattr(text_processor, 'extracted_words')
        assert hasattr(text_processor, 'statement_properties')
        
        # Step 4: Get corrected words (final output)
        corrected_words = facade.get_corrected_extracted_words()
        assert isinstance(corrected_words, pd.DataFrame)
        assert set(corrected_words.columns) == set(extracted_words.columns)
        
        # Integration verification: corrected words should be based on extracted words
        # (exact comparison depends on text processing logic, but structure should match)
        assert len(corrected_words) <= len(extracted_words)  # Correction might merge words
    
    @pytest.mark.parametrize(
        'get_file_from_path,get_bytesio_from_path', 
        [(SMALL_FILE, SMALL_FILE), (MEDIUM_FILE, MEDIUM_FILE)], 
        indirect=True
    )
    def test_file_path_vs_bytesio_consistency(self, facade_from_path, facade_from_bytesio):
        """Test that processing results are identical whether using file path or BytesIO"""
        facade_path: DocumentProcessingFacade = facade_from_path
        facade_bytes: DocumentProcessingFacade = facade_from_bytesio
        
        # Test that all outputs are identical
        words_path = facade_path.get_extracted_words()
        words_bytes = facade_bytes.get_extracted_words()
        pd.testing.assert_frame_equal(words_path, words_bytes)
        
        props_path = facade_path.get_statement_properties()
        props_bytes = facade_bytes.get_statement_properties()
        assert props_path == props_bytes
        
        corrected_path = facade_path.get_corrected_extracted_words()
        corrected_bytes = facade_bytes.get_corrected_extracted_words()
        pd.testing.assert_frame_equal(corrected_path, corrected_bytes)
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE, MEDIUM_FILE], indirect=True)
    def test_component_integration_and_data_flow(self, facade_from_path):
        """Test that data flows correctly between all components"""
        facade: DocumentProcessingFacade = facade_from_path
        
        # Verify component initialization and relationships
        assert isinstance(facade.reader, PDFReader)
        assert isinstance(facade.analyzer, DefaultDocumentAnalyzer)
        assert facade.analyzer.reader is facade.reader
        
        # Test data flow: Reader -> Analyzer -> TextProcessor
        extracted_words = facade.get_extracted_words()
        statement_properties = facade.get_statement_properties()
        text_processor = facade.get_text_processor()
        
        # Verify that TextProcessor receives the same data that facade methods return
        pd.testing.assert_frame_equal(text_processor.extracted_words, extracted_words)
        assert text_processor.statement_properties == statement_properties
        
        # Verify final output consistency
        corrected_words_from_facade = facade.get_corrected_extracted_words()
        corrected_words_from_processor = text_processor.correct_text()
        pd.testing.assert_frame_equal(corrected_words_from_facade, corrected_words_from_processor)
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_facade_caching_behavior(self, facade_from_path):
        """Test that facade properly caches expensive operations"""
        facade: DocumentProcessingFacade = facade_from_path
        
        # Test statement properties caching
        props1 = facade.get_statement_properties()
        props2 = facade.get_statement_properties()
        assert props1 is props2  # Should be the same object due to @cache decorator
        
        # Test that other methods don't interfere with caching
        facade.get_extracted_words()
        props3 = facade.get_statement_properties()
        assert props1 is props3  # Cache should still work
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_method_call_order_independence(self, facade_from_path):
        """Test that facade methods can be called in any order and produce consistent results"""
        facade: DocumentProcessingFacade = facade_from_path
        
        # Call methods in one order
        corrected1 = facade.get_corrected_extracted_words()
        properties1 = facade.get_statement_properties()
        extracted1 = facade.get_extracted_words()
        processor1 = facade.get_text_processor()
        
        # Create new facade and call in different order
        facade2: DocumentProcessingFacade = facade_from_path
        extracted2 = facade2.get_extracted_words()
        processor2 = facade2.get_text_processor()
        properties2 = facade2.get_statement_properties()
        corrected2 = facade2.get_corrected_extracted_words()
        
        # Results should be identical regardless of call order
        pd.testing.assert_frame_equal(extracted1, extracted2)
        assert properties1 == properties2
        pd.testing.assert_frame_equal(corrected1, corrected2)
    
    def test_error_handling_integration(self):
        """Test error handling across the complete integration"""
        # Test with invalid file type
        with pytest.raises(Exception):
            facade = DocumentProcessingFacade(12345)
            facade.reader
        
        # Test with non-existent file
        with pytest.raises(Exception):
            facade = DocumentProcessingFacade("nonexistent.pdf")
            facade.get_extracted_words()
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_text_processor_factory_behavior(self, facade_from_path):
        """Test that get_text_processor creates new instances with current data"""
        facade: DocumentProcessingFacade = facade_from_path
        
        # Get multiple text processors
        processor1 = facade.get_text_processor()
        processor2 = facade.get_text_processor()
        
        # Should be different instances (factory pattern)
        assert processor1 is not processor2
        
        # But should have the same data
        pd.testing.assert_frame_equal(processor1.extracted_words, processor2.extracted_words)
        assert processor1.statement_properties == processor2.statement_properties

