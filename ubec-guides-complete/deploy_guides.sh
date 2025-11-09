#!/bin/bash
#
# UBEC Documentation Guides - Quick Deployment Script
# 
# This script copies all documentation guides to the correct location
# 
# Usage: bash deploy_guides.sh
#

set -e  # Exit on error

echo "======================================================================"
echo "UBEC Documentation Guides - Deployment"
echo "======================================================================"
echo ""

# Configuration
PROJECT_ROOT="/srv/ubec-www/app"
SOURCE_DIR="./docs"

# Check if running from correct directory
if [ ! -f "deploy_guides.sh" ]; then
    echo "❌ Error: Please run this script from the directory containing deploy_guides.sh"
    exit 1
fi

# Check if source docs directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Error: Source directory $SOURCE_DIR not found"
    echo "   Make sure you've extracted the docs folder in this directory"
    exit 1
fi

# Check if project root exists
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ Error: Project root $PROJECT_ROOT not found"
    echo "   Update PROJECT_ROOT variable in this script to match your installation"
    exit 1
fi

echo "✓ Source directory found: $SOURCE_DIR"
echo "✓ Target directory found: $PROJECT_ROOT"
echo ""

# Create target docs directory if it doesn't exist
if [ ! -d "$PROJECT_ROOT/docs" ]; then
    echo "Creating $PROJECT_ROOT/docs directory..."
    mkdir -p "$PROJECT_ROOT/docs"
fi

if [ ! -d "$PROJECT_ROOT/docs/guides" ]; then
    echo "Creating $PROJECT_ROOT/docs/guides directory..."
    mkdir -p "$PROJECT_ROOT/docs/guides"
fi

echo "======================================================================"
echo "Deploying Documentation Files"
echo "======================================================================"
echo ""

# Deploy guides subdirectory
echo "📁 Deploying guides directory..."
cp -v "$SOURCE_DIR/guides/"*.md "$PROJECT_ROOT/docs/guides/"
echo ""

# Deploy main documentation files
echo "📚 Deploying main documentation guides..."
cp -v "$SOURCE_DIR/"*.md "$PROJECT_ROOT/docs/" 2>/dev/null || true
echo ""

# Set permissions
echo "🔒 Setting file permissions..."
chmod 644 "$PROJECT_ROOT/docs"/*.md 2>/dev/null || true
chmod 644 "$PROJECT_ROOT/docs/guides"/*.md
echo ""

# Count deployed files
GUIDE_COUNT=$(ls -1 "$PROJECT_ROOT/docs/guides"/*.md 2>/dev/null | wc -l)
DOC_COUNT=$(ls -1 "$PROJECT_ROOT/docs"/*.md 2>/dev/null | wc -l)

echo "======================================================================"
echo "Deployment Summary"
echo "======================================================================"
echo "✓ Deployed $GUIDE_COUNT files to docs/guides/"
echo "✓ Deployed $DOC_COUNT files to docs/"
echo ""

# List deployed files
echo "Deployed guide files:"
ls -lh "$PROJECT_ROOT/docs/guides/"*.md | awk '{print "  - " $9 " (" $5 ")"}'
echo ""

echo "Deployed documentation files:"
ls -lh "$PROJECT_ROOT/docs/"*.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}' || echo "  (none in root)"
echo ""

echo "======================================================================"
echo "Testing URLs"
echo "======================================================================"
echo ""
echo "Test these URLs in your browser:"
echo "  • https://bioregional.ubec.network/docs/guides/"
echo "  • https://bioregional.ubec.network/docs/guides/participation-guide"
echo "  • https://bioregional.ubec.network/docs/UBEC_Token_Holders_User_Guides"
echo "  • https://bioregional.ubec.network/docs/UBEC_Public_Guide"
echo ""

echo "======================================================================"
echo "✓ Deployment Complete!"
echo "======================================================================"
echo ""
echo "No restart required - guides are served dynamically."
echo "Changes will be visible immediately on next page load."
echo ""
