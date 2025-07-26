import pytest
import sys
from unittest.mock import patch, MagicMock
from spclone.cli import normalize_github_input, main, clone


class TestNormalizeGithubInput:
    """Test cases for the normalize_github_input function."""
    
    def test_normalize_owner_repo_format(self):
        """Test conversion of owner/repo format to full URL."""
        assert normalize_github_input('psf/requests') == 'https://github.com/psf/requests'
        assert normalize_github_input('microsoft/vscode') == 'https://github.com/microsoft/vscode'
        assert normalize_github_input('django/django') == 'https://github.com/django/django'
    
    def test_normalize_full_url_unchanged(self):
        """Test that full URLs are returned unchanged."""
        url = 'https://github.com/psf/requests'
        assert normalize_github_input(url) == url
        
        http_url = 'http://github.com/psf/requests'
        assert normalize_github_input(http_url) == http_url
    
    def test_normalize_github_com_prefix(self):
        """Test URLs starting with github.com/ get https prefix."""
        assert normalize_github_input('github.com/psf/requests') == 'https://github.com/psf/requests'
    
    def test_normalize_removes_git_suffix(self):
        """Test that .git suffixes are removed."""
        assert normalize_github_input('psf/requests.git') == 'https://github.com/psf/requests'
        assert normalize_github_input('https://github.com/psf/requests.git') == 'https://github.com/psf/requests'
    
    def test_normalize_handles_whitespace(self):
        """Test that whitespace is stripped."""
        assert normalize_github_input('  psf/requests  ') == 'https://github.com/psf/requests'
        assert normalize_github_input('  psf/requests.git  ') == 'https://github.com/psf/requests'
    
    def test_normalize_empty_input_raises_error(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="Repository input cannot be empty"):
            normalize_github_input('')
        
        with pytest.raises(ValueError, match="Repository input cannot be empty"):
            normalize_github_input(None)
        
        with pytest.raises(ValueError, match="Repository input cannot be empty"):
            normalize_github_input('   ')
    
    def test_normalize_special_characters_in_repo_names(self):
        """Test handling of special characters in repository names."""
        assert normalize_github_input('user-name/repo-name') == 'https://github.com/user-name/repo-name'
        assert normalize_github_input('user_name/repo_name') == 'https://github.com/user_name/repo_name'
        assert normalize_github_input('user.name/repo.name') == 'https://github.com/user.name/repo.name'


class TestMainFunction:
    """Test cases for the main function (spinstall)."""
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_with_owner_repo_format(self, mock_install):
        """Test main function with owner/repo format."""
        with patch.object(sys, 'argv', ['spinstall', 'psf/requests']):
            main()
        mock_install.assert_called_once_with('https://github.com/psf/requests', branch='main', force_build=False)
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_with_full_url(self, mock_install):
        """Test main function with full GitHub URL."""
        with patch.object(sys, 'argv', ['spinstall', 'https://github.com/psf/requests']):
            main()
        mock_install.assert_called_once_with('https://github.com/psf/requests', branch='main', force_build=False)
    
    @patch('spclone.cli.install_from_github_with_url')
    @patch('builtins.print')
    def test_main_with_verbose_flag(self, mock_print, mock_install):
        """Test main function with verbose output."""
        with patch.object(sys, 'argv', ['spinstall', 'psf/requests', '--verbose']):
            main()
        mock_install.assert_called_once_with('https://github.com/psf/requests', branch='main', force_build=False)
        # Check that verbose messages were printed
        assert any('Processing repository' in str(call) for call in mock_print.call_args_list)
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_with_branch_flag(self, mock_install):
        """Test main function with custom branch."""
        with patch.object(sys, 'argv', ['spinstall', 'psf/requests', '--branch', 'develop']):
            main()
        mock_install.assert_called_once_with('https://github.com/psf/requests', branch='develop', force_build=False)
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_with_force_build_flag(self, mock_install):
        """Test main function with force build flag."""
        with patch.object(sys, 'argv', ['spinstall', 'psf/requests', '--force-build']):
            main()
        mock_install.assert_called_once_with('https://github.com/psf/requests', branch='main', force_build=True)
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_with_all_flags(self, mock_install):
        """Test main function with all flags."""
        with patch.object(sys, 'argv', ['spinstall', 'psf/requests', '--branch', 'develop', '--force-build']):
            main()
        mock_install.assert_called_once_with('https://github.com/psf/requests', branch='develop', force_build=True)
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_missing_argument(self, mock_install):
        """Test main function with missing repository argument."""
        with patch.object(sys, 'argv', ['spinstall']):
            with pytest.raises(SystemExit):
                main()
        mock_install.assert_not_called()
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_handles_keyboard_interrupt(self, mock_install):
        """Test main function handles KeyboardInterrupt gracefully."""
        mock_install.side_effect = KeyboardInterrupt()
        
        with patch('builtins.print') as mock_print:
            with patch.object(sys, 'argv', ['spinstall', 'psf/requests']):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                mock_print.assert_any_call("\nOperation cancelled by user")
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_main_handles_general_exception(self, mock_install):
        """Test main function handles general exceptions gracefully."""
        mock_install.side_effect = Exception("Test error")
        
        with patch('builtins.print') as mock_print:
            with patch.object(sys, 'argv', ['spinstall', 'psf/requests']):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                # Check that error was printed to stderr
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any('spinstall: Error - Test error' in call for call in print_calls)


class TestCloneFunction:
    """Test cases for the clone function (spclone)."""
    
    @patch('spclone.cli.clone_github')
    def test_clone_with_owner_repo_format(self, mock_clone):
        """Test clone function with owner/repo format."""
        with patch.object(sys, 'argv', ['spclone', 'psf/requests']):
            clone()
        mock_clone.assert_called_once_with('https://github.com/psf/requests', branch='main')
    
    @patch('spclone.cli.clone_github')
    def test_clone_with_full_url(self, mock_clone):
        """Test clone function with full GitHub URL."""
        with patch.object(sys, 'argv', ['spclone', 'https://github.com/psf/requests']):
            clone()
        mock_clone.assert_called_once_with('https://github.com/psf/requests', branch='main')
    
    @patch('spclone.cli.clone_github')
    @patch('builtins.print')
    def test_clone_with_verbose_flag(self, mock_print, mock_clone):
        """Test clone function with verbose output."""
        with patch.object(sys, 'argv', ['spclone', 'psf/requests', '--verbose']):
            clone()
        mock_clone.assert_called_once_with('https://github.com/psf/requests', branch='main')
        # Check that verbose messages were printed
        assert any('Processing repository' in str(call) for call in mock_print.call_args_list)
    
    @patch('spclone.cli.clone_github')
    def test_clone_with_branch_flag(self, mock_clone):
        """Test clone function with custom branch."""
        with patch.object(sys, 'argv', ['spclone', 'psf/requests', '--branch', 'develop']):
            clone()
        mock_clone.assert_called_once_with('https://github.com/psf/requests', branch='develop')
    
    @patch('spclone.cli.clone_github')
    @patch('inspect.signature')
    def test_clone_with_directory_parameter(self, mock_signature, mock_clone):
        """Test clone function with directory parameter when supported."""
        # Mock the signature to include 'directory' parameter
        mock_param = MagicMock()
        mock_signature.return_value.parameters = {'url': mock_param, 'branch': mock_param, 'directory': mock_param}
        
        with patch.object(sys, 'argv', ['spclone', 'psf/requests', '-d', 'custom-dir']):
            clone()
        mock_clone.assert_called_once_with('https://github.com/psf/requests', branch='main', directory='custom-dir')
    
    @patch('spclone.cli.clone_github')
    @patch('inspect.signature')
    def test_clone_without_directory_parameter_support(self, mock_signature, mock_clone):
        """Test clone function with directory parameter when not supported."""
        # Mock the signature to not include 'directory' parameter
        mock_param = MagicMock()
        mock_signature.return_value.parameters = {'url': mock_param, 'branch': mock_param}
        
        with patch.object(sys, 'argv', ['spclone', 'psf/requests', '-d', 'custom-dir']):
            clone()
        mock_clone.assert_called_once_with('https://github.com/psf/requests', branch='main')
    
    @patch('spclone.cli.clone_github')
    @patch('inspect.signature')
    def test_clone_with_all_parameters(self, mock_signature, mock_clone):
        """Test clone function with all parameters."""
        # Mock the signature to include all parameters
        mock_param = MagicMock()
        mock_signature.return_value.parameters = {
            'url': mock_param, 
            'branch': mock_param, 
            'directory': mock_param
        }
        
        with patch.object(sys, 'argv', ['spclone', 'psf/requests', '--branch', 'develop', '-d', 'custom-dir']):
            clone()
        mock_clone.assert_called_once_with(
            'https://github.com/psf/requests', 
            branch='develop', 
            directory='custom-dir'
        )
    
    @patch('spclone.cli.clone_github')
    def test_clone_missing_argument(self, mock_clone):
        """Test clone function with missing repository argument."""
        with patch.object(sys, 'argv', ['spclone']):
            with pytest.raises(SystemExit):
                clone()
        mock_clone.assert_not_called()
    
    @patch('spclone.cli.clone_github')
    def test_clone_handles_keyboard_interrupt(self, mock_clone):
        """Test clone function handles KeyboardInterrupt gracefully."""
        mock_clone.side_effect = KeyboardInterrupt()
        
        with patch('builtins.print') as mock_print:
            with patch.object(sys, 'argv', ['spclone', 'psf/requests']):
                with pytest.raises(SystemExit) as exc_info:
                    clone()
                
                assert exc_info.value.code == 1
                mock_print.assert_any_call("\nOperation cancelled by user")
    
    @patch('spclone.cli.clone_github')
    def test_clone_handles_general_exception(self, mock_clone):
        """Test clone function handles general exceptions gracefully."""
        mock_clone.side_effect = Exception("Test error")
        
        with patch('builtins.print') as mock_print:
            with patch.object(sys, 'argv', ['spclone', 'psf/requests']):
                with pytest.raises(SystemExit) as exc_info:
                    clone()
                
                assert exc_info.value.code == 1
                # Check that error was printed to stderr
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any('spclone: Error - Test error' in call for call in print_calls)


class TestIntegration:
    """Integration tests for the CLI module."""
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_multiple_input_formats_same_result(self, mock_install):
        """Test that different input formats for the same repo produce the same result."""
        formats = [
            'psf/requests',
            'https://github.com/psf/requests',
            'github.com/psf/requests',
            'psf/requests.git',
            '  psf/requests  '
        ]
        
        expected_url = 'https://github.com/psf/requests'
        
        for repo_format in formats:
            with patch.object(sys, 'argv', ['spinstall', repo_format]):
                main()
                mock_install.assert_called_with(expected_url, branch='main', force_build=False)
            mock_install.reset_mock()
    
    @patch('spclone.cli.clone_github')
    def test_clone_multiple_input_formats_same_result(self, mock_clone):
        """Test that different input formats for clone produce the same result."""
        formats = [
            'psf/requests',
            'https://github.com/psf/requests',
            'github.com/psf/requests',
            'psf/requests.git',
            '  psf/requests  '
        ]
        
        expected_url = 'https://github.com/psf/requests'
        
        for repo_format in formats:
            with patch.object(sys, 'argv', ['spclone', repo_format]):
                clone()
                mock_clone.assert_called_with(expected_url, branch='main')
            mock_clone.reset_mock()


class TestNewFeatures:
    """Test cases for new CLI features."""
    
    @patch('spclone.cli.install_from_github_with_url')
    def test_install_short_branch_flag(self, mock_install):
        """Test install with short branch flag."""
        with patch.object(sys, 'argv', ['spinstall', 'psf/requests', '-b', 'develop']):
            main()
        mock_install.assert_called_once_with('https://github.com/psf/requests', branch='develop', force_build=False)
    
    @patch('spclone.cli.clone_github')
    def test_clone_short_branch_flag(self, mock_clone):
        """Test clone with short branch flag."""
        with patch.object(sys, 'argv', ['spclone', 'psf/requests', '-b', 'develop']):
            clone()
        mock_clone.assert_called_once_with('https://github.com/psf/requests', branch='develop')
    
    @patch('spclone.cli.install_from_github_with_url')
    @patch('builtins.print')
    def test_complex_package_installation(self, mock_print, mock_install):
        """Test installation of complex package with all flags."""
        with patch.object(sys, 'argv', ['spinstall', 'pandas-dev/pandas', '--force-build', '--verbose']):
            main()
        mock_install.assert_called_once_with('https://github.com/pandas-dev/pandas', branch='main', force_build=True)
        # Check verbose output
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any('Force build mode enabled' in call for call in print_calls)