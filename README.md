# spclone
[![Python package](https://github.com/SermetPekin/spclone/actions/workflows/python-package.yml/badge.svg)](https://github.com/SermetPekin/spclone/actions/workflows/python-package.yml)
[![PyPI](https://img.shields.io/pypi/v/spclone)](https://img.shields.io/pypi/v/spclone) ![PyPI Downloads](https://static.pepy.tech/badge/spclone?2)![t](https://img.shields.io/badge/status-maintained-yellow.svg) [![](https://img.shields.io/github/license/SermetPekin/spclone.svg)](https://github.com/SermetPekin/spclone/blob/master/LICENSE.md) [![](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) 

# spclone

A lightweight CLI tool that lets you install Python packages directly from GitHub — no need to `git clone` and manually install.

---

## 🚀 Features

- 🔗 Install packages directly from GitHub URLs or shorthand (`user/repo`)
- 🐍 Automatically uses `pip` to install the package in your current environment
- 🧼 Avoids cluttering your filesystem with cloned directories
- 🧪 Lightweight and focused on Python package installation (not general cloning)

---

## 📦 Installation

```bash

pip install spclone

```

## Examples

```
spinstall pandas-dev/pandas
spinstall https://github.com/psf/requests
```

## Development 

```bash

git clone https://github.com/SermetPekin/spclone.git
cd spclone
pip install -e ".[dev]"

 
```