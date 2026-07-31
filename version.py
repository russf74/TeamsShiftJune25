"""
Teams Shift Monitor Application
Version tracking and changelog
"""

__version__ = "1.1.9"
__version_date__ = "2026-07-31"

# Changelog
CHANGELOG = """
Version 1.1.9 (2026-07-31) - Professional docked GUI with full-month calendar
===============================================================================
UI: Redesigned monitor strip under Teams for a clean professional look
   - Fluent-inspired palette, slim single-row toolbar, colour legend chips.
   - Canvas-drawn month grid scales into the remaining work-area height so
     all weeks (including days 27-31) stay fully visible under Teams.
   - Click a day cell to toggle availability (past/booked stay locked).
   - Dock geometry uses the Windows work area so the app never overlaps
     Teams or the taskbar.

Version 1.1.8 (2026-07-31) - Countdown after scan + docked full-width GUI
==========================================================================
🐛 FIX: Next-scan countdown no longer starts when a scan begins
   - Root cause: start_countdown() reset remaining and rescheduled itself
     immediately after launching auto_scan(), so the interval overlapped the
     in-progress scan.
   - Fix: pause the timer while scanning; restart the full interval only from
     _manual_scan_worker after the scan thread finishes.

✨ UI: App window docks full-width directly under the Teams scan window
   - Controls compacted into a top toolbar; calendar fills remaining height.
   - Geometry uses TEAMS_SCAN_HEIGHT_RATIO so the monitor never overlaps Teams
     when both are in their production layout.

Version 1.1.7 (2026-07-31) - Taller Teams scan window for multi-row open shifts
================================================================================
🐛 FIX: Personal row clipped when 2+ open-shift rows appear above it
   - Root cause: TEAMS_SCAN_HEIGHT_RATIO=0.50 (~540px on 1080p) was too short
     once Bank "Open shifts" stacked a second row for same-day multi-shifts.
   - Requirement: fit up to 3 open-shift rows above the personal row, with
     ~1.5 rows of extra margin so the personal row is fully visible for OCR.
   - Fix: raise TEAMS_SCAN_HEIGHT_RATIO from 0.50 to 0.65 (~702px on 1080p).
     Live OCR checks at 0.58–0.68 confirmed Month view, Open shifts, and
     the personal row ("Fray, Laura") remain visible at 0.65.

Version 1.1.6 (2026-07-08) - HOTFIX: Scanning broken by over-aggressive OCR skip
==================================================================================
🐛 FIX: Every month was being skipped with "Could not OCR month/year" warning
   - Root cause: v1.1.4 changed the OCR-failure path to skip the month entirely.
     The month-label OCR (extract_month_year_from_image) frequently returns None
     even during normal scans because the arrow-template threshold (0.85) is
     strict and the static fallback region depends on Teams window position.
     This caused ALL four months to be skipped on every regular scan.
   - The underlying midnight false-positive race is already fully protected by
     the _midnight_reset_in_progress flag added to gui.py (v1.1.4), which
     aborts any scan before it even starts during the reset window.
   - Fix: revert the OCR-failure path to warn-and-continue (using the expected
     month value), matching pre-v1.1.4 behaviour. The hard-skip is removed
     because it is redundant given the gui.py guard and actively breaks scans.

Version 1.1.5 (2026-07-08) - COUNTDOWN SKIP BUTTON
===================================================
✨ NEW: -10s button below the countdown timer
   - Clicking the button subtracts 10 seconds from the current countdown.
   - If fewer than 10 seconds remain the button has no effect, preventing
     an accidental immediate trigger.
   - Useful for quickly advancing to the next scan during testing without
     waiting for the full interval.

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
