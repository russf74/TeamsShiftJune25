"""
Teams Shift Monitor Application
Version tracking and changelog
"""

__version__ = "1.1.4"
__version_date__ = "2026-07-08"

# Changelog
CHANGELOG = """
Version 1.1.4 (2026-07-08) - MIDNIGHT RESET FALSE-POSITIVE FIX
===============================================================
🐛 FIX: Spurious shift alerts generated immediately after midnight reset
   - Root cause 1 (race condition): countdown auto_scan() could fire while
     refresh_teams_shifts() was still navigating Teams away, causing a scan
     to run against a partially-loaded or stale calendar view.
   - Root cause 2 (month OCR bypass): when extract_month_year_from_image()
     returned None (Teams loading), the scan silently used the *expected*
     month (e.g. October) even if Teams was still showing August, assigning
     wrong-month day numbers to the database.
   - Root cause 3 (colour fallback): blocks with H≈103 (teal/cyan, NOT
     orange) and S>40 fell through to a default 'A' (available) rule,
     recording transient Teams UI elements as open shifts.
   - Evidence: Oct 4, Oct 17, Oct 26 inserted at 00:04:25 on 2026-07-08;
     Oct 17 matched availability → false email alert sent.

✅ Fixes Applied:
   - gui.py: _midnight_reset_in_progress flag set before any reset action;
     _run_manual_scan aborts immediately when flag is set (closes race).
   - automation.py: month scan now SKIPPED (continue) when month label OCR
     fails, instead of proceeding with expected month value.
   - open_shift_ocr.py: default colour fallback changed from 'A' to 'U';
     only genuinely orange blocks (orange_ratio > 0.30) or OCR-confirmed
     'A' badges are treated as open shifts.

Version 1.1.2 (2025-01-27) - MIDNIGHT RESET TIMING IMPROVEMENTS
================================================================
?? IMPROVEMENTS: Midnight Reset Stability & Reliability
   - Problem: Calendar full-screen mode caused reset to fail
   - Observation: Shifts button sometimes stays in main view instead of ... menu
   - Solution: Increased all timing delays for better stability
   
?? Timing Improvements:
   - Dots menu delay: 2s ? 5s (allows menu to fully open)
   - Shifts view load: 10s ? 15s (allows full transition from calendar)
   - Detection loop: 10 ? 20 attempts (max wait 20 seconds for loading)
   - Total max wait per attempt: ~32s ? ~50s (much more reliable)

?? Rationale:
   - No rush for midnight reset - reliability more important than speed
   - Longer delays ensure Teams UI has time to respond
   - Prevents false failures when UI is slower than expected
   - Files: gui.py refresh_teams_shifts() method

Version 1.1.1 (2025-01-27) - MIDNIGHT RESET DETECTION FIX
==========================================================
?? FIX: Midnight Reset Detection Failing
   - Problem: shiftloaded.png matching at 0.75 but code checking at 0.8
   - Impact: Midnight reset appeared to fail even though Teams refreshed successfully
   - Solution: Lowered detection confidence threshold from 0.8 to 0.7
   - Evidence: Diagnostic tool confirmed image matches at 0.7 reliably
   - File: gui.py line ~580 in refresh_teams_shifts()
 
??? Diagnostic Tools Added:
   - diagnose_shiftloaded.py: Tests detection at multiple confidence levels
   - test_midnight_fix.py: Quick verification of the fix
   - MIDNIGHT_RESET_DETECTION_ISSUE.md: Complete technical analysis
   - MIDNIGHT_RESET_FIX_APPLIED.md: Fix documentation and verification

?? Also Fixed:
   - Line 216: Syntax error self interval_var.get() ? self.interval_var.get()

Version 1.1.0 (2025-01-27) - CRITICAL BUG FIXES
================================================
?? FIX #0: Preserve alerted flag during UPDATE operations
   - Root cause: UPDATE only set count, causing SQLite to reset alerted to 0
   - Impact: Prevented duplicate availability alerts at midnight
   - Evidence: Midnight scan at 00:10 was re-alerting for shift 2026-02-27
   - Solution: Fetch and log alerted flag, preserve by not updating it

?? FIX #1: Atomic flag-setting for alert tracking
   - Changed from loop-based marking to single atomic transaction
   - Eliminates race condition where new scan starts mid-flag-setting
   - Function: mark_multiple_shifts_alerted() replaces individual calls

?? FIX #3: Protect booked shifts from deletion
   - Never delete booked shifts with confirmed_email_sent=1
   - Prevents OCR failures from causing duplicate confirmation emails
   - Comprehensive logging of protected shifts

?? Enhanced Logging:
   - All database operations now logged to shift_operations.log
   - Visibility into UPDATE operations showing alerted flag status
   - PROTECTED messages when shifts saved from deletion

Version 1.0.0 (2025-01-26) - Initial Production Release
========================================================
- Multi-channel alerting (Email, WhatsApp, SMS)
- Automated Teams shift scanning (4-month window)
- OCR-based shift detection (open and booked)
- Midnight Teams app refresh with recording
- Daily summary emails
- Calendar-based availability tracking
- Comprehensive error handling and logging
"""

def get_version():
    """Return current version string"""
    return __version__

def get_version_info():
    """Return detailed version information"""
    return {
        'version': __version__,
        'date': __version_date__,
        'changelog': CHANGELOG
    }

def print_version():
    """Print version banner"""
    print("=" * 60)
    print(f"  Teams Shift Monitor v{__version__}")
    print(f"  Release Date: {__version_date__}")
    print("=" * 60)
