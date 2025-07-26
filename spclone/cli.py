import argparse
import re
import sys
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
    if not input_str or not input_str.strip():
        raise ValueError("Repository input cannot be empty")

    # Remove whitespace first
    input_str = input_str.strip()

    # If it's already a full URL, handle .git removal and return
    if input_str.startswith(("http://", "https://")):
        if input_str.endswith('.git'):
            input_str = input_str[:-4]
        return input_str

    # If it looks like a GitHub URL without protocol, add https and handle .git
    if input_str.startswith("github.com/"):
        if input_str.endswith('.git'):
            input_str = input_str[:-4]
        return f"https://{input_str}"

    # If it's in owner/repo format (with or without .git), convert to full URL
    owner_repo_pattern = r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+(?:\.git)?$"
    if re.match(owner_repo_pattern, input_str):
        if input_str.endswith('.git'):
            input_str = input_str[:-4]
        return f"https://github.com/{input_str}"

    # For anything else, return as-is (let the underlying function handle validation)
    return input_str


def main():
    """Entry point for spinstall command - install a package from GitHub."""
    parser = argparse.ArgumentParser(
        prog="spinstall",
        description="Install a package from GitHub repository with support for modern build systems.",
        epilog="""Examples:
  spinstall psf/requests
  spinstall pandas-dev/pandas
  spinstall https://github.com/psf/requests
  spinstall github.com/psf/requests
  spinstall microsoft/vscode --branch develop
  spinstall pandas-dev/pandas --force-build --verbose""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "repo", 
        help="GitHub repository in 'owner/repo' format or full GitHub URL"
    )

    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output with detailed build information"
    )

    parser.add_argument(
        "-b", "--branch",
        default="main",
        help="Branch to install from (default: main)"
    )

    parser.add_argument(
        "--force-build",
        action="store_true",
        help="Force building from ZIP source instead of using git+https method for complex packages"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="spclone 1.0.0",
    )

    try:
        args = parser.parse_args()

        if args.verbose:
            print(f"spinstall: Processing repository '{args.repo}' (branch: {args.branch})")
            if args.force_build:
                print("spinstall: Force build mode enabled")

        url = normalize_github_input(args.repo)

        if args.verbose:
            print(f"spinstall: Installing from {url}")

        install_from_github_with_url(url, branch=args.branch, force_build=args.force_build)

        if args.verbose:
            print("spinstall: Installation completed successfully")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"spinstall: Error - {e}", file=sys.stderr)
        if 'args' in locals() and hasattr(args, 'verbose') and args.verbose:
            import traceback
            print("\nFull traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


def clone():
    """Entry point for spclone command - clone a repository from GitHub."""
    parser = argparse.ArgumentParser(
        prog="spclone",
        description="Clone a repository from GitHub.",
        epilog="""Examples:
  spclone psf/requests
  spclone pandas-dev/pandas --branch develop
  spclone https://github.com/psf/requests
  spclone github.com/psf/requests
  spclone microsoft/vscode -d my-vscode-fork""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "repo", 
        help="GitHub repository in 'owner/repo' format or full GitHub URL"
    )

    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )

    parser.add_argument(
        "-b", "--branch",
        default="main",
        help="Branch to clone (default: main)"
    )

    parser.add_argument(
        "-d", "--directory",
        help="Directory to clone into (defaults to owner-repository format)"
    )

    parser.add_argument(
        "--version", 
        action="version", 
        version="spclone 1.0.0"
    )

    try:
        args = parser.parse_args()

        if args.verbose:
            print(f"spclone: Processing repository '{args.repo}' (branch: {args.branch})")

        url = normalize_github_input(args.repo)

        if args.verbose:
            print(f"spclone: Cloning from {url}")
            if args.directory:
                print(f"spclone: Target directory: {args.directory}")

        # Check if clone_github function accepts directory parameter
        import inspect

        clone_signature = inspect.signature(clone_github)

        # Pass all supported parameters
        kwargs = {"branch": args.branch}
        if "directory" in clone_signature.parameters and args.directory:
            kwargs["directory"] = args.directory

        clone_github(url, **kwargs)

        if args.verbose:
            print("spclone: Clone completed successfully")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"spclone: Error - {e}", file=sys.stderr)
        if 'args' in locals() and hasattr(args, 'verbose') and args.verbose:
            import traceback
            print("\nFull traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


# For direct module execution (testing purposes)
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-clone":
        sys.argv = ["spclone"] + sys.argv[2:]  # Remove --test-clone
        clone()
    else:
        main()