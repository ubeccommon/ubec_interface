#!/bin/bash
# Find Template Issues Script
# ===========================
# Searches through your templates to find the issues shown in screenshots

echo "=========================================="
echo "UBEC Template Issue Finder"
echo "=========================================="
echo

cd /srv/ubec-www/app || { echo "Error: Cannot find /srv/ubec-www/app"; exit 1; }

echo "[1/5] Searching for 'Unknown' in templates..."
echo "------------------------------------------"
if grep -rn "Unknown" templates/ 2>/dev/null; then
    echo "✗ Found 'Unknown' in templates - NEEDS FIXING"
else
    echo "✓ No 'Unknown' found in templates"
fi

echo
echo "[2/5] Checking token.element usage..."
echo "------------------------------------------"
if grep -rn "token\.element" templates/ 2>/dev/null; then
    echo "Found token.element usage (check if it's showing 'Unknown')"
else
    echo "✓ No direct token.element subscript usage found"
fi

echo
echo "[3/5] Checking token.name usage..."
echo "------------------------------------------"
if grep -rn "token\.name\|token\[.*name.*\]" templates/ 2>/dev/null; then
    echo "✓ Found token.name usage (good)"
else
    echo "⚠ No token.name found - this might be the issue!"
fi

echo
echo "[4/5] Checking health status templates..."
echo "------------------------------------------"
grep -rn "Unhealthy\|health_status\|network.*health" templates/ 2>/dev/null | head -10

echo
echo "[5/5] Listing all template files..."
echo "------------------------------------------"
find templates/ -name "*.html" 2>/dev/null

echo
echo "=========================================="
echo "RECOMMENDATIONS"
echo "=========================================="
echo
echo "To fix 'Unknown' token names:"
echo "  1. Find the file(s) listed in section [1/5]"
echo "  2. Replace 'Unknown' with '{{ token.name }}'"
echo
echo "To verify backend data:"
echo "  curl http://92.205.230.245:8000/api/v1/tokens | jq '.tokens[0]'"
echo
echo "To see full diagnostic:"
echo "  python3 diagnose_frontend_issues.py"
echo
