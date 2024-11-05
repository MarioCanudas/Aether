import os

# Root folder of the project
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths for documents
DOCUMENTS_FOLDER = os.path.join(PROJECT_ROOT, 'documents')
INPUTS_FOLDER = os.path.join(DOCUMENTS_FOLDER, 'inputs')
OUTPUTS_FOLDER = os.path.join(DOCUMENTS_FOLDER, 'outputs')

# Other config variables
DEFAULT_BANK = 'Nu'
DEFAULT_STATEMENT_TYPE = 'credit'
MONTH_PATTERNS = {
    'january': 'ENE',
    'february': 'FEB',
    'may': 'MAY',
    'june': 'JUN',
    'july': 'JUL',
    'august': 'AGO',
    'september': 'SEP',
    'october': 'OCT',
    'november': 'NOV',
    'december': 'DEC'
}
