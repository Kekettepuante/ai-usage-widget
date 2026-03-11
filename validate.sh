#!/usr/bin/env bash
# Pre-release validation
set -euo pipefail

if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

echo "AI Usage Widget — Validation"
echo "============================="
echo ""

ERRORS=0

echo "Python syntax..."
if "$PYTHON" -m compileall -q ai_usage_widget ai_usage_widget.py 2>/dev/null; then
    echo "  OK"
else
    echo "  FAIL"; ((ERRORS++))
fi

echo "Lint..."
if "$PYTHON" -m ruff check . >/dev/null 2>&1 && "$PYTHON" -m ruff format --check . >/dev/null 2>&1; then
    echo "  OK"
else
    echo "  FAIL"; ((ERRORS++))
fi

echo "Shell scripts..."
if bash -n install.sh 2>/dev/null && bash -n uninstall.sh 2>/dev/null && bash -n upgrade.sh 2>/dev/null && bash -n validate.sh 2>/dev/null; then
    echo "  OK"
else
    echo "  FAIL"; ((ERRORS++))
fi

echo "Unit tests..."
if "$PYTHON" -m pytest -q >/dev/null 2>&1; then
    echo "  OK"
else
    echo "  FAIL"; ((ERRORS++))
fi

echo "Token leak check..."
if grep -rE "sk-ant-oat[0-9a-zA-Z_-]{50,}" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.pyc" >/dev/null 2>&1; then
    echo "  WARNING: real token found!"; ((ERRORS++))
else
    echo "  OK"
fi

echo "Required files..."
for f in LICENSE README.md ai_usage_widget.py install.sh uninstall.sh .gitignore; do
    if [ -f "$f" ]; then
        echo "  $f OK"
    else
        echo "  $f MISSING"; ((ERRORS++))
    fi
done

echo "Version..."
VERSION=$("$PYTHON" -c 'from ai_usage_widget import __version__; print(__version__)')
echo "  v$VERSION"

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "All checks passed."
else
    echo "$ERRORS error(s) found."
    exit 1
fi
