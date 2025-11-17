#!/bin/bash
################################################################################
# Legal Page Troubleshooting Script
# Diagnoses why /legal route isn't working
################################################################################

echo "🔍 UBEC Legal Page Diagnostic"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ISSUES_FOUND=0

# 1. Check if legal.html exists in templates
echo "1️⃣  Checking template file location..."
if [ -f "templates/legal.html" ]; then
    echo -e "${GREEN}✓ templates/legal.html exists${NC}"
    echo "   Size: $(ls -lh templates/legal.html | awk '{print $5}')"
else
    echo -e "${RED}✗ templates/legal.html NOT FOUND${NC}"
    echo "   Expected location: templates/legal.html"
    ((ISSUES_FOUND++))
fi
echo ""

# 2. Check if route exists in main_web.py
echo "2️⃣  Checking route definition in main_web.py..."
if grep -q '@app.get("/legal"' main_web.py; then
    echo -e "${GREEN}✓ /legal route found in main_web.py${NC}"
    echo "   Route definition:"
    grep -A 5 '@app.get("/legal"' main_web.py | head -6
else
    echo -e "${RED}✗ /legal route NOT FOUND in main_web.py${NC}"
    echo "   The route needs to be added to main_web.py"
    ((ISSUES_FOUND++))
fi
echo ""

# 3. Check route order (catch-all routes can interfere)
echo "3️⃣  Checking route order..."
if grep -n '@app.get' main_web.py | grep -q '/{.*}'; then
    echo -e "${YELLOW}⚠ Warning: Wildcard routes detected${NC}"
    echo "   Make sure /legal route is defined BEFORE any catch-all routes"
    grep -n '@app.get.*{' main_web.py
else
    echo -e "${GREEN}✓ No problematic wildcard routes found${NC}"
fi
echo ""

# 4. Check for syntax errors around the route
echo "4️⃣  Checking for syntax issues..."
if python3 -m py_compile main_web.py 2>/dev/null; then
    echo -e "${GREEN}✓ No Python syntax errors in main_web.py${NC}"
else
    echo -e "${RED}✗ Syntax errors found in main_web.py${NC}"
    python3 -m py_compile main_web.py
    ((ISSUES_FOUND++))
fi
echo ""

# 5. Check if templates directory is properly configured
echo "5️⃣  Checking templates configuration..."
if grep -q "templates = Jinja2Templates" main_web.py; then
    echo -e "${GREEN}✓ Jinja2Templates configured${NC}"
    TEMPLATE_DIR=$(grep "templates = Jinja2Templates" main_web.py | grep -o '"[^"]*"' | tr -d '"')
    echo "   Directory: ${TEMPLATE_DIR:-templates}"
else
    echo -e "${RED}✗ Jinja2Templates not found${NC}"
    ((ISSUES_FOUND++))
fi
echo ""

# 6. Test if server is running
echo "6️⃣  Testing server status..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running on port 8001${NC}"
    
    # Test the legal endpoint
    echo ""
    echo "7️⃣  Testing /legal endpoint..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/legal)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ /legal endpoint returns 200 OK${NC}"
        echo "   The page is working!"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${RED}✗ /legal endpoint returns 404 Not Found${NC}"
        echo "   The route is not registered or server needs restart"
        ((ISSUES_FOUND++))
    elif [ "$HTTP_CODE" = "500" ]; then
        echo -e "${RED}✗ /legal endpoint returns 500 Internal Server Error${NC}"
        echo "   Template rendering error - check logs"
        ((ISSUES_FOUND++))
    else
        echo -e "${YELLOW}⚠ /legal endpoint returns ${HTTP_CODE}${NC}"
        ((ISSUES_FOUND++))
    fi
else
    echo -e "${YELLOW}⚠ Server not running on port 8001${NC}"
    echo "   Start server with: uvicorn main_web:app --reload --port 8001"
fi
echo ""

# 8. Check server logs for errors
echo "8️⃣  Checking for recent errors in logs..."
if [ -f "logs/application.log" ]; then
    RECENT_ERRORS=$(grep -i "error.*legal" logs/application.log | tail -5)
    if [ -n "$RECENT_ERRORS" ]; then
        echo -e "${YELLOW}⚠ Recent errors found:${NC}"
        echo "$RECENT_ERRORS"
    else
        echo -e "${GREEN}✓ No recent errors in logs${NC}"
    fi
else
    echo "   No log file found"
fi
echo ""

# 9. Check template syntax
echo "9️⃣  Checking template syntax..."
if [ -f "templates/legal.html" ]; then
    # Check for common template issues
    if grep -q "{% extends" templates/legal.html; then
        echo -e "${GREEN}✓ Template extends base.html${NC}"
    else
        echo -e "${YELLOW}⚠ Template may not extend base.html${NC}"
    fi
    
    if grep -q "{% block content %}" templates/legal.html; then
        echo -e "${GREEN}✓ Content block found${NC}"
    else
        echo -e "${RED}✗ Content block missing${NC}"
        ((ISSUES_FOUND++))
    fi
    
    # Check for unclosed tags
    OPEN_TAGS=$(grep -o "{% " templates/legal.html | wc -l)
    CLOSE_TAGS=$(grep -o " %}" templates/legal.html | wc -l)
    if [ "$OPEN_TAGS" -eq "$CLOSE_TAGS" ]; then
        echo -e "${GREEN}✓ Template tags balanced${NC}"
    else
        echo -e "${YELLOW}⚠ Template tags may be unbalanced (${OPEN_TAGS} open, ${CLOSE_TAGS} close)${NC}"
    fi
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No issues found!${NC}"
    echo ""
    echo "Possible solutions:"
    echo "1. Restart the server:"
    echo "   pkill -f 'uvicorn main_web'"
    echo "   uvicorn main_web:app --reload --port 8001"
    echo ""
    echo "2. Clear browser cache and try again"
    echo ""
    echo "3. Check browser console for JavaScript errors"
else
    echo -e "${RED}✗ Found ${ISSUES_FOUND} potential issue(s)${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Fix the issues listed above"
    echo "2. Restart the server"
    echo "3. Run this diagnostic again"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Additional debugging commands
echo "📋 Useful debugging commands:"
echo ""
echo "# View all routes registered:"
echo "python3 -c \"from main_web import app; print('\\n'.join([f'{r.path} -> {r.name}' for r in app.routes]))\""
echo ""
echo "# Test endpoint directly:"
echo "curl -v http://localhost:8001/legal"
echo ""
echo "# Check server logs:"
echo "tail -f logs/application.log"
echo ""
echo "# Restart server:"
echo "pkill -f 'uvicorn main_web' && uvicorn main_web:app --reload --port 8001"
echo ""
