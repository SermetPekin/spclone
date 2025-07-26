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
    if not input_str:
        raise ValueError("Repository input cannot be empty")

    # Remove any trailing .git and whitespace
    input_str = input_str.strip().rstrip(".git")

    # If it's already a full URL, return as is
    if input_str.startswith(("http://", "https://")):
        return input_str

    # If it's in owner/repo format, convert to full URL
    if re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", input_str):
        return f"https://github.com/{input_str}"

    # If it looks like a GitHub URL without protocol, add https
    if input_str.startswith("github.com/"):
        return f"https://{input_str}"

    # Otherwise, return as is and let the underlying function handle validation
    return input_str


def main():
    """Entry point for spinstall command - install a package from GitHub."""
    parser = argparse.ArgumentParser(
        prog="spinstall",
        description="Install a package from GitHub repository.",
        epilog="""Examples:
  spinstall psf/requests
  spinstall https://github.com/psf/requests
  spinstall github.com/psf/requests
  spinstall microsoft/vscode""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "repo", help="GitHub repository in 'owner/repo' format or full GitHub URL"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="spclone 1.0.0",  # Update this to match your actual version
    )

    try:
        args = parser.parse_args()

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
        print(f"spinstall: Error - {e}", file=sys.stderr)
        sys.exit(1)


def clone():
    """Entry point for spclone command - clone a repository from GitHub."""
    parser = argparse.ArgumentParser(
        prog="spclone",
        description="Clone a repository from GitHub.",
        epilog="""Examples:
  spclone psf/requests
  spclone https://github.com/psf/requests
  spclone github.com/psf/requests
  spclone microsoft/vscode""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "repo", help="GitHub repository in 'owner/repo' format or full GitHub URL"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "-d",
        "--directory",
        help="Directory to clone into (defaults to repository name)",
    )

    parser.add_argument("--version", action="version", version="spclone 1.0.0")

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

        if "directory" in clone_signature.parameters and args.directory:
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
