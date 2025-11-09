#!/bin/bash

################################################################################
# UBEC Interface Quick Fix Script
# ===============================
# 
# One-command diagnosis and fix for CSS/head issues in UBEC interface
#
# Usage:
#   bash quick_fix_ubec.sh                    # Use default path
#   bash quick_fix_ubec.sh /path/to/interface # Use custom path
#
# Attribution:
#   This project uses the services of Claude and Anthropic PBC to inform 
#   our decisions and recommendations. This project was made possible with 
#   the assistance of Claude and Anthropic PBC.
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INTERFACE_PATH="${1:-/srv/ubec-www/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  $1${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_step() {
    echo -e "\n${CYAN}▶ $1${NC}\n"
}

################################################################################
# Main Script
################################################################################

clear

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║           UBEC Interface Quick Fix Tool                          ║
║           Diagnose & Fix CSS/Head Issues                         ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

print_info "Interface path: $INTERFACE_PATH"

# Check if path exists
if [ ! -d "$INTERFACE_PATH" ]; then
    print_error "Directory not found: $INTERFACE_PATH"
    echo ""
    print_info "Usage: bash quick_fix_ubec.sh [path_to_interface]"
    exit 1
fi

echo ""
print_info "This script will:"
echo "  1. Diagnose the CSS/head issue"
echo "  2. Create a backup of your files"
echo "  3. Apply fixes automatically"
echo "  4. Provide next steps"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Cancelled by user"
    exit 0
fi

################################################################################
# Step 1: Diagnostic
################################################################################

print_header "Step 1: Running Diagnostic"

if [ -f "$SCRIPT_DIR/diagnose_ubec_interface.py" ]; then
    python3 "$SCRIPT_DIR/diagnose_ubec_interface.py" "$INTERFACE_PATH"
    DIAGNOSTIC_EXIT=$?
else
    print_error "Diagnostic script not found: $SCRIPT_DIR/diagnose_ubec_interface.py"
    print_info "Continuing without diagnostic..."
    DIAGNOSTIC_EXIT=1
fi

################################################################################
# Step 2: Apply Fixes
################################################################################

print_header "Step 2: Applying Fixes"

if [ -f "$SCRIPT_DIR/fix_ubec_interface.py" ]; then
    python3 "$SCRIPT_DIR/fix_ubec_interface.py" "$INTERFACE_PATH"
    FIX_EXIT=$?
    
    if [ $FIX_EXIT -eq 0 ]; then
        print_success "Fixes applied successfully!"
    else
        print_warning "Some issues encountered during fix"
    fi
else
    print_error "Fix script not found: $SCRIPT_DIR/fix_ubec_interface.py"
    exit 1
fi

################################################################################
# Step 3: Post-Fix Instructions
################################################################################

print_header "Step 3: Complete the Fix"

echo -e "${YELLOW}⚠ IMPORTANT: You must complete these steps:${NC}\n"

echo "1. Restart the web server:"
echo -e "   ${CYAN}sudo systemctl restart ubec-www${NC}"
echo "   OR"
echo -e "   ${CYAN}cd $INTERFACE_PATH && uvicorn main_web:app --reload --port 8001${NC}"
echo ""

echo "2. Clear your browser cache:"
echo "   Chrome/Edge: Ctrl+Shift+R (Cmd+Shift+R on Mac)"
echo "   Firefox: Ctrl+F5"
echo "   Safari: Cmd+Option+E then Cmd+R"
echo ""

echo "3. Refresh the page and verify:"
echo "   - Navigation bar should be styled horizontally"
echo "   - Colors should match Ubuntu theme"
echo "   - Hover effects should work"
echo ""

################################################################################
# Step 4: Verification Helper
################################################################################

print_header "Step 4: Quick Verification"

echo "Would you like to run a quick verification check?"
echo "(This checks if files were fixed correctly)"
echo ""
read -p "Run verification? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Checking CSS file..."
    
    CSS_FILE="$INTERFACE_PATH/static/css/main.css"
    if [ -f "$CSS_FILE" ]; then
        CSS_SIZE=$(wc -c < "$CSS_FILE")
        if [ $CSS_SIZE -gt 1000 ]; then
            print_success "CSS file exists and has content ($CSS_SIZE bytes)"
            
            # Check for navbar styles
            if grep -q ".navbar" "$CSS_FILE"; then
                print_success "CSS file contains navbar styles"
            else
                print_warning "CSS file may be missing navbar styles"
            fi
        else
            print_warning "CSS file is very small ($CSS_SIZE bytes) - may be incomplete"
        fi
    else
        print_error "CSS file not found: $CSS_FILE"
    fi
    
    print_step "Checking template..."
    
    TEMPLATE_FILE="$INTERFACE_PATH/templates/base.html"
    if [ -f "$TEMPLATE_FILE" ]; then
        if grep -q "/static/css/main.css" "$TEMPLATE_FILE"; then
            print_success "Template has correct CSS link"
        else
            print_warning "Template may have incorrect CSS link"
        fi
        
        if grep -q 'class="navbar"' "$TEMPLATE_FILE"; then
            print_success "Template has navbar structure"
        else
            print_warning "Template may be missing navbar structure"
        fi
    else
        print_error "Template not found: $TEMPLATE_FILE"
    fi
fi

################################################################################
# Final Summary
################################################################################

print_header "Summary & Next Steps"

echo -e "${GREEN}✓ Diagnostic completed${NC}"
echo -e "${GREEN}✓ Fixes applied${NC}"
echo ""
echo -e "${YELLOW}⚠ Action Required:${NC}"
echo "   1. Restart web server"
echo "   2. Clear browser cache"
echo "   3. Test the interface"
echo ""

print_info "For detailed troubleshooting, see: TROUBLESHOOTING_GUIDE.md"

################################################################################
# Optional: Restart Service
################################################################################

echo ""
echo "Would you like to attempt restarting the service now?"
echo "(Requires sudo/root privileges)"
echo ""
read -p "Restart service? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if systemctl is-active --quiet ubec-www; then
        print_step "Restarting ubec-www service..."
        sudo systemctl restart ubec-www
        
        if [ $? -eq 0 ]; then
            print_success "Service restarted successfully"
            
            # Give it a moment to start
            sleep 2
            
            # Check if it's running
            if systemctl is-active --quiet ubec-www; then
                print_success "Service is running"
                
                # Try to access the CSS file
                if command -v curl &> /dev/null; then
                    print_step "Testing CSS access..."
                    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/static/css/main.css)
                    
                    if [ "$HTTP_CODE" -eq 200 ]; then
                        print_success "CSS is accessible via HTTP (200 OK)"
                    else
                        print_warning "CSS returned HTTP $HTTP_CODE"
                    fi
                fi
            else
                print_error "Service failed to start - check logs"
                echo "   sudo journalctl -u ubec-www -n 50"
            fi
        else
            print_error "Failed to restart service"
        fi
    else
        print_info "Service 'ubec-www' not found or not running"
        print_info "Start manually with:"
        echo "   cd $INTERFACE_PATH"
        echo "   uvicorn main_web:app --reload --host 0.0.0.0 --port 8001"
    fi
fi

################################################################################
# Completion
################################################################################

echo ""
print_header "Fix Complete!"

echo -e "${GREEN}✓ All automated fixes have been applied${NC}"
echo ""
echo "Next: Clear your browser cache and refresh the page"
echo ""
print_info "If issues persist, run: python3 diagnose_ubec_interface.py"
echo ""

exit 0
