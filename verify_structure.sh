#!/bin/bash
# verify_structure.sh - Validate project structure

set -e

PACKAGE_NAME="illustrative_vocabulary_mcp"
FAILED=0

echo "=== Verifying Project Structure ==="
echo ""

# Check directories
echo "Checking directories..."
for dir in "src" "src/$PACKAGE_NAME" "src/$PACKAGE_NAME/ologs" "tests" "tests/fixtures" "docs"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/"
    else
        echo "✗ MISSING: $dir/"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Checking core files..."

# Check files
FILES=(
    "pyproject.toml:Project configuration"
    "README.md:Project documentation"
    ".gitignore:Git configuration"
    "setup.cfg:Pytest configuration"
    "tests/run_tests.sh:Test runner script"
    "src/$PACKAGE_NAME/__init__.py:Package init"
    "tests/__init__.py:Tests init"
)

for file_info in "${FILES[@]}"; do
    IFS=":" read -r file desc <<< "$file_info"
    if [ -f "$file" ]; then
        echo "✓ $file ($desc)"
    else
        echo "✗ MISSING: $file ($desc)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Checking main server file..."
if [ -f "src/$PACKAGE_NAME/server.py" ]; then
    echo "✓ src/$PACKAGE_NAME/server.py (main server)"
    python -m py_compile "src/$PACKAGE_NAME/server.py" && echo "  ✓ Syntax valid" || echo "  ✗ Syntax error"
else
    echo "⚠ src/$PACKAGE_NAME/server.py (to be added manually)"
fi

echo ""
echo "Checking test files..."
TEST_COUNT=$(find tests -name "test_*.py" -type f | wc -l)
if [ $TEST_COUNT -gt 0 ]; then
    echo "✓ Found $TEST_COUNT test file(s)"
    find tests -name "test_*.py" -type f | sed 's/^/  - /'
else
    echo "⚠ No test files yet (expected, to be added manually)"
fi

echo ""
echo "Checking olog files..."
OLOG_COUNT=$(find "src/$PACKAGE_NAME/ologs" -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l)
if [ $OLOG_COUNT -gt 0 ]; then
    echo "✓ Found $OLOG_COUNT olog file(s)"
    find "src/$PACKAGE_NAME/ologs" \( -name "*.yaml" -o -name "*.yml" \) | sed 's/^/  - /'
else
    echo "⚠ No olog files yet (expected if using dict-based taxonomy)"
fi

echo ""
echo "=== Verification Summary ==="
if [ $FAILED -eq 0 ]; then
    echo "✅ Structure verified successfully!"
    echo ""
    echo "Ready for next steps:"
    echo "1. Copy server.py to src/$PACKAGE_NAME/"
    echo "2. Copy test files to tests/"
    echo "3. pip install -e \".[dev]\" from project root"
    echo "4. ./tests/run_tests.sh"
    exit 0
else
    echo "❌ $FAILED issue(s) found!"
    echo ""
    echo "Fix with: ./create_structure.sh"
    exit 1
fi
