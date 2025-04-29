import pytest
import os
import pandas as pd
from core import TableBoundaryDetector
from new_model.document_reader import PDFReader
from new_model.bank_detector import DefaultBankDetector
from new_model.table_boundary_detector import TransactionTableBoundaryDetector

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
def table_boundary_detector_instance(test_data_input_dir, request):
    """Creates a TransactionTableBoundaryDetector instance for a given file path."""
    file_path  = request.param
    pdf_path= os.path.join(test_data_input_dir, file_path)

    reader = PDFReader(pdf_path)    
    bank_detector = DefaultBankDetector(reader)

    extracted_words = bank_detector.extracted_words
    statement_properties = bank_detector.get_statement_properties()
    
    try:
        table_boundary_detector = TransactionTableBoundaryDetector(extracted_words, statement_properties)    
        yield table_boundary_detector, bank_detector, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableBoundaryDetector for {pdf_path}: {str(e)}")

@pytest.mark.parametrize('table_boundary_detector_instance', BANK_FILES, indirect=True)
def test_table_boundary_detector_init(table_boundary_detector_instance):
    """Tests if the TransactionTableBoundaryDetector initializes with the correct path."""
    table_boundary_detector, _, _ = table_boundary_detector_instance
    try:
        assert isinstance(table_boundary_detector, TableBoundaryDetector), f"Expected TableBoundaryDetector instance, got {type(table_boundary_detector)}"
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableBoundaryDetector: {str(e)}")

@pytest.mark.parametrize('table_boundary_detector_instance', BANK_FILES, indirect=True)
def test_df_corrected(table_boundary_detector_instance):
    """Tests the df_corrected property."""
    table_boundary_detector, _, pdf_path = table_boundary_detector_instance
    try:
        df_corrected = table_boundary_detector.df_corrected
        assert isinstance(df_corrected, pd.DataFrame), f"Expected DataFrame, got {type(df_corrected)}"
        assert not df_corrected.empty, "DataFrame should not be empty"

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
            assert col in df_corrected.columns, f"'{col}' column missing in DataFrame for {pdf_path}"
            # Allow for potential variations like int32/int64, float32/float64 if needed, 
            # but strict check is often better.
            assert str(df_corrected[col].dtype) == dtype, f"'{col}' column should be of type {dtype}, got {df_corrected[col].dtype} for {pdf_path}"
    except Exception as e:
        pytest.fail(f"Failed to get df_corrected: {str(e)}")

@pytest.mark.parametrize('table_boundary_detector_instance', BANK_FILES, indirect=True)
def test_start_idx(table_boundary_detector_instance):
    """Tests the start_idx property."""
    table_boundary_detector, bank_detector, pdf_path = table_boundary_detector_instance

    try:
        start_idx = table_boundary_detector.start_idx

        if start_idx is None:
            statement_properties = bank_detector.get_statement_properties(new_credit_format= True)
            table_boundary_detector = TransactionTableBoundaryDetector(bank_detector.extracted_words, statement_properties)

            start_idx = table_boundary_detector.start_idx

        assert isinstance(start_idx, int), f"Expected int, got {type(start_idx)} for {pdf_path}"
        assert start_idx >= 0, f"start_idx should be non-negative, got {start_idx} for {pdf_path}"
    except Exception as e:
        pytest.fail(f"Failed to get start_idx: {str(e)}")

@pytest.mark.parametrize('table_boundary_detector_instance', BANK_FILES, indirect=True)
def test_end_idx(table_boundary_detector_instance):
    """Tests the end_idx property."""
    table_boundary_detector, bank_detector, pdf_path = table_boundary_detector_instance

    try:
        end_idx = table_boundary_detector.end_idx

        if end_idx is None:
            statement_properties = bank_detector.get_statement_properties(new_credit_format= True)
            table_boundary_detector = TransactionTableBoundaryDetector(bank_detector.extracted_words, statement_properties)

            end_idx = table_boundary_detector.end_idx

        assert isinstance(end_idx, int), f"Expected int, got {type(end_idx)} for {pdf_path}"
        assert end_idx >= 0, f"end_idx should be non-negative, got {end_idx} for {pdf_path}"
    except Exception as e:
        pytest.fail(f"Failed to get start_idx: {str(e)}")

@pytest.mark.parametrize('table_boundary_detector_instance', BANK_FILES, indirect=True)
def test_get_filtered_table_words(table_boundary_detector_instance):
    """Tests the get_filtered_table_words method."""
    table_boundary_detector, bank_detector, pdf_path = table_boundary_detector_instance

    if table_boundary_detector.start_idx is None or table_boundary_detector.end_idx is None:
        statement_properties = bank_detector.get_statement_properties(new_credit_format= True)
        table_boundary_detector = TransactionTableBoundaryDetector(bank_detector.extracted_words, statement_properties)

    try:
        filtered_table_words = table_boundary_detector.get_filtered_table_words()
        assert isinstance(filtered_table_words, pd.DataFrame), f"Expected DataFrame, got {type(filtered_table_words)} for {pdf_path}"
        assert not filtered_table_words.empty, "Filtered DataFrame should not be empty"

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
            assert col in filtered_table_words.columns, f"'{col}' column missing in DataFrame for {pdf_path}"
            # Allow for potential variations like int32/int64, float32/float64 if needed, 
            # but strict check is often better.
            assert str(filtered_table_words[col].dtype) == dtype, f"'{col}' column should be of type {dtype}, got {filtered_table_words[col].dtype} for {pdf_path}"
    except Exception as e:
        pytest.fail(f"Failed to get filtered table words: {str(e)}")