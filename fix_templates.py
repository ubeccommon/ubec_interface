#!/usr/bin/env python3
"""
Automated Template Fix Script
==============================

Fixes the template issues identified in the UBEC frontend:
1. Replaces "Unknown" with proper token.name
2. Fixes element_symbol references
3. Updates token display logic

Usage:
    python3 fix_templates.py [--dry-run]
    
Options:
    --dry-run    Show what would be changed without making changes
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Template fixes
FIXES = {
    'protocol.html': [
        {
            'old': r"token\.get\('element', 'Unknown'\)",
            'new': "token.element",
            'description': "Fix element reference"
        },
        {
            'old': r"token\.get\('element_symbol', 'Unknown'\)",
            'new': "token_element_emoji(token.element)",
            'description': "Fix element symbol (needs helper function)"
        },
        {
            'old': r"{{ token\.token_code }} - {{ token\.get\('element', 'Unknown'\) }}",
            'new': "{{ token.name }}",
            'description': "Fix token name display"
        }
    ],
    'home.html': [
        {
            'old': r"token\.get\('element', 'Unknown'\)",
            'new': "token.element",
            'description': "Fix element reference"
        },
        {
            'old': r"token\.get\('element_symbol', 'Unknown'\)",
            'new': "token_element_emoji(token.element)",
            'description': "Fix element symbol"
        },
        {
            'old': r'<h3 class="element-name">{{ token\.get\(\'element\', \'Unknown\'\) }}</h3>',
            'new': '<h3 class="element-name">{{ token.name }}</h3>',
            'description': "Fix token name in header"
        }
    ]
}

# Simple fix patterns (direct string replacements)
SIMPLE_FIXES = {
    "token.get('element', 'Unknown')": "token.element",
    "token.get('element_symbol', 'Unknown')": "token.element_symbol",
    '{{ token.token_code }} - {{ token.get(\'element\', \'Unknown\') }}': '{{ token.name }}',
    '<h3 class="element-name">{{ token.get(\'element\', \'Unknown\') }}</h3>': '<h3 class="element-name">{{ token.name }}</h3>',
}


def backup_file(filepath):
    """Create a backup of the file."""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    content = Path(filepath).read_text()
    Path(backup_path).write_text(content)
    print(f"  ✓ Backed up to: {backup_path}")
    return backup_path


def fix_template(filepath, dry_run=False):
    """Fix a single template file."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"  ⚠ File not found: {filepath}")
        return False
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Fixing: {filepath}")
    print("-" * 70)
    
    content = path.read_text()
    original_content = content
    changes_made = 0
    
    # Apply simple fixes
    for old_pattern, new_pattern in SIMPLE_FIXES.items():
        if old_pattern in content:
            count = content.count(old_pattern)
            content = content.replace(old_pattern, new_pattern)
            changes_made += count
            print(f"  ✓ Replaced '{old_pattern[:50]}...' ({count} occurrences)")
    
    if changes_made == 0:
        print("  ℹ No changes needed")
        return False
    
    print(f"\n  Total changes: {changes_made}")
    
    if not dry_run:
        # Backup original
        backup_file(filepath)
        
        # Write fixed content
        path.write_text(content)
        print(f"  ✓ File updated successfully")
    else:
        print(f"  [DRY RUN] Would make {changes_made} changes")
    
    return True


def main():
    """Main function."""
    dry_run = '--dry-run' in sys.argv
    
    print("=" * 70)
    print("UBEC Template Auto-Fix Script")
    print("=" * 70)
    
    if dry_run:
        print("\n⚠ DRY RUN MODE - No files will be modified")
    
    base_path = Path('/srv/ubec-www/app/templates')
    
    if not base_path.exists():
        print(f"\n❌ Error: Template directory not found: {base_path}")
        sys.exit(1)
    
    # Files to fix
    files_to_fix = [
        base_path / 'protocol.html',
        base_path / 'home.html',
    ]
    
    fixed_count = 0
    
    for filepath in files_to_fix:
        if fix_template(filepath, dry_run):
            fixed_count += 1
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {len(files_to_fix)}")
    print(f"Files {'that would be ' if dry_run else ''}modified: {fixed_count}")
    
    if fixed_count > 0 and not dry_run:
        print("\n✓ Templates fixed successfully!")
        print("\nNext steps:")
        print("  1. Restart the web service:")
        print("     sudo systemctl restart ubec-www")
        print("  2. Clear browser cache (Ctrl+Shift+R)")
        print("  3. Check the pages - should show proper token names now")
    elif fixed_count > 0 and dry_run:
        print("\nTo apply these fixes, run:")
        print("  python3 fix_templates.py")
    else:
        print("\n✓ All templates are already correct!")
    
    print()


if __name__ == '__main__':
    main()
