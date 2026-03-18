#!/usr/bin/env python3
# Simple script to apply atomic flag fix to gui.py

with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the loop with atomic function call
old = """     # Mark all emailed shifts as alerted
        from database import mark_shift_alerted
             for date_str in matched_dates:
  mark_shift_alerted(date_str)
     self.scan_status_var.set(f"Alert email sent for {len(matched_dates)} new matched shifts.")"""

new = """          # Mark all emailed shifts as alerted IN A SINGLE ATOMIC TRANSACTION
        # This prevents race conditions where a new scan starts while flags are being set
         from database import mark_multiple_shifts_alerted
  mark_multiple_shifts_alerted(matched_dates)
            self.scan_status_var.set(f"Alert email sent for {len(matched_dates)} new matched shifts.")"""

if old in content:
 content = content.replace(old, new)
 with open('gui.py', 'w', encoding='utf-8') as f:
     f.write(content)
    print("SUCCESS: Applied atomic flag fix to gui.py")
else:
    print("ERROR: Could not find target code section")
    print("Trying backup replacement strategy...")
    # Try alternate pattern
    old2 = """for date_str in matched_dates:
           mark_shift_alerted(date_str)"""
    new2 = """mark_multiple_shifts_alerted(matched_dates)"""
    if old2 in content:
    content = content.replace(old2, new2)
     content = content.replace("from database import mark_shift_alerted", "from database import mark_multiple_shifts_alerted")
        with open('gui.py', 'w', encoding='utf-8') as f:
            f.write(content)
  print("SUCCESS: Applied fix using backup strategy")
    else:
        print("ERROR: Backup strategy also failed")
