"""
Pytest configuration and fixtures for spclone tests.
"""

import pytest
import sys
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_sys_argv():
    """Reset sys.argv after each test to prevent test interference."""
    original_argv = sys.argv.copy()
    yield
    sys.argv = original_argv


@pytest.fixture
def mock_functions():
    """Mock the core functions to prevent actual GitHub operations during tests."""
    with patch('spclone.cli.install_from_github_with_url') as mock_install, \
         patch('spclone.cli.clone_github') as mock_clone:
        yield {
            'install': mock_install,
            'clone': mock_clone
        }