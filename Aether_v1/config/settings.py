import os

# Root folder of the project
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths for documents
DOCUMENTS_FOLDER = os.path.join(PROJECT_ROOT, 'documents')
INPUTS_FOLDER = os.path.join(DOCUMENTS_FOLDER, 'inputs')
OUTPUTS_FOLDER = os.path.join(DOCUMENTS_FOLDER, 'outputs')