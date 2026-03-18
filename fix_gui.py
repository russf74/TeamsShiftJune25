import re

with open('gui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the section around line 945-955 and fix it
output = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Look for the problematic section
    if 'Mark all emailed shifts as alerted' in line and i > 900:
        # Skip the old code (next 3 lines)
        output.append('    # Mark all emailed shifts as alerted IN A SINGLE ATOMIC TRANSACTION\n')
        output.append('    # This prevents race conditions while flags are being set\n')
        output.append(' from database import mark_multiple_shifts_alerted\n')
        output.append('     mark_multiple_shifts_alerted(matched_dates)\n')
        output.append('        \n')
        output.append('                self.scan_status_var.set(f"Alert email sent for {len(matched_dates)} new matched shifts.")\n')
        # Skip next 4 lines (old code)
        i += 5
    else:
        output.append(line)
    i += 1

with open('gui.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print("Fixed gui.py")
