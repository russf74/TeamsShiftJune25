#!/usr/bin/env python3
"""
Apply Fix #1: Atomic flag-setting to gui.py
This replaces the loop-based alert flagging with a single atomic transaction.
"""

import re

# Read the file
with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Strategy 1: Replace the specific code block
# Look for the pattern of the loop and replace it
original_pattern = r'''(\s+)# Mark all emailed shifts as alerted\s+from database import mark_shift_alerted\s+for date_str in matched_dates:\s+mark_shift_alerted\(date_str\)'''

replacement = r'''\1# Mark all emailed shifts as alerted IN A SINGLE ATOMIC TRANSACTION
\1# This prevents race conditions where a new scan starts while flags are being set
\1from database import mark_multiple_shifts_alerted
\1mark_multiple_shifts_alerted(matched_dates)'''

# Apply the replacement
new_content = re.sub(original_pattern, replacement, content, flags=re.MULTILINE)

# Check if replacement was successful
if new_content != content:
    # Write the updated content
    with open('gui.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("? SUCCESS: Applied Fix #1 to gui.py")
    print("   - Replaced loop-based flagging with atomic transaction")
    print(" - Function changed from mark_shift_alerted to mark_multiple_shifts_alerted")
else:
    print("??Pattern not found with regex, trying simpler replacement...")
    
    # Strategy 2: Simpler replacement
    old_import = "from database import mark_shift_alerted"
    new_import = "from database import mark_multiple_shifts_alerted"
    
    old_loop = """for date_str in matched_dates:
         mark_shift_alerted(date_str)"""
    new_call = "mark_multiple_shifts_alerted(matched_dates)"
    
    if old_import in content and old_loop in content:
        content = content.replace(old_import, new_import)
        content = content.replace(old_loop, new_call)
    
        with open('gui.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("? SUCCESS: Applied Fix #1 using simple replacement")
    else:
        print("? ERROR: Could not find target code to replace")
        print("   Please verify gui.py structure")
        exit(1)

print("\n?? Testing compilation...")
import py_compile
try:
    py_compile.compile('gui.py', doraise=True)
    print("? gui.py compiles successfully!")
except SyntaxError as e:
    print(f"? Syntax error in gui.py: {e}")
    exit(1)

print("\n?? Fix #1 applied successfully!")
print("   Both fixes are now active:")
print("   ? Fix #3: Protected booked shifts from deletion")
print("   ? Fix #1: Atomic flag-setting for open shifts")
