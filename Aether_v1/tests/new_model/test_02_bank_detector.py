import pytest
import os
from core import BankDetector
from new_model.document_reader import PDFReader
from new_model.bank_detector import DefaultBankDetector

# List of test cases with their expected bank and type: (filename, bank, type)
BANK_TEST_CASES = [
    # Amex cases
    #('amex_credit_new.pdf', 'amex', 'credit'), ¡Don't have this sample yet!
    #('amex_credit_old.pdf', 'amex', 'credit'), ¡Model not working yet!

    # Banamex cases
    ('banamex_credit_new.pdf', 'banamex', 'credit'),
    ('banamex_credit_old.pdf', 'banamex', 'credit'),
    #('banamex_debit.pdf', 'banamex', 'debit'),

    # Banorte cases
    ('banorte_credit_new.pdf', 'banorte', 'credit'),
    ('banorte_credit_old.pdf', 'banorte', 'credit'),
    ('banorte_debit.pdf', 'banorte', 'debit'),
    
    # BBVA cases
    ('bbva_credit_new.pdf', 'bbva', 'credit'),
    ('bbva_credit_old.pdf', 'bbva', 'credit'),
    ('bbva_debit.pdf', 'bbva', 'debit'),

    # HSBC cases
    #('hsbc_credit_new.pdf', 'hsbc', 'credit'), ¡Don't have this sample yet!
    ('hsbc_credit_old.pdf', 'hsbc', 'credit'),
    #('hsbc_debit.pdf', 'hsbc', 'debit'), ¡Don't have this sample yet!

    # Inbursa cases
    #('inbursa_credit_new.pdf', 'inbursa', 'credit'), ¡Don't have this sample yet!
    ('inbursa_credit_old.pdf', 'inbursa', 'credit'),
    ('inbursa_debit.pdf', 'inbursa', 'debit'),

    # Nu cases
    ('nu_credit.pdf', 'nu', 'credit'),
    ('nu_debit.pdf', 'nu', 'debit'),

    # Santander cases
    #('santander_credit_new.pdf', 'santander', 'credit'), ¡Don't have this sample yet!
    #('santander_credit_old.pdf', 'santander', 'credit'), ¡Model not working yet!
    #('santander_debit.pdf', 'santander', 'debit'),¡Model not working yet!
]

@pytest.fixture
def bank_detector_instance(test_data_input_dir, request):
    """Creates a DefaultBankDetector instance for a given file path."""
    file_path, expected_bank, expected_type  = request.param
    pdf_path= os.path.join(test_data_input_dir, file_path)
    
    try:
        reader = PDFReader(pdf_path)    
        detector = DefaultBankDetector(reader)    
        yield detector, expected_bank, expected_type
    except Exception as e:
        pytest.fail(f"Failed to initialize DefaultBankDetector for {pdf_path}: {str(e)}")

@pytest.mark.parametrize('bank_detector_instance', BANK_TEST_CASES, indirect=True)
def test_bank_detector_init(bank_detector_instance):
    """Tests if the DefaultBankDetector initializes with the correct path."""
    detector = bank_detector_instance[0]
    assert isinstance(detector, BankDetector), f"Expected DefaultBankDetector instance, got {type(detector)}"

@pytest.mark.parametrize('bank_detector_instance', BANK_TEST_CASES, indirect=True)
def test_detect_bank(bank_detector_instance):
    """Tests the detect_bank method of DefaultBankDetector."""
    detector, expected_bank, _ = bank_detector_instance

    # Test detect_bank method
    try:
        detected_bank = detector.detect_bank()
        assert isinstance(detected_bank, str), f"Expected string for detected bank, got {type(detected_bank)}"
        assert detected_bank == expected_bank, f"Expected bank '{expected_bank}', got '{detected_bank}'"
    except Exception as e:
        pytest.fail(f"Failed to detect bank: {str(e)}")

@pytest.mark.parametrize('bank_detector_instance', BANK_TEST_CASES, indirect=True)
def test_detect_statement_type(bank_detector_instance):
    """Tests the detect_statement_type method of DefaultBankDetector."""
    detector, _, expected_type = bank_detector_instance

    # Test detect_statement_type method
    try:
        detected_type = detector.detect_statement_type()
        assert isinstance(detected_type, str), f"Expected string for detected type, got {type(detected_type)}"
        assert detected_type == expected_type, f"Expected type '{expected_type}', got '{detected_type}'"
    except Exception as e:
        pytest.fail(f"Failed to detect statement type: {str(e)}")

@pytest.mark.parametrize('bank_detector_instance', BANK_TEST_CASES, indirect=True)
def test_properties(bank_detector_instance):
    """Tests the properties method of DefaultBankDetector."""
    detector, _, _ = bank_detector_instance

    expected_properties = {
        # Phrase properties
        'start_phrase' : list,
        'end_phrase' : list,
        
        # Column distribution properties
        'columns': list,
        'date_column' : str,
        'description_column' : str,
        'amount_column' : list,
        'income_column' : str,
        'expense_column' : str,
        'balance_column' : (str, type(None)),
        
        # Date properties
        'date_pattern' : str,
        'date_groups' : tuple, # groups: (year, month, day)
        'month_pattern' : dict,
        
        # Amount properties
        'income_sign': (str, type(None)),
        'expense_sign': (str, type(None)),
        
        # Period properties
        'period_phrase' : (list, type(None)),
        'period_pattern' : (str, type(None)),
        'year_group' : (int, type(None)),
        
        # Trheshold properties
        'row_treshold_adjust' : bool,
        'date_treshold_adjust' : bool,
        'amount_treshold_adjust' : bool
    }
    

    # Test get_statement_properties method
    try:
        properties = detector.get_statement_properties()
        assert isinstance(properties, dict), f"Expected dictionary for properties, got {type(properties)}"
        assert len(properties) > 0, "Expected non-empty properties dictionary"

        for key, expected_type in expected_properties.items():
            assert key in properties, f"'{key}' key missing in properties dictionary"
            assert isinstance(properties[key], expected_type), f"Expected '{key}' to be of type {expected_type}, got {type(properties[key])}"

    except Exception as e:
        pytest.fail(f"Failed to get statement properties: {str(e)}")
