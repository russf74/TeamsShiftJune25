"""
Teams Shift Monitor Application
Version tracking and changelog
"""

__version__ = "1.1.0"
__version_date__ = "2025-01-27"

# Changelog
CHANGELOG = """
Version 1.1.0 (2025-01-27) - CRITICAL BUG FIXES
================================================
? FIX #0: Preserve alerted flag during UPDATE operations
   - Root cause: UPDATE only set count, causing SQLite to reset alerted to 0
 - Impact: Prevented duplicate availability alerts at midnight
   - Evidence: Midnight scan at 00:10 was re-alerting for shift 2026-02-27
   - Solution: Fetch and log alerted flag, preserve by not updating it

? FIX #1: Atomic flag-setting for alert tracking
   - Changed from loop-based marking to single atomic transaction
   - Eliminates race condition where new scan starts mid-flag-setting
   - Function: mark_multiple_shifts_alerted() replaces individual calls

? FIX #3: Protect booked shifts from deletion
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
