#!/bin/bash

################################################################################
# UBEC Ubuntu Enhancement Deployment Script
# Version: 2.0.0
# Date: November 5, 2025
#
# This script deploys Ubuntu-styled CSS, JavaScript, and templates
# to the UBEC web interface.
#
# Usage: sudo bash deploy_ubuntu_enhancements.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/srv/ubec-www/app"
BACKUP_DIR="/srv/ubec-www/backups/ubuntu_v1_backup_$(date +%Y%m%d_%H%M%S)"
USER="kelpit"
GROUP="kelpit"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "════════════════════════════════════════════════════════════════"
    echo "$1"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
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

################################################################################
# Pre-flight Checks
################################################################################

print_header "UBEC Ubuntu Enhancement Deployment"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    print_error "App directory not found: $APP_DIR"
    exit 1
fi

print_success "Pre-flight checks passed"

################################################################################
# Backup Existing Files
################################################################################

print_header "Backing Up Existing Files"

mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/static/css"
mkdir -p "$BACKUP_DIR/static/js"
mkdir -p "$BACKUP_DIR/templates"

# Backup CSS
if [ -f "$APP_DIR/static/css/main.css" ]; then
    cp "$APP_DIR/static/css/main.css" "$BACKUP_DIR/static/css/"
    print_success "Backed up main.css"
fi

# Backup JS
if [ -f "$APP_DIR/static/js/main.js" ]; then
    cp "$APP_DIR/static/js/main.js" "$BACKUP_DIR/static/js/"
    print_success "Backed up main.js"
fi

# Backup templates
if [ -f "$APP_DIR/templates/home.html" ]; then
    cp "$APP_DIR/templates/home.html" "$BACKUP_DIR/templates/"
    print_success "Backed up home.html"
fi

if [ -f "$APP_DIR/templates/base.html" ]; then
    cp "$APP_DIR/templates/base.html" "$BACKUP_DIR/templates/"
    print_success "Backed up base.html"
fi

print_success "Backup complete: $BACKUP_DIR"

################################################################################
# Create Directories
################################################################################

print_header "Creating Directory Structure"

mkdir -p "$APP_DIR/static/css"
mkdir -p "$APP_DIR/static/js"
mkdir -p "$APP_DIR/templates"

print_success "Directories ready"

################################################################################
# Deploy Files
################################################################################

print_header "Deploying Ubuntu-Enhanced Files"

# Note: The actual file content will be created in separate scripts
# This main script will call them

print_info "Creating CSS file..."
bash /tmp/create_css.sh

print_info "Creating JavaScript file..."
bash /tmp/create_js.sh

print_info "Creating home.html template..."
bash /tmp/create_home.sh

print_info "Creating base.html template..."
bash /tmp/create_base.sh

################################################################################
# Set Permissions
################################################################################

print_header "Setting Permissions"

chown -R $USER:$GROUP "$APP_DIR/static"
chown -R $USER:$GROUP "$APP_DIR/templates"

chmod 644 "$APP_DIR/static/css/main.css"
chmod 644 "$APP_DIR/static/js/main.js"
chmod 644 "$APP_DIR/templates/home.html"
chmod 644 "$APP_DIR/templates/base.html"

print_success "Permissions set"

################################################################################
# Verify Deployment
################################################################################

print_header "Verifying Deployment"

# Check file sizes
CSS_SIZE=$(stat -f%z "$APP_DIR/static/css/main.css" 2>/dev/null || stat -c%s "$APP_DIR/static/css/main.css" 2>/dev/null)
JS_SIZE=$(stat -f%z "$APP_DIR/static/js/main.js" 2>/dev/null || stat -c%s "$APP_DIR/static/js/main.js" 2>/dev/null)

if [ $CSS_SIZE -gt 80000 ]; then
    print_success "CSS file size correct: $CSS_SIZE bytes"
else
    print_warning "CSS file seems small: $CSS_SIZE bytes (expected ~85KB)"
fi

if [ $JS_SIZE -gt 18000 ]; then
    print_success "JS file size correct: $JS_SIZE bytes"
else
    print_warning "JS file seems small: $JS_SIZE bytes (expected ~20KB)"
fi

# Check for Ubuntu colors in CSS
if grep -q "ubuntu-integrator" "$APP_DIR/static/css/main.css"; then
    print_success "Ubuntu colors found in CSS"
else
    print_error "Ubuntu colors NOT found in CSS"
fi

# Check for UBEC object in JS
if grep -q "window.UBEC" "$APP_DIR/static/js/main.js"; then
    print_success "UBEC object found in JavaScript"
else
    print_error "UBEC object NOT found in JavaScript"
fi

################################################################################
# Restart Service
################################################################################

print_header "Restarting UBEC Web Service"

if systemctl restart ubec-www; then
    print_success "Service restarted successfully"
    sleep 2
    
    if systemctl is-active --quiet ubec-www; then
        print_success "Service is running"
    else
        print_error "Service failed to start"
        systemctl status ubec-www
        exit 1
    fi
else
    print_error "Failed to restart service"
    exit 1
fi

################################################################################
# Post-Deployment Instructions
################################################################################

print_header "Deployment Complete!"

echo ""
print_success "Ubuntu enhancements deployed successfully!"
echo ""
print_info "Next steps:"
echo "  1. Clear your browser cache (Ctrl+Shift+R)"
echo "  2. Visit: http://localhost:8001 or http://your-server-ip:8001"
echo "  3. Verify Ubuntu colors are displayed"
echo ""
print_info "Expected changes:"
echo "  ✓ Earth-tone color palette (sage green, sky blue, etc.)"
echo "  ✓ Smooth gradient backgrounds"
echo "  ✓ Element cards with colored top borders"
echo "  ✓ Professional animations"
echo "  ✓ Proper emoji display (🌬️💧🌍🔥)"
echo ""
print_info "Backup location: $BACKUP_DIR"
echo ""
print_warning "If you need to rollback:"
echo "  sudo cp -r $BACKUP_DIR/* $APP_DIR/"
echo "  sudo systemctl restart ubec-www"
echo ""

################################################################################
# Clean up temp files
################################################################################

rm -f /tmp/create_css.sh
rm -f /tmp/create_js.sh
rm -f /tmp/create_home.sh
rm -f /tmp/create_base.sh

print_success "Deployment script complete!"
echo ""
