def test_parse_pyproject_manual_debug_scipy(self):
        """Debug test for scipy-style parsing."""
        content = '''
[build-system]
requires = [
    "wheel",
    "setuptools_scm[toml]",
    "Cython>=0.29.18"
]
build-backend = "setuptools.build_meta"
'''
        
        with patch('pathlib.Path.read_text', return_value=content):
            result = parse_pyproject_manual(Path('pyproject.toml'))
            
            requires = result['build-system']['requires']
            print(f"DEBUG Simple: {requires}")
            
            # This should definitely work
            assert 'wheel' in requires
            assert any('setuptools_scm' in req for req in requires)
            assert any('Cython' in req for req in requires)