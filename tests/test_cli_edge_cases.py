"""
Edge case tests for CLI functionality.
"""

import pytest
from spclone.cli import normalize_github_input


class TestNormalizeGithubInputEdgeCases:
    """Test edge cases for normalize_github_input function."""
    
    def test_normalize_preserves_non_git_strings(self):
        """Test that non-git strings are preserved unchanged."""
        non_git_inputs = [
            "just-a-string",
            "not.a.repo", 
            "single-word",
            "123456",
            "special!@#$%",
            "word1/word2/word3",  # Too many slashes
            "/invalid/start",     # Starts with slash
            "invalid/",           # Ends with slash
        ]
        
        for input_str in non_git_inputs:
            result = normalize_github_input(input_str)
            # Should return the input unchanged for non-standard formats
            assert result == input_str, f"Expected {input_str}, got {result}"
    
    def test_normalize_handles_git_suffix_correctly(self):
        """Test that .git suffix is only removed from valid git-like inputs."""
        test_cases = [
            # Should remove .git from valid patterns
            ("psf/requests.git", "https://github.com/psf/requests"),
            ("https://github.com/psf/requests.git", "https://github.com/psf/requests"),
            ("github.com/psf/requests.git", "https://github.com/psf/requests"),
            
            # Should NOT remove .git from invalid patterns  
            ("just-a-string.git", "just-a-string.git"),
            ("no-slash.git", "no-slash.git"),
            ("file.git", "file.git"),
        ]
        
        for input_str, expected in test_cases:
            result = normalize_github_input(input_str)
            assert result == expected, f"Input: {input_str}, Expected: {expected}, Got: {result}"
    
    def test_normalize_valid_github_patterns(self):
        """Test that valid GitHub patterns are correctly normalized."""
        test_cases = [
            ("psf/requests", "https://github.com/psf/requests"),
            ("microsoft/vscode", "https://github.com/microsoft/vscode"),
            ("user-name/repo-name", "https://github.com/user-name/repo-name"),
            ("user_name/repo_name", "https://github.com/user_name/repo_name"),
            ("user.name/repo.name", "https://github.com/user.name/repo.name"),
            ("123user/456repo", "https://github.com/123user/456repo"),
        ]
        
        for input_str, expected in test_cases:
            result = normalize_github_input(input_str)
            assert result == expected, f"Input: {input_str}, Expected: {expected}, Got: {result}"
    
    def test_normalize_github_urls(self):
        """Test that GitHub URLs are handled correctly."""
        test_cases = [
            ("https://github.com/psf/requests", "https://github.com/psf/requests"),
            ("http://github.com/psf/requests", "http://github.com/psf/requests"),
            ("github.com/psf/requests", "https://github.com/psf/requests"),
        ]
        
        for input_str, expected in test_cases:
            result = normalize_github_input(input_str)
            assert result == expected, f"Input: {input_str}, Expected: {expected}, Got: {result}"
    
    def test_normalize_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        test_cases = [
            ("  psf/requests  ", "https://github.com/psf/requests"),
            ("\tpst/requests\t", "https://github.com/pst/requests"),
            (" https://github.com/psf/requests ", "https://github.com/psf/requests"),
            ("  just-a-string  ", "just-a-string"),
        ]
        
        for input_str, expected in test_cases:
            result = normalize_github_input(input_str)
            assert result == expected, f"Input: '{input_str}', Expected: {expected}, Got: {result}"
    
    def test_normalize_empty_input_raises_error(self):
        """Test that empty input raises ValueError."""
        empty_inputs = ["", None, "   ", "\t\n"]
        
        for empty_input in empty_inputs:
            with pytest.raises(ValueError, match="Repository input cannot be empty"):
                normalize_github_input(empty_input)
    
    def test_normalize_complex_edge_cases(self):
        """Test complex edge cases."""
        test_cases = [
            # Multiple slashes - should be preserved as-is (invalid format)
            ("user/repo/extra", "user/repo/extra"),
            ("user/repo/branch/path", "user/repo/branch/path"),
            
            # Special characters in non-owner/repo format
            ("special@chars#here", "special@chars#here"),
            ("has spaces in it", "has spaces in it"),
            
            # Edge cases with dots
            ("user.with.dots/repo", "https://github.com/user.with.dots/repo"),
            ("user/repo.with.dots", "https://github.com/user/repo.with.dots"),
            
            # GitHub enterprise or other domains (should be preserved)
            ("github.enterprise.com/user/repo", "github.enterprise.com/user/repo"),
            ("gitlab.com/user/repo", "gitlab.com/user/repo"),
        ]
        
        for input_str, expected in test_cases:
            result = normalize_github_input(input_str)
            assert result == expected, f"Input: {input_str}, Expected: {expected}, Got: {result}"
    
    def test_normalize_regex_pattern_validation(self):
        """Test that the regex pattern correctly identifies valid owner/repo formats."""
        valid_patterns = [
            "user/repo",
            "user-name/repo-name", 
            "user_name/repo_name",
            "user.name/repo.name",
            "123user/456repo",
            "a/b",  # Minimal valid case
        ]
        
        for pattern in valid_patterns:
            result = normalize_github_input(pattern)
            assert result.startswith("https://github.com/"), f"Pattern {pattern} should be converted to GitHub URL"
        
        invalid_patterns = [
            "user",           # No slash
            "user/",          # Ends with slash
            "/repo",          # Starts with slash
            "user//repo",     # Double slash
            "user/repo/extra", # Too many parts
            "user repo",      # Space (invalid character)
        ]
        
        for pattern in invalid_patterns:
            result = normalize_github_input(pattern)
            assert not result.startswith("https://github.com/"), f"Pattern {pattern} should NOT be converted to GitHub URL, got: {result}"