import pytest
import os
import pandas as pd
from new_model.document_reader import PDFReader

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

@pytest.fixture
def pdf_reader_instance(test_data_input_dir, request):
    """Creates a PDFReader instance for a given file path."""
    file_path = request.param
    pdf_path = os.path.join(test_data_input_dir, file_path)
    
    try:
        reader = PDFReader(pdf_path)    

        yield reader, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize PDFReader for {pdf_path}: {str(e)}")

# Parametrize each test function individually using the fixture indirectly
# The 'indirect=True' tells pytest to pass the parameters to the fixture first
@pytest.mark.parametrize('pdf_reader_instance', BANK_FILES, indirect=True)
def test_pdf_reader_init(pdf_reader_instance):
    """Tests if the PDFReader initializes with the correct path."""
    reader, pdf_path = pdf_reader_instance # Unpack the fixture result
    assert reader.file_path == pdf_path, f"PDF path mismatch: {reader.file_path} != {pdf_path}"

@pytest.mark.parametrize('pdf_reader_instance', BANK_FILES, indirect=True)
def test_get_height(pdf_reader_instance):
    """Tests getting the height of the PDF."""
    reader, pdf_path = pdf_reader_instance
    try:
        height = reader.get_height()
        assert isinstance(height, (float, int)), f"Height should be a number, got {type(height)} for {pdf_path}"
        assert height > 0, f"Height should be positive, got {height} for {pdf_path}"
    except Exception as e:
        pytest.fail(f"Failed to get height for {pdf_path}: {str(e)}")

@pytest.mark.parametrize('pdf_reader_instance', BANK_FILES, indirect=True)
def test_get_width(pdf_reader_instance):
    """Tests getting the width of the PDF."""
    reader, pdf_path = pdf_reader_instance
    try:
        width = reader.get_width()
        assert isinstance(width, (float, int)), f"Width should be a number, got {type(width)} for {pdf_path}"
        assert width > 0, f"Width should be positive, got {width} for {pdf_path}"
    except Exception as e:
        pytest.fail(f"Failed to get width for {pdf_path}: {str(e)}")

@pytest.mark.parametrize('pdf_reader_instance', BANK_FILES, indirect=True)
def test_extract_words(pdf_reader_instance):
    """Tests extracting words from the PDF."""
    reader, pdf_path = pdf_reader_instance
    try:
        words_df = reader.extract_words()
        assert isinstance(words_df, pd.DataFrame), f"Extracted words should be a DataFrame, got {type(words_df)} for {pdf_path}"
        assert not words_df.empty, f"Extracted words DataFrame should not be empty for {pdf_path}"

        # Check columns and dtypes
        expected_columns = {
            'page': 'int64',
            'text': 'object',
            'x0': 'float64',
            'top': 'float64',
            'x1': 'float64',
            'bottom': 'float64'
        }

        for col, dtype in expected_columns.items():
            assert col in words_df.columns, f"'{col}' column missing in DataFrame for {pdf_path}"
            # Allow for potential variations like int32/int64, float32/float64 if needed, 
            # but strict check is often better.
            assert str(words_df[col].dtype) == dtype, f"'{col}' column should be of type {dtype}, got {words_df[col].dtype} for {pdf_path}"

    except Exception as e:
        pytest.fail(f"Failed to extract words for {pdf_path}: {str(e)}")
