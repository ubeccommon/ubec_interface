# Complete Documentation Guides - Deployment Guide

## 📚 All Guide Files Ready

All UBEC documentation guides are now prepared for deployment. Here's what you have:

---

## 📁 File Structure

```
docs/
├── guides/
│   ├── README.md                                    # Guides directory index
│   └── participation-guide.md                       # Main entry guide (✓ WORKING)
│
├── UBEC_Token_Holders_User_Guides.md               # Token holders guide (152KB)
├── UBEC_Developer_Onboarding_Guide.md              # Developers guide (104KB)
├── UBEC_Governance_Participant_Guide.md            # Governance guide (44KB)
├── UBEC_Community_Organizer_Guide.md               # Organizers guide (46KB)
├── UBEC_Community_Organizer_Quick_Start_Checklist.md  # Quick start (14KB)
├── UBEC_Onboarding_User_Guides.md                  # Onboarding (farmers/communities/activators) (92KB)
├── UBEC_Public_Guide.md                            # Public/general audience (22KB)
├── SYSTEM_ADMINISTRATOR_ONBOARDING_GUIDE.md        # System admins guide (33KB)
├── TECHNICAL_OPERATOR_ONBOARDING_GUIDE.md          # Technical operators guide (56KB)
├── UBEC_Core_Beneficiary_Profiles.md               # Beneficiary profiles (31KB)
└── UBEC_User_Group_Definitions.md                  # User types reference (21KB)
```

**Total:** 12 comprehensive guides covering all user types

---

## 📖 Guide Descriptions

### Core Entry Point
**✓ participation-guide.md** (ALREADY WORKING)
- Main entry point for all users
- Helps users find their appropriate pathway
- Links to all other guides
- URL: `/docs/guides/participation-guide`

### User-Specific Guides

#### 1. **UBEC_Token_Holders_User_Guides.md** (152KB - Comprehensive)
**For:** Anyone holding or transacting with UBEC tokens
**Content:**
- Understanding the four-token system
- Holonic evaluation framework
- Building your Ubuntu alignment score
- Transaction best practices
- Advanced participation strategies
**URL:** `/docs/UBEC_Token_Holders_User_Guides`

#### 2. **UBEC_Developer_Onboarding_Guide.md** (104KB - Technical)
**For:** Software developers and technical contributors
**Content:**
- Development environment setup
- API integration guide
- Code contribution guidelines
- Architecture overview
- Testing and deployment
**URL:** `/docs/UBEC_Developer_Onboarding_Guide`

#### 3. **UBEC_Governance_Participant_Guide.md** (44KB)
**For:** Token holders participating in governance
**Content:**
- Governance structure and process
- Proposal creation and voting
- Holonic score influence
- Constitutional principles
- Best practices for participation
**URL:** `/docs/UBEC_Governance_Participant_Guide`

#### 4. **UBEC_Community_Organizer_Guide.md** (46KB)
**For:** Local leaders establishing UBEC in their bioregions
**Content:**
- Community organizing strategies
- Onboarding new users
- Building local networks
- Facilitating adoption
- Measuring success
**URL:** `/docs/UBEC_Community_Organizer_Guide`

#### 5. **UBEC_Community_Organizer_Quick_Start_Checklist.md** (14KB)
**For:** New community organizers
**Content:**
- 90-day action plan
- Week-by-week checklist
- Quick wins and milestones
- Common pitfalls to avoid
**URL:** `/docs/UBEC_Community_Organizer_Quick_Start_Checklist`

#### 6. **UBEC_Onboarding_User_Guides.md** (92KB - Comprehensive)
**For:** Core beneficiaries (farmers, communities, activators)
**Content:**
- Three separate onboarding paths:
  - Farmer onboarding process
  - Community onboarding process
  - Community activator onboarding
- Application processes
- First 90 days guidance
- Reporting requirements
**URL:** `/docs/UBEC_Onboarding_User_Guides`

#### 7. **UBEC_Public_Guide.md** (22KB)
**For:** General public and curious learners
**Content:**
- What is UBEC?
- Ubuntu philosophy explained
- How the system works
- Ways to get involved
- FAQ for beginners
**URL:** `/docs/UBEC_Public_Guide`

#### 8. **SYSTEM_ADMINISTRATOR_ONBOARDING_GUIDE.md** (33KB)
**For:** System administrators managing infrastructure
**Content:**
- System setup and configuration
- Monitoring and maintenance
- Health checks and troubleshooting
- Security best practices
- Operations protocols
**URL:** `/docs/SYSTEM_ADMINISTRATOR_ONBOARDING_GUIDE`

#### 9. **TECHNICAL_OPERATOR_ONBOARDING_GUIDE.md** (56KB)
**For:** DevOps and operations professionals
**Content:**
- Deployment procedures
- Performance optimization
- Incident response
- Automation setup
- Scaling strategies
**URL:** `/docs/TECHNICAL_OPERATOR_ONBOARDING_GUIDE`

### Reference Documents

#### 10. **UBEC_Core_Beneficiary_Profiles.md** (31KB)
**For:** Understanding grant recipients
**Content:**
- Farmer profile definitions
- Community profile definitions
- Activator profile definitions
- Application criteria
- Support systems
**URL:** `/docs/UBEC_Core_Beneficiary_Profiles`

#### 11. **UBEC_User_Group_Definitions.md** (21KB)
**For:** System-wide reference
**Content:**
- Complete taxonomy of all user types
- Needs and tools matrix
- Journey stages
- Success metrics
**URL:** `/docs/UBEC_User_Group_Definitions`

---

## 🚀 Deployment Instructions

### Method 1: Deploy All Guides (Recommended)

```bash
# On your server, from project root
cd /srv/ubec-www/app

# Copy entire docs directory
cp -r /path/to/docs ./

# Verify structure
ls -la docs/
ls -la docs/guides/

# Files should be:
# docs/UBEC_*.md (11 files)
# docs/SYSTEM_*.md (1 file)
# docs/TECHNICAL_*.md (1 file)
# docs/guides/README.md
# docs/guides/participation-guide.md
```

### Method 2: Deploy Selectively (As Needed)

Deploy guides one at a time based on priority:

**Priority 1 - Already Working:**
- ✓ participation-guide.md

**Priority 2 - Most Used:**
```bash
cp UBEC_Token_Holders_User_Guides.md /srv/ubec-www/app/docs/
cp UBEC_Onboarding_User_Guides.md /srv/ubec-www/app/docs/
cp UBEC_Public_Guide.md /srv/ubec-www/app/docs/
```

**Priority 3 - Community Tools:**
```bash
cp UBEC_Community_Organizer_Guide.md /srv/ubec-www/app/docs/
cp UBEC_Community_Organizer_Quick_Start_Checklist.md /srv/ubec-www/app/docs/
```

**Priority 4 - Technical:**
```bash
cp UBEC_Developer_Onboarding_Guide.md /srv/ubec-www/app/docs/
cp SYSTEM_ADMINISTRATOR_ONBOARDING_GUIDE.md /srv/ubec-www/app/docs/
cp TECHNICAL_OPERATOR_ONBOARDING_GUIDE.md /srv/ubec-www/app/docs/
```

**Priority 5 - Governance & Reference:**
```bash
cp UBEC_Governance_Participant_Guide.md /srv/ubec-www/app/docs/
cp UBEC_Core_Beneficiary_Profiles.md /srv/ubec-www/app/docs/
cp UBEC_User_Group_Definitions.md /srv/ubec-www/app/docs/
```

---

## 🔗 URL Patterns

All guides will be accessible at:

**Base Pattern:** `https://bioregional.ubec.network/docs/{filename-without-.md}`

**Examples:**
- `/docs/UBEC_Token_Holders_User_Guides`
- `/docs/UBEC_Developer_Onboarding_Guide`
- `/docs/UBEC_Governance_Participant_Guide`
- `/docs/SYSTEM_ADMINISTRATOR_ONBOARDING_GUIDE`
- etc.

**Guides Index:**
- `/docs/guides/` - Main guide directory

---

## ✅ Testing After Deployment

### Test Each Guide:

```bash
# From your local machine or via curl

# Token Holders
curl https://bioregional.ubec.network/docs/UBEC_Token_Holders_User_Guides

# Developer
curl https://bioregional.ubec.network/docs/UBEC_Developer_Onboarding_Guide

# Public
curl https://bioregional.ubec.network/docs/UBEC_Public_Guide

# All should return HTML (200 status), not 404
```

### Visual Browser Test:

Visit each URL in browser and verify:
- ✓ Page loads (no 404)
- ✓ Markdown rendered as HTML
- ✓ Navigation works
- ✓ Tables display correctly
- ✓ Links work
- ✓ Emojis render

---

## 📝 Updating Links in Participation Guide

The participation guide currently has relative links like:
```markdown
[Token Holder Guide](../UBEC_Token_Holders_User_Guides.md)
```

These should work correctly with the file structure above. If you get 404s on these links, you may need to update them to:
```markdown
[Token Holder Guide](/docs/UBEC_Token_Holders_User_Guides)
```

---

## 🎯 What Each Guide Is Used For

### For New Users:
1. **Start:** participation-guide.md
2. **Then:** UBEC_Public_Guide.md

### For Token Holders:
1. **Start:** participation-guide.md
2. **Then:** UBEC_Token_Holders_User_Guides.md

### For Farmers/Communities:
1. **Start:** participation-guide.md
2. **Then:** UBEC_Onboarding_User_Guides.md

### For Developers:
1. **Start:** participation-guide.md
2. **Then:** UBEC_Developer_Onboarding_Guide.md

### For Organizers:
1. **Start:** participation-guide.md
2. **Then:** UBEC_Community_Organizer_Guide.md
3. **Use:** UBEC_Community_Organizer_Quick_Start_Checklist.md

### For Governance:
1. **Start:** UBEC_Token_Holders_User_Guides.md
2. **Then:** UBEC_Governance_Participant_Guide.md

### For Admins:
1. **Start:** SYSTEM_ADMINISTRATOR_ONBOARDING_GUIDE.md (direct)

---

## 📊 File Sizes Reference

| File | Size | Density |
|------|------|---------|
| UBEC_Token_Holders_User_Guides.md | 152KB | Comprehensive |
| UBEC_Developer_Onboarding_Guide.md | 104KB | Very Detailed |
| UBEC_Onboarding_User_Guides.md | 92KB | Comprehensive |
| TECHNICAL_OPERATOR_ONBOARDING_GUIDE.md | 56KB | Detailed |
| UBEC_Community_Organizer_Guide.md | 46KB | Detailed |
| UBEC_Governance_Participant_Guide.md | 44KB | Moderate |
| SYSTEM_ADMINISTRATOR_ONBOARDING_GUIDE.md | 33KB | Moderate |
| UBEC_Core_Beneficiary_Profiles.md | 31KB | Reference |
| UBEC_Public_Guide.md | 22KB | Light |
| UBEC_User_Group_Definitions.md | 21KB | Reference |
| UBEC_Community_Organizer_Quick_Start_Checklist.md | 14KB | Quick Ref |

**Total:** ~616KB of comprehensive documentation

---

## 🔄 Maintenance

### Updating a Guide:

1. Edit the .md file in the docs/ directory
2. No restart needed - changes take effect on next page load
3. Markdown is converted to HTML on each request

### Adding a New Guide:

1. Create new .md file in docs/ directory
2. Add link to guides/README.md
3. Add link to participation-guide.md if appropriate
4. No code changes needed - auto-discoverable

---

## 💡 Tips

### For Best Performance:
- Keep markdown files under 200KB
- Use relative links between guides
- Optimize images if adding any

### For Best User Experience:
- Maintain consistent formatting across guides
- Use clear section headers
- Include navigation links at top/bottom
- Add table of contents for long guides

### For Maintenance:
- Use version numbers in guides
- Document update dates
- Keep a changelog for major revisions
- Test all internal links after updates

---

## 🎉 Current Status

✅ **Working Now:**
- participation-guide.md accessible at `/docs/guides/participation-guide`
- All guide files ready for deployment
- Route handlers configured in main_web.py
- Template ready for rendering

⏳ **Deploy Next:**
- Copy all 11 guide files to `/srv/ubec-www/app/docs/`
- Test each URL
- Update any broken internal links

---

## 🆘 Troubleshooting

### Guide Returns 404
```bash
# Check file exists
ls -la /srv/ubec-www/app/docs/UBEC_Token_Holders_User_Guides.md

# Check permissions
chmod 644 /srv/ubec-www/app/docs/*.md

# Test route
curl http://localhost:8001/docs/UBEC_Token_Holders_User_Guides
```

### Markdown Not Rendering
- Verify markdown package installed
- Check file encoding: `file docs/UBEC_Token_Holders_User_Guides.md`
- Should show: "UTF-8 Unicode text"

### Links Don't Work
- Update relative links to absolute paths
- Or ensure file structure matches link paths

---

## 📦 What's in Outputs Folder

All files are ready in `/mnt/user-data/outputs/docs/`:

```
docs/
├── guides/
│   ├── README.md
│   └── participation-guide.md
└── [All 11 guide files]
```

**Ready to copy to your server!**

---

## Attribution

This project uses the services of Claude and Anthropic PBC to inform our decisions and recommendations. This project was made possible with the assistance of Claude and Anthropic PBC.

---

**Next Action:** Deploy all guide files to your server using the commands above! 🚀
