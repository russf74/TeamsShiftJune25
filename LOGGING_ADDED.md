# COMPREHENSIVE LOGGING ADDED

## Date: January 26, 2025

## Problem
Duplicate "Shift Confirmed" emails being sent for Jan 31st shift over several days, despite `confirmed_email_sent` flag being set.

## Root Cause (Suspected)
Shift is being **deleted** by `delete_shifts_not_in_list()` when OCR fails to detect it, then **re-added** as "new" by the next scan, triggering another confirmation email.

## Solution Implemented
Added comprehensive logging to track every shift operation:

### 1. Database Operations (`database.py`)
**Now logs:**
- ? Every shift deletion with reason
- ? Every shift addition (new vs re-add vs update)
- ? Every booking detection
- ? Email flag status checks
- ? Timestamp preservation for re-adds

**Example log entries:**
```
[2025-01-26 15:30:00] [WARNING] [delete_shifts_not_in_list] DELETING booked shift: 2026-01-31 (not found in scan results)
[2025-01-26 15:40:00] [WARNING] [add_shift] RE-ADDING booked shift: 2026-01-31 with original timestamp 2026-01-14 15:27:21 (was previously deleted!)
[2025-01-26 15:40:00] [INFO] [add_shift] NEW BOOKING detected: 2026-01-31 (will send confirmation email)
[2025-01-26 15:40:00] [INFO] [add_shift] SENDING confirmation email for NEW booking: 2026-01-31
```

### 2. Email Operations (`email_alert.py`)
**Now logs:**
- ? Every email send attempt
- ? Blocked emails (past dates, already sent)
- ? Email flag checks before sending
- ? Email flag updates after sending
- ? Success/failure status

**Example log entries:**
```
[2025-01-26 15:40:00] [INFO] [EMAIL] send_shift_confirmation_email() called for 2026-01-31
[2025-01-26 15:40:00] [INFO] [EMAIL] Proceeding to send confirmation email for 2026-01-31 (confirmed_email_sent=0)
[2025-01-26 15:40:00] [INFO] [EMAIL] SENDING email to russfray74@gmail.com, laurafray74@gmail.com - Subject: 'Shift Confirmed: Fri 31 Jan'
[2025-01-26 15:40:00] [INFO] [EMAIL] SUCCESS: Confirmation email sent for 2026-01-31, flag set to 1
```

### 3. Log File Location
**File:** `shift_operations.log` (in app directory)
**Format:** `[timestamp] [level] [function] message`
**Retention:** Persistent (not auto-deleted)

### 4. Log Viewer Tool
**File:** `view_shift_logs.py`

**Usage:**
```bash
# Show last 50 operations
python view_shift_logs.py

# Show all Jan 31st operations
python view_shift_logs.py jan31

# Search for specific date
python view_shift_logs.py 2026-01-31

# Search for specific operation
python view_shift_logs.py DELETING
```

**Features:**
- Color-coded output (red=delete, yellow=re-add, green=email)
- Easy searching
- Tail functionality

## What to Watch For

### Evidence of Bug (Delete/Re-Add Cycle)
If the bug is happening, you'll see this sequence:
```
[TIME1] DELETING booked shift: 2026-01-31 (not found in scan results)
[TIME2] RE-ADDING booked shift: 2026-01-31 with original timestamp ... (was previously deleted!)
[TIME2] NEW BOOKING detected: 2026-01-31 (will send confirmation email)
[TIME2] SENDING confirmation email for NEW booking: 2026-01-31
```

### Evidence of Proper Operation
If working correctly, you'll see:
```
[TIME] UPDATING existing booked shift: 2026-01-31, count 1->1, created_at=..., email_sent=1
[TIME] Existing booked shift: 2026-01-31, confirmed_email_sent=1
```

## Next Steps

### 1. Monitor for 24-48 Hours
- Let the app run with new logging
- Check logs after each scan
- Watch for delete/re-add patterns

### 2. If Bug Confirmed
We'll see the exact sequence:
1. OCR fails to detect Jan 31st in scan
2. Cleanup deletes it as "stale"
3. Next scan detects it again
4. Re-adds as "new" (even though it's not)
5. Sends another confirmation email

### 3. Permanent Fix
Once confirmed, add this check to `add_shift()`:
```python
# Before sending email, check if it was already sent
if is_new_booking and shift_type == 'booked':
    c.execute("SELECT confirmed_email_sent FROM shift_history WHERE date = ? AND shift_type = 'booked'", (date_str,))
    history = c.fetchone()
    if history and history[0] == 1:
      logger.info(f"BLOCKED: Email already sent previously for {date_str}")
return  # Don't send duplicate
```

## Files Modified
1. ? `database.py` - Added logging to all shift operations
2. ? `email_alert.py` - Added logging to email operations
3. ? `view_shift_logs.py` - Created log viewer tool

## No Breaking Changes
- All existing functionality preserved
- Only added logging statements
- No logic changes
- Safe to deploy immediately

## Testing
Run this to see current status:
```bash
python view_shift_logs.py jan31
```

If no logs yet (first run), they'll start appearing after next scan.
