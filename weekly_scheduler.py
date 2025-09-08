#!/usr/bin/env python3
"""
Weekly Health Check Scheduler - Completely Isolated
Schedules and runs weekly health checks every Friday at 7:30pm.
Designed to be completely safe and never interfere with main application.
"""

import datetime
import threading
import time
import json
import traceback
from pathlib import Path

class WeeklyHealthScheduler:
    """
    Completely isolated weekly health check scheduler.
    Runs in background thread and never interferes with main app.
    """
    
    def __init__(self):
        self.app_dir = Path(__file__).parent.absolute()
        self.scheduler_thread = None
        self.is_running = False
        self.last_health_check = None
        
        # Load last health check time if available
        self.load_last_check_time()
    
    def load_last_check_time(self):
        """Load the last health check timestamp"""
        try:
            status_file = self.app_dir / 'health_check_status.json'
            if status_file.exists():
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    last_check_str = data.get('last_health_check')
                    if last_check_str:
                        self.last_health_check = datetime.datetime.fromisoformat(last_check_str)
        except Exception as e:
            print(f"[HEALTH SCHEDULER] Could not load last check time: {e}")
            self.last_health_check = None
    
    def save_last_check_time(self, check_time):
        """Save the last health check timestamp"""
        try:
            status_file = self.app_dir / 'health_check_status.json'
            data = {
                'last_health_check': check_time.isoformat(),
                'next_scheduled_check': self.get_next_friday_730pm().isoformat()
            }
            with open(status_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[HEALTH SCHEDULER] Could not save last check time: {e}")
    
    def get_next_friday_730pm(self, from_date=None):
        """Calculate next Friday 7:30pm from given date (or now)"""
        if from_date is None:
            from_date = datetime.datetime.now()
        
        # Find next Friday
        days_ahead = 4 - from_date.weekday()  # Friday is weekday 4
        if days_ahead <= 0:  # Friday is today or has passed
            days_ahead += 7
        
        next_friday = from_date + datetime.timedelta(days=days_ahead)
        
        # Set time to 7:30pm
        next_friday = next_friday.replace(hour=19, minute=30, second=0, microsecond=0)
        
        return next_friday
    
    def should_run_health_check(self):
        """Check if it's time to run weekly health check"""
        now = datetime.datetime.now()
        
        # Check if it's Friday and between 7:30pm and 8:00pm
        if now.weekday() == 4 and 19 <= now.hour < 20 and now.minute >= 30:
            # Make sure we haven't already run today
            if self.last_health_check is None:
                return True
            
            # Check if last health check was more than 6 days ago
            time_since_last = now - self.last_health_check
            if time_since_last.days >= 6:
                return True
        
        return False
    
    def run_safe_health_check(self):
        """
        Run health check completely safely.
        This function has multiple layers of error handling.
        """
        check_start_time = datetime.datetime.now()
        
        try:
            print(f"[HEALTH SCHEDULER] Starting weekly health check at {check_start_time}")
            
            # Import health check modules safely
            try:
                from health_check import run_weekly_health_check
                from health_reporter import send_weekly_health_report
            except ImportError as e:
                print(f"[HEALTH SCHEDULER] Could not import health check modules: {e}")
                return
            
            # Run health check
            health_results = run_weekly_health_check()
            
            if health_results:
                print(f"[HEALTH SCHEDULER] Health check completed: {health_results.get('overall_status', 'UNKNOWN')}")
                
                # Send report
                report_result = send_weekly_health_report(health_results)
                
                if report_result.get('email_sent'):
                    print("[HEALTH SCHEDULER] Weekly health report email sent successfully")
                else:
                    print("[HEALTH SCHEDULER] Failed to send health report email")
                
                if report_result.get('whatsapp_sent'):
                    print("[HEALTH SCHEDULER] WhatsApp notification sent successfully")
                else:
                    print("[HEALTH SCHEDULER] Failed to send WhatsApp notification")
                
                # Save success timestamp
                self.last_health_check = check_start_time
                self.save_last_check_time(check_start_time)
                
            else:
                print("[HEALTH SCHEDULER] Health check returned no results")
        
        except Exception as e:
            print(f"[HEALTH SCHEDULER] Critical error during health check: {e}")
            traceback.print_exc()
            
            # Try to send emergency notification
            try:
                emergency_results = {
                    'overall_status': 'CRITICAL',
                    'timestamp': check_start_time.isoformat(),
                    'tests_completed': 0,
                    'tests_failed': 1,
                    'errors': [f'Health check system failure: {str(e)}'],
                    'warnings': [],
                    'total_execution_time': 0
                }
                
                from health_reporter import send_weekly_health_report
                send_weekly_health_report(emergency_results)
                print("[HEALTH SCHEDULER] Emergency health report sent")
                
            except Exception as emergency_error:
                print(f"[HEALTH SCHEDULER] Could not send emergency report: {emergency_error}")
    
    def scheduler_loop(self):
        """Main scheduler loop - runs in background thread"""
        print("[HEALTH SCHEDULER] Weekly health check scheduler started")
        print(f"[HEALTH SCHEDULER] Next check scheduled for: {self.get_next_friday_730pm()}")
        
        while self.is_running:
            try:
                # Check every minute if it's time for health check
                if self.should_run_health_check():
                    print("[HEALTH SCHEDULER] Time for weekly health check!")
                    self.run_safe_health_check()
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                print(f"[HEALTH SCHEDULER] Error in scheduler loop: {e}")
                time.sleep(60)  # Continue running even if there's an error
    
    def start_scheduler(self):
        """Start the weekly health check scheduler"""
        if self.is_running:
            print("[HEALTH SCHEDULER] Scheduler already running")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(
            target=self.scheduler_loop,
            daemon=True,  # Dies when main program exits
            name="WeeklyHealthScheduler"
        )
        self.scheduler_thread.start()
        
        print("[HEALTH SCHEDULER] Weekly health check scheduler started successfully")
        print(f"[HEALTH SCHEDULER] Next check: {self.get_next_friday_730pm()}")
    
    def stop_scheduler(self):
        """Stop the weekly health check scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        print("[HEALTH SCHEDULER] Weekly health check scheduler stopped")
    
    def get_status(self):
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'next_scheduled_check': self.get_next_friday_730pm().isoformat(),
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }

# Global scheduler instance
_weekly_scheduler = None

def start_weekly_health_scheduler():
    """
    Start the weekly health check scheduler.
    Completely safe to call - will not interfere with main application.
    """
    global _weekly_scheduler
    
    try:
        if _weekly_scheduler is None:
            _weekly_scheduler = WeeklyHealthScheduler()
        
        if not _weekly_scheduler.is_running:
            _weekly_scheduler.start_scheduler()
            return True
        else:
            print("[HEALTH SCHEDULER] Weekly scheduler already running")
            return True
            
    except Exception as e:
        print(f"[HEALTH SCHEDULER] Failed to start weekly scheduler: {e}")
        return False

def stop_weekly_health_scheduler():
    """Stop the weekly health check scheduler"""
    global _weekly_scheduler
    
    if _weekly_scheduler:
        _weekly_scheduler.stop_scheduler()

def get_weekly_scheduler_status():
    """Get status of weekly health check scheduler"""
    global _weekly_scheduler
    
    if _weekly_scheduler:
        return _weekly_scheduler.get_status()
    else:
        return {'is_running': False, 'scheduler_exists': False}

if __name__ == "__main__":
    # Test the scheduler
    print("Testing Weekly Health Check Scheduler...")
    
    scheduler = WeeklyHealthScheduler()
    print(f"Next Friday 7:30pm: {scheduler.get_next_friday_730pm()}")
    print(f"Should run now: {scheduler.should_run_health_check()}")
    
    # Start scheduler for testing
    scheduler.start_scheduler()
    
    try:
        # Run for 30 seconds for testing
        time.sleep(30)
    finally:
        scheduler.stop_scheduler()
