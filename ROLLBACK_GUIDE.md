# Rollback Guide - Teams Shift Application

## Quick Rollback Instructions

### If Something Breaks After New Changes

#### Option 1: Rollback to Tagged Snapshot (Recommended)
```powershell
# Go to your project directory
cd C:\Users\russf\TeamsShiftJune25

# See all available backup tags
git tag -l

# Rollback to the snapshot
git checkout backup-snapshot-2025-01-26

# If you want to make this permanent (discard all changes after snapshot)
git reset --hard backup-snapshot-2025-01-26
```

#### Option 2: Rollback Just One File
```powershell
# Rollback a specific file to the snapshot version
git checkout backup-snapshot-2025-01-26 -- filename.py

# Example: Rollback just the database module
git checkout backup-snapshot-2025-01-26 -- database.py
```

#### Option 3: See What Changed
```powershell
# Compare current code to snapshot
git diff backup-snapshot-2025-01-26

# See list of changed files
git diff --name-only backup-snapshot-2025-01-26

# See changes in a specific file
git diff backup-snapshot-2025-01-26 gui.py
```

---

## Current Backup Status

**? Backup Created:** January 26, 2025  
**? Snapshot Tag:** `backup-snapshot-2025-01-26`  
**? Pushed to GitHub:** Yes  
**? Branch:** enhancement/whatsapp-disable-sms-alerts  

### What's Backed Up
- ? All core Python modules (main.py, gui.py, automation.py, database.py, etc.)
- ? All reference images (PNG templates)
- ? Documentation (README.md, BACKUP_RESTORE_GUIDE.md, SYSTEM_ANALYSIS.md)
- ? Requirements.txt
- ? .gitignore

### What's NOT Backed Up (By Design)
- ? Database files (shifts.db, email.db) - contain user data
- ? Configuration files (smtp_settings.json, sms_config.json) - contain credentials
- ? Screenshots and video recordings
- ? Debug/test scripts

---

## Rollback Scenarios

### Scenario 1: "The app won't start"
```powershell
# Full rollback to last working version
git reset --hard backup-snapshot-2025-01-26
git push --force origin enhancement/whatsapp-disable-sms-alerts
```

### Scenario 2: "Scans are failing"
```powershell
# Rollback just the automation and OCR modules
git checkout backup-snapshot-2025-01-26 -- automation.py
git checkout backup-snapshot-2025-01-26 -- ocr_processing.py
git checkout backup-snapshot-2025-01-26 -- open_shift_ocr.py
git checkout backup-snapshot-2025-01-26 -- booked_shift_ocr.py
```

### Scenario 3: "Database errors"
```powershell
# Rollback database module
git checkout backup-snapshot-2025-01-26 -- database.py

# If database is corrupted, restore from backup (if you have one)
# Or delete and let app recreate: rm shifts.db
```

### Scenario 4: "Email/SMS not working"
```powershell
# Rollback alert modules
git checkout backup-snapshot-2025-01-26 -- email_alert.py
git checkout backup-snapshot-2025-01-26 -- sms_alert.py
git checkout backup-snapshot-2025-01-26 -- email_db.py
```

### Scenario 5: "GUI broken/calendar not showing"
```powershell
# Rollback GUI module
git checkout backup-snapshot-2025-01-26 -- gui.py
```

---

## How to Create Your Own Backup Before Making Changes

### Quick Snapshot (Every Time Before Changing Code)
```powershell
# 1. Commit your current work
git add .
git commit -m "Describe your changes here"

# 2. Create a new tag with today's date
git tag -a snapshot-YYYY-MM-DD -m "Backup before [what you're about to do]"

# 3. Push to GitHub
git push origin enhancement/whatsapp-disable-sms-alerts
git push origin snapshot-YYYY-MM-DD
```

### Full Backup (Important Milestones)
```powershell
# Create a new branch to preserve current state
git checkout -b backup-working-state-YYYY-MM-DD
git push origin backup-working-state-YYYY-MM-DD

# Go back to your working branch
git checkout enhancement/whatsapp-disable-sms-alerts
```

---

## Emergency Recovery (GitHub)

If your local copy is completely broken, you can always re-clone from GitHub:

```powershell
# 1. Backup your config files first!
# Copy these to a safe location:
#    - smtp_settings.json
#    - sms_config.json
#    - config.json
#    - shifts.db (if you want to keep your data)

# 2. Delete the broken directory
cd C:\Users\russf
rm -r -force TeamsShiftJune25

# 3. Re-clone from GitHub
git clone https://github.com/russf74/TeamsShiftJune25.git
cd TeamsShiftJune25

# 4. Checkout the snapshot tag
git checkout backup-snapshot-2025-01-26

# 5. Restore your config files from the backup location

# 6. Run the app
python main.py
```

---

## Verification After Rollback

After rolling back, verify everything works:

1. ? **App starts without errors**
   ```powershell
   python main.py
   ```

2. ? **Calendar displays correctly**
   - Check that current month shows
   - Shifts are color-coded correctly (blue/green/orange)

3. ? **Manual scan works**
 - Click "Scan" button
   - Verify 4-month scan completes
   - Check that shifts are detected

4. ? **Test messaging works**
   - Click "Test Msg" button
   - Verify email arrives
   - Check WhatsApp/SMS if configured

5. ? **Database integrity**
   - Navigate between months
   - Check availability checkboxes work
   - Verify shift counts are correct

---

## Contact & Support

- **GitHub Repository:** https://github.com/russf74/TeamsShiftJune25
- **Current Snapshot Tag:** backup-snapshot-2025-01-26
- **System Analysis:** See SYSTEM_ANALYSIS.md
- **Full Restore:** See BACKUP_RESTORE_GUIDE.md

---

**Remember:** Always create a backup before making significant changes!

