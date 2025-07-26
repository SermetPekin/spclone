import pytest
from spclone.cli import normalize_github_input


def test_normalize_basic_cases():
    """Test basic normalization cases."""
    assert normalize_github_input('psf/requests') == 'https://github.com/psf/requests'
    assert normalize_github_input('https://github.com/psf/requests') == 'https://github.com/psf/requests'
    assert normalize_github_input('github.com/psf/requests') == 'https://github.com/psf/requests'


def test_normalize_with_git_suffix():
    """Test .git suffix removal."""
    assert normalize_github_input('psf/requests.git') == 'https://github.com/psf/requests'
    assert normalize_github_input('https://github.com/psf/requests.git') == 'https://github.com/psf/requests'


def test_normalize_empty_input():
    """Test empty input handling."""
    with pytest.raises(ValueError):
        normalize_github_input('')
    
    with pytest.raises(ValueError):
        normalize_github_input(None)


def test_normalize_preserves_invalid():
    """Test that invalid formats are preserved."""
    assert normalize_github_input('just-a-string') == 'just-a-string'
    assert normalize_github_input('not/a/valid/format') == 'not/a/valid/format'