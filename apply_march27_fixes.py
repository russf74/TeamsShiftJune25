#!/usr/bin/env python3
"""
Apply March 27 duplicate alert fixes automatically
"""

import re
import sys

def apply_gui_fixes():
 """Apply all fixes to gui.py"""
    
    with open('gui.py', 'r', encoding='utf-8') as f:
        content = f.read()
  
    # FIX 1: Replace the midnight reset success section with 5am delay version
    old_pattern = r'''# Success!
  self\.scan_status_var\.set\("Teams Shifts app refreshed successfully\. Resuming scanning\."\)
   
 # Send success confirmation email
    try:
     send_email_alert\(
           "Teams Shifts app reset successful",
    "Teams Shifts app was successfully refreshed at midnight\. All systems are running normally\.",
    "russfray74@gmail\.com"
            \)
           print\(f"\[Reset\] Success confirmation email sent"\)
         except Exception as e:
          print\(f"\[Reset\] Failed to send success email: \{e\}"\)
           
      self\.timer_running = True
      self\.scanning_on = True
             self\._scanning = False
    self\.start_countdown\(\)
                return'''
    
    new_text = '''# Success!
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
          return'''
    
    content = re.sub(old_pattern, new_text, content, flags=re.MULTILINE)
    
    # FIX 2: Add enhanced logging around send_availability_alert
    old_pattern2 = r'''if matched_dates:
           summary = f"New matched shifts found: \{len\(matched_dates\)\}\\n" \+ ", "\.join\(matched_dates\)
   self\.scan_status_var\.set\(summary\)
      send_availability_alert\(matched_dates\)
          else:'''
    
    new_text2 = '''if matched_dates:
         summary = f"New matched shifts found: {len(matched_dates)}\\n" + ", ".join(matched_dates)
           self.scan_status_var.set(summary)
    # CRITICAL: Log this alert attempt for debugging
             print(f"[ALERT] Attempting to send availability alert for {len(matched_dates)} shifts: {matched_dates}")
      send_availability_alert(matched_dates)
      print(f"[ALERT] Availability alert sent successfully for {matched_dates}")
       else:'''
    
    content = re.sub(old_pattern2, new_text2, content, flags=re.MULTILINE)
    
    with open('gui.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("? Applied fixes to gui.py")

def apply_email_fixes():
    """Apply all fixes to email_alert.py"""
    
    with open('email_alert.py', 'r', encoding='utf-8') as f:
 content = f.read()
    
    # FIX 3 & 4: Replace entire send_availability_alert function
    old_pattern = r'''def send_availability_alert\(matched_dates_with_counts\):
    """
    Sends an email alert when open shifts are found that match the user's availability\.
    
 Args:
        matched_dates_with_counts: List of tuples \(date_str, count\) where open shifts match availability
    """
    
    if not matched_dates_with_counts:
  return
  
    config = load_config\(\)'''
    
    new_text = '''def send_availability_alert(matched_dates_with_counts):
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
  
    config = load_config()'''
    
    content = re.sub(old_pattern, new_text, content, flags=re.MULTILINE | re.DOTALL)
    
    # Add logging before email send
    old_send = r'''    # Send the email
    send_email_alert\(subject, "\\n"\.join\(body\), to_email\)'''
    
  new_send = '''    # Send the email
    logger.info(f"About to send email alert to {to_email} for shifts: {[d[0] for d in matched_dates_with_counts]}")
    send_email_alert(subject, "\\n".join(body), to_email)
    logger.info(f"SUCCESS: Email alert sent for {len(matched_dates_with_counts)} shifts")'''
    
    content = re.sub(old_send, new_send, content)
    
    with open('email_alert.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("? Applied fixes to email_alert.py")

if __name__ == "__main__":
    print("=" * 60)
    print("APPLYING MARCH 27 DUPLICATE ALERT FIXES")
    print("=" * 60)
    print()
    
    try:
    apply_gui_fixes()
   apply_email_fixes()
     
        print()
        print("=" * 60)
  print("? ALL FIXES APPLIED SUCCESSFULLY")
      print("=" * 60)
     print()
   print("Next steps:")
     print("1. Restart the application")
        print("2. Monitor shift_operations.log for new log entries")
      print("3. Verify no duplicate alerts occur")
        
    except Exception as e:
        print(f"\n? ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
