#!/bin/bash
# tests/run_tests.sh - Run all tests

set -e

echo "Running tests..."
python -m pytest tests/ -v --tb=short

echo "All tests passed!"
