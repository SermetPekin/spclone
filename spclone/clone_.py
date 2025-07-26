"""
GitHub repository cloning and installation utilities.

This module provides functions to download, clone, and install Python packages
directly from GitHub repositories using ZIP archives.
"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple
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
        response = requests.get(zip_url, timeout=30)
        response.raise_for_status()
        
        if len(response.content) == 0:
            raise GitHubError(f"Downloaded ZIP file is empty for {owner}/{repo}")
        
        return response.content
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
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
        with open(zip_path, "wb") as f:
            f.write(zip_content)
        
        # Extract ZIP
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the extracted folder (GitHub creates folder as repo-branch)
        extracted_folder = temp_dir / f"{repo}-{branch}"
        
        if not extracted_folder.exists():
            # Try to find any directory that was extracted
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]
            if extracted_dirs:
                extracted_folder = extracted_dirs[0]
            else:
                raise GitHubError(f"No valid directory found in extracted ZIP for {repo}")
        
        return extracted_folder
        
    except (zipfile.BadZipFile, OSError) as e:
        raise GitHubError(f"Failed to extract ZIP file for {repo}: {e}") from e


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


def install_helper(owner: str, repo: str, branch: str = "main") -> None:
    """
    Install a Python package from a GitHub repository.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        branch: Branch name (default: "main")
        
    Raises:
        GitHubError: If download fails
        InstallationError: If installation fails
    """
    extracted_folder = None
    temp_parent = None
    
    try:
        # Download ZIP
        zip_content = download_github_zip(owner, repo, branch)
        
        # Extract to temporary location
        extracted_folder = extract_zip_to_temp(zip_content, repo, branch)
        temp_parent = extracted_folder.parent
        
        # Check if it's a valid Python package
        setup_files = ['setup.py', 'pyproject.toml', 'setup.cfg']
        if not any((extracted_folder / setup_file).exists() for setup_file in setup_files):
            print(f"Warning: No setup files found in {owner}/{repo}. "
                  f"This might not be a valid Python package.")
        
        # Install the package
        print(f"Installing {owner}/{repo} from {extracted_folder}...")
        
        # Use pip install with explicit upgrade flag
        result = subprocess.run(
            ["pip", "install", "--upgrade", str(extracted_folder)], 
            check=True,
            capture_output=True,
            text=True
        )
        
        print("Installation completed successfully!")
        
        # Show installation output if verbose
        if result.stdout:
            print("Installation output:")
            print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to install {owner}/{repo}: {e}"
        if e.stderr:
            error_msg += f"\nError details: {e.stderr}"
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


def install_from_github_with_url(repo_url: str, branch: str = "main") -> None:
    """
    Download a GitHub repository from URL and install it as a Python package.
    
    Args:
        repo_url: GitHub repository URL or owner/repo format
        branch: Branch name (default: "main")
        
    Raises:
        GitHubError: If URL parsing or download fails
        InstallationError: If installation fails
        
    Examples:
        >>> install_from_github_with_url('https://github.com/psf/requests')
        >>> install_from_github_with_url('psf/requests')
    """
    owner, repo = parse_github_url(repo_url)
    return install_helper(owner, repo, branch=branch)


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


def install_from_github_owner_repo(owner: str, repo: str, branch: str = "main") -> None:
    """
    Install a Python package from GitHub using owner and repo name.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        branch: Branch name (default: "main")
        
    Raises:
        GitHubError: If download fails
        InstallationError: If installation fails
        
    Examples:
        >>> install_from_github_owner_repo('psf', 'requests')
    """
    return install_helper(owner, repo, branch=branch)


def install_from_github(repo_url: str, branch: str = "main") -> None:
    """
    Alias for install_from_github_with_url for backward compatibility.
    
    Args:
        repo_url: GitHub repository URL or owner/repo format
        branch: Branch name (default: "main")
        
    Raises:
        GitHubError: If URL parsing or download fails
        InstallationError: If installation fails
    """
    return install_from_github_with_url(repo_url, branch=branch)


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