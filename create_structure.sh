#!/bin/bash
# create_structure.sh - Generate MCP project structure automatically
# Usage: ./create_structure.sh

set -e

PROJECT_NAME="illustrative-vocabulary-mcp"
PACKAGE_NAME="illustrative_vocabulary_mcp"

echo "Creating directory structure for $PROJECT_NAME..."

# Create directory structure
mkdir -p src/$PACKAGE_NAME/ologs
mkdir -p tests/fixtures
mkdir -p docs

echo "✓ Directories created"

# Create __init__.py files
touch src/$PACKAGE_NAME/__init__.py
touch tests/__init__.py

echo "✓ __init__.py files created"

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# MCP
*.log
node_modules/
EOF

echo "✓ .gitignore created"

# Create setup.cfg for pytest
cat > setup.cfg << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers

[coverage:run]
source = src
omit =
    */site-packages/*
    */distutils/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
EOF

echo "✓ setup.cfg created"

# Create tests/run_tests.sh
mkdir -p tests
cat > tests/run_tests.sh << 'EOF'
#!/bin/bash
# tests/run_tests.sh - Run all tests

set -e

echo "Running tests..."
python -m pytest tests/ -v --tb=short

echo "All tests passed!"
EOF

chmod +x tests/run_tests.sh

echo "✓ tests/run_tests.sh created"

# Create docs/INSTALLATION.md
cat > docs/INSTALLATION.md << 'EOF'
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
EOF

echo "✓ docs/INSTALLATION.md created"

# Create empty README placeholder
touch docs/README_PLACEHOLDER.txt

echo ""
echo "✅ Structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Run: ./verify_structure.sh"
echo "2. Copy server.py to src/$PACKAGE_NAME/"
echo "3. Copy test files to tests/"
echo "4. Copy YAML ologs to src/$PACKAGE_NAME/ologs/"
echo "5. Run: pip install -e \".[dev]\" from project root"
echo "6. Run: ./tests/run_tests.sh"
