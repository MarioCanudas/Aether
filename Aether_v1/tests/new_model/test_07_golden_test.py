import os
import pytest
import pandas as pd
from new_model.document_reader import PDFReader
from new_model.bank_detector import DefaultBankDetector
from new_model.table_boundary_detector import TransactionTableBoundaryDetector
from new_model.row_segmenter import TransactionRowSegmenter
from new_model.table_reconstructor import TransactionTableReconstructor
from new_model.table_normalizer import TransactionTableNormalizer

OUTPUTS_FOLDER = os.path.join('tests', 'new_model', 'test_data', 'outputs')

GOLDEN_FILES = [
    #'amex_credit_new.pdf',
    #'amex_credit_old.pdf': '',
    ('banamex_credit_new.pdf', 'banamex_credit_new_output.csv'),
    ('banamex_credit_old.pdf', 'banamex_credit_old_output.csv'),
    #'banamex_debit.pdf': '',
    ('banorte_credit_new.pdf', 'banorte_credit_new_output.csv'),
    ('banorte_credit_old.pdf', 'banorte_credit_old_output.csv'),
    ('banorte_debit.pdf', 'banorte_debit_output.csv'),
    ('bbva_credit_new.pdf', 'bbva_credit_new_output.csv'),
    ('bbva_credit_old.pdf', 'bbva_credit_old_output.csv'), 
    ('bbva_debit.pdf', 'bbva_debit_output.csv'),
    #'hsbc_credit_new.pdf': '',
    ('hsbc_credit_old.pdf', 'hsbc_credit_old_output.csv'),
    #'hsbc_debit.pdf': '',
    #'inbursa_credit_new.pdf': '',
    ('inbursa_credit_old.pdf', 'inbursa_credit_old_output.csv'),
    ('inbursa_debit.pdf', 'inbursa_debit_output.csv'),
    ('nu_credit.pdf', 'nu_credit_output.csv'),
    ('nu_debit.pdf', 'nu_debit_output.csv'),
]

@pytest.mark.parametrize("get_test_file,get_expected_file", GOLDEN_FILES, indirect=True)
def test_golden_test(get_test_file, get_expected_file):
    test_file = get_test_file
    expected_file = get_expected_file
    
    try:
        expected_df = pd.read_csv(expected_file)
    except FileNotFoundError:
        pytest.fail(f"File {expected_file} not found")
    
    reader = PDFReader(test_file)
    bank_detector = DefaultBankDetector(reader)

    extracted_words = bank_detector.extracted_words
    statement_properties = bank_detector.get_statement_properties()

    boundary_detector = TransactionTableBoundaryDetector(extracted_words, statement_properties)
    start_idx = boundary_detector.start_idx
    end_idx = boundary_detector.end_idx
    if start_idx is None or end_idx is None:
        statement_properties = bank_detector.get_statement_properties(new_credit_format= True)
        boundary_detector = TransactionTableBoundaryDetector(extracted_words, statement_properties)
        start_idx = boundary_detector.start_idx
        end_idx = boundary_detector.end_idx
    df_filtered = boundary_detector.get_filtered_table_words()

    row_segmenter = TransactionRowSegmenter(df_filtered, statement_properties)
    column_delimitation = row_segmenter.delimit_column_positions()
    grouped_rows = row_segmenter.group_rows()

    table_reconstructor = TransactionTableReconstructor(grouped_rows, column_delimitation, statement_properties)
    reconstructed_table = table_reconstructor.reconstruct_table()

    normalizer = TransactionTableNormalizer(reconstructed_table, extracted_words, statement_properties)
    normalized_table = normalizer.normalize_table()
    
    assert normalized_table.equals(expected_df), f"Normalized table does not match expected output for {test_file}"
    
    
