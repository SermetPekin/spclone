"""
GitHub repository cloning and installation utilities.

This module provides functions to download, clone, and install Python packages
directly from GitHub repositories using ZIP archives.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple, List
from urllib.parse import urlparse

import requests


class GitHubError(Exception):
    """Custom exception for GitHub-related errors."""
    pass


class InstallationError(Exception):
    """Custom exception for installation-related errors."""
    pass


def parse_github_url(repo_url: str) -> Tuple[str, str]:
    """
    Parse a GitHub URL to extract owner and repository name.
    
    Args:
        repo_url: GitHub repository URL (e.g., 'https://github.com/owner/repo')
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        GitHubError: If the URL format is invalid
        
    Examples:
        >>> parse_github_url('https://github.com/psf/requests')
        ('psf', 'requests')
    """
    try:
        # Handle different URL formats
        if repo_url.startswith(('http://', 'https://')):
            parsed = urlparse(repo_url)
            if parsed.netloc != 'github.com':
                raise GitHubError(f"Only GitHub URLs are supported, got: {parsed.netloc}")
            path_parts = parsed.path.strip('/').split('/')
        else:
            # Assume it's already in owner/repo format
            path_parts = repo_url.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise GitHubError(f"Invalid repository format. Expected 'owner/repo', got: {repo_url}")
        
        owner, repo = path_parts[0], path_parts[1]
        
        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        if not owner or not repo:
            raise GitHubError(f"Invalid repository format. Owner and repo cannot be empty: {repo_url}")
        
        return owner, repo
        
    except (IndexError, AttributeError) as e:
        raise GitHubError(f"Failed to parse GitHub URL: {repo_url}") from e


def download_github_zip(owner: str, repo: str, branch: str = "main") -> bytes:
    """
    Download a GitHub repository as a ZIP archive.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        branch: Branch name (default: "main")
        
    Returns:
        ZIP file content as bytes
        
    Raises:
        GitHubError: If download fails
    """
    zip_url = f"https://github.com/{owner}/{repo}/archive/{branch}.zip"
    
    try:
        print(f"Downloading {zip_url}...")
        response = requests.get(zip_url, timeout=60)  # Increased timeout for large repos
        response.raise_for_status()
        
        if len(response.content) == 0:
            raise GitHubError(f"Downloaded ZIP file is empty for {owner}/{repo}")
        
        print(f"Downloaded {len(response.content):,} bytes")
        return response.content
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                # Try common alternative branch names
                alternative_branches = ['master', 'develop', 'dev']
                if branch == 'main':
                    print(f"Branch 'main' not found, trying alternative branches...")
                    for alt_branch in alternative_branches:
                        try:
                            return download_github_zip(owner, repo, alt_branch)
                        except GitHubError:
                            continue
                
                raise GitHubError(
                    f"Repository not found: {owner}/{repo} (branch: {branch}). "
                    f"Please check if the repository exists and is public."
                ) from e
            elif e.response.status_code == 403:
                raise GitHubError(
                    f"Access denied to repository: {owner}/{repo}. "
                    f"The repository might be private or rate-limited."
                ) from e
        
        raise GitHubError(f"Failed to download from {zip_url}: {e}") from e


def extract_zip_to_temp(zip_content: bytes, repo: str, branch: str = "main") -> Path:
    """
    Extract ZIP content to a temporary directory.
    
    Args:
        zip_content: ZIP file content as bytes
        repo: Repository name
        branch: Branch name (default: "main")
        
    Returns:
        Path to the extracted repository directory
        
    Raises:
        GitHubError: If extraction fails
    """
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"spclone_{repo}_"))
        zip_path = temp_dir / f"{repo}.zip"
        
        # Save ZIP file
        print(f"Saving ZIP to temporary location...")
        with open(zip_path, "wb") as f:
            f.write(zip_content)
        
        # Extract ZIP
        print(f"Extracting ZIP archive...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the extracted folder (GitHub creates folder as repo-branch)
        extracted_folder = temp_dir / f"{repo}-{branch}"
        
        if not extracted_folder.exists():
            # Try to find any directory that was extracted
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]
            if extracted_dirs:
                extracted_folder = extracted_dirs[0]
                print(f"Using extracted directory: {extracted_folder.name}")
            else:
                raise GitHubError(f"No valid directory found in extracted ZIP for {repo}")
        
        return extracted_folder
        
    except (zipfile.BadZipFile, OSError) as e:
        raise GitHubError(f"Failed to extract ZIP file for {repo}: {e}") from e


def check_build_requirements(extracted_folder: Path) -> List[str]:
    """
    Check if the package has complex build requirements.
    
    Args:
        extracted_folder: Path to extracted repository
        
    Returns:
        List of missing build requirements
    """
    missing_reqs = []
    
    # Check for common build requirements
    build_indicators = {
        'Cython': ['*.pyx', '*.pxd'],
        'numpy': ['setup.py'],  # Many packages need numpy for building
        'setuptools_scm': ['pyproject.toml', 'setup.cfg'],
        'wheel': ['pyproject.toml', 'setup.py'],
    }
    
    # Check for C/C++ extensions
    c_extensions = list(extracted_folder.glob('**/*.c')) + list(extracted_folder.glob('**/*.cpp'))
    if c_extensions:
        print(f"Found C/C++ extensions: {len(c_extensions)} files")
        missing_reqs.extend(['build-essential', 'python-dev'])
    
    # Check for Cython files
    cython_files = list(extracted_folder.glob('**/*.pyx')) + list(extracted_folder.glob('**/*.pxd'))
    if cython_files:
        print(f"Found Cython files: {len(cython_files)} files")
        missing_reqs.append('Cython')
    
    # Check pyproject.toml for build requirements
    pyproject_file = extracted_folder / 'pyproject.toml'
    if pyproject_file.exists():
        try:
            content = pyproject_file.read_text()
            if 'build-system' in content:
                print("Found build-system configuration in pyproject.toml")
                if 'setuptools_scm' in content:
                    missing_reqs.append('setuptools_scm')
                if 'Cython' in content:
                    missing_reqs.append('Cython')
                if 'numpy' in content:
                    missing_reqs.append('numpy')
        except Exception as e:
            print(f"Warning: Could not parse pyproject.toml: {e}")
    
    return list(set(missing_reqs))  # Remove duplicates


def install_build_dependencies(requirements: List[str]) -> None:
    """
    Install build dependencies before main installation.
    
    Args:
        requirements: List of build dependencies to install
    """
    if not requirements:
        return
    
    print(f"Installing build dependencies: {', '.join(requirements)}")
    
    # Filter out system dependencies (can't install via pip)
    pip_requirements = [req for req in requirements if req not in ['build-essential', 'python-dev']]
    
    if pip_requirements:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade"] + pip_requirements,
                check=True,
                capture_output=True,
                text=True
            )
            print("Build dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install some build dependencies: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")


def clone_helper(owner: str, repo: str, branch: str = "main", target_dir: Optional[Path] = None) -> Path:
    """
    Clone a GitHub repository by downloading and extracting it.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        branch: Branch name (default: "main")
        target_dir: Target directory (default: current_dir/owner-repo)
        
    Returns:
        Path to the cloned repository
        
    Raises:
        GitHubError: If cloning fails
    """
    try:
        # Download ZIP
        zip_content = download_github_zip(owner, repo, branch)
        
        # Extract to temporary location
        extracted_folder = extract_zip_to_temp(zip_content, repo, branch)
        
        # Determine target directory
        if target_dir is None:
            current_dir = Path.cwd()
            target_folder = current_dir / f"{owner}-{repo}"
        else:
            target_folder = Path(target_dir)
        
        # Remove existing folder if it exists
        if target_folder.exists():
            print(f"Removing existing folder: {target_folder}")
            shutil.rmtree(target_folder)
        
        # Move to target location
        shutil.move(str(extracted_folder), str(target_folder))
        
        # Clean up temp directory
        shutil.rmtree(extracted_folder.parent)
        
        print(f"Successfully cloned {owner}/{repo} to {target_folder}")
        return target_folder
        
    except Exception as e:
        if isinstance(e, (GitHubError, InstallationError)):
            raise
        raise GitHubError(f"Unexpected error during cloning {owner}/{repo}: {e}") from e


def install_helper(owner: str, repo: str, branch: str = "main", force_build: bool = False) -> None:
    """
    Install a Python package from a GitHub repository.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        branch: Branch name (default: "main")
        force_build: Force building from source even if wheel exists
        
    Raises:
        GitHubError: If download fails
        InstallationError: If installation fails
    """
    extracted_folder = None
    temp_parent = None
    
    try:
        # For complex packages, try pip install from git first
        if not force_build and repo.lower() in ['pandas', 'numpy', 'scipy', 'matplotlib', 'scikit-learn']:
            git_url = f"git+https://github.com/{owner}/{repo}.git@{branch}"
            print(f"Attempting to install {owner}/{repo} directly from git (recommended for complex packages)...")
            
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", git_url],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout for complex builds
                )
                print("Installation completed successfully via git!")
                if result.stdout:
                    print("Installation output:")
                    print(result.stdout)
                return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"Git installation failed, falling back to ZIP method: {e}")
        
        # Download ZIP
        zip_content = download_github_zip(owner, repo, branch)
        
        # Extract to temporary location
        extracted_folder = extract_zip_to_temp(zip_content, repo, branch)
        temp_parent = extracted_folder.parent
        
        # Check if it's a valid Python package
        setup_files = ['setup.py', 'pyproject.toml', 'setup.cfg']
        has_setup = any((extracted_folder / setup_file).exists() for setup_file in setup_files)
        
        if not has_setup:
            print(f"Warning: No setup files found in {owner}/{repo}. "
                  f"This might not be a valid Python package.")
        
        # Check for complex build requirements
        build_reqs = check_build_requirements(extracted_folder)
        if build_reqs:
            print(f"Detected complex build requirements for {owner}/{repo}")
            install_build_dependencies(build_reqs)
        
        # Install the package
        print(f"Installing {owner}/{repo} from {extracted_folder}...")
        
        # Use different strategies based on package complexity
        install_cmd = [sys.executable, "-m", "pip", "install"]
        
        # Add build options for complex packages
        if build_reqs or repo.lower() in ['pandas', 'numpy', 'scipy']:
            install_cmd.extend([
                "--no-build-isolation",  # Allow using pre-installed build deps
                "--verbose",  # Show build progress
            ])
        
        install_cmd.extend(["--upgrade", str(extracted_folder)])
        
        print(f"Running: {' '.join(install_cmd)}")
        
        result = subprocess.run(
            install_cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout for very complex builds
        )
        
        print("Installation completed successfully!")
        
        # Show installation output if verbose or if there were warnings
        if result.stdout and (build_reqs or "warning" in result.stdout.lower()):
            print("Installation output:")
            print(result.stdout)
        
    except subprocess.TimeoutExpired as e:
        raise InstallationError(
            f"Installation of {owner}/{repo} timed out. "
            f"This package might be too complex to build from source. "
            f"Consider installing from PyPI instead: pip install {repo}"
        ) from e
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to install {owner}/{repo}: {e}"
        
        # Provide helpful error messages for common issues
        if e.stderr:
            stderr_lower = e.stderr.lower()
            if "microsoft visual c++" in stderr_lower or "cl.exe" in stderr_lower:
                error_msg += (
                    f"\n\nThis appears to be a C++ compilation error on Windows. "
                    f"Try installing Microsoft C++ Build Tools or Visual Studio."
                )
            elif "gcc" in stderr_lower or "compilation failed" in stderr_lower:
                error_msg += (
                    f"\n\nThis appears to be a compilation error. "
                    f"Make sure you have the necessary build tools installed."
                )
            elif "cython" in stderr_lower:
                error_msg += (
                    f"\n\nThis package requires Cython. Try: pip install Cython"
                )
            elif "numpy" in stderr_lower and "import" in stderr_lower:
                error_msg += (
                    f"\n\nThis package requires NumPy for building. Try: pip install numpy"
                )
            
            error_msg += f"\nError details: {e.stderr}"
        
        # Suggest alternatives for well-known complex packages
        if repo.lower() in ['pandas', 'numpy', 'scipy', 'matplotlib']:
            error_msg += (
                f"\n\nSuggestion: Complex packages like {repo} are usually better "
                f"installed from PyPI: pip install {repo}"
            )
        
        raise InstallationError(error_msg) from e
        
    except Exception as e:
        if isinstance(e, (GitHubError, InstallationError)):
            raise
        raise InstallationError(f"Unexpected error during installation of {owner}/{repo}: {e}") from e
        
    finally:
        # Clean up temporary directory
        if temp_parent and temp_parent.exists():
            try:
                shutil.rmtree(temp_parent)
            except OSError as e:
                print(f"Warning: Failed to clean up temporary directory {temp_parent}: {e}")


def install_from_github_with_url(repo_url: str, branch: str = "main", force_build: bool = False) -> None:
    """
    Download a GitHub repository from URL and install it as a Python package.
    
    Args:
        repo_url: GitHub repository URL or owner/repo format
        branch: Branch name (default: "main")
        force_build: Force building from source even for complex packages
        
    Raises:
        GitHubError: If URL parsing or download fails
        InstallationError: If installation fails
        
    Examples:
        >>> install_from_github_with_url('https://github.com/psf/requests')
        >>> install_from_github_with_url('psf/requests')
        >>> install_from_github_with_url('pandas-dev/pandas', force_build=True)
    """
    owner, repo = parse_github_url(repo_url)
    return install_helper(owner, repo, branch=branch, force_build=force_build)


def clone_github(repo_url: str, branch: str = "main", directory: Optional[str] = None) -> Path:
    """
    Clone a GitHub repository from URL.
    
    Args:
        repo_url: GitHub repository URL or owner/repo format
        branch: Branch name (default: "main")
        directory: Target directory name (optional)
        
    Returns:
        Path to the cloned repository
        
    Raises:
        GitHubError: If URL parsing or cloning fails
        
    Examples:
        >>> clone_github('https://github.com/psf/requests')
        >>> clone_github('psf/requests', directory='my-requests')
    """
    owner, repo = parse_github_url(repo_url)
    target_dir = Path(directory) if directory else None
    return clone_helper(owner, repo, branch=branch, target_dir=target_dir)


def install_from_github_owner_repo(owner: str, repo: str, branch: str = "main", force_build: bool = False) -> None:
    """
    Install a Python package from GitHub using owner and repo name.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        branch: Branch name (default: "main")
        force_build: Force building from source even for complex packages
        
    Raises:
        GitHubError: If download fails
        InstallationError: If installation fails
        
    Examples:
        >>> install_from_github_owner_repo('psf', 'requests')
        >>> install_from_github_owner_repo('pandas-dev', 'pandas', force_build=True)
    """
    return install_helper(owner, repo, branch=branch, force_build=force_build)


def install_from_github(repo_url: str, branch: str = "main", force_build: bool = False) -> None:
    """
    Alias for install_from_github_with_url for backward compatibility.
    
    Args:
        repo_url: GitHub repository URL or owner/repo format
        branch: Branch name (default: "main")
        force_build: Force building from source even for complex packages
        
    Raises:
        GitHubError: If URL parsing or download fails
        InstallationError: If installation fails
    """
    return install_from_github_with_url(repo_url, branch=branch, force_build=force_build)


# For backward compatibility and convenience
def download_and_install_github_repo(repo_url: str, branch: str = "main") -> None:
    """
    Legacy function name - use install_from_github_with_url instead.
    
    Args:
        repo_url: GitHub repository URL
        branch: Branch name (default: "main")
        
    Raises:
        GitHubError: If URL parsing or download fails
        InstallationError: If installation fails
    """
    import warnings
    warnings.warn(
        "download_and_install_github_repo is deprecated, use install_from_github_with_url instead",
        DeprecationWarning,
        stacklevel=2
    )
    return install_from_github_with_url(repo_url, branch=branch)