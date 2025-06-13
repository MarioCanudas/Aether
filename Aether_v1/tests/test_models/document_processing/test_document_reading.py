from io import BytesIO
import pytest
import pandas as pd
from models import PDFReader

# Archivos específicos para diferentes tipos de pruebas
SMALL_FILE = 'nu_debit.pdf'
MEDIUM_FILE = 'bbva_debit.pdf'

class TestPDFReaderInitialization:
    """Test cases for PDFReader initialization"""
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_init_with_path(self, get_file_from_path):
        """Test PDFReader initialization with file path"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        assert pdf_reader.file == file_path, "File is not the same as the file path"
    
    @pytest.mark.parametrize('get_bytesio_from_path', [SMALL_FILE], indirect=True)
    def test_init_with_bytesio(self, get_bytesio_from_path):
        """Test PDFReader initialization with BytesIO object"""
        bytes_io = get_bytesio_from_path
        pdf_reader = PDFReader(bytes_io)
        assert isinstance(pdf_reader.file, BytesIO), "File is not a BytesIO object"
        assert pdf_reader.file == bytes_io, "File is not the same as the BytesIO object"

class TestPDFReaderValidation:
    """Test cases for file validation methods"""
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_is_path_with_valid_pdf_path(self, get_file_from_path):
        """Test _is_path method with valid PDF path"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        assert pdf_reader._is_path() is True, "Valid PDF path is not a path"
    
    def test_is_path_with_invalid_path(self):
        """Test _is_path method with invalid path"""
        pdf_reader = PDFReader("invalid_file.txt")
        assert pdf_reader._is_path() is False, "Invalid path is not a path"
    
    @pytest.mark.parametrize('get_bytesio_from_path', [SMALL_FILE], indirect=True)
    def test_is_bytes_io_with_bytesio(self, get_bytesio_from_path):
        """Test _is_bytes_io method with BytesIO object"""
        bytes_io = get_bytesio_from_path
        pdf_reader = PDFReader(bytes_io)
        assert pdf_reader._is_bytes_io() is True, "BytesIO object is not a BytesIO object"
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_is_bytes_io_with_path(self, get_file_from_path):
        """Test _is_bytes_io method with file path"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        assert pdf_reader._is_bytes_io() is False, "File path is not a BytesIO object"
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_get_valid_file_with_path(self, get_file_from_path):
        """Test get_valid_file method with valid PDF path"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        result = pdf_reader.get_valid_file()
        assert result == file_path, "Result is not the same as the file path"
    
    @pytest.mark.parametrize('get_bytesio_from_path', [SMALL_FILE], indirect=True)
    def test_get_valid_file_with_bytesio(self, get_bytesio_from_path):
        """Test get_valid_file method with BytesIO object"""
        bytes_io = get_bytesio_from_path
        pdf_reader = PDFReader(bytes_io)
        result = pdf_reader.get_valid_file()
        assert isinstance(result, BytesIO), "Result is not a BytesIO object"
    
    def test_get_valid_file_with_invalid_type(self):
        """Test get_valid_file method with invalid file type"""
        pdf_reader = PDFReader(12345)  # Invalid type
        with pytest.raises(ValueError, match="Invalid file type"):
            pdf_reader.get_valid_file()


class TestPDFReaderMetadata:
    """Test cases for PDF metadata extraction"""
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_get_height_with_path(self, get_file_from_path):
        """Test get_height method with file path"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        height = pdf_reader.get_height()
        assert isinstance(height, (int, float)), "Height is not a number"
        assert height > 0, "Height is not positive"
    
    @pytest.mark.parametrize('get_bytesio_from_path', [SMALL_FILE], indirect=True)
    def test_get_height_with_bytesio(self, get_bytesio_from_path):
        """Test get_height method with BytesIO object"""
        bytes_io = get_bytesio_from_path
        pdf_reader = PDFReader(bytes_io)
        height = pdf_reader.get_height()
        assert isinstance(height, (int, float)), "Height is not a number"
        assert height > 0, "Height is not positive"
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_get_width_with_path(self, get_file_from_path):
        """Test get_width method with file path"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        width = pdf_reader.get_width()
        assert isinstance(width, (int, float)), "Width is not a number"
        assert width > 0, "Width is not positive"
    
    @pytest.mark.parametrize('get_bytesio_from_path', [SMALL_FILE], indirect=True)
    def test_get_width_with_bytesio(self, get_bytesio_from_path):
        """Test get_width method with BytesIO object"""
        bytes_io = get_bytesio_from_path
        pdf_reader = PDFReader(bytes_io)
        width = pdf_reader.get_width()
        assert isinstance(width, (int, float)), "Width is not a number"
        assert width > 0, "Width is not positive"
    
    @pytest.mark.parametrize(
        'get_file_from_path,get_bytesio_from_path', 
        [(SMALL_FILE, SMALL_FILE), (MEDIUM_FILE, MEDIUM_FILE)], 
        indirect=True
    )
    def test_metadata_consistency(self, get_file_from_path, get_bytesio_from_path):
        """Test that metadata is consistent between path and BytesIO initialization"""
        file_path = get_file_from_path
        bytes_io = get_bytesio_from_path
        
        # Initialize with path
        pdf_reader_path = PDFReader(file_path)
        height_path = pdf_reader_path.get_height()
        width_path = pdf_reader_path.get_width()
        
        # Initialize with BytesIO
        pdf_reader_bytes = PDFReader(bytes_io)
        height_bytes = pdf_reader_bytes.get_height()
        width_bytes = pdf_reader_bytes.get_width()
        
        # Should be the same
        assert height_path == height_bytes, "Height is not the same for path and BytesIO"
        assert width_path == width_bytes, "Width is not the same for path and BytesIO"

class TestPDFReaderWordExtraction:
    """Test cases for word extraction functionality"""
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_extract_words_basic(self, get_file_from_path):
        """Test basic word extraction functionality"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        words_df = pdf_reader.extract_words()
        
        # Verify it returns a DataFrame
        assert isinstance(words_df, pd.DataFrame), "Words DataFrame is not a pandas DataFrame"
        
        # Verify expected columns are present
        expected_columns = {'page', 'text', 'x0', 'top', 'x1', 'bottom'}
        assert set(words_df.columns) == expected_columns, "Expected columns are not present"
        
        # Verify DataFrame is not empty (assuming our test files have content)
        assert len(words_df) > 0, "Words DataFrame is empty"
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_extract_words_data_types(self, get_file_from_path):
        """Test that extracted words have correct data types"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        words_df = pdf_reader.extract_words()
        
        # Check data types
        assert words_df['page'].dtype in ['int64', 'int32'], "Page column is not an integer"
        assert words_df['text'].dtype == 'object', "Text column is not a string"
        assert words_df['x0'].dtype in ['float64', 'int64'], "X0 column is not a number"
        assert words_df['top'].dtype in ['float64', 'int64'], "Top column is not a number"
        assert words_df['x1'].dtype in ['float64', 'int64'], "X1 column is not a number"
        assert words_df['bottom'].dtype in ['float64', 'int64'], "Bottom column is not a number"
        
        # Check that page numbers start from 1
        assert words_df['page'].min() >= 1, "Page numbers do not start from 1"
        
        # Check coordinate consistency (x1 >= x0, bottom >= top)
        assert (words_df['x1'] >= words_df['x0']).all(), "X1 is not greater than X0"
        assert (words_df['bottom'] >= words_df['top']).all(), "Bottom is not greater than Top"
    
    @pytest.mark.parametrize('get_bytesio_from_path', [SMALL_FILE], indirect=True)
    def test_extract_words_with_bytesio(self, get_bytesio_from_path):
        """Test word extraction with BytesIO object"""
        bytes_io = get_bytesio_from_path
        pdf_reader = PDFReader(bytes_io)
        words_df = pdf_reader.extract_words()
        
        assert isinstance(words_df, pd.DataFrame), "Words DataFrame is not a pandas DataFrame"
        assert len(words_df) > 0, "Words DataFrame is empty"
        assert set(words_df.columns) == {'page', 'text', 'x0', 'top', 'x1', 'bottom'}, "Expected columns are not present"
    
    @pytest.mark.parametrize('get_file_from_path', [SMALL_FILE], indirect=True)
    def test_extract_words_caching(self, get_file_from_path):
        """Test that extract_words method caches results"""
        file_path = get_file_from_path
        pdf_reader = PDFReader(file_path)
        
        # First call
        words_df1 = pdf_reader.extract_words()
        
        # Second call - should return cached result
        words_df2 = pdf_reader.extract_words()
        
        # Should be the same object due to caching
        assert words_df1 is words_df2, "Words DataFrame is not the same object"
        pd.testing.assert_frame_equal(words_df1, words_df2, "Words DataFrame is not the same")
    
    @pytest.mark.parametrize(
        'get_file_from_path,get_bytesio_from_path', 
        [(SMALL_FILE, SMALL_FILE), (MEDIUM_FILE, MEDIUM_FILE)], 
        indirect=True
    )
    def test_extract_words_consistency(self, get_file_from_path, get_bytesio_from_path):
        """Test that word extraction is consistent between path and BytesIO"""
        file_path = get_file_from_path
        
        # Extract with path
        pdf_reader_path = PDFReader(file_path)
        words_path = pdf_reader_path.extract_words()
        
        # Extract with BytesIO
        bytes_io = get_bytesio_from_path
        pdf_reader_bytes = PDFReader(bytes_io)
        words_bytes = pdf_reader_bytes.extract_words()
        
        # Should be identical
        pd.testing.assert_frame_equal(words_path, words_bytes)

class TestPDFReaderErrorHandling:
    """Test cases for error handling"""
    
    def test_nonexistent_file(self):
        """Test behavior with non-existent file path"""
        pdf_reader = PDFReader("nonexistent_file.pdf")
        
        with pytest.raises(Exception):  # Should raise FileNotFoundError or similar
            pdf_reader.get_height()
        
        with pytest.raises(Exception):
            pdf_reader.get_width()
        
        with pytest.raises(Exception):
            pdf_reader.extract_words()
    
    def test_corrupted_bytesio(self):
        """Test behavior with corrupted BytesIO data"""
        corrupted_bytes = BytesIO(b"This is not a PDF file")
        pdf_reader = PDFReader(corrupted_bytes)
        
        with pytest.raises(Exception):  # Should raise pdfplumber error
            pdf_reader.get_height()
        
        with pytest.raises(Exception):
            pdf_reader.get_width()
        
        with pytest.raises(Exception):
            pdf_reader.extract_words()

