import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
import re
from io import BytesIO
from config import PROJECT_ROOT

INPUTS_FOLDER = os.path.join(PROJECT_ROOT, 'tests', 'test_data', 'inputs')
OUTPUTS_FOLDER = os.path.join(PROJECT_ROOT, 'tests', 'test_data', 'outputs')

@pytest.fixture(scope= 'session')
def get_file_from_path(request) -> str:
    file_path = request.param
    return os.path.join(INPUTS_FOLDER, file_path)

@pytest.fixture(scope= 'session')
def get_bytesio_from_path(request) -> BytesIO:
    file_path = os.path.join(INPUTS_FOLDER, request.param)
    with open(file_path, 'rb') as file:
        return BytesIO(file.read())
    
@pytest.fixture(scope= 'session')
def get_input_data_from_path(request) -> pd.DataFrame:
    file_path = os.path.join(INPUTS_FOLDER, request.param)
    
    if re.match(r'.*\.csv$', file_path):
        return pd.read_csv(file_path), file_path
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    
    