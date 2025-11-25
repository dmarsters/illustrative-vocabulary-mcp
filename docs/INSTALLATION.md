# Installation Guide

## Prerequisites
- Python 3.10+
- pip

## Development Installation

1. From project root (where pyproject.toml lives):
```bash
pip install -e ".[dev]"
```

2. Verify installation:
```bash
python -m illustrative_vocabulary_mcp --help
```

3. Run tests:
```bash
./tests/run_tests.sh
```

## Common Errors

**Error: "No module named 'illustrative_vocabulary_mcp'"**
- Ensure you ran `pip install -e ".[dev]"` from project root
- Check you're not inside src/ directory
- Verify pyproject.toml exists in project root

**Error: "ModuleNotFoundError" during tests**
- Reinstall: `pip install -e ".[dev]"`
- Clear cache: `rm -rf build/ dist/ *.egg-info/`
