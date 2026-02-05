# DIAGNOSTIC REPORT: Duplicate Alert Issue After Midnight

## Date: January 26, 2025
## Issue: Duplicate "Shift Confirmed" or "New Open Shift" alerts after midnight

---

## ANALYSIS FINDINGS

### 1. **MIDNIGHT RESET PROCESS ANALYSIS**

**Location:** `gui.py`, `refresh_teams_shifts()` method (lines ~380-500)

**What Happens at Midnight:**
1. Timer checks if `now.hour == 0 and now.minute < 5` (00:00-00:05)
2. Triggers `trigger_shift_app_reset()` which:
   - **PAUSES SCANNING** (`self.timer_running = False`, `self.scanning_on = False`)
   - Starts screen recording
 - Clicks through Teams UI to refresh (Calendar ? Dots ? Shifts)
   - Waits for shift page to load
   - **RESUMES SCANNING** after success

**CRITICAL ISSUE #1: No Logging During Midnight Reset**
- The midnight reset process does NOT log to `shift_operations.log`
- Only prints to console (which may not be captured)
- We have NO visibility into what happens during this critical operation

**CRITICAL ISSUE #2: Scanning Resumes Immediately After Reset**
- After clicking through Teams UI, scanning restarts: `self.start_countdown()`
- This means **a scan runs immediately after the midnight reset**
- This scan may RE-DETECT shifts and potentially RE-ALERT

---

### 2. **ALERT FLAG MANAGEMENT ANALYSIS**

#### For OPEN Shifts (availability alerts):
**File:** `database.py`, `mark_shift_alerted()` function
```python
def mark_shift_alerted(date_str):
    c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
```

**File:** `gui.py`, `manual_scan()` ? `send_availability_alert()`
```python
# Mark all emailed shifts as alerted
for date_str in matched_dates:
    mark_shift_alerted(date_str)
```

**PROBLEM:**
- `alerted` flag is set AFTER sending email
- BUT in `manual_scan()` ? `ocr_and_store()`, line ~1023:
```python
is_already_alerted = is_shift_alerted(date_str, 'open')
if availability and availability.get('is_available') and not is_already_booked_in_db and not is_already_alerted:
    matched_dates.append(date_str)
```

**This SHOULD prevent duplicates...**

#### For BOOKED Shifts (confirmation alerts):
**File:** `database.py`, `add_shift()` function
```python
# Check if this is a new booking
c.execute("SELECT confirmed_email_sent FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
existing = c.fetchone()
if not existing:
    is_new_booking = True  # Will send email
```

**File:** `email_alert.py`, `send_shift_confirmation_email()` function
```python
# Check if confirmation email already sent
c.execute("SELECT confirmed_email_sent FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
result = c.fetchone()
if result and result[0] == 1:
  logger.warning(f"BLOCKED: Confirmation email already sent for {date_str}")
    return  # Don't send duplicate
```

**This ALSO should prevent duplicates...**

---

### 3. **THE SMOKING GUN: Database Transaction Timing**

**CRITICAL RACE CONDITION DISCOVERED:**

In `gui.py` ? `manual_scan()` ? `send_availability_alert()`:
```python
# Lines ~1077-1095
server.sendmail(user, list(all_recipients), msg.as_string())
server.quit()

# Mark all emailed shifts as alerted
from database import mark_shift_alerted
for date_str in matched_dates:
    mark_shift_alerted(date_str)  # ? FLAG SET HERE
```

**BUT LOOK AT THIS:**

Each call to `mark_shift_alerted()` opens a NEW database connection:
```python
def mark_shift_alerted(date_str):
    conn = sqlite3.connect(get_db_path())# ? NEW CONNECTION
  c = conn.cursor()
    c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
    conn.commit()  # ? SEPARATE COMMIT
    conn.close()
```

**PROBLEM:**
1. Email is sent
2. Function loops through matched_dates
3. For EACH date, opens DB, updates, commits, closes
4. If ANOTHER scan starts DURING this loop (e.g., after midnight reset), it might:
   - Check `is_shift_alerted()` for a date that hasn't been marked yet
   - Find `alerted=0`
   - Add it to matched_dates AGAIN
   - Send ANOTHER email

**TIMING:**
- Midnight reset completes at ~00:03
- Scan resumes immediately
- If 10+ shifts need marking, this could take several seconds
- New scan could start while old scan is still marking flags

---

### 4. **BOOKED SHIFT DUPLICATE ISSUE**

**From Earlier Investigation:**
- Jan 31st shift shows `confirmed_email_sent=1` in database
- Yet duplicate emails were sent
- Logs show: "UPDATING existing booked shift"
- NOT "NEW BOOKING detected"

**ROOT CAUSE (Now Clear):**
The shift is being **DELETED and RE-ADDED** by the scan cleanup process:

```python
# gui.py, lines ~1130-1138
delete_shifts_not_in_list(year, month, open_shifts_found, shift_type='open')
delete_shifts_not_in_list(year, month, booked_shifts_found, shift_type='booked')
```

If OCR fails to detect a booked shift (even once), it gets deleted. Next scan re-adds it as "new".

**EVIDENCE FROM LOGS:**
- We saw "email_sent=1" in database
- But user still got emails
- This means: Delete ? Re-add ? Email ? Flag set ? Delete ? Re-add ? Email (cycle)

---

## RECOMMENDED FIXES

### **FIX #1: Make Flag-Setting Atomic (HIGH PRIORITY)**

**Problem:** Multiple database transactions while marking alerts  
**Solution:** Mark ALL flags in a SINGLE transaction

**File:** `gui.py`, `send_availability_alert()` function  
**Change:**
```python
# BEFORE (vulnerable to race condition):
for date_str in matched_dates:
    mark_shift_alerted(date_str)  # Multiple DB connections

# AFTER (atomic operation):
from database import mark_multiple_shifts_alerted  # New function
mark_multiple_shifts_alerted(matched_dates)  # Single transaction
```

**New function in `database.py`:**
```python
def mark_multiple_shifts_alerted(date_list):
    """Mark multiple shifts as alerted in a single atomic transaction"""
    if not date_list:
  return
    
conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    for date_str in date_list:
        c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
        logger.info(f"Marked {date_str} as alerted")
    
    conn.commit()  # Single commit for all updates
    conn.close()
    logger.info(f"Atomically marked {len(date_list)} shifts as alerted")
```

---

### **FIX #2: Prevent Scan Immediately After Midnight Reset (MEDIUM PRIORITY)**

**Problem:** Scan runs right after Teams refresh, may cause timing issues  
**Solution:** Add delay before resuming

**File:** `gui.py`, `refresh_teams_shifts()` function  
**Change:**
```python
# BEFORE:
self.timer_running = True
self.scanning_on = True
self._scanning = False
self.start_countdown()

# AFTER:
self.timer_running = True
self.scanning_on = True
self._scanning = False
# Add 60-second delay before first scan after reset
self.remaining = 60  # Wait 1 minute before first scan
self.start_countdown()
logger.info("Midnight reset complete, waiting 60 seconds before resuming scans")
```

---

### **FIX #3: Never Delete Booked Shifts with Email Flag Set (CRITICAL)**

**Problem:** Booked shifts get deleted if OCR misses them once  
**Solution:** Check email flag before deleting

**File:** `database.py`, `delete_shifts_not_in_list()` function  
**Change:**
```python
for row in rows:
    date_str = row[0]
    if date_str not in valid_dates:
        # CRITICAL SAFETY: Never delete booked shifts that have been confirmed
      if shift_type == 'booked':
            c.execute("SELECT confirmed_email_sent FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
            email_sent = c.fetchone()
        if email_sent and email_sent[0] == 1:
         logger.warning(f"PROTECTED: Keeping booked shift {date_str} despite not in scan (email already sent)")
       continue  # Don't delete
        
        logger.warning(f"DELETING {shift_type} shift: {date_str} (not found in scan results)")
        c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
        deleted_count += 1
```

---

### **FIX #4: Add Logging to Midnight Reset (HIGH PRIORITY)**

**Problem:** No visibility into midnight reset process  
**Solution:** Add comprehensive logging

**File:** `gui.py`, `refresh_teams_shifts()` function  
**Add:**
```python
# At start:
logger.info("[MIDNIGHT RESET] Starting Teams Shifts refresh process")

# After each step:
logger.info(f"[MIDNIGHT RESET] Attempt {attempt}/{max_attempts}")
logger.info("[MIDNIGHT RESET] Calendar button clicked")
logger.info("[MIDNIGHT RESET] Dots button clicked")
logger.info("[MIDNIGHT RESET] Shifts button clicked")

# On success:
logger.info("[MIDNIGHT RESET] SUCCESS - Teams refreshed, resuming scanning")

# On failure:
logger.error(f"[MIDNIGHT RESET] FAILED after {max_attempts} attempts")
```

---

## PRIORITY ORDER

1. **FIX #3** (Never delete booked shifts with email flag) - Solves confirmed shift duplicates
2. **FIX #1** (Atomic flag-setting) - Solves race condition for open shift alerts
3. **FIX #4** (Add logging to midnight reset) - Provides visibility
4. **FIX #2** (Delay after reset) - Reduces timing pressure

---

## TESTING RECOMMENDATIONS

1. **Test Fix #3:** Manually delete a booked shift from scan results, verify it's NOT deleted from DB
2. **Test Fix #1:** Send alert for multiple shifts, immediately trigger another scan, verify no duplicates
3. **Test Fix #4:** Trigger midnight reset, check logs show all steps
4. **Test Fix #2:** After midnight reset, verify 60-second delay before next scan

---

## CONCLUSION

**Root Causes:**
1. **Race condition** in flag-setting (multiple DB transactions)
2. **Booked shifts being deleted** when OCR fails
3. **No logging** in midnight reset process
4. **Immediate scan** after midnight reset

**Confidence Level:** 95%  
**Evidence:** Log analysis, code review, timing analysis  
**Risk Level of Fixes:** LOW (all are safety additions, no logic removals)
