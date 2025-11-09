# Documentation Guides Setup Instructions

## Quick Fix for 404 Error

Your 404 error occurs because the Flask routes to serve the guides haven't been set up yet. Follow these steps:

---

## Step 1: Install Required Python Package

```bash
pip install markdown --break-system-packages
```

This package converts markdown to HTML.

---

## Step 2: Create the Guides Directory Structure

```bash
# In your project root
mkdir -p docs/guides
```

---

## Step 3: Copy Guide Files

Copy these files to `docs/guides/`:
- `participation-guide.md`
- `README.md`
- All other guide files from the delivery

```bash
# From wherever you have the guide files
cp participation-guide.md docs/guides/
cp README.md docs/guides/
```

---

## Step 4: Add Routes to Your Flask App

Open your main Flask application file (likely `main_web.py` or `app.py`) and add these routes:

```python
import markdown
from pathlib import Path
from flask import render_template, abort

# Add these routes after your other route definitions

@app.route('/docs/guides/')
@app.route('/docs/guides/index')
async def guides_index():
    """Serve the guides directory index"""
    try:
        guides_dir = Path('docs/guides')
        readme_path = guides_dir / 'README.md'
        
        if not readme_path.exists():
            abort(404)
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'tables', 'toc']
        )
        
        return render_template(
            'guide_template.html',
            title='UBEC User Guides',
            content=html_content
        )
    except Exception as e:
        print(f"Error serving guides index: {e}")
        abort(404)


@app.route('/docs/guides/<path:guide_name>')
async def serve_guide(guide_name):
    """Serve individual guide markdown files"""
    try:
        if not guide_name.endswith('.md'):
            guide_name = f"{guide_name}.md"
        
        guides_dir = Path('docs/guides')
        guide_path = guides_dir / guide_name
        
        # Security check
        if not str(guide_path.resolve()).startswith(str(guides_dir.resolve())):
            abort(403)
        
        if not guide_path.exists():
            abort(404)
        
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title
        title = guide_name.replace('.md', '').replace('-', ' ').title()
        if content.startswith('# '):
            title = content.split('\n')[0].replace('# ', '')
        
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'tables', 'toc']
        )
        
        return render_template(
            'guide_template.html',
            title=title,
            content=html_content
        )
    except Exception as e:
        print(f"Error serving guide {guide_name}: {e}")
        abort(404)
```

---

## Step 5: Create Template File

Copy the `guide_template.html` file to your `templates/` directory:

```bash
cp guide_template.html templates/
```

The template should be at: `templates/guide_template.html`

---

## Step 6: Restart Your Flask Application

```bash
# Stop the current application (Ctrl+C if running in terminal)
# Then restart it
python main_web.py
```

Or if using systemd:
```bash
sudo systemctl restart ubec-web
```

---

## Step 7: Test the Routes

Visit these URLs to verify:

1. **Guides Index:** https://bioregional.ubec.network/docs/guides/
2. **Participation Guide:** https://bioregional.ubec.network/docs/guides/participation-guide

---

## Troubleshooting

### Still getting 404?

**Check 1: File locations**
```bash
ls -la docs/guides/
# Should show: README.md, participation-guide.md, etc.
```

**Check 2: Template exists**
```bash
ls -la templates/guide_template.html
# Should exist
```

**Check 3: Routes registered**
Add this to your Flask app and visit `/test-routes`:
```python
@app.route('/test-routes')
async def test_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(str(rule))
    return "<br>".join(sorted(routes))
```

Look for `/docs/guides/` and `/docs/guides/<path:guide_name>` in the output.

**Check 4: Check logs**
```bash
# Check application logs for errors
tail -f /var/log/ubec/app.log
# or wherever your logs are
```

### Markdown not rendering?

Make sure you installed the markdown package:
```bash
pip list | grep -i markdown
# Should show: Markdown  x.x.x
```

### Links in guides returning 404?

Update the links in the guide files to match your actual file structure. For example, if you're linking to other guides, the path should be relative:

```markdown
[Token Holder Guide](../UBEC_Token_Holders_User_Guides.md)
```

Or absolute:
```markdown
[Token Holder Guide](/docs/UBEC_Token_Holders_User_Guides)
```

---

## Alternative: Simple Static File Serving

If you want a simpler approach without markdown rendering, use this instead:

```python
from flask import send_from_directory

@app.route('/docs/guides/<path:filename>')
async def serve_guide_static(filename):
    """Serve guide files as static files"""
    return send_from_directory('docs/guides', filename)
```

**Note:** With this approach, users will download the .md files instead of seeing rendered HTML.

---

## File Structure Summary

After setup, your structure should look like:

```
your-project/
├── docs/
│   └── guides/
│       ├── README.md
│       ├── participation-guide.md
│       └── [other guide files]
├── templates/
│   ├── base.html
│   ├── docs.html
│   └── guide_template.html
└── main_web.py (or app.py)
```

---

## Quick Test Commands

```bash
# Test guide index
curl https://bioregional.ubec.network/docs/guides/

# Test participation guide
curl https://bioregional.ubec.network/docs/guides/participation-guide

# Both should return HTML, not 404
```

---

## Need More Help?

If you're still getting 404 errors after following these steps:

1. Check the application logs for specific errors
2. Verify the routes are registered (`/test-routes` endpoint above)
3. Confirm file permissions allow reading the markdown files
4. Ensure your Flask app is actually restarted with the new routes

---

**Attribution:** This project uses the services of Claude and Anthropic PBC to inform our decisions and recommendations. This project was made possible with the assistance of Claude and Anthropic PBC.
