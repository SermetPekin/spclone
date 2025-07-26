import argparse
import re
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
    # Remove any trailing .git
    input_str = input_str.rstrip('.git')
    
    # If it's already a full URL, return as is
    if input_str.startswith(('http://', 'https://')):
        return input_str
    
    # If it's in owner/repo format, convert to full URL
    if re.match(r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$', input_str):
        return f'https://github.com/{input_str}'
    
    # If it looks like a GitHub URL without protocol, add https
    if input_str.startswith('github.com/'):
        return f'https://{input_str}'
    
    # Otherwise, assume it's already in the correct format or handle as error
    return input_str


def main():
    """Entry point for spinstall command - install a package from GitHub."""
    parser = argparse.ArgumentParser(
        prog='spinstall',
        description="Install a package from GitHub repository.",
        epilog="Examples:\n"
               "  spinstall psf/requests\n"
               "  spinstall https://github.com/psf/requests\n"
               "  spinstall github.com/psf/requests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'repo', 
        help="GitHub repository (owner/repo) or full GitHub URL"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output"
    )
    
    try:
        args = parser.parse_args()
        url = normalize_github_input(args.repo)
        
        if args.verbose:
            print(f"Installing from: {url}")
            
        install_from_github_with_url(url)
        
    except Exception as e:
        print(f"Error: {e}")
        parser.print_help()
        return 1
    
    return 0


def clone():
    """Entry point for spclone command - clone a repository from GitHub."""
    parser = argparse.ArgumentParser(
        prog='spclone',
        description="Clone a repository from GitHub.",
        epilog="Examples:\n"
               "  spclone psf/requests\n"
               "  spclone https://github.com/psf/requests\n"
               "  spclone github.com/psf/requests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'repo', 
        help="GitHub repository (owner/repo) or full GitHub URL"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output"
    )
    parser.add_argument(
        '-d', '--directory',
        help="Directory to clone into (optional)"
    )
    
    try:
        args = parser.parse_args()
        url = normalize_github_input(args.repo)
        
        if args.verbose:
            print(f"Cloning from: {url}")
            
        # Pass directory argument if your clone_github function supports it
        if hasattr(clone_github, '__code__') and 'directory' in clone_github.__code__.co_varnames:
            clone_github(url, directory=args.directory)
        else:
            clone_github(url)
            
    except Exception as e:
        print(f"Error: {e}")
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    # For testing purposes
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'clone':
        sys.argv.pop(1)  # Remove 'clone' from args
        clone()
    else:
        main()