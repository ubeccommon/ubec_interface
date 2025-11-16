#!/bin/bash
# Fix protocol.html holonic_scores attributes

TEMPLATE="/srv/ubec-www/app/templates/protocol.html"
BACKUP="/srv/ubec-www/app/templates/protocol.html.backup_$(date +%Y%m%d_%H%M%S)"

echo "Fixing protocol.html holonic_scores attributes..."

# Create backup
cp "$TEMPLATE" "$BACKUP"
echo "✓ Backup created: $BACKUP"

# Fix all holonic_scores attributes
sed -i 's/holonic_scores\.autonomy_integration/holonic_scores.get("autonomy_integration", 0)/g' "$TEMPLATE"
sed -i 's/holonic_scores\.ubuntu_alignment/holonic_scores.get("ubuntu_alignment", 0)/g' "$TEMPLATE"
sed -i 's/holonic_scores\.reciprocity_health/holonic_scores.get("reciprocity_health", 0)/g' "$TEMPLATE"
sed -i 's/holonic_scores\.mutualism_capacity/holonic_scores.get("mutualism_capacity", 0)/g' "$TEMPLATE"
sed -i 's/holonic_scores\.regeneration_impact/holonic_scores.get("regeneration_impact", 0)/g' "$TEMPLATE"
sed -i 's/holonic_scores\.overall_network_health/holonic_scores.get("overall_network_health", 0)/g' "$TEMPLATE"

echo "✓ Fixed holonic_scores attributes"
echo ""
echo "Next step: sudo systemctl restart ubec-web"
