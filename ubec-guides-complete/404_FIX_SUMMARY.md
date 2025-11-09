# 404 Error Fix - Quick Summary

## The Problem
You're getting a 404 error because the Flask routes to serve `/docs/guides/` haven't been set up yet.

## The Solution (3 Files + Setup)

### Files Provided:
1. ✅ **SETUP_INSTRUCTIONS.md** - Complete step-by-step setup guide
2. ✅ **docs_guides_routes.py** - Flask route handlers to copy into your app
3. ✅ **guide_template.html** - Template for rendering markdown guides

---

## Quick Start (5 Minutes)

### 1. Install Markdown Package
```bash
pip install markdown --break-system-packages
```

### 2. Create Directory
```bash
mkdir -p docs/guides
```

### 3. Copy Guide Files
```bash
# Copy the participation-guide.md and README.md files to docs/guides/
cp participation-guide.md docs/guides/
cp README.md docs/guides/
```

### 4. Add Routes to Flask App
Open your `main_web.py` (or wherever your Flask app is) and add the routes from `docs_guides_routes.py`

### 5. Copy Template
```bash
cp guide_template.html templates/
```

### 6. Restart Flask
```bash
# Restart your Flask application
python main_web.py
# OR
sudo systemctl restart ubec-web
```

### 7. Test
Visit: https://bioregional.ubec.network/docs/guides/participation-guide

---

## Files You Need:

### From This Delivery:
- ✅ SETUP_INSTRUCTIONS.md (detailed steps)
- ✅ docs_guides_routes.py (route code)
- ✅ guide_template.html (HTML template)

### From Previous Delivery (docs/guides/ folder):
- ✅ participation-guide.md
- ✅ README.md
- ✅ All other .md guide files

### Already Have:
- ✅ docs.html (already updated with correct links)

---

## What Each File Does:

### SETUP_INSTRUCTIONS.md
Complete step-by-step instructions with troubleshooting tips.

### docs_guides_routes.py
Contains two Flask routes:
- `/docs/guides/` - Serves the guides index (README.md)
- `/docs/guides/<guide_name>` - Serves individual guides

Copy these routes into your main Flask application file.

### guide_template.html
Template that renders the markdown content with proper styling.
Must be placed in your `templates/` directory.

---

## Next Steps:

1. **Read:** SETUP_INSTRUCTIONS.md
2. **Install:** markdown package
3. **Copy:** Files to correct locations
4. **Add:** Routes to Flask app
5. **Restart:** Application
6. **Test:** Visit the URLs

---

## Support:

If still having issues after setup:
1. Check application logs
2. Verify file locations
3. Confirm routes are registered
4. Check markdown package is installed

---

**All files ready in outputs folder!**

[View SETUP_INSTRUCTIONS.md](computer:///mnt/user-data/outputs/SETUP_INSTRUCTIONS.md)
[View docs_guides_routes.py](computer:///mnt/user-data/outputs/docs_guides_routes.py)
[View guide_template.html](computer:///mnt/user-data/outputs/guide_template.html)
