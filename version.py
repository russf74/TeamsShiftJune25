"""
Teams Shift Monitor Application
Version tracking and changelog
"""

__version__ = "1.2.12"
__version_date__ = "2026-10-13"

# Changelog
CHANGELOG = """
Version 1.2.12 (2026-10-13) - Tolerate OCR errors in month label
===============================================================================
FIX: Month label OCR often returned 'Yctober' / 'Jecember', so the month could
    not be verified and the 12 Oct scan stored October's shifts as December
    (plus false bookings and confirmation emails). The parser now accepts a
    single unambiguous near-match month name and still rejects anything else.
DATA: December 2026 and January 2027 corrected against live Teams capture.

Version 1.2.11 (2026-10-12) - Verify calendar month before scanning
===============================================================================
FIX: Month-label OCR now recognizes full and abbreviated month names even
    when weekday/date text precedes them. Scans are skipped when the screenshot
    month cannot be verified, preventing dates from being assigned to the
    requested month based only on fallback assumptions.

Version 1.2.10 (2026-08-22) - Keep current month; restore hidden Teams
===============================================================================
FIX: The monitor board jumped to September because each scan month
   overwrote the visible starting card. The board now always starts on
   the current month (Today) after scans. The month being scanned gets
   a temporary glow border, then the glow is removed when the scan ends.
FIX: Midnight refresh failed when Teams was minimized or closed because
   window lookup ignored hidden windows and never relaunched the app.
   Refresh now restores a minimized Teams window or launches Teams.

Version 1.2.9 (2026-08-19) - Tile Teams and monitor with no gap
===============================================================================
FIX: Calendar vanished and a wallpaper gap sat between Teams and the
   monitor. Docking chased Teams' current height and then force-refreshed
   an unmapped board into a blank strip. Both windows now share the
   work area full-width: Teams on top, monitor flush underneath, and
   the calendar redraws in place instead of destroying itself.

Version 1.2.8 (2026-08-19) - Stop overlapping month titles / off-screen dock
===============================================================================
FIX: Narrow month cards drew "September 2026" over "1 booked · 5 open".
   Counts now wrap under the title when both will not fit.
FIX: Monitor opened halfway off the bottom because Teams was sized to 65%
   of the full screen (including taskbar) and the dock forced 280px even
   when that overflowed. Teams now uses 58% of the work area and the
   monitor is clamped inside the remaining strip.

Version 1.2.7 (2026-08-19) - Catch up a missed midnight reset
===============================================================================
FIX: If the monitor is down at 00:00 (Teams update dialog, crash, or
   closed app) the midnight refresh email never sent and startup did a
   quiet refresh with no email. Startup now catches up once before 5 AM
   when today's midnight email is missing. Midnight emails are tracked
   separately from the daily summary, and app_runtime.log records crashes.

Version 1.2.6 (2026-08-19) - Dismiss Teams update OK dialogs
===============================================================================
FIX: A Teams update screen with a centered OK button can block month-view
   refresh. The monitor then stalls or exits, so the midnight reset email
   never sends. Popup dismissal now clicks OK/Got it/Continue on update
   cards as well as the older rating-survey close controls.

Version 1.2.5 (2026-08-11) - Detect late-month booked/open tiles (26 Sep)
===============================================================================
FIX: 26 Sep stayed as Available after a real booking because late-month
   tiles sit on the right screenshot edge and were discarded
   (x + w >= image width). Assignment OCR could also lose to extra A
   preprocessing votes. Compact right-edge tiles are kept, day mapping
   clamps one column past month-end, and any L/E/P reading wins.
   2026-09-26 is backfilled as a verified booking (no extra email).

Version 1.2.4 (2026-08-11) - Block midnight false open-shift alerts
===============================================================================
FIX: After midnight reset the scanner could alert on phantom open shifts
   (e.g. Sat 7 Nov / Fri 13 Nov) that do not exist in Teams.
   Root cause: an in-flight four-month scan could continue while midnight
   refresh rewrote the Teams view, and a single bad open-tile observation
   was enough to insert+alert immediately.
   - Open shifts now require two consecutive healthy observations (same
     candidate model as booked) before they can enter the DB or alert.
   - Midnight reset invalidates any running scan, waits for the scan thread
     to exit before touching Teams, discards mid-scan OCR/reconcile/alerts,
     and keeps the midnight guard active until 5:00 AM resume.
   - Automation scan loop accepts should_abort and stops mid-loop on reset.

Version 1.2.3 (2026-08-08) - Dismiss Shifts rating/NPS popups
===============================================================================
FIX: Teams Shifts can show blocking cards such as "Enjoying Shifts? Tap the
   stars to share your rating" with an X close control. These overlays cover
   calendar chrome and can break refresh/OCR. Added dismiss_shifts_popups()
   which OCR-detects rating/feedback nags and clicks the nearby X (or a
   top-right geometric close), then wired it into navigate, month-view lock,
   midnight refresh, content wait loops, and four-month scans.

Version 1.2.2 (2026-08-08) - Reliable midnight Month-view refresh
===============================================================================
FIX: Midnight Teams refresh could navigate/reload but still hard-fail with
   "Could not refresh Microsoft Teams Shifts monthly view" because success
   depended on brittle window-title startswith("shifts") checks and a single
   OCR pass requiring exact phrases ("month" + "people scheduled"/"open shifts")
   plus fixed 1920px click coordinates.
   Refresh now retries leave/re-enter + Ctrl+R, waits for multi-signal content
   load (OCR + today/openshifts/shiftloaded templates), selects Month via OCR
   with resolution-scaled fallbacks, soft-confirms month calendar chrome, and
   writes screenshots/refresh_*.png on incomplete attempts. GUI failure mail
   points at those diagnostics. Unit coverage in test_month_view_refresh.py.

Version 1.2.1 (2026-08-01) - Personal-row L/E/P assignment OCR
===============================================================================
FIX: Personal-row booked detection missed pastel L/E/P assignment tiles because
   OCR preprocessing was too weak and any stray A reading forced availability.
   Added CLAHE/hard-threshold variants and vote scoring so readable assignment
   codes (L, E, P, PL) are recognized while grey A tiles stay availability-only.
   Validated against August 2026 Teams capture (booked 4/8/15; open 12/17-21).

Version 1.2.0 (2026-07-31) - Multi-month board + professional toolbar
===============================================================================
UI: Compact 2–3 month calendar with true square day cells and centered cards
   (no ultra-wide day slabs). Strong Booked/Open colour fills, coloured toolbar
   buttons instead of plain white ttk controls, and a slim docked strip under Teams.

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
