# Publishing ZON to PyPI - Complete Guide

## Prerequisites

1. **Install build tools**:
```bash
pip install --upgrade pip setuptools wheel twine build
```

2. **Create PyPI accounts**:
- TestPyPI: https://test.pypi.org/account/register/
- PyPI: https://pypi.org/account/register/

3. **Create API tokens** (recommended over passwords):
- TestPyPI: https://test.pypi.org/manage/account/#api-tokens
- PyPI: https://pypi.org/manage/account/#api-tokens

Save tokens securely - you'll need them!

---

## Step 1: Prepare Your Package

### 1.1 Verify Package Structure

Your structure should look like:
```
zon-format/
├── src/
│   └── zon/
│       ├── __init__.py
│       ├── encoder.py
│       ├── decoder.py
│       ├── constants.py
│       ├── exceptions.py
│       └── cli.py
├── pyproject.toml
├── MANIFEST.in
├── README.md
├── LICENSE
└── SPEC.md
```

### 1.2 Clean Previous Builds

```bash
cd /Users/roni/Developer/ZON/zon-format

# Remove old builds
rm -rf build/ dist/ *.egg-info
```

---

## Step 2: Build the Package

```bash
# Build distribution packages
python -m build

# This creates:
# dist/zon-format-1.0.0.tar.gz (source distribution)
# dist/zon_format-1.0.0-py3-none-any.whl (wheel distribution)
```

### Verify the build:
```bash
ls -lh dist/
# You should see both .tar.gz and .whl files
```

---

## Step 3: Upload to TestPyPI (Testing)

**Always test on TestPyPI first!**

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# username: __token__
# password: <your TestPyPI API token>
```

### Test Installation from TestPyPI:

```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ zon-format

# Test it works
python -c "import zon; print('ZON v1.0 installed!'); data = [{'id': 1}]; print(zon.encode(data))"

# If successful, deactivate and remove test env
deactivate
rm -rf test_env
```

---

## Step 4: Upload to PyPI (Production)

**Only after TestPyPI testing succeeds!**

```bash
# Upload to production PyPI
python -m twine upload dist/*

# You'll be prompted for:
# username: __token__
# password: <your PyPI API token>
```

### Verify on PyPI:

Visit: https://pypi.org/project/zon-format/

---

## Step 5: Test Production Installation

```bash
# In a fresh environment
pip install zon-format

# Test
python -c "import zon; print(zon.encode([{'test': 'success'}]))"
```

---

## Using .pypirc (Optional - Easier Authentication)

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**Security**: Make sure this file is only readable by you:
```bash
chmod 600 ~/.pypirc
```

Then you can upload without entering credentials:
```bash
twine upload --repository testpypi dist/*  # TestPyPI
twine upload dist/*                         # PyPI
```

---

## Updating Your Package (Future Versions)

### 1. Update version in `pyproject.toml`:
```toml
version = "1.0.1"  # or 1.1.0, 2.0.0, etc.
```

### 2. Clean and rebuild:
```bash
rm -rf build/ dist/ *.egg-info
python -m build
```

### 3. Upload new version:
```bash
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*                         # Then production
```

---

## Troubleshooting

### "File already exists"
- You cannot re-upload the same version
- Bump the version number in `pyproject.toml`

### "Invalid distribution"
- Check `pyproject.toml` syntax
- Ensure `src/zon/__init__.py` exists
- Verify `README.md` is present

### "Authentication failed"
- Double-check your API token
- Make sure you're using `__token__` as username
- Token should start with `pypi-`

### "Package name already taken"
- Choose a different name in `pyproject.toml`
- Current name: `zon-format`

---

## Quick Reference Commands

```bash
# Complete workflow
cd /Users/roni/Developer/ZON/zon-format

# 1. Clean
rm -rf build/ dist/ *.egg-info

# 2. Build
python -m build

# 3. Check package
twine check dist/*

# 4. Test on TestPyPI
twine upload --repository testpypi dist/*

# 5. Test installation
pip install --index-url https://test.pypi.org/simple/ zon-format

# 6. Upload to PyPI
twine upload dist/*
```

---

## Post-Publication Checklist

- [ ] Package appears on https://pypi.org/project/zon-format/
- [ ] README renders correctly on PyPI page
- [ ] Installation works: `pip install zon-format`
- [ ] Update GitHub README with PyPI badge:
  ```markdown
  [![PyPI](https://img.shields.io/pypi/v/zon-format.svg)](https://pypi.org/project/zon-format/)
  ```
- [ ] Announce on social media / relevant communities

---

**Congratulations! Your package is now on PyPI! 🎉**

Users can install with: `pip install zon-format`
