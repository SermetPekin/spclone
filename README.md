# spclone

[![Python package](https://github.com/SermetPekin/spclone/actions/workflows/python-package.yml/badge.svg?1)](https://github.com/SermetPekin/spclone/actions/workflows/python-package.yml?1)
[![PyPI](https://img.shields.io/pypi/v/spclone)](https://pypi.org/project/spclone/)
![PyPI Downloads](https://static.pepy.tech/badge/spclone?2)
![Status](https://img.shields.io/badge/status-maintained-yellow.svg)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/SermetPekin/spclone/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A lightweight CLI tool that lets you install and clone Python packages directly from GitHub — no need to manually `git clone` and install.

## 🚀 Features

- 📦 **Direct Installation**: Install packages directly from GitHub URLs or shorthand (`user/repo`)
- 🔧 **Modern Build Support**: Handles complex build systems (Meson, setuptools, wheel)
- 🐍 **Environment Integration**: Automatically uses `pip` to install in your current environment
- 🧼 **Clean Workflow**: No cluttered filesystem with temporary clone directories
- ⚡ **Fast & Lightweight**: Focused on Python package management
- 🌿 **Branch Support**: Install from specific branches or tags

## 📦 Installation

```bash
pip install spclone
```

## 🛠️ Usage

### Package Installation (`spinstall`)

Install Python packages directly from GitHub:

```bash
# Install from owner/repo format
spinstall pandas-dev/pandas
spinstall microsoft/pylance

# Install from full URLs
spinstall https://github.com/psf/requests
spinstall https://github.com/django/django

# Install from specific branch
spinstall pandas-dev/pandas --branch main
spinstall scikit-learn/scikit-learn -b develop

# Verbose output for debugging
spinstall numpy/numpy --verbose

# Force build from source (for complex packages)
spinstall pandas-dev/pandas --force-build
```

### Repository Cloning (`spclone`)

Clone repositories for development:

```bash
# Clone to default directory (owner-repo)
spclone pandas-dev/pandas
spclone https://github.com/psf/requests

# Clone to specific directory
spclone django/django --directory my-django-fork
spclone microsoft/vscode -d vscode-dev

# Clone specific branch
spclone pytorch/pytorch --branch nightly
spclone tensorflow/tensorflow -b r2.13

# Verbose output
spclone fastapi/fastapi --verbose
```

### Advanced Examples

```bash
# Install bleeding-edge pandas with verbose output
spinstall pandas-dev/pandas --branch main --verbose --force-build

# Clone multiple repositories
spclone numpy/numpy -d numpy-dev
spclone scipy/scipy -d scipy-dev
spclone matplotlib/matplotlib -d matplotlib-dev

# Install from .git URLs (automatically handled)
spinstall https://github.com/psf/requests.git
```

## 🏗️ Build System Support

`spclone` automatically detects and handles various Python build systems:

- **setuptools** - Traditional `setup.py` packages
- **PEP 518** - Modern `pyproject.toml` packages  
- **Meson** - Complex packages like pandas, numpy
- **Cython** - Packages with compiled extensions
- **Wheel** - Binary distributions

For complex packages (pandas, numpy, scipy), build dependencies are automatically installed:
- `meson-python`, `meson`, `ninja` for Meson-based packages
- `Cython` for packages with Cython extensions
- `setuptools`, `wheel` for standard packages

## 📋 Command Reference

### `spinstall` - Install Packages

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output |
| `--branch` | `-b` | Specify branch/tag to install from |
| `--force-build` | | Force building from source |
| `--version` | | Show version information |

### `spclone` - Clone Repositories

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output |
| `--branch` | `-b` | Specify branch/tag to clone |
| `--directory` | `-d` | Target directory name |
| `--version` | | Show version information |

## 🔍 Input Formats

All commands accept flexible input formats:

```bash
# All of these work:
spinstall psf/requests
spinstall https://github.com/psf/requests
spinstall github.com/psf/requests
spinstall psf/requests.git
```

## 💡 Use Cases

- **Development**: Quickly install development versions of packages
- **Testing**: Test against latest upstream changes
- **Contributing**: Install your fork for development
- **CI/CD**: Install specific versions in automated workflows
- **Research**: Use cutting-edge features not yet released

## 🐛 Troubleshooting


### Installation Issues

```bash
# For complex packages, try force-build mode
spinstall pandas-dev/pandas --force-build --verbose

# Check if build dependencies are installed
pip list | grep -E "(meson|ninja|cython)"
```

### Common Solutions

- **Build failures**: Use `--force-build` flag
- **Missing dependencies**: Enable `--verbose` to see detailed error messages
- **Network issues**: Check your internet connection and GitHub access
- **Permission errors**: Ensure you have write access to your Python environment

## 🏗️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/SermetPekin/spclone.git
cd spclone

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=spclone --cov-report=html
```

### Project Structure

```
spclone/
├── spclone/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   └── clone_.py       # Core functionality
├── tests/              # Test suite
├── pyproject.toml      # Project configuration
└── README.md
```


## 🪟 Windows Users

### Build Tools Required

Some Python packages (pandas, numpy, scipy, etc.) require C++ compilation on Windows. If you get errors about `vswhere.exe` or "Microsoft Visual C++ 14.0 is required":

```bash
# Check if build tools are available
spinstall --check-build-tools

# Get installation instructions
spinstall --install-build-help
```

### Quick Fix

**Option 1: Install Visual Studio Build Tools (Recommended)**
1. Download [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install with "C++ build tools" workload
3. Include "Windows 10/11 SDK"
4. Restart your terminal

**Option 2: Try pre-compiled packages first**
```bash
# Install from PyPI first (if available), then try development version
pip install pandas  # Get stable version first
spinstall pandas-dev/pandas  # Then try development version
```

### Common Issues

- **Long paths**: Windows has path length limits - temp directories use short names
- **File permissions**: Admin privileges may be needed for some installations
- **Antivirus software**: May interfere with compilation - add Python folder to exclusions
- 
### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Submit a pull request

## 📝 License

This project is licensed under the BSD-3-Clause License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for simpler Python package installation workflows
- Built on top of Python's excellent `pip` and `requests` libraries
- Thanks to the Python packaging community for modern build standards

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/SermetPekin/spclone/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/SermetPekin/spclone/discussions)
- 📧 **Contact**: Create an issue for support questions

---

