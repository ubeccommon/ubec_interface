#!/usr/bin/env python3
"""
UBEC Interface CSS/Head Fix Script
===================================

Repairs common issues with CSS loading and head section in the UBEC web interface.

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BLUE}{'=' * 70}")
    print(f"{text}")
    print(f"{'=' * 70}{RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")


class InterfaceFixer:
    """Fix common UBEC interface issues"""
    
    def __init__(self, base_path: str = "/srv/ubec-www/app"):
        """
        Initialize fixer
        
        Args:
            base_path: Path to the UBEC interface directory
        """
        self.base_path = Path(base_path)
        self.backup_dir = None
        
    def create_backup(self) -> Optional[Path]:
        """Create backup of existing files"""
        print_header("Creating Backup")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.base_path / f"backup_{timestamp}"
        
        try:
            self.backup_dir.mkdir(exist_ok=True)
            print_success(f"Backup directory created: {self.backup_dir}")
            
            # Backup key files
            files_to_backup = [
                "static/css/main.css",
                "templates/base.html",
                "main_web.py"
            ]
            
            for file_path in files_to_backup:
                src = self.base_path / file_path
                if src.exists():
                    dst = self.backup_dir / file_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    print_success(f"Backed up: {file_path}")
            
            return self.backup_dir
            
        except Exception as e:
            print_error(f"Backup failed: {e}")
            return None
    
    def fix_base_template(self) -> bool:
        """Fix base.html template head section"""
        print_header("Fixing Base Template")
        
        template_path = self.base_path / "templates" / "base.html"
        
        # Correct base template with proper head section
        correct_base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Ubuntu Bioregional Economic Commons - Four Element Token Ecosystem">
    <meta name="keywords" content="UBEC, Ubuntu, blockchain, tokens, economic commons, regenerative economy">
    <title>{% block title %}UBEC Protocol Network{% endblock %}</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="/static/images/favicon.png">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/static/css/main.css">
    
    <!-- Additional page-specific styles -->
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="container">
            <div class="navbar-brand">
                <a href="/" class="logo">
                    <span class="logo-text">UBEC Protocol</span>
                </a>
            </div>
            
            <ul class="navbar-menu">
                <li><a href="/" class="nav-link {% if page == 'home' %}active{% endif %}">Home</a></li>
                <li><a href="/protocol" class="nav-link {% if page == 'protocol' %}active{% endif %}">Protocol</a></li>
                <li><a href="/dashboard" class="nav-link {% if page == 'dashboard' %}active{% endif %}">Dashboard</a></li>
                <li><a href="/stories" class="nav-link {% if page == 'stories' %}active{% endif %}">Token Stories</a></li>
                <li><a href="/about" class="nav-link {% if page == 'about' %}active{% endif %}">About</a></li>
            </ul>
        </div>
    </nav>
    
    <!-- Main Content -->
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-section">
                    <h3>UBEC Protocol</h3>
                    <p class="ubuntu-quote">"I am because we are"</p>
                    <p>Ubuntu Bioregional Economic Commons</p>
                </div>
                
                <div class="footer-section">
                    <h4>Four Elements</h4>
                    <ul>
                        <li>🌬️ Air (UBEC) - Diversity</li>
                        <li>💧 Water (UBECrc) - Reciprocity</li>
                        <li>🌍 Earth (UBECgpi) - Mutualism</li>
                        <li>🔥 Fire (UBECtt) - Regeneration</li>
                    </ul>
                </div>
                
                <div class="footer-section">
                    <h4>Resources</h4>
                    <ul>
                        <li><a href="/docs">Documentation</a></li>
                        <li><a href="/about">About</a></li>
                        <li><a href="https://github.com/ubec" target="_blank">GitHub</a></li>
                    </ul>
                </div>
                
                <div class="footer-section">
                    <h4>Community</h4>
                    <ul>
                        <li><a href="#">Discord</a></li>
                        <li><a href="#">Forum</a></li>
                        <li><a href="#">Newsletter</a></li>
                    </ul>
                </div>
            </div>
            
            <div class="footer-bottom">
                <p>&copy; 2025 UBEC Protocol. All rights reserved.</p>
                <p class="attribution">
                    This project uses the services of Claude and Anthropic PBC to inform our 
                    decisions and recommendations. This project was made possible with the 
                    assistance of Claude and Anthropic PBC.
                </p>
            </div>
        </div>
    </footer>
    
    <!-- Scripts -->
    <script src="/static/js/main.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>'''
        
        try:
            # Ensure templates directory exists
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the corrected template
            with open(template_path, 'w') as f:
                f.write(correct_base_template)
            
            print_success(f"Fixed base template: {template_path}")
            return True
            
        except Exception as e:
            print_error(f"Failed to fix base template: {e}")
            return False
    
    def ensure_css_exists(self) -> bool:
        """Ensure main.css exists with proper navbar styles"""
        print_header("Checking CSS File")
        
        css_path = self.base_path / "static" / "css" / "main.css"
        
        # Check if CSS exists and has content
        if css_path.exists() and css_path.stat().st_size > 1000:
            print_success("CSS file exists and has content")
            
            # Verify it has navbar styles
            try:
                with open(css_path, 'r') as f:
                    content = f.read()
                if '.navbar' in content:
                    print_success("CSS file has navbar styles")
                    return True
            except Exception as e:
                print_warning(f"Could not verify CSS content: {e}")
        
        print_warning("CSS file missing or incomplete")
        print_info("To fix: Run deploy_ubuntu_enhancements.sh")
        return False
    
    def fix_static_mount(self) -> bool:
        """Verify static files mount in main_web.py"""
        print_header("Verifying Static Files Configuration")
        
        main_web_path = self.base_path / "main_web.py"
        
        if not main_web_path.exists():
            print_error(f"main_web.py not found: {main_web_path}")
            return False
        
        try:
            with open(main_web_path, 'r') as f:
                content = f.read()
            
            # Check for static files mount
            if 'app.mount("/static"' in content and 'StaticFiles' in content:
                print_success("Static files mount is configured correctly")
                return True
            else:
                print_warning("Static files mount may not be configured correctly")
                print_info("Expected: app.mount(\"/static\", StaticFiles(directory=...))")
                return False
                
        except Exception as e:
            print_error(f"Could not read main_web.py: {e}")
            return False
    
    def set_permissions(self) -> bool:
        """Set correct file permissions"""
        print_header("Setting File Permissions")
        
        files_to_fix = [
            "static/css/main.css",
            "templates/base.html"
        ]
        
        all_success = True
        for file_path in files_to_fix:
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    os.chmod(full_path, 0o644)
                    print_success(f"Set permissions for: {file_path}")
                except Exception as e:
                    print_error(f"Could not set permissions for {file_path}: {e}")
                    all_success = False
            else:
                print_warning(f"File not found: {file_path}")
        
        return all_success
    
    def generate_fix_instructions(self):
        """Generate instructions for remaining fixes"""
        print_header("Next Steps")
        
        print_info("After running this script:")
        print("\n1. Restart the web server:")
        print("   systemctl restart ubec-www")
        print("   OR")
        print("   uvicorn main_web:app --reload --host 0.0.0.0 --port 8001")
        
        print("\n2. Clear browser cache:")
        print("   - Chrome/Edge: Ctrl+Shift+R (Cmd+Shift+R on Mac)")
        print("   - Firefox: Ctrl+F5 (Cmd+Shift+R on Mac)")
        print("   - Safari: Cmd+Option+E then Cmd+R")
        
        print("\n3. Check browser console:")
        print("   - Press F12 to open developer tools")
        print("   - Look for errors in Console tab")
        print("   - Check Network tab for failed CSS requests")
        
        print("\n4. If issues persist:")
        print("   - Run: python diagnose_ubec_interface.py")
        print("   - Check server logs for errors")
        print("   - Verify backend API is running (port 8000)")
    
    def run_fix(self) -> bool:
        """Run all fixes"""
        print(f"\n{BLUE}╔═══════════════════════════════════════════════════════════════════╗")
        print("║              UBEC Interface Head/CSS Fix Tool                 ║")
        print("╚═══════════════════════════════════════════════════════════════════╝{RESET}\n")
        
        print_info(f"Working directory: {self.base_path}\n")
        
        # Create backup
        backup = self.create_backup()
        if backup:
            print_success(f"Backup created at: {backup}")
        else:
            print_warning("Continuing without backup...")
        
        # Run fixes
        template_fixed = self.fix_base_template()
        css_ok = self.ensure_css_exists()
        static_ok = self.fix_static_mount()
        perms_ok = self.set_permissions()
        
        # Generate next steps
        self.generate_fix_instructions()
        
        # Summary
        print_header("Summary")
        
        if template_fixed and static_ok:
            print_success("Core fixes applied successfully! ✨")
            if not css_ok:
                print_warning("CSS file needs attention - run deploy_ubuntu_enhancements.sh")
            return True
        else:
            print_error("Some fixes could not be applied")
            if backup:
                print_info(f"Backup available at: {backup}")
            return False


def main():
    """Main entry point"""
    # Check if running as root/sudo
    if os.geteuid() == 0:
        print_warning("Running as root - this is usually not necessary")
        print_info("Press Ctrl+C to cancel, or Enter to continue...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)
    
    # Get base path from command line or use default
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/srv/ubec-www/app"
    
    # Check if path exists
    if not Path(base_path).exists():
        print_error(f"Directory not found: {base_path}")
        print_info("Usage: python fix_ubec_interface.py [path_to_ubec_interface]")
        sys.exit(1)
    
    # Run fixer
    fixer = InterfaceFixer(base_path)
    success = fixer.run_fix()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
