"""
COMPREHENSIVE FIX FOR MARCH 27 DUPLICATE ALERTS
================================================

This document contains the exact code changes needed to fix the duplicate alert bug.

Apply these fixes manually to:
1. gui.py
2. email_alert.py

All three critical fixes are included:
- Enhanced email alert logging
- 5am delay after midnight reset
- Double-check of alerted flag
"""

# =============================================================================
# FIX 1: GUI.PY - Midnight Reset 5am Delay
# =============================================================================

"""
In gui.py, find the refresh_teams_shifts() function.
Replace the "Success!" section (around line 480-500) with this:
"""

REPLACE_THIS = """
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
"""

WITH_THIS = """
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
"""

# =============================================================================
# FIX 2: GUI.PY - Enhanced Alert Logging
# =============================================================================

"""
In gui.py, find the manual_scan() function.
Find the line that calls send_availability_alert (around line 380).
Replace:
"""

REPLACE_THIS_2 = """
     send_availability_alert(matched_dates)
"""

WITH_THIS_2 = """
     # CRITICAL: Log this alert attempt for debugging
        print(f"[ALERT] Attempting to send availability alert for {len(matched_dates)} shifts: {matched_dates}")
     send_availability_alert(matched_dates)
   print(f"[ALERT] Availability alert sent successfully for {matched_dates}")
"""

# =============================================================================
# FIX 3: EMAIL_ALERT.PY - Double-Check Alerted Flag
# =============================================================================

"""
In email_alert.py, find the send_availability_alert() function.
Replace the entire beginning of the function (after the docstring) with this:
"""

REPLACE_THIS_3 = """
def send_availability_alert(matched_dates_with_counts):
    \"\"\"
    Sends an email alert when open shifts are found that match the user's availability.
    
 Args:
        matched_dates_with_counts: List of tuples (date_str, count) where open shifts match availability
    \"\"\"
    
    if not matched_dates_with_counts:
        return
"""

WITH_THIS_3 = """
def send_availability_alert(matched_dates_with_counts):
    \"\"\"
    Sends an email alert when open shifts are found that match the user's availability.
    
    Args:
        matched_dates_with_counts: List of tuples (date_str, count) where open shifts match availability
  \"\"\"
 
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
"""

# =============================================================================
# FIX 4: EMAIL_ALERT.PY - Enhanced Email Send Logging
# =============================================================================

"""
In email_alert.py, in the send_availability_alert() function,
find the line that sends the email (near the end):
"""

REPLACE_THIS_4 = """
    # Send the email
    send_email_alert(subject, "\\n".join(body), to_email)
"""

WITH_THIS_4 = """
    # Send the email
    logger.info(f"About to send email alert to {to_email} for shifts: {[d[0] for d in matched_dates_with_counts]}")
    send_email_alert(subject, "\\n".join(body), to_email)
    logger.info(f"SUCCESS: Email alert sent for {len(matched_dates_with_counts)} shifts")
"""

# =============================================================================
# VERIFICATION STEPS
# =============================================================================

"""
After applying all fixes:

1. Search gui.py for "resume_at_5am" - should find it
2. Search gui.py for "[ALERT] Attempting to send" - should find it
3. Search email_alert.py for "Double-check that none of these" - should find it
4. Search email_alert.py for "SENDING availability alert for" - should find it

If all 4 searches succeed, the fixes are correctly applied.

5. Restart the application
6. Monitor shift_operations.log for the new log entries
7. After next midnight reset, verify:
   - Log shows "Scheduling scan resumption at 5:00 AM"
   - No scans occur between midnight and 5am
   - No duplicate alerts for any shifts

Expected log entries after fixes:
- [Reset] Scheduling scan resumption at 5:00 AM (in XXXX seconds)
- [Reset] Resuming scanning at 5:00 AM
- [ALERT] Attempting to send availability alert for X shifts: [...]
- [EMAIL] SENDING availability alert for X shifts: [...]
- [EMAIL] SUCCESS: Email alert sent for X shifts
- BLOCKED: Skipping alert for YYYY-MM-DD - already alerted (alerted=1)
"""
