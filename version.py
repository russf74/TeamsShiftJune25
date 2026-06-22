"""
Teams Shift Monitor Application
Version tracking and changelog
"""

__version__ = "5.0.5"
__version_date__ = "2026-06-21"

# Changelog
CHANGELOG = """
Version 5.0.5 (2026-06-21) - FEATURE: Detection overlays and scan log
=======================================================================
🆕 NEW: Cell type badge inside every coloured calendar cell
   - open cells show "open (N)" with count
   - booked cells show "booked"
   - unavailable cells show "unavail"
🆕 NEW: Live scan log panel in the left sidebar
   - Shows timestamped detection results for each scanned month
   - Lists which day numbers were found as open / booked / unavail
   - Scrollable, keeps last 15 scan entries
   - Updates immediately as each month finishes scanning

Version 5.0.4 (2026-06-21) - FIX: Correct unavailable block detection
=======================================================================
🔧 FIX: U... blocks (June 22-26) were never detected - band was only 80px tall
   - bookedshifts marker at y=410 but U... blocks at y=490 -> band extended to bottom of image
🔧 FIX: Grey mask V ceiling raised 200->220 (U... blocks have V=215, previously excluded)
🔧 FIX: Empty calendar grid cells (V=240, fill=6%) rejected via 20% fill-ratio guard
🔧 FIX: Reverted failed OCR-based U detection (text invisible against grey background)
   - Classification is now purely colour-based: V=100-220 neutral grey = unavailable
   - A... blocks are V=255 (white), empty cells V=240 - both correctly excluded

Version 5.0.3 (2026-06-21) - PATCH: Use OCR text to confirm Unavailable blocks
=================================================================================
🔧 FIX: Grey blocks misclassified as 'unavailable' when they are actually 'A...' (Available)
   - Root cause: colour mask alone cannot distinguish A... from U... (both are grey)
   - Fix: for any grey-coloured contour, OCR the block text; only accept as 'unavailable'
     if the first character is 'U'. All other grey blocks (A..., Ea..., etc.) are skipped.
   - Removed wrong 2026-06-13 unavailable record from database

Version 5.0.2 (2026-06-21) - FEATURE: Bump -10 countdown button
=================================================================
🆕 NEW: "Bump -10" button below the countdown timer
   - Clicking the button subtracts 10 seconds from the remaining scan countdown
   - Only applies if the result would be >= 10 seconds (no-op otherwise)
   - Allows fast-forwarding to the next scan without waiting

Version 5.0.1 (2026-06-21) - PATCH: Fix unavailable detection false positives
=================================================================================
🔧 FIX: Blue-grey booked shifts (A...) were misclassified as unavailable
   - Root cause: Grey HSV saturation ceiling was 80 — too broad
   - Fix: Tightened to S ≤ 30, V 100–200 (neutral grey only)
   - Booked shift blocks have Teams blue-grey tint (S ≈30–50) — now excluded
   - Only truly neutral U... blocks (S ≈0–15) classified as unavailable

Version 5.0.0 (2026-06-21) - UNAVAILABLE SHIFT DETECTION
=========================================================
🆕 NEW: Detect and display Teams 'Unavailable' blocks
   - Grey blocks (U...) in the shifts calendar are now correctly identified
   - Previously misclassified as booked; now stored as 'unavailable' type
   - Calendar cells display with grey (#C0C0C0) background
   - No false alerts triggered for unavailable days
   - booked_shift_ocr.py: per-contour HSV classification (coloured=booked, grey=unavailable)

🆕 NEW: Version label visible in app UI
   - Version shown in top-right of control bar and in window title

🔧 FIX: ocr_processing.py indentation corruption repaired
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
