import pytest
import os
import sys
from pandas import DataFrame
from functools import lru_cache
from typing import Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import PROJECT_ROOT

# Bases for the classes to be tested
from core import DocumentReader, BankDetector, TableBoundaryDetector, RowSegmenter, TableReconstructor, TableNormalizer, DataExporter

# Classes to be tested
from new_model.document_reader import PDFReader
from new_model.bank_detector import DefaultBankDetector
from new_model.table_boundary_detector import TransactionTableBoundaryDetector
from new_model.row_segmenter import TransactionRowSegmenter
from new_model.table_reconstructor import TransactionTableReconstructor
from new_model.table_normalizer import TransactionTableNormalizer
from new_model.data_exporter import CsvExporter

INPUTS_FOLDER = os.path.join(PROJECT_ROOT, 'tests', 'new_model', 'test_data', 'inputs')

@lru_cache(maxsize=None)
def _get_cached_reader(file_path: str) -> DocumentReader:
    """
    Creates a PDFReader instance for a given file path.
    Uses caching to avoid re-initializing the reader for the same file.
    """
    print(f"Creating PDFReader instance for {file_path}")
    try: 
        return PDFReader(file_path)
    except Exception as e:
        pytest.fail(f"Failed to initialize PDFReader for {file_path}: {str(e)}")

@lru_cache(maxsize=None)
def _get_cached_bank_detector(file_path: str) -> Tuple[BankDetector, DataFrame, dict]:
    """
    Creates a DefaultBankDetector instance for a given file path.
    Uses caching to avoid re-initializing the detector for the same file.
    """
    print(f"Creating DefaultBankDetector instance for {file_path}")
    reader = _get_cached_reader(file_path)    
    try:
        detector = DefaultBankDetector(reader)

        extracted_words = detector.extracted_words
        properties = detector.get_statement_properties()

        return detector, extracted_words, properties
    except Exception as e:
        pytest.fail(f"Failed to initialize DefaultBankDetector for {file_path}: {str(e)}")

@lru_cache(maxsize=None)
def _get_cached_table_boundary_detector(file_path: str) -> Tuple[TableBoundaryDetector, DataFrame, dict]:
    """
    Creates a TransactionTableBoundaryDetector instance for a given file path.
    Uses caching to avoid re-initializing the detector for the same file.
    """
    print(f"Creating TransactionTableBoundaryDetector instance for {file_path}")
    detector, extracted_words, properties = _get_cached_bank_detector(file_path)
    
    try:
        table_boundary_detector = TransactionTableBoundaryDetector(extracted_words, properties)

        start_idx = table_boundary_detector.start_idx
        end_idx = table_boundary_detector.end_idx

        if start_idx is None or end_idx is None:
            try:
                properties = detector.get_statement_properties(new_credit_format= True)
                table_boundary_detector = TransactionTableBoundaryDetector(extracted_words, properties)
            except Exception as e:
                pytest.fail(f"Failed to get new statement properties for {file_path}: {str(e)}")
        
        filtered_table_words = table_boundary_detector.get_filtered_table_words()

        return table_boundary_detector, filtered_table_words, properties
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableBoundaryDetector for {file_path}: {str(e)}")

@lru_cache(maxsize=None)
def _get_cached_row_segmenter(file_path: str) -> Tuple[RowSegmenter, DataFrame, dict]:
    """
    Creates a TransactionRowSegmenter instance for a given file path.
    Uses caching to avoid re-initializing the segmenter for the same file.
    """
    print(f"Creating TransactionRowSegmenter instance for {file_path}")
    _, filtered_table_words, properties = _get_cached_table_boundary_detector(file_path)
    try:
        row_segmenter = TransactionRowSegmenter(filtered_table_words, properties)

        grouped_rows = row_segmenter.group_rows()
        columns_positions = row_segmenter.delimit_column_positions()

        return row_segmenter, grouped_rows, columns_positions
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionRowSegmenter for {file_path}: {str(e)}")

@lru_cache(maxsize=None)
def _get_cached_table_reconstructor(file_path: str) -> Tuple[TableReconstructor, DataFrame]:
    """
    Creates a TransactionTableReconstructor instance for a given file path.
    Uses caching to avoid re-initializing the reconstructor for the same file.
    """
    print(f"Creating TransactionTableReconstructor instance for {file_path}")
    _, grouped_rows, columns_positions= _get_cached_row_segmenter(file_path)
    _, _, properties = _get_cached_table_boundary_detector(file_path)

    try:
        table_reconstructor = TransactionTableReconstructor(grouped_rows, columns_positions, properties)

        reconstructed_table = table_reconstructor.reconstruct_table()

        return table_reconstructor, reconstructed_table
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableReconstructor for {file_path}: {str(e)}")

@lru_cache(maxsize=None)
def _get_cached_table_normalizer(file_path: str) -> Tuple[TableNormalizer, DataFrame]:
    """
    Creates a TransactionTableNormalizer instance for a given file path.
    Uses caching to avoid re-initializing the normalizer for the same file.
    """
    print(f"Creating TransactionTableNormalizer instance for {file_path}")
    _, reconstructed_table = _get_cached_table_reconstructor(file_path)
    _, _, properties = _get_cached_table_boundary_detector(file_path)
    _, extracted_words, _ = _get_cached_bank_detector(file_path)

    try:
        table_normalizer = TransactionTableNormalizer(reconstructed_table, extracted_words, properties)

        normalized_table = table_normalizer.normalize_table()

        return table_normalizer, normalized_table
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableNormalizer for {file_path}: {str(e)}")

@lru_cache(maxsize=None)
def _get_cached_data_exporter(file_path: str) -> DataExporter:
    """
    Creates a CsvExporter instance for a given file path.
    Uses caching to avoid re-initializing the exporter for the same file.
    """
    print(f"Creating CsvExporter instance for {file_path}")
    _, normalized_table = _get_cached_table_normalizer(file_path)

    try:
        data_exporter = CsvExporter(normalized_table)

        return data_exporter
    except Exception as e:
        pytest.fail(f"Failed to initialize CsvExporter for {file_path}: {str(e)}")

# 
@pytest.fixture(scope='session')
def pdf_reader_instance(request):
    """Creates a PDFReader instance for a given file path."""
    file_path = request.param
    pdf_path = os.path.join(INPUTS_FOLDER, file_path)
    
    try:
        reader = _get_cached_reader(pdf_path)    
        yield reader, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize PDFReader for {pdf_path}: {str(e)}")

@pytest.fixture(scope='session')
def bank_detector_instance(request):
    """Creates a DefaultBankDetector instance for a given file path."""
    file_path, expected_bank, expected_type  = request.param
    pdf_path= os.path.join(INPUTS_FOLDER, file_path)
    
    try:
        detector, _, _ = _get_cached_bank_detector(pdf_path)    
        yield detector, expected_bank, expected_type
    except Exception as e:
        pytest.fail(f"Failed to initialize DefaultBankDetector for {pdf_path}: {str(e)}")

@pytest.fixture(scope='session')
def table_boundary_detector_instance(request):
    """Creates a TransactionTableBoundaryDetector instance for a given file path."""
    file_path  = request.param
    pdf_path= os.path.join(INPUTS_FOLDER, file_path)

    try:
        table_boundary_detector, _, _ = _get_cached_table_boundary_detector(pdf_path)    
        yield table_boundary_detector, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableBoundaryDetector for {pdf_path}: {str(e)}")

@pytest.fixture(scope='session')
def row_segmenter_instance(request):
    """Creates a TransactionRowSegmenter instance for a given file path."""
    file_path  = request.param
    pdf_path= os.path.join(INPUTS_FOLDER, file_path)

    try:
        row_segmenter, _, _ = _get_cached_row_segmenter(pdf_path)    
        yield row_segmenter, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionRowSegmenter for {pdf_path}: {str(e)}")

@pytest.fixture(scope='session')
def table_reconstructor_instance(request):
    """Creates a TransactionTableReconstructor instance for a given file path."""
    file_path  = request.param
    pdf_path= os.path.join(INPUTS_FOLDER, file_path)

    try:
        table_reconstructor, _ = _get_cached_table_reconstructor(pdf_path)    
        yield table_reconstructor, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableReconstructor for {pdf_path}: {str(e)}")

@pytest.fixture(scope='session')
def table_normalizer_instance(request):
    """Creates a TransactionTableNormalizer instance for a given file path."""
    file_path  = request.param
    pdf_path= os.path.join(INPUTS_FOLDER, file_path)

    try:
        table_normalizer, _ = _get_cached_table_normalizer(pdf_path)    
        yield table_normalizer, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize TransactionTableNormalizer for {pdf_path}: {str(e)}")

@pytest.fixture(scope='session')
def data_exporter_instance(request):
    """Creates a CsvExporter instance for a given file path."""
    file_path  = request.param
    pdf_path= os.path.join(INPUTS_FOLDER, file_path)

    try:
        data_exporter = _get_cached_data_exporter(pdf_path)    
        yield data_exporter, pdf_path
    except Exception as e:
        pytest.fail(f"Failed to initialize CsvExporter for {pdf_path}: {str(e)}")