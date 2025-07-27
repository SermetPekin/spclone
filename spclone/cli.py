import argparse
import os
import re
import sys
import platform
from spclone.clone_ import install_from_github_with_url, clone_github

# Import our new Windows build tools
if platform.system() == 'Windows':
    from spclone.windows_build_tools import check_and_setup_windows_build_tools, print_windows_build_help, WindowsBuildTools
else:
    # Dummy functions for non-Windows
    def check_and_setup_windows_build_tools(verbose=False): return True
    def print_windows_build_help(): print("Windows build tools help is only available on Windows")
    WindowsBuildTools = None

def normalize_github_input(input_str):
    """
    Normalize GitHub input to a full URL.
    """
    if not input_str:
        raise ValueError("Repository input cannot be empty")
    input_str = input_str.strip()
    if input_str.endswith('.git'):
        input_str = input_str[:-4]
    if input_str.startswith(('http://', 'https://')):
        return input_str
    if re.match(r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$', input_str):
        return f'https://github.com/{input_str}'
    if input_str.startswith('github.com/'):
        return f'https://{input_str}'
    return input_str

def setup_rtools_env(rtools_gcc_path, verbose=False):
    """Set environment variables for Rtools GCC."""
    gcc_dir = os.path.dirname(rtools_gcc_path)
    gxx_path = rtools_gcc_path.replace("gcc.exe", "g++.exe")
    os.environ["CC"] = rtools_gcc_path
    os.environ["CXX"] = gxx_path
    os.environ["PATH"] = f"{gcc_dir};{os.environ['PATH']}"
    os.environ["DISTUTILS_USE_SDK"] = "1"
    os.environ["MSSdk"] = "1"
    if verbose:
        print(f"Using Rtools GCC at {rtools_gcc_path}")

def find_rtools_gcc():
    """Try to locate Rtools gcc.exe automatically."""
    possible_paths = [
        r"C:\rtools44\mingw64\bin\gcc.exe",
        r"C:\rtools43\mingw64\bin\gcc.exe",
        r"C:\rtools42\mingw64\bin\gcc.exe",
        r"C:\rtools40\mingw64\bin\gcc.exe",
        r"C:\Rtools\mingw64\bin\gcc.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    # Try searching PATH for gcc.exe containing "rtools"
    for p in os.environ.get("PATH", "").split(";"):
        if "rtools" in p.lower() and os.path.exists(os.path.join(p, "gcc.exe")):
            return os.path.join(p, "gcc.exe")
    return None

def main():
    """Entry point for spinstall command - install a package from GitHub."""
    parser = argparse.ArgumentParser(
        prog='spinstall',
        description="Install a package from GitHub repository.",
        epilog="""Examples:
  spinstall psf/requests
  spinstall pandas-dev/pandas --verbose
  spinstall https://github.com/psf/requests

Windows Users:
  spinstall --check-build-tools    # Check available build tools
  spinstall --build-help           # Installation guide for build tools
  spinstall --use-rtools           # Use Rtools GCC for building if detected
  spinstall --rtools-gcc PATH      # Specify path to Rtools gcc.exe manually
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'repo', 
        nargs='?',
        help="GitHub repository in 'owner/repo' format or full GitHub URL"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output including build tools status"
    )
    parser.add_argument(
        '--check-build-tools',
        action='store_true',
        help="Check available Windows build tools (Windows only)"
    )
    parser.add_argument(
        '--build-help',
        action='store_true',
        help="Show build tools installation guide (Windows only)"
    )
    parser.add_argument(
        '--use-rtools',
        action='store_true',
        help="Use Rtools GCC for building if detected (Windows only)"
    )
    parser.add_argument(
        '--rtools-gcc',
        type=str,
        help="Manually specify path to Rtools gcc.exe (Windows only)"
    )
    parser.add_argument(
        '--version',
        action='version',
        version='spclone 1.0.0'
    )
    
    try:
        args = parser.parse_args()
        # Handle special flags
        if args.build_help:
            print_windows_build_help()
            return
        if args.check_build_tools:
            if platform.system() == 'Windows':
                tools = WindowsBuildTools()
                tools.print_status_report()
            else:
                print("Build tools check is only available on Windows")
            return
        # Require repo argument for actual installation
        if not args.repo:
            parser.error("Repository argument is required for installation")
        # Check and setup build tools on Windows
        if platform.system() == 'Windows':
            build_tools_ok = check_and_setup_windows_build_tools(verbose=args.verbose)
            if not build_tools_ok:
                print("⚠️  Warning: No Windows build tools detected")
                print("Some packages may fail to install. Run 'spinstall --build-help' for help.")
                print()
            gcc_path = None
            if args.rtools_gcc:
                if os.path.exists(args.rtools_gcc):
                    gcc_path = args.rtools_gcc
                else:
                    print(f"Specified --rtools-gcc path not found: {args.rtools_gcc}", file=sys.stderr)
                    sys.exit(1)
            elif args.use_rtools:
                gcc_path = find_rtools_gcc()
                if not gcc_path:
                    print("Rtools gcc.exe not found automatically. Specify with --rtools-gcc.", file=sys.stderr)
                    sys.exit(1)
            if gcc_path:
                setup_rtools_env(gcc_path, verbose=args.verbose)
        if args.verbose:
            print(f"spinstall: Processing repository '{args.repo}'")
        url = normalize_github_input(args.repo)
        if args.verbose:
            print(f"spinstall: Installing from {url}")
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
                                                 ['vswhere', 'microsoft visual c++', 'build tools', 'compiler', 'gcc']):
            print("\n" + "="*50, file=sys.stderr)
            print("This looks like a Windows build tools issue!", file=sys.stderr)
            print("Run: spinstall --build-help", file=sys.stderr)
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
  spclone django/django --directory my-django""",
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

if __name__ == "__main__":
    main()