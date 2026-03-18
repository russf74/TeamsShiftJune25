#!/usr/bin/env python3
"""
Comprehensive fix for March 27 (and all future) duplicate alert issues.

This script implements three critical fixes:
1. Enhanced email alert logging to track every alert sent
2. Delay first scan after midnight reset until 5am to avoid nighttime scanning
3. Double-check alerted flag before sending any availability alert

Apply this fix to:
- gui.py (midnight reset delay + logging)
- email_alert.py (enhanced logging + double-check)
- database.py (verification that alerted flag is properly checked)
"""

import os
import sys
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a timestamped backup of a file before modifying it"""
    if not os.path.exists(filepath):
        print(f"WARNING: File {filepath} does not exist, skipping backup")
     return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"? Backed up {filepath} to {backup_path}")
    return backup_path

def apply_gui_fixes():
    """Apply fixes to gui.py for midnight reset delay and enhanced logging"""
    
    gui_file = "gui.py"
    
    if not os.path.exists(gui_file):
    print(f"ERROR: {gui_file} not found!")
        return False
    
    # Backup first
    backup_file(gui_file)
    
    with open(gui_file, 'r', encoding='utf-8') as f:
     content = f.read()
    
    # Fix 1: Add delay until 5am after midnight reset
    # Find the refresh_teams_shifts function and modify the success section
  
    old_success_code = """  # Success!
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
                return"""
    
    new_success_code = """      # Success!
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
           return"""
    
if old_success_code in content:
        content = content.replace(old_success_code, new_success_code)
        print("? Applied midnight reset 5am delay fix to gui.py")
    else:
        print("WARNING: Could not find exact midnight reset success code - may need manual fix")

    # Fix 2: Add enhanced logging to send_availability_alert calls in gui.py
    old_alert_call = """    send_availability_alert(matched_dates)"""
    
    new_alert_call = """                # CRITICAL: Log this alert attempt for debugging
          print(f"[ALERT] Attempting to send availability alert for {len(matched_dates)} shifts: {matched_dates}")
     send_availability_alert(matched_dates)
     print(f"[ALERT] Availability alert sent successfully for {matched_dates}")"""
    
  if old_alert_call in content:
        content = content.replace(old_alert_call, new_alert_call)
        print("? Applied enhanced alert logging to gui.py")
    else:
        print("WARNING: Could not find send_availability_alert call - may need manual fix")
    
    # Write the modified content
    with open(gui_file, 'w', encoding='utf-8') as f:
    f.write(content)
    
    print(f"? Successfully updated {gui_file}")
    return True

def apply_email_alert_fixes():
    """Apply fixes to email_alert.py for enhanced logging and double-checking"""
    
  email_file = "email_alert.py"
    
    if not os.path.exists(email_file):
   print(f"ERROR: {email_file} not found!")
        return False
    
    # Backup first
    backup_file(email_file)
    
    with open(email_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 3: Add double-check of alerted flag at the START of send_availability_alert
    # Find the function and add safety check right after the docstring
    
    old_function_start = '''def send_availability_alert(matched_dates_with_counts):
    """
    Sends an email alert when open shifts are found that match the user's availability.
    
    Args:
        matched_dates_with_counts: List of tuples (date_str, count) where open shifts match availability
    """
    
    if not matched_dates_with_counts:
        return'''
    
    new_function_start = '''def send_availability_alert(matched_dates_with_counts):
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
    return'''
 
    if old_function_start in content:
      content = content.replace(old_function_start, new_function_start)
        print("? Applied double-check alerted flag fix to email_alert.py")
    else:
        print("WARNING: Could not find exact function start - may need manual fix")
  
    # Add logging at the end of the function after email is sent
    old_email_send = """    # Send the email
    send_email_alert(subject, "\\n".join(body), to_email)"""
    
    new_email_send = """ # Send the email
    logger.info(f"About to send email alert to {to_email} for shifts: {[d[0] for d in matched_dates_with_counts]}")
    send_email_alert(subject, "\\n".join(body), to_email)
    logger.info(f"SUCCESS: Email alert sent for {len(matched_dates_with_counts)} shifts")"""
    
    if old_email_send in content:
      content = content.replace(old_email_send, new_email_send)
   print("? Applied email send logging to email_alert.py")
  else:
     print("WARNING: Could not find email send code - may need manual fix")
    
    # Write the modified content
    with open(email_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
  print(f"? Successfully updated {email_file}")
    return True

def verify_fixes():
    """Verify that all fixes were applied correctly"""
    
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    checks = []
    
    # Check gui.py for 5am delay
    if os.path.exists("gui.py"):
        with open("gui.py", 'r', encoding='utf-8') as f:
     content = f.read()
    
      if "resume_at_5am" in content and "next_5am" in content:
    print("? gui.py contains midnight reset 5am delay code")
   checks.append(True)
      else:
        print("? gui.py missing 5am delay code")
  checks.append(False)
        
if "[ALERT] Attempting to send availability alert" in content:
            print("? gui.py contains enhanced alert logging")
     checks.append(True)
   else:
            print("? gui.py missing enhanced alert logging")
checks.append(False)
    else:
        print("? gui.py not found")
        checks.append(False)
    
    # Check email_alert.py for double-check
    if os.path.exists("email_alert.py"):
 with open("email_alert.py", 'r', encoding='utf-8') as f:
     content = f.read()
        
        if "Double-check that none of these shifts have already been alerted" in content:
            print("? email_alert.py contains double-check alerted flag code")
            checks.append(True)
  else:
            print("? email_alert.py missing double-check code")
            checks.append(False)
        
        if "SENDING availability alert for" in content:
 print("? email_alert.py contains enhanced logging")
            checks.append(True)
  else:
            print("? email_alert.py missing enhanced logging")
            checks.append(False)
    else:
     print("? email_alert.py not found")
        checks.append(False)
    
    print("\n" + "=" * 80)
    if all(checks):
        print("? ALL FIXES VERIFIED SUCCESSFULLY")
     return True
    else:
        print("? SOME FIXES FAILED - Review warnings above")
        return False

def main():
  """Main execution function"""
    
    print("=" * 80)
    print("COMPREHENSIVE FIX FOR MARCH 27 DUPLICATE ALERTS")
    print("=" * 80)
  print()
    print("This script will apply three critical fixes:")
    print("1. Enhanced email alert logging to track every alert sent")
    print("2. Delay first scan after midnight reset until 5am")
    print("3. Double-check alerted flag before sending any availability alert")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("gui.py") or not os.path.exists("email_alert.py"):
        print("ERROR: This script must be run from the TeamsShiftJune25 directory!")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    input("Press ENTER to continue with the fixes, or Ctrl+C to cancel...")
    print()
    
    # Apply fixes
    success = True
    
    print("\n" + "=" * 80)
    print("APPLYING FIXES TO GUI.PY")
print("=" * 80)
    if not apply_gui_fixes():
        success = False
    
    print("\n" + "=" * 80)
    print("APPLYING FIXES TO EMAIL_ALERT.PY")
    print("=" * 80)
    if not apply_email_alert_fixes():
    success = False
    
    # Verify all fixes
    print()
    if not verify_fixes():
        success = False
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if success:
        print("? All fixes applied successfully!")
        print()
        print("Changes made:")
        print("  1. gui.py - Midnight reset now delays scanning until 5:00 AM")
        print("  2. gui.py - Enhanced logging for all alert attempts")
        print("  3. email_alert.py - Double-checks alerted flag before sending emails")
      print("  4. email_alert.py - Logs every email send attempt and success")
print()
        print("Next steps:")
        print("  1. Restart the application to load the new code")
        print("  2. Monitor shift_operations.log for detailed alert tracking")
        print("  3. After next midnight reset, verify no scans occur until 5am")
print("  4. Verify no duplicate alerts for March 27 or any other date")
        print()
      print("If issues persist, check the log file for:")
     print("  - '[ALERT] Attempting to send availability alert'")
        print("  - '[EMAIL] SENDING availability alert for'")
        print("  - 'BLOCKED: Skipping alert for ... - already alerted'")
    else:
        print("? Some fixes failed to apply properly")
        print("Please review the warnings above and apply manual fixes if needed")
     print()
  print("Backup files have been created with .backup_TIMESTAMP extension")
        print("You can restore from backups if needed")
    
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
  print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
    sys.exit(1)
