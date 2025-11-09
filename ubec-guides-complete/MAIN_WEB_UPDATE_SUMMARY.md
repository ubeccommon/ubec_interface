# main_web.py Update Summary

## Changes Made (Minimal - Only What's Necessary)

### 1. Added Import (Line 42)
```python
import markdown
```
**Purpose:** Required for converting markdown files to HTML

---

### 2. Added Documentation Guides Routes (Lines 682-828)

#### Route 1: Guides Index
```python
@app.get("/docs/guides/", response_class=HTMLResponse, name="guides_index")
@app.get("/docs/guides/index", response_class=HTMLResponse)
async def guides_index(request: Request):
```
**Purpose:** Serves `/docs/guides/` and displays the README.md as the guide directory index

**What it does:**
- Reads `docs/guides/README.md`
- Converts markdown to HTML
- Renders using `guide_template.html`
- Includes error handling with fallback HTML

#### Route 2: Individual Guides
```python
@app.get("/docs/guides/{guide_name:path}", response_class=HTMLResponse, name="serve_guide")
async def serve_guide(request: Request, guide_name: str):
```
**Purpose:** Serves individual guide files like `/docs/guides/participation-guide`

**What it does:**
- Takes guide name (with or without .md extension)
- Reads the markdown file from `docs/guides/`
- Includes security check to prevent directory traversal
- Converts markdown to HTML
- Extracts title from first H1 or filename
- Renders using `guide_template.html`
- Includes error handling with fallback HTML

---

## What Was NOT Changed

✅ All existing routes unchanged
✅ All existing logic unchanged  
✅ All middleware unchanged
✅ All error handlers unchanged
✅ All fallback data unchanged
✅ Application configuration unchanged
✅ Logging configuration unchanged
✅ Settings unchanged
✅ Health check unchanged

---

## Total Lines Changed

- **1 line added** to imports (markdown)
- **147 lines added** for the two new routes
- **0 lines modified** from existing code
- **0 lines removed**

**Total impact:** 148 new lines, 0 changes to existing code

---

## Files Required for Routes to Work

### 1. Guide Files (Already Created)
Place these in `docs/guides/`:
- `README.md` (guide directory index)
- `participation-guide.md` (main participation guide)
- All other guide markdown files

### 2. Template File (Already Created)
Place in `templates/`:
- `guide_template.html` (renders markdown as HTML)

### 3. Python Package
```bash
pip install markdown --break-system-packages
```

---

## Route Behavior

### `/docs/guides/` or `/docs/guides/index`
- **Reads:** `docs/guides/README.md`
- **Returns:** HTML page with rendered markdown
- **On Error:** Fallback HTML with link back to /docs

### `/docs/guides/{guide-name}`
- **Reads:** `docs/guides/{guide-name}.md`
- **Returns:** HTML page with rendered markdown
- **Security:** Prevents directory traversal attacks
- **On Error:** Fallback HTML with links to guides index and docs

---

## Testing After Deployment

1. **Install markdown package:**
   ```bash
   pip install markdown --break-system-packages
   ```

2. **Ensure files exist:**
   ```bash
   ls -la docs/guides/README.md
   ls -la docs/guides/participation-guide.md
   ls -la templates/guide_template.html
   ```

3. **Restart application:**
   ```bash
   sudo systemctl restart ubec-web
   # OR
   python main_web.py
   ```

4. **Test routes:**
   - https://bioregional.ubec.network/docs/guides/
   - https://bioregional.ubec.network/docs/guides/participation-guide

---

## Architecture Alignment

These changes follow all UBEC design principles:

✅ **Principle #2:** Service Pattern - Routes are part of centralized web service  
✅ **Principle #5:** Strict Async - Both routes use `async def`  
✅ **Principle #10:** Separation of Concerns - Guides routes separate from other routes  
✅ **Principle #11:** Comprehensive Documentation - Routes fully documented  

---

## Error Handling

Both routes include:
- Try/catch blocks for all operations
- Specific HTTPException handling
- Fallback HTML for display errors
- Proper logging of errors
- User-friendly error messages with navigation links

---

## Security Considerations

1. **Directory Traversal Prevention:**
   - Path resolution and validation
   - Checks that requested file is within guides directory
   - Logs suspicious attempts

2. **File Extension Enforcement:**
   - Only `.md` files are served
   - Extension added if missing

3. **Error Information Disclosure:**
   - Generic error messages to users
   - Detailed errors only in logs

---

## Performance

- **Markdown conversion:** Done per request (could be cached in future)
- **File reading:** Direct file I/O (small files, fast)
- **No database queries:** Pure file system operations
- **UTF-8 encoding:** Handled by existing middleware

---

## Future Enhancements (Not Implemented)

These could be added later without breaking changes:
- Markdown caching for performance
- Breadcrumb navigation
- Search functionality
- Version control for guides
- Multi-language support

---

**Attribution:** This project uses the services of Claude and Anthropic PBC to inform our decisions and recommendations. This project was made possible with the assistance of Claude and Anthropic PBC.
