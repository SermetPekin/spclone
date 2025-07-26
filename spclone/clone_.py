import requests
import zipfile
import os
import subprocess
import tempfile
from pathlib import Path
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path


def clone_helper(owner, repo, branch="main"):
    # Download ZIP
    zip_url = f"https://github.com/{owner}/{repo}/archive/{branch}.zip"
    print(f"Downloading {zip_url}...")
    response = requests.get(zip_url)
    response.raise_for_status()

    # Target directory in current folder
    current_dir = Path.cwd()
    target_folder = current_dir / f"{owner}-{repo}"

    # Remove existing folder if it exists
    if target_folder.exists():
        print(f"Removing existing folder: {target_folder}")
        shutil.rmtree(target_folder)
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / f"{repo}.zip"
        # Save ZIP file
        with open(zip_path, "wb") as f:
            f.write(response.content)
        # Extract ZIP
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        # Find the extracted folder (GitHub creates folder as repo-branch)
        extracted_folder = Path(temp_dir) / f"{repo}-{branch}"

        # Move to target location with desired name
        shutil.move(str(extracted_folder), str(target_folder))

    print(f"Successfully cloned {owner}/{repo} to {target_folder}")
    return target_folder


def install_helper(owner, repo, branch="main"):
    # Download ZIP
    zip_url = f"https://github.com/{owner}/{repo}/archive/{branch}.zip"
    print(f"Downloading {zip_url}...")
    response = requests.get(zip_url)
    response.raise_for_status()
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / f"{repo}.zip"
        # Save ZIP file
        with open(zip_path, "wb") as f:
            f.write(response.content)
        # Extract ZIP
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        # Find the extracted folder
        extracted_folder = Path(temp_dir) / f"{repo}-{branch}"
        # Install the package
        print(f"Installing from {extracted_folder}...")
        subprocess.run(["pip", "install", str(extracted_folder)], check=True)
    print("Installation completed!")


def install_from_github_with_url(repo_url, branch="main"):
    """
    Download a GitHub repository as ZIP and install it
    """
    # Extract owner and repo name from URL
    # e.g., https://github.com/SermetPekin/smartrun
    repo_parts = repo_url.replace("https://github.com/", "").split("/")
    owner, repo = repo_parts[0], repo_parts[1]
    return install_helper(owner, repo, branch=branch)


def clone_github(repo_url: str, branch="main"):
    repo_parts = repo_url.replace("https://github.com/", "").split("/")
    owner, repo = repo_parts[0], repo_parts[1]
    clone_helper(owner, repo, branch=branch)


def install_from_github_owner_repo(owner, repo, branch="main"):
    return install_helper(owner, repo, branch=branch)


def install_from_github(repo_url, branch="main"):
    return install_from_github_with_url(repo_url, branch=branch)


# Usage
# download_and_install_github_repo("https://github.com/SermetPekin/smartrun")
