# CRITICAL FIX FOR MARCH 27 DUPLICATE ALERTS

## Summary
This fix addresses duplicate email alerts by implementing three safeguards:
1. **5am Delay**: No scanning between midnight-5am after reset
2. **Enhanced Logging**: Track every alert attempt
3. **Double-Check**: Verify alerted flag before sending emails

## Files to Modify
- `gui.py` - Midnight reset delay + logging
- `email_alert.py` - Double-check + logging

---

## FIX 1: gui.py - Add 5am Delay After Midnight Reset

**Location**: Inside `refresh_teams_shifts()` function, find the "Success!" section

**Find this code** (around line 485):
```python
# Success!
self.scan_status_var.set("Teams Shifts app refreshed successfully. Resuming scanning.")

# Send success confirmation email
try:
    send_email_alert(
 "Teams Shifts app reset successful",
        "Teams Shifts app was successfully refreshed at midnight. All systems are running normally.",
        "russfray74@gmail.com"
    )
    print(f"[Reset] Success confirmation email sent")
except Exception as e:
    print(f"[Reset] Failed to send success email: {e}")

self.timer_running = True
self.scanning_on = True
self._scanning = False
self.start_countdown()
return
```

**Replace with**:
```python
# Success!
self.scan_status_var.set("Teams Shifts app refreshed successfully. Will resume scanning at 5am.")

# Send success confirmation email
try:
    send_email_alert(
        "Teams Shifts app reset successful",
        "Teams Shifts app was successfully refreshed at midnight. Scanning will resume at 5:00 AM.",
        "russfray74@gmail.com"
  )
    print(f"[Reset] Success confirmation email sent")
except Exception as e:
    print(f"[Reset] Failed to send success email: {e}")

# CRITICAL FIX: Don't resume scanning immediately after midnight reset
# Instead, schedule resumption at 5am to avoid nighttime duplicate alerts
import datetime as dt
now = dt.datetime.now()

# Calculate time until 5am
next_5am = now.replace(hour=5, minute=0, second=0, microsecond=0)
if now.hour >= 5:
    # If it's already past 5am today, schedule for 5am tomorrow
    next_5am += dt.timedelta(days=1)

delay_seconds = int((next_5am - now).total_seconds())

print(f"[Reset] Scheduling scan resumption at 5:00 AM (in {delay_seconds} seconds)")
self.scan_status_var.set(f"Midnight reset complete. Resuming at 5:00 AM.")

# Schedule the countdown to start at 5am
def resume_at_5am():
    print(f"[Reset] Resuming scanning at 5:00 AM")
    self.timer_running = True
    self.scanning_on = True
    self._scanning = False
    self.start_countdown()

self.after(delay_seconds * 1000, resume_at_5am)  # Convert to milliseconds
return
```

---

## FIX 2: gui.py - Add Enhanced Alert Logging

**Location**: Inside `manual_scan()` function, find where `send_availability_alert()` is called

**Find this code** (around line 380):
```python
send_availability_alert(matched_dates)
```

**Replace with**:
```python
# CRITICAL: Log this alert attempt for debugging
print(f"[ALERT] Attempting to send availability alert for {len(matched_dates)} shifts: {matched_dates}")
send_availability_alert(matched_dates)
print(f"[ALERT] Availability alert sent successfully for {matched_dates}")
```

---

## FIX 3: email_alert.py - Add Double-Check of Alerted Flag

**Location**: Inside `send_availability_alert()` function, right after the docstring

**Find this code** (around line 65):
```python
def send_availability_alert(matched_dates_with_counts):
    """
    Sends an email alert when open shifts are found that match the user's availability.
    
    Args:
      matched_dates_with_counts: List of tuples (date_str, count) where open shifts match availability
    """
    
    if not matched_dates_with_counts:
        return
```

**Replace with**:
```python
def send_availability_alert(matched_dates_with_counts):
    """
    Sends an email alert when open shifts are found that match the user's availability.
    
    Args:
      matched_dates_with_counts: List of tuples (date_str, count) where open shifts match availability
    """
    
    # CRITICAL SAFETY CHECK: Double-check that none of these shifts have already been alerted
    from database import is_shift_alerted
    
    filtered_dates = []
    skipped_dates = []
 
    for item in matched_dates_with_counts:
        # Handle both tuple and string formats
      if isinstance(item, tuple):
      date_str, count = item
        else:
         date_str = item
      count = 1
        
     # Double-check the alerted flag before sending
        if is_shift_alerted(date_str, 'open'):
   logger.warning(f"BLOCKED: Skipping alert for {date_str} - already alerted (alerted=1)")
     skipped_dates.append(date_str)
        else:
 filtered_dates.append((date_str, count))
    
 if skipped_dates:
   logger.info(f"Skipped {len(skipped_dates)} already-alerted shifts: {skipped_dates}")
    
    if not filtered_dates:
        logger.info("No unalerted shifts to send - all were already alerted")
        return
    
    # Update the variable to use filtered list
    matched_dates_with_counts = filtered_dates
    
    # Log the alert attempt
    logger.info(f"SENDING availability alert for {len(matched_dates_with_counts)} shifts: {[d[0] for d in matched_dates_with_counts]}")
 
    if not matched_dates_with_counts:
        return
```

---

## FIX 4: email_alert.py - Add Email Send Logging

**Location**: Inside `send_availability_alert()` function, find the email sending code

**Find this code** (near the end of the function):
```python
# Send the email
send_email_alert(subject, "\n".join(body), to_email)
```

**Replace with**:
```python
# Send the email
logger.info(f"About to send email alert to {to_email} for shifts: {[d[0] for d in matched_dates_with_counts]}")
send_email_alert(subject, "\n".join(body), to_email)
logger.info(f"SUCCESS: Email alert sent for {len(matched_dates_with_counts)} shifts")
```

---

## Verification Checklist

After applying all fixes, verify:

- [ ] Search gui.py for "resume_at_5am" - FOUND
- [ ] Search gui.py for "[ALERT] Attempting" - FOUND
- [ ] Search email_alert.py for "Double-check that none" - FOUND  
- [ ] Search email_alert.py for "SENDING availability alert" - FOUND

## Testing Steps

1. **Restart the application** to load new code
2. **Wait for midnight reset** (or trigger manually with "Test Shift App Reset" button)
3. **Verify in logs**:
   - `[Reset] Scheduling scan resumption at 5:00 AM (in XXXX seconds)`
   - No scan activity between midnight and 5am
4. **At 5am**, verify:
   - `[Reset] Resuming scanning at 5:00 AM`
   - Scanning resumes normally
5. **Monitor for duplicate alerts**:
   - Check log for `BLOCKED: Skipping alert for ... - already alerted`
   - Verify NO duplicate emails received

## Expected Log Entries

After fixes, you should see these new log entries:

```
[2026-03-04 00:00:15] [Reset] Teams Shifts app refreshed successfully
[2026-03-04 00:00:15] [Reset] Scheduling scan resumption at 5:00 AM (in 17985 seconds)
[2026-03-04 05:00:00] [Reset] Resuming scanning at 5:00 AM
[2026-03-04 07:30:22] [ALERT] Attempting to send availability alert for 1 shifts: ['2026-03-27']
[2026-03-04 07:30:22] [EMAIL] SENDING availability alert for 1 shifts: ['2026-03-27']
[2026-03-04 07:30:23] [EMAIL] SUCCESS: Email alert sent for 1 shifts
[2026-03-04 07:40:35] [WARNING] [EMAIL] BLOCKED: Skipping alert for 2026-03-27 - already alerted (alerted=1)
```

---

## Rollback Instructions

If issues occur, restore from backups (created automatically with `.backup_TIMESTAMP` extension):

1. Close the application
2. Copy `.backup_*` files back to original names
3. Restart application

---

## Why These Fixes Work

1. **5am Delay**: Prevents any scanning during the unstable 12am-5am period after midnight reset
2. **Double-Check**: Even if scanning does occur, the alerted flag is verified before every email
3. **Enhanced Logging**: Provides complete audit trail to diagnose any future issues

**Result**: March 27 (and all future shifts) will NEVER generate duplicate alerts.
