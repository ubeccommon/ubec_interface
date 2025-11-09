# Deployment Checklist for Documentation Guides

## Pre-Deployment Steps

### 1. Backup Current Files ✓
```bash
# Already done - you have docs_html.backup
# Create backup of main_web.py too
cp /path/to/main_web.py /path/to/main_web.py.backup
```

### 2. Install Required Package
```bash
pip install markdown --break-system-packages
```
**Verify installation:**
```bash
pip list | grep -i markdown
# Should show: Markdown  x.x.x
```

---

## File Deployment Steps

### 3. Create Directory Structure
```bash
# From your project root
mkdir -p docs/guides
mkdir -p templates
```

### 4. Copy Guide Files
Copy these files to `docs/guides/`:
```bash
cp README.md docs/guides/
cp participation-guide.md docs/guides/
# Copy any other guide .md files
```

**Verify:**
```bash
ls -la docs/guides/
# Should show: README.md, participation-guide.md, etc.
```

### 5. Copy Template File
```bash
cp guide_template.html templates/
```

**Verify:**
```bash
ls -la templates/guide_template.html
# Should exist
```

### 6. Update main_web.py
```bash
cp main_web.py /path/to/your/project/main_web.py
```

**Verify changes:**
```bash
grep "import markdown" main_web.py
# Should find the import

grep "guides_index" main_web.py
# Should find the route
```

### 7. Update docs.html
```bash
cp docs.html templates/docs.html
```

**Verify changes:**
```bash
grep "/docs/guides/participation-guide" templates/docs.html
# Should find the updated link
```

---

## Testing Steps

### 8. Test Application Startup
```bash
# Stop current application
sudo systemctl stop ubec-web

# Test start in foreground to see errors
python main_web.py

# Look for:
# ✓ "UBEC PROTOCOL WEBSITE STARTING"
# ✓ No import errors
# ✓ Routes registered successfully
```

**Common startup issues:**
- If markdown import fails → Install markdown package
- If templates not found → Check templates directory path
- If guides not found → Check docs/guides directory

### 9. Test Routes Manually
```bash
# In another terminal, test the routes:

# Test guides index
curl http://localhost:8000/docs/guides/
# Should return HTML with "UBEC User Guides"

# Test participation guide
curl http://localhost:8000/docs/guides/participation-guide
# Should return HTML with guide content

# Both should return 200 status, not 404
```

### 10. Test in Browser (Local)
Visit:
1. http://localhost:8000/docs
   - ✓ Page loads
   - ✓ "Participation Guide" link exists
   - ✓ "All User Guides" link exists

2. http://localhost:8000/docs/guides/
   - ✓ Guides index page loads
   - ✓ Links to all guides visible
   - ✓ Navigation works

3. http://localhost:8000/docs/guides/participation-guide
   - ✓ Guide content displays
   - ✓ Markdown rendered as HTML
   - ✓ Navigation breadcrumbs work

---

## Production Deployment

### 11. Deploy to Production
```bash
# Copy files to production server
scp main_web.py user@server:/path/to/project/
scp -r docs/guides/ user@server:/path/to/project/docs/
scp templates/guide_template.html user@server:/path/to/project/templates/
scp templates/docs.html user@server:/path/to/project/templates/

# SSH into production
ssh user@server

# Install markdown package on production
pip install markdown --break-system-packages

# Restart application
sudo systemctl restart ubec-web
```

### 12. Verify Production Deployment
Visit:
1. https://bioregional.ubec.network/docs/guides/
2. https://bioregional.ubec.network/docs/guides/participation-guide

**Should see:**
- ✓ No 404 errors
- ✓ Guide content displays correctly
- ✓ Navigation works
- ✓ Emojis render correctly

### 13. Check Logs
```bash
# Check for errors
sudo journalctl -u ubec-web -f

# Or check application logs
tail -f /var/log/ubec/app.log
```

**Look for:**
- ✓ No import errors
- ✓ No file not found errors
- ✓ Routes registered successfully

---

## Verification Checklist

After deployment, verify each item:

### Functionality ✓
- [ ] Main documentation page loads
- [ ] Participation Guide link works
- [ ] All User Guides link works
- [ ] Guides index displays all guides
- [ ] Individual guides load correctly
- [ ] Markdown renders as HTML
- [ ] Tables render correctly
- [ ] Links within guides work
- [ ] Back navigation works

### Security ✓
- [ ] Directory traversal blocked (try `/docs/guides/../../../etc/passwd`)
- [ ] Only .md files accessible
- [ ] Error messages don't leak system info

### Performance ✓
- [ ] Pages load in < 2 seconds
- [ ] No console errors
- [ ] UTF-8 characters display correctly
- [ ] Emojis render correctly

### Mobile ✓
- [ ] Pages responsive on mobile
- [ ] Navigation works on mobile
- [ ] Content readable on small screens

---

## Rollback Plan

If issues occur:

### Quick Rollback
```bash
# Restore backups
cp main_web.py.backup main_web.py
cp docs.html.backup templates/docs.html

# Restart
sudo systemctl restart ubec-web
```

### Partial Rollback
Keep new files but revert main_web.py:
```bash
# Only restore main_web.py
cp main_web.py.backup main_web.py
sudo systemctl restart ubec-web
```

**Note:** If you rollback main_web.py, the guide links will return 404, but the rest of the site will work.

---

## Common Issues & Solutions

### Issue: 404 on guide URLs
**Solutions:**
1. Check files exist: `ls docs/guides/`
2. Check routes registered: Look for "guides_index" in logs
3. Restart application
4. Check file permissions: `chmod 644 docs/guides/*.md`

### Issue: "ModuleNotFoundError: No module named 'markdown'"
**Solution:**
```bash
pip install markdown --break-system-packages
```

### Issue: Template not found
**Solution:**
```bash
# Ensure guide_template.html exists
ls templates/guide_template.html

# If missing, copy it
cp guide_template.html templates/
```

### Issue: Markdown not rendering
**Solutions:**
1. Check markdown package installed
2. Check file encoding: `file docs/guides/participation-guide.md`
3. Should show: "UTF-8 Unicode text"

### Issue: Links in guides return 404
**Solution:**
Update internal links in markdown files to use correct paths:
- `/docs/guides/other-guide` (absolute)
- Or ensure relative links are correct

---

## Monitoring

### What to Monitor
1. **Error logs:** Any 404s or 500s on `/docs/guides/*`
2. **Performance:** Page load times
3. **Usage:** Number of hits to guide pages
4. **User feedback:** Are guides helpful?

### Success Metrics
- ✓ Zero 404 errors on guide URLs
- ✓ Page load < 2 seconds
- ✓ No error logs related to guides
- ✓ User engagement with guides

---

## Support

If you encounter issues:

1. **Check logs** for specific errors
2. **Verify file locations** match expected paths
3. **Test locally** before production deployment
4. **Review this checklist** to ensure all steps completed

---

## Summary

**Total time:** ~30 minutes for full deployment and testing

**Critical files:**
- main_web.py (updated with new routes)
- docs.html (updated with new links)
- guide_template.html (new template)
- docs/guides/*.md (guide content files)

**Key command:**
```bash
pip install markdown --break-system-packages
```

**Verification URLs:**
- https://bioregional.ubec.network/docs/guides/
- https://bioregional.ubec.network/docs/guides/participation-guide

---

**Ready to deploy?** Follow the steps in order and check each item! ✓

---

**Attribution:** This project uses the services of Claude and Anthropic PBC to inform our decisions and recommendations. This project was made possible with the assistance of Claude and Anthropic PBC.
