#!/bin/bash
# Comprehensive Fix for ALL Template Dict Attributes
# Handles token, holonic_scores, network_status, and other dict objects

set -e

TEMPLATES_DIR="/srv/ubec-www/app/templates"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${TEMPLATES_DIR}/backups_final_${TIMESTAMP}"

echo "=============================================="
echo "UBEC Template - Final Comprehensive Fix"
echo "=============================================="
echo ""

# Create backup
echo "Creating backups..."
mkdir -p "$BACKUP_DIR"
for file in home.html protocol.html dashboard.html; do
    if [ -f "${TEMPLATES_DIR}/${file}" ]; then
        cp "${TEMPLATES_DIR}/${file}" "$BACKUP_DIR/"
        echo "✓ Backed up: $file"
    fi
done
echo ""

# Function to safely replace dict attributes
fix_template() {
    local file=$1
    local filepath="${TEMPLATES_DIR}/${file}"
    
    if [ ! -f "$filepath" ]; then
        echo "⚠ Skipping $file (not found)"
        return
    fi
    
    echo "Fixing $file..."
    
    # Token attributes (if not already fixed)
    sed -i 's/\btoken\.total_supply\b/token.get("total_supply", 0)/g' "$filepath"
    sed -i 's/\btoken\.name\b/token.get("name", "Unknown")/g' "$filepath"
    sed -i 's/\btoken\.code\b/token.get("code", "N\/A")/g' "$filepath"
    sed -i 's/\btoken\.element\b/token.get("element", "Unknown")/g' "$filepath"
    sed -i 's/\btoken\.description\b/token.get("description", "")/g' "$filepath"
    sed -i 's/\btoken\.element_symbol\b/token.get("element_symbol", "")/g' "$filepath"
    sed -i 's/\btoken\.ubuntu_principle\b/token.get("ubuntu_principle", "")/g' "$filepath"
    
    # Holonic scores attributes
    sed -i 's/\bholonic_scores\.autonomy_integration\b/holonic_scores.get("autonomy_integration", 0)/g' "$filepath"
    sed -i 's/\bholonic_scores\.ubuntu_alignment\b/holonic_scores.get("ubuntu_alignment", 0)/g' "$filepath"
    sed -i 's/\bholonic_scores\.reciprocity_health\b/holonic_scores.get("reciprocity_health", 0)/g' "$filepath"
    sed -i 's/\bholonic_scores\.mutualism_capacity\b/holonic_scores.get("mutualism_capacity", 0)/g' "$filepath"
    sed -i 's/\bholonic_scores\.regeneration_impact\b/holonic_scores.get("regeneration_impact", 0)/g' "$filepath"
    sed -i 's/\bholonic_scores\.overall_network_health\b/holonic_scores.get("overall_network_health", 0)/g' "$filepath"
    
    # Network status attributes
    sed -i 's/\bnetwork_status\.active_participants\b/network_status.get("active_participants", 0)/g' "$filepath"
    sed -i 's/\bnetwork_status\.total_transactions_24h\b/network_status.get("total_transactions_24h", 0)/g' "$filepath"
    sed -i 's/\bnetwork_status\.bioregions_count\b/network_status.get("bioregions_count", 0)/g' "$filepath"
    sed -i 's/\bnetwork_status\.average_ubuntu_score\b/network_status.get("average_ubuntu_score", 0)/g' "$filepath"
    
    # Watershed attributes
    sed -i 's/\bwatershed\.area_sqkm\b/watershed.get("area_sqkm", 0)/g' "$filepath"
    sed -i 's/\bwatershed\.name\b/watershed.get("name", "Unknown")/g' "$filepath"
    sed -i 's/\bwatershed\.feow_id\b/watershed.get("feow_id", 0)/g' "$filepath"
    
    # Ecoregion attributes
    sed -i 's/\becoregion\.name\b/ecoregion.get("name", "Unknown")/g' "$filepath"
    sed -i 's/\becoregion\.biome\b/ecoregion.get("biome", "Unknown")/g' "$filepath"
    sed -i 's/\becoregion\.realm\b/ecoregion.get("realm", "Unknown")/g' "$filepath"
    sed -i 's/\becoregion\.eco_id\b/ecoregion.get("eco_id", 0)/g' "$filepath"
    
    # Transaction attributes
    sed -i 's/\btx\.hash\b/tx.get("hash", "")/g' "$filepath"
    sed -i 's/\btx\.type\b/tx.get("type", "unknown")/g' "$filepath"
    sed -i 's/\btx\.amount\b/tx.get("amount", 0)/g' "$filepath"
    sed -i 's/\btx\.timestamp\b/tx.get("timestamp", "")/g' "$filepath"
    
    # Distribution stats attributes
    sed -i 's/\bdistribution_stats\.total_supply\b/distribution_stats.get("total_supply", 0)/g' "$filepath"
    sed -i 's/\bdistribution_stats\.circulating_supply\b/distribution_stats.get("circulating_supply", 0)/g' "$filepath"
    
    echo "✓ Fixed $file"
}

# Fix all templates
fix_template "home.html"
fix_template "protocol.html"
fix_template "dashboard.html"

echo ""
echo "=============================================="
echo "Fix Complete!"
echo "=============================================="
echo ""
echo "Backups saved to: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. sudo systemctl restart ubec-web"
echo "  2. Test all pages"
echo ""
