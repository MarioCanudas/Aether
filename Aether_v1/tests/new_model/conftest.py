import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

import pytest

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_data')))

@pytest.fixture(scope='session')
def test_data_input_dir():
    if not os.path.isdir(TEST_DATA_DIR) or not os.path.exists(TEST_DATA_DIR):
        pytest.fail(f"Test data directory {TEST_DATA_DIR} does not exist.")
    return os.path.join(TEST_DATA_DIR, 'inputs')

@pytest.fixture(scope='session')
def test_data_output_dir():
    if not os.path.isdir(TEST_DATA_DIR) or not os.path.exists(TEST_DATA_DIR):
        pytest.fail(f"Test data directory {TEST_DATA_DIR} does not exist.")
    return os.path.join(TEST_DATA_DIR, 'outputs')
