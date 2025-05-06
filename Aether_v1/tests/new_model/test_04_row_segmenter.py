import pytest
from pandas import DataFrame
from core import RowSegmenter

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

@pytest.mark.parametrize('row_segmenter_instance', BANK_FILES, indirect=True)
def test_row_segmenter_init(row_segmenter_instance):
    """Tests if the RowSegmenter initializes with the correct path."""
    row_segmenter, pdf_file = row_segmenter_instance
    try:
        assert isinstance(row_segmenter, RowSegmenter), f"Expected RowSegmenter instance, got {type(row_segmenter)}"
    except Exception as e:
        pytest.fail(f"Failed to initialize RowSegmenter for {pdf_file}: {str(e)}")

@pytest.mark.parametrize('row_segmenter_instance', BANK_FILES, indirect=True)
def test_delimit_column_positions(row_segmenter_instance):
    """Tests the delimit_column_positions method."""
    row_segmenter, pdf_file = row_segmenter_instance
    try:
        delimitations = row_segmenter.delimit_column_positions()
        assert isinstance(delimitations, dict), f"Expected dict, got {type(delimitations)} for {pdf_file}"
        assert all(len(delimitations[key]) == len(delimitations['columns']) for key in ['x0', 'x1']), f"Length mismatch in delimitations for {pdf_file}"
        
        description_column = row_segmenter.statement_propertys['description_column']

        for col, x0, x1 in zip(delimitations['columns'], delimitations['x0'], delimitations['x1']):
            if col == description_column:
                assert isinstance(x0, (float, type(None))), f"x0 should be float or None for {col} in {pdf_file}"
                assert isinstance(x1, (float, type(None))), f"x1 should be float or None for {col} in {pdf_file}"
            else:
                assert isinstance(x0, float), f"x0 should be float for {col} in {pdf_file}"
                assert isinstance(x1, float), f"x1 should be float for {col} in {pdf_file}"

    except Exception as e:
        pytest.fail(f"Failed to get column delimitations for {pdf_file}: {str(e)}")

@pytest.mark.parametrize('row_segmenter_instance', BANK_FILES, indirect=True)
def test_delimit_row_threshold(row_segmenter_instance):
    row_segmenter, pdf_file = row_segmenter_instance

    try:
        row_threshold = row_segmenter.row_threshold
        assert isinstance(row_threshold, float), f"Expected float, got {type(row_threshold)} for {pdf_file}"
        assert 0 < row_threshold, f"Row threshold should be a positive float {pdf_file}"
    except Exception as e:
        pytest.fail(f"Failed to get row threshold for {pdf_file}: {str(e)}")

def is_valid_word_list(value):
    """
    Checks if an element is a list of (str, float, float) tuples.
    For be used to check the words column in the grouped rows.
    """
    if not isinstance(value,list):
        return False
    
    return all(
        isinstance(item, tuple) and len(item) == 3 and
        isinstance(item[0], str) and isinstance(item[1], float) and isinstance(item[2], float)
        for item in value
    )

@pytest.mark.parametrize('row_segmenter_instance', BANK_FILES, indirect=True)
def test_group_rows(row_segmenter_instance):
    """Tests the group_rows method."""
    row_segmenter, pdf_file = row_segmenter_instance
    try:
        grouped_rows = row_segmenter.group_rows()
        assert isinstance(grouped_rows, DataFrame), f"Expected DataFrame, got {type(grouped_rows)} for {pdf_file}"
        assert not grouped_rows.empty, f"Grouped rows should not be empty for {pdf_file}"

        expected_columns = {
            'row_group': 'int64',
            'text': 'object',
            'words': 'object',
            'top': 'float64',
            'bottom': 'float64',
            'page': 'int64',
        }

        for col, dtype in expected_columns.items():
            assert col in grouped_rows.columns, f"'{col}' column missing in grouped rows for {pdf_file}"
            assert str(grouped_rows[col].dtype) == dtype, f"'{col}' column should be of type {dtype}, got {grouped_rows[col].dtype} for {pdf_file}"

        all_words_valid = grouped_rows['words'].apply(is_valid_word_list).all()
        assert all_words_valid, f"All elements in 'words' column should be list of (str, float, float) tuples for {pdf_file}"
        
    except Exception as e:
        pytest.fail(f"Failed to group rows for {pdf_file}: {str(e)}")