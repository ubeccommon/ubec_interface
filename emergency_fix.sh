#!/bin/bash
# Emergency Template Fix Script
# Fixes both remaining unfixed attributes AND broken syntax from incorrect replacements

set -e  # Exit on error

TEMPLATES_DIR="/srv/ubec-www/app/templates"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${TEMPLATES_DIR}/backups_${TIMESTAMP}"

echo "=============================================="
echo "UBEC Template Emergency Fix"
echo "=============================================="
echo ""

# Create backup
echo "Creating backup..."
mkdir -p "$BACKUP_DIR"
cp "${TEMPLATES_DIR}/home.html" "$BACKUP_DIR/" 2>/dev/null || true
cp "${TEMPLATES_DIR}/protocol.html" "$BACKUP_DIR/" 2>/dev/null || true
cp "${TEMPLATES_DIR}/dashboard.html" "$BACKUP_DIR/" 2>/dev/null || true
echo "✓ Backups saved to: $BACKUP_DIR"
echo ""

# Fix home.html
echo "Fixing home.html..."

# Fix broken syntax patterns (compound attributes that were incorrectly split)
sed -i "s/token\.get('element', 'Unknown')_symbol/token.get('element_symbol', 'Unknown')/g" "${TEMPLATES_DIR}/home.html"
sed -i "s/token\.get('code', 'N\/A')_symbol/token.get('code_symbol', 'N\/A')/g" "${TEMPLATES_DIR}/home.html"

# Fix remaining unfixed attributes
sed -i 's/token\.total_supply/token.get("total_supply", 0)/g' "${TEMPLATES_DIR}/home.html"
sed -i 's/token\.name/token.get("name", "Unknown Token")/g' "${TEMPLATES_DIR}/home.html"
sed -i 's/token\.code/token.get("code", "N\/A")/g' "${TEMPLATES_DIR}/home.html"
sed -i 's/token\.element/token.get("element", "Unknown")/g' "${TEMPLATES_DIR}/home.html"
sed -i 's/token\.description/token.get("description", "")/g' "${TEMPLATES_DIR}/home.html"
sed -i 's/token\.element_symbol/token.get("element_symbol", "")/g' "${TEMPLATES_DIR}/home.html"

echo "✓ Fixed home.html"

# Fix protocol.html
echo "Fixing protocol.html..."

# Fix broken syntax patterns
sed -i "s/token\.get('element', 'Unknown')_symbol/token.get('element_symbol', 'Unknown')/g" "${TEMPLATES_DIR}/protocol.html"
sed -i "s/token\.get('code', 'N\/A')_symbol/token.get('code_symbol', 'N\/A')/g" "${TEMPLATES_DIR}/protocol.html"

# Fix remaining unfixed attributes
sed -i 's/token\.total_supply/token.get("total_supply", 0)/g' "${TEMPLATES_DIR}/protocol.html"
sed -i 's/token\.name/token.get("name", "Unknown Token")/g' "${TEMPLATES_DIR}/protocol.html"
sed -i 's/token\.code/token.get("code", "N\/A")/g' "${TEMPLATES_DIR}/protocol.html"
sed -i 's/token\.element/token.get("element", "Unknown")/g' "${TEMPLATES_DIR}/protocol.html"
sed -i 's/token\.description/token.get("description", "")/g' "${TEMPLATES_DIR}/protocol.html"
sed -i 's/token\.element_symbol/token.get("element_symbol", "")/g' "${TEMPLATES_DIR}/protocol.html"

echo "✓ Fixed protocol.html"

# Fix dashboard.html
echo "Fixing dashboard.html..."

# Fix watershed attributes
sed -i 's/watershed\.area_sqkm/watershed.get("area_sqkm", 0)/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/watershed\.name/watershed.get("name", "Unknown Watershed")/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/watershed\.feow_id/watershed.get("feow_id", 0)/g' "${TEMPLATES_DIR}/dashboard.html"

# Fix ecoregion attributes
sed -i 's/ecoregion\.name/ecoregion.get("name", "Unknown Ecoregion")/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/ecoregion\.biome/ecoregion.get("biome", "Unknown Biome")/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/ecoregion\.realm/ecoregion.get("realm", "Unknown Realm")/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/ecoregion\.eco_id/ecoregion.get("eco_id", 0)/g' "${TEMPLATES_DIR}/dashboard.html"

# Fix transaction attributes
sed -i 's/tx\.hash/tx.get("hash", "")/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/tx\.type/tx.get("type", "unknown")/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/tx\.amount/tx.get("amount", 0)/g' "${TEMPLATES_DIR}/dashboard.html"
sed -i 's/tx\.timestamp/tx.get("timestamp", "")/g' "${TEMPLATES_DIR}/dashboard.html"

echo "✓ Fixed dashboard.html"

echo ""
echo "=============================================="
echo "Fix Complete!"
echo "=============================================="
echo ""
echo "Changes made:"
echo "  • Fixed broken syntax (element_symbol, etc.)"
echo "  • Fixed remaining unfixed attributes"
echo "  • Applied safe .get() pattern throughout"
echo ""
echo "Backups saved to: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Restart service: sudo systemctl restart ubec-web"
echo "  2. Test pages: /, /protocol, /dashboard"
echo ""
