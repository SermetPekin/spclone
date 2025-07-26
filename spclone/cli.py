import argparse
import re
import sys
import platform
from spclone.clone_ import install_from_github_with_url, clone_github


def normalize_github_input(input_str):
    """
    Normalize GitHub input to a full URL.
    
    Args:
        input_str: Either a full GitHub URL or shorthand format like 'owner/repo'
        
    Returns:
        str: Full GitHub URL
        
    Examples:
        normalize_github_input('psf/requests') -> 'https://github.com/psf/requests'
        normalize_github_input('https://github.com/psf/requests') -> 'https://github.com/psf/requests'
    """
    if not input_str:
        raise ValueError("Repository input cannot be empty")
    
    # Remove whitespace first
    input_str = input_str.strip()
    
    # Only remove .git suffix if it actually ends with .git (not just contains those characters)
    if input_str.endswith('.git'):
        input_str = input_str[:-4]
    
    # If it's already a full URL, return as is
    if input_str.startswith(('http://', 'https://')):
        return input_str
    
    # If it's in owner/repo format, convert to full URL
    if re.match(r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$', input_str):
        return f'https://github.com/{input_str}'
    
    # If it looks like a GitHub URL without protocol, add https
    if input_str.startswith('github.com/'):
        return f'https://{input_str}'
    
    # Otherwise, return as is and let the underlying function handle validation
    return input_str


def print_windows_build_help():
    """Print helpful information for Windows build issues."""
    print("\n" + "="*60)
    print("🪟 WINDOWS BUILD TOOLS REQUIRED")
    print("="*60)
    print("This package requires C++ compilation on Windows.")
    print("Please install Microsoft C++ Build Tools:")
    print()
    print("Option 1 - Visual Studio Build Tools (Recommended):")
    print("  https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    print("  - Download and install 'Build Tools for Visual Studio'")
    print("  - Select 'C++ build tools' workload")
    print("  - Include 'Windows 10/11 SDK'")
    print()
    print("Option 2 - Full Visual Studio Community (Free):")
    print("  https://visualstudio.microsoft.com/vs/community/")
    print("  - Install with 'Desktop development with C++' workload")
    print()
    print("Option 3 - Alternative approach:")
    print("  Try installing pre-compiled version from PyPI:")
    print(f"  pip install {extract_package_name_from_error()}")
    print()
    print("After installing build tools, restart your terminal and try again.")
    print("="*60)


def extract_package_name_from_error():
    """Extract likely package name from current context."""
    # This is a simple heuristic - in a real implementation you'd want to
    # track which package was being installed when the error occurred
    return "package-name"


def check_windows_build_environment():
    """Check if Windows has proper build environment."""
    if platform.system() != 'Windows':
        return True
    
    import subprocess
    try:
        # Try to find vswhere.exe
        result = subprocess.run(['where', 'vswhere'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check for Visual Studio installation paths
    vs_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"
    ]
    
    for vs_path in vs_paths:
        if os.path.exists(vs_path):
            return True
    
    return False


def main():
    """Entry point for spinstall command - install a package from GitHub."""
    parser = argparse.ArgumentParser(
        prog='spinstall',
        description="Install a package from GitHub repository.",
        epilog="""Examples:
  spinstall psf/requests
  spinstall https://github.com/psf/requests
  spinstall github.com/psf/requests
  spinstall microsoft/vscode

Windows Users:
  Some packages require Visual C++ Build Tools.
  Use --check-build-tools to verify your setup.""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'repo', 
        nargs='?',  # Make repo optional when using --check-build-tools
        help="GitHub repository in 'owner/repo' format or full GitHub URL"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output"
    )
    
    parser.add_argument(
        '--check-build-tools',
        action='store_true',
        help="Check if Windows build tools are available (Windows only)"
    )
    
    parser.add_argument(
        '--install-build-help',
        action='store_true',
        help="Show help for installing build tools on Windows"
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='spclone 1.0.0'
    )
    
    try:
        args = parser.parse_args()
        
        # Handle special flags
        if args.install_build_help:
            print_windows_build_help()
            return
        
        if args.check_build_tools:
            if platform.system() == 'Windows':
                has_build_tools = check_windows_build_environment()
                if has_build_tools:
                    print("✅ Windows build tools appear to be available")
                else:
                    print("❌ Windows build tools not found")
                    print("Run 'spinstall --install-build-help' for installation instructions")
            else:
                print("Build tools check is only available on Windows")
            return
        
        # Require repo argument for actual installation
        if not args.repo:
            parser.error("Repository argument is required for installation")
        
        if args.verbose:
            print(f"spinstall: Processing repository '{args.repo}'")
            if platform.system() == 'Windows':
                has_build_tools = check_windows_build_environment()
                print(f"spinstall: Windows build tools available: {has_build_tools}")
        
        url = normalize_github_input(args.repo)
        
        if args.verbose:
            print(f"spinstall: Installing from {url}")
        
        # Pre-check for Windows build tools for known complex packages
        if platform.system() == 'Windows':
            complex_packages = ['pandas', 'numpy', 'scipy', 'matplotlib', 'scikit-learn']
            repo_name = url.split('/')[-1].lower()
            if any(pkg in repo_name for pkg in complex_packages):
                if not check_windows_build_environment():
                    print(f"⚠️  Warning: {repo_name} requires C++ compilation on Windows")
                    print("If installation fails, run 'spinstall --install-build-help'")
                    print()
        
        install_from_github_with_url(url)
        
        if args.verbose:
            print("spinstall: Installation completed successfully")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        print(f"spinstall: Error - {error_msg}", file=sys.stderr)
        
        # Provide Windows-specific help for build errors
        if platform.system() == 'Windows' and any(keyword in error_msg.lower() for keyword in 
                                                 ['vswhere', 'microsoft visual c++', 'build tools', 'compiler']):
            print("\n" + "="*50, file=sys.stderr)
            print("This looks like a Windows build tools issue!", file=sys.stderr)
            print("Run: spinstall --install-build-help", file=sys.stderr)
            print("="*50, file=sys.stderr)
        
        sys.exit(1)


def clone():
    """Entry point for spclone command - clone a repository from GitHub."""
    parser = argparse.ArgumentParser(
        prog='spclone',
        description="Clone a repository from GitHub.",
        epilog="""Examples:
  spclone psf/requests
  spclone https://github.com/psf/requests
  spclone github.com/psf/requests
  spclone microsoft/vscode""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'repo', 
        help="GitHub repository in 'owner/repo' format or full GitHub URL"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output"
    )
    
    parser.add_argument(
        '-d', '--directory',
        help="Directory to clone into (defaults to repository name)"
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='spclone 1.0.0'
    )
    
    try:
        args = parser.parse_args()
        
        if args.verbose:
            print(f"spclone: Processing repository '{args.repo}'")
        
        url = normalize_github_input(args.repo)
        
        if args.verbose:
            print(f"spclone: Cloning from {url}")
            if args.directory:
                print(f"spclone: Target directory: {args.directory}")
        
        # Check if clone_github function accepts directory parameter
        import inspect
        
        clone_signature = inspect.signature(clone_github)
        
        if 'directory' in clone_signature.parameters and args.directory:
            clone_github(url, directory=args.directory)
        else:
            clone_github(url)
        
        if args.verbose:
            print("spclone: Clone completed successfully")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"spclone: Error - {e}", file=sys.stderr)
        sys.exit(1)


# For direct module execution (testing purposes)
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-clone":
        sys.argv = ["spclone"] + sys.argv[2:]  # Remove --test-clone
        clone()
    else:
        main()