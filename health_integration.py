#!/usr/bin/env python3
"""
Health Check Integration - SAFE Integration Point
This module safely integrates the health check system with the main application.
Designed with maximum safety - if anything goes wrong, main app continues normally.
"""

import datetime
import traceback

def safely_start_weekly_health_checks():
    """
    Safely start the weekly health check system.
    If anything goes wrong, main application continues normally.
    This function can be called from main app without any risk.
    """
    try:
        print("[HEALTH INTEGRATION] Attempting to start weekly health check system...")
        
        # Import the scheduler safely
        from weekly_scheduler import start_weekly_health_scheduler, get_weekly_scheduler_status
        
        # Start the scheduler
        success = start_weekly_health_scheduler()
        
        if success:
            status = get_weekly_scheduler_status()
            next_check = status.get('next_scheduled_check', 'Unknown')
            print(f"[HEALTH INTEGRATION] ✅ Weekly health checks started successfully")
            print(f"[HEALTH INTEGRATION] Next check scheduled: {next_check}")
            return True
        else:
            print("[HEALTH INTEGRATION] ❌ Failed to start weekly health checks")
            return False
            
    except ImportError as e:
        print(f"[HEALTH INTEGRATION] Health check modules not available: {e}")
        return False
    except Exception as e:
        print(f"[HEALTH INTEGRATION] Error starting health checks (main app unaffected): {e}")
        # Deliberately not printing full traceback to avoid cluttering main app logs
        return False

def safely_check_health_system_status():
    """
    Safely check if health check system is running.
    Returns status info or None if system not available.
    """
    try:
        from weekly_scheduler import get_weekly_scheduler_status
        return get_weekly_scheduler_status()
    except Exception:
        return None

def safely_run_immediate_health_check():
    """
    Safely run an immediate health check for testing.
    Returns results or None if failed.
    """
    try:
        from health_check import run_weekly_health_check
        from health_reporter import send_weekly_health_report
        
        print("[HEALTH INTEGRATION] Running immediate health check...")
        results = run_weekly_health_check()
        
        if results:
            print(f"[HEALTH INTEGRATION] Health check completed: {results.get('overall_status', 'UNKNOWN')}")
            
            # Optionally send report
            report_result = send_weekly_health_report(results)
            
            return {
                'health_results': results,
                'report_sent': report_result
            }
        else:
            print("[HEALTH INTEGRATION] Health check failed to return results")
            return None
            
    except Exception as e:
        print(f"[HEALTH INTEGRATION] Error running immediate health check: {e}")
        return None

# Integration instructions for main application
INTEGRATION_INSTRUCTIONS = """
SAFE INTEGRATION WITH MAIN APPLICATION:

1. Add to main.py or gui.py __init__ method:

    # Safely start weekly health checks (completely optional)
    try:
        from health_integration import safely_start_weekly_health_checks
        safely_start_weekly_health_checks()
    except:
        pass  # Health checks are optional - main app continues normally

2. Optional: Add status check to existing GUI:

    # Check health system status (optional)
    try:
        from health_integration import safely_check_health_system_status
        health_status = safely_check_health_system_status()
        if health_status and health_status.get('is_running'):
            print("Weekly health checks: ACTIVE")
    except:
        pass

3. Optional: Add manual health check button to GUI:

    def manual_health_check(self):
        try:
            from health_integration import safely_run_immediate_health_check
            result = safely_run_immediate_health_check()
            if result:
                self.scan_status_var.set("Health check completed - email sent")
        except:
            self.scan_status_var.set("Health check not available")

SAFETY GUARANTEES:
- All health check code runs in separate threads
- Uses temporary directories to avoid file conflicts
- Read-only access to main app database
- Multiple layers of error handling
- Main app continues normally even if health checks fail completely
- Can be disabled/removed without affecting main functionality
"""

if __name__ == "__main__":
    print("Health Check Integration Module")
    print("=" * 50)
    print(INTEGRATION_INSTRUCTIONS)
    print("\nTesting integration...")
    
    # Test the integration
    success = safely_start_weekly_health_checks()
    print(f"Health check startup: {'SUCCESS' if success else 'FAILED'}")
    
    status = safely_check_health_system_status()
    if status:
        print(f"Health system status: {status}")
    
    # Test immediate health check (comment out for normal operation)
    # result = safely_run_immediate_health_check()
    # print(f"Immediate health check: {'SUCCESS' if result else 'FAILED'}")
