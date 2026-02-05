# MANUAL FIX GUIDE - Duplicate Alert Prevention

## Summary
Due to indentation issues in automated edits, here's a clean manual guide to apply the 2 critical fixes.

---

## FIX #3: Protect Booked Shifts (5-minute fix)

### File: `database.py`
### Function: `delete_shifts_not_in_list()` (starts around line 30)

### FIND THIS BLOCK (around line 54-62):
```python
    # Get all shifts for this month/type
    c.execute("SELECT date FROM shifts WHERE date >= ? AND date < ? AND shift_type = ?", (start, end, shift_type))
    rows = c.fetchall()
    deleted_count = 0
    deleted_dates = []
  for row in rows:
        date_str = row[0]
      if date_str not in valid_dates:
       # LOG EVERY DELETION
 logger.warning(f"DELETING {shift_type} shift: {date_str} (not found in scan results)")
      c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
            deleted_count += 1
        deleted_dates.append(date_str)
```

### REPLACE WITH:
```python
    # Get all shifts for this month/type with email status
    if shift_type == 'booked':
     c.execute("SELECT date, confirmed_email_sent FROM shifts WHERE date >= ? AND date < ? AND shift_type = ?", (start, end, shift_type))
    else:
        c.execute("SELECT date, alerted FROM shifts WHERE date >= ? AND date < ? AND shift_type = ?", (start, end, shift_type))
    
    rows = c.fetchall()
    deleted_count = 0
    protected_count = 0
    deleted_dates = []
    protected_dates = []
    
    for row in rows:
        date_str = row[0]
        email_flag = row[1] if len(row) > 1 else 0
        
        if date_str not in valid_dates:
   # CRITICAL SAFETY: Never delete booked shifts that have been confirmed via email
if shift_type == 'booked' and email_flag == 1:
      logger.warning(f"PROTECTED: Keeping booked shift {date_str} despite not in scan (confirmation email already sent)")
        protected_count += 1
         protected_dates.append(date_str)
         continue  # Don't delete this shift
        
          # Safe to delete
            logger.warning(f"DELETING {shift_type} shift: {date_str} (not found in scan results)")
            c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
    deleted_count += 1
            deleted_dates.append(date_str)
```

### AND ADD BEFORE `conn.commit()` (around line 67):
```python
    if protected_count > 0:
      logger.info(f"Protected {protected_count} confirmed booked shifts from deletion: {', '.join(protected_dates)}")
```

---

## FIX #1: Atomic Flag-Setting (3-minute fix)

### Part A: Add new function to `database.py`

### FIND (around line 230):
```python
def mark_shift_alerted(date_str):
    conn = sqlite3.connect(get_db_path())
  c = conn.cursor()
c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
    conn.commit()
    conn.close()
```

### ADD AFTER IT:
```python
def mark_multiple_shifts_alerted(date_list):
    """
Mark multiple shifts as alerted in a single atomic transaction.
    This prevents race conditions where a new scan starts while flags are being set.
    """
    if not date_list:
        return
    
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
for date_str in date_list:
        c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
    
    conn.commit()  # Single commit for ALL updates - atomic!
    conn.close()
    logger.info(f"Atomically marked {len(date_list)} shifts as alerted: {', '.join(date_list)}")
```

### Part B: Update `gui.py`

### FIND IN `send_availability_alert()` function (around line 945):
```python
          server.sendmail(user, list(all_recipients), msg.as_string())
                server.quit()
      # Mark all emailed shifts as alerted
      from database import mark_shift_alerted
       for date_str in matched_dates:
         mark_shift_alerted(date_str)
         self.scan_status_var.set(f"Alert email sent for {len(matched_dates)} new matched shifts.")
```

### REPLACE WITH:
```python
                server.sendmail(user, list(all_recipients), msg.as_string())
     server.quit()
 # Mark all emailed shifts as alerted IN A SINGLE ATOMIC TRANSACTION
     from database import mark_multiple_shifts_alerted
     mark_multiple_shifts_alerted(matched_dates)
 self.scan_status_var.set(f"Alert email sent for {len(matched_dates)} new matched shifts.")
```

---

## TESTING

After applying both fixes:

1. Test compilation:
```sh
python -m py_compile database.py gui.py
```

2. Test the app:
```sh
python main.py
```

3. Watch logs for:
```sh
python view_shift_logs.py
```

Look for:
- `PROTECTED: Keeping booked shift...` (Fix #3 working)
- `Atomically marked X shifts as alerted` (Fix #1 working)

---

## ROLLBACK

If anything breaks:
```sh
git reset --hard v1.0-pre-duplicate-fix
```

---

## WHAT THESE FIXES DO

**Fix #3:** Stops booked shifts from being deleted when OCR misses them, preventing duplicate confirmation emails

**Fix #1:** Makes alert flag-setting atomic, preventing race conditions that cause duplicate availability alerts

Both are **safe additions** - they only add protection, don't remove any logic.
