#!/bin/bash
################################################################################
# Update Legal Notice Copyright to CC-BY License
# 
# This script updates the copyright section in legal.html to reference
# Creative Commons Attribution (CC-BY 4.0) license instead of standard copyright
#
# Ubuntu Philosophy: "I am because we are" - share knowledge freely
################################################################################

set -e

echo "🔄 Updating Copyright Section to CC-BY License"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "templates/legal.html" ]; then
    echo "❌ Error: templates/legal.html not found"
    echo "   Please run this from /srv/ubec-www/app directory"
    exit 1
fi

# Create backup
BACKUP="templates/legal.html.backup_$(date +%Y%m%d_%H%M%S)"
cp templates/legal.html "$BACKUP"
echo "✓ Backup created: $BACKUP"
echo ""

# The new copyright section with CC-BY license
read -r -d '' NEW_COPYRIGHT << 'EOF' || true
            <!-- Copyright -->
            <div style="margin-bottom: 3rem;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #8AA67E; padding-bottom: 0.75rem; margin-bottom: 1.5rem; font-size: 1.75rem; font-weight: 600;">
                    Copyright & Licensing
                </h2>
                <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, rgba(138, 166, 126, 0.1) 0%, rgba(127, 199, 196, 0.1) 100%); padding: 1.5rem; border-radius: 8px; border-left: 4px solid #8AA67E; margin-bottom: 1.5rem;">
                        <h3 style="color: #2c3e50; margin-bottom: 0.75rem; font-size: 1.25rem;">Creative Commons Attribution (CC-BY 4.0)</h3>
                        <p style="color: #2c3e50; font-weight: 600; margin-bottom: 0.5rem;">
                            This work is licensed under a Creative Commons Attribution 4.0 International License.
                        </p>
                        <p style="color: #666; line-height: 1.8; margin: 0;">
                            In the spirit of Ubuntu philosophy ("I am because we are"), we share our work openly for the benefit of all.
                        </p>
                    </div>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">You are free to:</h4>
                    <ul style="color: #666; line-height: 1.8; margin-bottom: 1.5rem; padding-left: 1.5rem;">
                        <li><strong>Share</strong> — copy and redistribute the material in any medium or format</li>
                        <li><strong>Adapt</strong> — remix, transform, and build upon the material for any purpose, even commercially</li>
                    </ul>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">Under the following terms:</h4>
                    <ul style="color: #666; line-height: 1.8; margin-bottom: 1.5rem; padding-left: 1.5rem;">
                        <li><strong>Attribution</strong> — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.</li>
                        <li><strong>No additional restrictions</strong> — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.</li>
                    </ul>
                    
                    <div style="background: #f8f9fa; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
                        <p style="color: #2c3e50; margin-bottom: 0.5rem;">
                            <strong>License:</strong> <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener" style="color: #7FC7C4; text-decoration: none;">CC BY 4.0 International</a>
                        </p>
                        <p style="color: #666; margin: 0; font-size: 0.95rem;">
                            To view a copy of this license, visit: <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener" style="color: #7FC7C4; text-decoration: none;">https://creativecommons.org/licenses/by/4.0/</a>
                        </p>
                    </div>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">How to attribute this work:</h4>
                    <div style="background: #f8f9fa; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
                        <p style="color: #666; line-height: 1.8; margin-bottom: 0.75rem;">
                            When using or adapting UBEC Protocol materials, please include:
                        </p>
                        <code style="display: block; background: white; padding: 1rem; border-radius: 4px; border: 1px solid #e0e0e0; color: #2c3e50; font-family: 'Courier New', monospace; font-size: 0.9rem; line-height: 1.6; overflow-x: auto;">
"UBEC Protocol" by UBEC Protocol Network is licensed under CC BY 4.0.<br>
To view a copy of this license, visit https://creativecommons.org/licenses/by/4.0/
                        </code>
                    </div>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">Third-Party Content</h4>
                    <p style="color: #666; line-height: 1.8; margin-bottom: 1rem;">
                        Some content on this website may be created or owned by third parties and is subject to their respective licenses and copyrights. Third-party content is clearly marked as such. Please respect the intellectual property rights of others.
                    </p>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">Trademarks</h4>
                    <p style="color: #666; line-height: 1.8; margin-bottom: 1rem;">
                        The UBEC Protocol name and logo are trademarks of UBEC Protocol Network. Use of these trademarks is not covered by the CC-BY license and requires separate permission. Please contact us at <a href="mailto:legal@ubec.network" style="color: #7FC7C4; text-decoration: none;">legal@ubec.network</a> for trademark usage inquiries.
                    </p>
                    
                    <div style="background: linear-gradient(135deg, rgba(138, 166, 126, 0.1) 0%, rgba(127, 199, 196, 0.1) 100%); padding: 1.25rem; border-radius: 8px; border-left: 4px solid #7FC7C4;">
                        <p style="color: #2c3e50; line-height: 1.8; margin: 0; font-style: italic;">
                            <strong>Ubuntu Philosophy in Practice:</strong> By licensing our work under CC-BY, we embody the principle of "I am because we are." Knowledge shared freely enriches the entire community and enables collective growth.
                        </p>
                    </div>
                </div>
            </div>
EOF

# Find and replace the copyright section
# Using Python for more reliable multiline replacement
python3 << 'PYTHON_EOF'
import re

with open('templates/legal.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the copyright section (between <!-- Copyright --> and next <!-- section)
pattern = r'(<!-- Copyright -->.*?)(?=<!-- [A-Z]|\s*<!-- Attribution -->)'
replacement = '''            <!-- Copyright -->
            <div style="margin-bottom: 3rem;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #8AA67E; padding-bottom: 0.75rem; margin-bottom: 1.5rem; font-size: 1.75rem; font-weight: 600;">
                    Copyright & Licensing
                </h2>
                <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, rgba(138, 166, 126, 0.1) 0%, rgba(127, 199, 196, 0.1) 100%); padding: 1.5rem; border-radius: 8px; border-left: 4px solid #8AA67E; margin-bottom: 1.5rem;">
                        <h3 style="color: #2c3e50; margin-bottom: 0.75rem; font-size: 1.25rem;">Creative Commons Attribution (CC-BY 4.0)</h3>
                        <p style="color: #2c3e50; font-weight: 600; margin-bottom: 0.5rem;">
                            This work is licensed under a Creative Commons Attribution 4.0 International License.
                        </p>
                        <p style="color: #666; line-height: 1.8; margin: 0;">
                            In the spirit of Ubuntu philosophy ("I am because we are"), we share our work openly for the benefit of all.
                        </p>
                    </div>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">You are free to:</h4>
                    <ul style="color: #666; line-height: 1.8; margin-bottom: 1.5rem; padding-left: 1.5rem;">
                        <li><strong>Share</strong> — copy and redistribute the material in any medium or format</li>
                        <li><strong>Adapt</strong> — remix, transform, and build upon the material for any purpose, even commercially</li>
                    </ul>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">Under the following terms:</h4>
                    <ul style="color: #666; line-height: 1.8; margin-bottom: 1.5rem; padding-left: 1.5rem;">
                        <li><strong>Attribution</strong> — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.</li>
                        <li><strong>No additional restrictions</strong> — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.</li>
                    </ul>
                    
                    <div style="background: #f8f9fa; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
                        <p style="color: #2c3e50; margin-bottom: 0.5rem;">
                            <strong>License:</strong> <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener" style="color: #7FC7C4; text-decoration: none;">CC BY 4.0 International</a>
                        </p>
                        <p style="color: #666; margin: 0; font-size: 0.95rem;">
                            To view a copy of this license, visit: <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener" style="color: #7FC7C4; text-decoration: none;">https://creativecommons.org/licenses/by/4.0/</a>
                        </p>
                    </div>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">How to attribute this work:</h4>
                    <div style="background: #f8f9fa; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
                        <p style="color: #666; line-height: 1.8; margin-bottom: 0.75rem;">
                            When using or adapting UBEC Protocol materials, please include:
                        </p>
                        <code style="display: block; background: white; padding: 1rem; border-radius: 4px; border: 1px solid #e0e0e0; color: #2c3e50; font-family: 'Courier New', monospace; font-size: 0.9rem; line-height: 1.6; overflow-x: auto;">
"UBEC Protocol" by UBEC Protocol Network is licensed under CC BY 4.0.<br>
To view a copy of this license, visit https://creativecommons.org/licenses/by/4.0/
                        </code>
                    </div>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">Third-Party Content</h4>
                    <p style="color: #666; line-height: 1.8; margin-bottom: 1rem;">
                        Some content on this website may be created or owned by third parties and is subject to their respective licenses and copyrights. Third-party content is clearly marked as such. Please respect the intellectual property rights of others.
                    </p>
                    
                    <h4 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1.1rem;">Trademarks</h4>
                    <p style="color: #666; line-height: 1.8; margin-bottom: 1rem;">
                        The UBEC Protocol name and logo are trademarks of UBEC Protocol Network. Use of these trademarks is not covered by the CC-BY license and requires separate permission. Please contact us at <a href="mailto:legal@ubec.network" style="color: #7FC7C4; text-decoration: none;">legal@ubec.network</a> for trademark usage inquiries.
                    </p>
                    
                    <div style="background: linear-gradient(135deg, rgba(138, 166, 126, 0.1) 0%, rgba(127, 199, 196, 0.1) 100%); padding: 1.25rem; border-radius: 8px; border-left: 4px solid #7FC7C4;">
                        <p style="color: #2c3e50; line-height: 1.8; margin: 0; font-style: italic;">
                            <strong>Ubuntu Philosophy in Practice:</strong> By licensing our work under CC-BY, we embody the principle of "I am because we are." Knowledge shared freely enriches the entire community and enables collective growth.
                        </p>
                    </div>
                </div>
            </div>

            '''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open('templates/legal.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✓ Copyright section updated successfully")
else:
    print("⚠ Warning: Copyright section not found or already updated")
PYTHON_EOF

echo ""
echo "✅ Update complete!"
echo ""
echo "The copyright section now references CC-BY 4.0 license"
echo ""
echo "Test the page:"
echo "  http://localhost:8001/legal"
echo ""
echo "Rollback if needed:"
echo "  cp $BACKUP templates/legal.html"
echo ""
