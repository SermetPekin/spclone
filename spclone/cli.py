import argparse
from spclone.clone_ import install_from_github_with_url, clone_github


def main():
    parser = argparse.ArgumentParser(
        add_help=False, description="Install a package from github."
    )
    parser.add_argument("url", help="Path to the github repo")
    args = parser.parse_args()
    url = args.url
    install_from_github_with_url(url)


def clone():
    parser = argparse.ArgumentParser(
        add_help=False, description="Install a package from github."
    )
    parser.add_argument("url", help="Path to the github repo")
    args = parser.parse_args()
    url = args.url
    clone_github(url)
