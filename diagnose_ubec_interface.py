#!/usr/bin/env python3
"""
UBEC Interface Diagnostic Script
=================================

Diagnoses issues with the head section and CSS loading in the UBEC web interface.

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

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


class InterfaceDiagnostic:
    """Diagnostic tool for UBEC interface issues"""
    
    def __init__(self, base_path: str = "/srv/ubec-www/app"):
        """
        Initialize diagnostic tool
        
        Args:
            base_path: Path to the UBEC interface directory
        """
        self.base_path = Path(base_path)
        self.issues: List[Dict[str, str]] = []
        self.warnings: List[str] = []
        
    def check_directory_structure(self) -> bool:
        """Check if required directories exist"""
        print_header("Checking Directory Structure")
        
        required_dirs = [
            "static/css",
            "static/js",
            "static/images",
            "templates",
            "config"
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            if full_path.exists():
                print_success(f"Found: {dir_path}")
            else:
                print_error(f"Missing: {dir_path}")
                self.issues.append({
                    "type": "missing_directory",
                    "path": str(full_path),
                    "severity": "high"
                })
                all_exist = False
        
        return all_exist
    
    def check_css_file(self) -> Tuple[bool, Dict]:
        """Check main.css file existence and content"""
        print_header("Checking CSS File")
        
        css_path = self.base_path / "static" / "css" / "main.css"
        result = {
            "exists": False,
            "size": 0,
            "readable": False,
            "has_navbar_styles": False,
            "permissions": None
        }
        
        # Check existence
        if css_path.exists():
            print_success(f"CSS file exists: {css_path}")
            result["exists"] = True
            
            # Check size
            size = css_path.stat().st_size
            result["size"] = size
            if size > 0:
                print_success(f"CSS file size: {size} bytes")
            else:
                print_error("CSS file is empty!")
                self.issues.append({
                    "type": "empty_css",
                    "path": str(css_path),
                    "severity": "critical"
                })
            
            # Check permissions
            result["permissions"] = oct(css_path.stat().st_mode)[-3:]
            print_info(f"File permissions: {result['permissions']}")
            
            # Check readability
            try:
                with open(css_path, 'r') as f:
                    content = f.read()
                result["readable"] = True
                print_success("CSS file is readable")
                
                # Check for navbar styles
                if '.navbar' in content:
                    result["has_navbar_styles"] = True
                    print_success("Found navbar styles in CSS")
                else:
                    print_error("No navbar styles found in CSS!")
                    self.issues.append({
                        "type": "missing_navbar_styles",
                        "path": str(css_path),
                        "severity": "high"
                    })
                    
            except Exception as e:
                print_error(f"Cannot read CSS file: {e}")
                result["readable"] = False
                self.issues.append({
                    "type": "css_read_error",
                    "path": str(css_path),
                    "error": str(e),
                    "severity": "critical"
                })
        else:
            print_error(f"CSS file not found: {css_path}")
            self.issues.append({
                "type": "missing_css",
                "path": str(css_path),
                "severity": "critical"
            })
        
        return result["exists"] and result["readable"], result
    
    def check_base_template(self) -> Tuple[bool, Dict]:
        """Check base.html template"""
        print_header("Checking Base Template")
        
        template_path = self.base_path / "templates" / "base.html"
        result = {
            "exists": False,
            "has_css_link": False,
            "css_path_correct": False,
            "has_nav_structure": False
        }
        
        if template_path.exists():
            print_success(f"Template exists: {template_path}")
            result["exists"] = True
            
            try:
                with open(template_path, 'r') as f:
                    content = f.read()
                
                # Check for CSS link
                if '/static/css/main.css' in content:
                    result["has_css_link"] = True
                    result["css_path_correct"] = True
                    print_success("Found correct CSS link in template")
                elif 'main.css' in content:
                    result["has_css_link"] = True
                    print_warning("Found CSS link but path might be incorrect")
                    self.warnings.append("CSS path in template may be incorrect")
                else:
                    print_error("No CSS link found in template!")
                    self.issues.append({
                        "type": "missing_css_link",
                        "path": str(template_path),
                        "severity": "critical"
                    })
                
                # Check for navbar structure
                if '<nav class="navbar">' in content or '<nav class=\'navbar\'>' in content:
                    result["has_nav_structure"] = True
                    print_success("Found navbar structure in template")
                else:
                    print_error("No navbar structure found in template!")
                    self.issues.append({
                        "type": "missing_navbar_structure",
                        "path": str(template_path),
                        "severity": "high"
                    })
                    
            except Exception as e:
                print_error(f"Cannot read template: {e}")
                self.issues.append({
                    "type": "template_read_error",
                    "path": str(template_path),
                    "error": str(e),
                    "severity": "critical"
                })
        else:
            print_error(f"Template not found: {template_path}")
            result["exists"] = False
            self.issues.append({
                "type": "missing_template",
                "path": str(template_path),
                "severity": "critical"
            })
        
        return result["exists"] and result["has_css_link"], result
    
    def check_main_web_config(self) -> Tuple[bool, Dict]:
        """Check main_web.py configuration"""
        print_header("Checking main_web.py Configuration")
        
        main_web_path = self.base_path / "main_web.py"
        result = {
            "exists": False,
            "mounts_static": False,
            "static_path_correct": False
        }
        
        if main_web_path.exists():
            print_success(f"main_web.py exists")
            result["exists"] = True
            
            try:
                with open(main_web_path, 'r') as f:
                    content = f.read()
                
                # Check for static files mount
                if 'app.mount' in content and 'StaticFiles' in content:
                    result["mounts_static"] = True
                    print_success("Found static files mount")
                    
                    if '"/static"' in content and 'static' in content.lower():
                        result["static_path_correct"] = True
                        print_success("Static files path appears correct")
                    else:
                        print_warning("Static files path may be incorrect")
                        self.warnings.append("Verify static files mount path")
                else:
                    print_error("No static files mount found!")
                    self.issues.append({
                        "type": "missing_static_mount",
                        "path": str(main_web_path),
                        "severity": "critical"
                    })
                    
            except Exception as e:
                print_error(f"Cannot read main_web.py: {e}")
                self.issues.append({
                    "type": "main_web_read_error",
                    "path": str(main_web_path),
                    "error": str(e),
                    "severity": "high"
                })
        else:
            print_error(f"main_web.py not found: {main_web_path}")
            result["exists"] = False
            self.issues.append({
                "type": "missing_main_web",
                "path": str(main_web_path),
                "severity": "critical"
            })
        
        return result["mounts_static"], result
    
    def generate_report(self):
        """Generate diagnostic report"""
        print_header("Diagnostic Report")
        
        if not self.issues and not self.warnings:
            print_success("No issues found! ✨")
            print_info("\nIf you're still seeing problems:")
            print_info("1. Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)")
            print_info("2. Check browser console for errors (F12)")
            print_info("3. Verify the web server is running")
            print_info("4. Check server logs for errors")
            return
        
        if self.issues:
            print_error(f"\nFound {len(self.issues)} issue(s):\n")
            for i, issue in enumerate(self.issues, 1):
                severity_color = RED if issue["severity"] == "critical" else YELLOW
                print(f"{severity_color}{i}. [{issue['severity'].upper()}] {issue['type']}{RESET}")
                print(f"   Path: {issue['path']}")
                if "error" in issue:
                    print(f"   Error: {issue['error']}")
                print()
        
        if self.warnings:
            print_warning(f"\nFound {len(self.warnings)} warning(s):\n")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{YELLOW}{i}. {warning}{RESET}")
            print()
        
        # Recommendations
        print_header("Recommendations")
        
        critical_issues = [i for i in self.issues if i["severity"] == "critical"]
        if critical_issues:
            print(f"{RED}CRITICAL: Fix these issues first:{RESET}\n")
            for issue in critical_issues:
                print(f"  • {issue['type']}: {issue['path']}")
            print()
        
        print_info("To fix common issues:")
        print("1. Run: bash deploy_ubuntu_enhancements.sh")
        print("2. Restart the web server")
        print("3. Clear browser cache")
        print("4. Check browser console (F12) for errors")
    
    def run_full_diagnostic(self):
        """Run complete diagnostic"""
        print(f"\n{BLUE}╔═══════════════════════════════════════════════════════════════════╗")
        print("║          UBEC Interface Head/CSS Diagnostic Tool              ║")
        print("╚═══════════════════════════════════════════════════════════════════╝{RESET}\n")
        
        print_info(f"Scanning directory: {self.base_path}\n")
        
        # Run all checks
        self.check_directory_structure()
        css_ok, css_result = self.check_css_file()
        template_ok, template_result = self.check_base_template()
        config_ok, config_result = self.check_main_web_config()
        
        # Generate report
        self.generate_report()
        
        # Return overall status
        return len([i for i in self.issues if i["severity"] == "critical"]) == 0


def main():
    """Main entry point"""
    # Get base path from command line or use default
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/srv/ubec-www/app"
    
    # Check if path exists
    if not Path(base_path).exists():
        print_error(f"Directory not found: {base_path}")
        print_info("Usage: python diagnose_ubec_interface.py [path_to_ubec_interface]")
        sys.exit(1)
    
    # Run diagnostic
    diagnostic = InterfaceDiagnostic(base_path)
    success = diagnostic.run_full_diagnostic()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
