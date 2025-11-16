#!/bin/bash
# Quick Template Fix Script
# =========================
# Fixes the "Unknown" token name issue in UBEC templates

set -e  # Exit on error

echo "=========================================="
echo "UBEC Template Quick Fix"
echo "=========================================="
echo

# Check if we're in the right directory
if [ ! -d "templates" ]; then
    echo "❌ Error: Must run from /srv/ubec-www/app directory"
    echo "Run: cd /srv/ubec-www/app && ./quick_fix_templates.sh"
    exit 1
fi

# Create backup directory
BACKUP_DIR="templates/backups/auto_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Creating backups in: $BACKUP_DIR"

# Files to fix
FILES=(
    "templates/protocol.html"
    "templates/home.html"
)

# Backup files
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        echo "  ✓ Backed up: $(basename $file)"
    fi
done

echo
echo "Applying fixes..."
echo

# Fix 1: Replace token.get('element', 'Unknown') with token.element
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        sed -i "s/token\.get('element', 'Unknown')/token.element/g" "$file"
        echo "  ✓ Fixed element references in $(basename $file)"
    fi
done

# Fix 2: Replace token.get('element_symbol', 'Unknown')
# Note: This is a placeholder - actual fix needs template logic for emojis
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        # Remove the get() wrapper, let template handle missing field
        sed -i "s/token\.get('element_symbol', 'Unknown')/token.element_symbol/g" "$file"
        echo "  ✓ Fixed element_symbol references in $(basename $file)"
    fi
done

echo
echo "=========================================="
echo "MANUAL FIXES STILL NEEDED"
echo "=========================================="
echo
echo "The following changes are too complex for sed and need manual editing:"
echo

cat << 'EOF'
1. In templates/protocol.html around line 371:
   
   FIND:    <h3>{{ token.token_code }} - {{ token.element }}</h3>
   REPLACE: <h3>{{ token.name }}</h3>

2. In templates/home.html around line 491:
   
   FIND:    <h3 class="element-name">{{ token.element }}</h3>
   REPLACE: <h3 class="element-name">{{ token.name }}</h3>

3. For proper emoji symbols, replace element_symbol sections with:

   {% if token.element == 'air' %}
       <span class="token-symbol">🌬️</span>
   {% elif token.element == 'water' %}
       <span class="token-symbol">💧</span>
   {% elif token.element == 'earth' %}
       <span class="token-symbol">🌍</span>
   {% elif token.element == 'fire' %}
       <span class="token-symbol">🔥</span>
   {% endif %}
EOF

echo
echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo
echo "1. Complete the manual fixes above using:"
echo "   nano templates/protocol.html"
echo "   nano templates/home.html"
echo
echo "2. Restart the service:"
echo "   sudo systemctl restart ubec-www"
echo
echo "3. Clear browser cache (Ctrl+Shift+R)"
echo
echo "4. Verify changes:"
echo "   python3 diagnose_frontend_issues.py"
echo

echo "Backups saved in: $BACKUP_DIR"
echo
