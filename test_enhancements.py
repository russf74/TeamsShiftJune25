#!/usr/bin/env python3

from datetime import datetime
import os

def test_enhancements():
    print("Testing Health Check System Enhancements")
    print("=" * 50)
    print(f"Time: {datetime.now()}")
    
    # Test 1: Verify the health_check.py has the WhatsApp method
    try:
        from health_check import SafeHealthChecker
        checker = SafeHealthChecker()
        
        # Check if the method exists
        if hasattr(checker, 'check_whatsapp_connectivity'):
            print("✅ WhatsApp connectivity method found in health_check.py")
        else:
            print("❌ WhatsApp connectivity method missing from health_check.py")
            
    except Exception as e:
        print(f"❌ Error importing health_check: {e}")
    
    # Test 2: Verify the health_reporter has critical issue analysis
    try:
        from health_reporter import HealthCheckReporter
        reporter = HealthCheckReporter()
        
        # Check if the method exists
        if hasattr(reporter, 'analyze_critical_issues'):
            print("✅ Critical issue analysis method found in health_reporter.py")
        else:
            print("❌ Critical issue analysis method missing from health_reporter.py")
            
    except Exception as e:
        print(f"❌ Error importing health_reporter: {e}")
    
    # Test 3: Verify email_alert has quick WhatsApp check
    try:
        from email_alert import check_whatsapp_quick
        print("✅ Quick WhatsApp check function found in email_alert.py")
        
        # Try to run a quick test
        result = check_whatsapp_quick()
        print(f"   Quick check result: {result['status']} - {result['message']}")
        
    except Exception as e:
        print(f"❌ Error with email_alert WhatsApp check: {e}")
    
    # Test 4: Check if weekly scheduler is available
    try:
        from weekly_scheduler import WeeklyHealthScheduler
        print("✅ Weekly health scheduler found")
    except Exception as e:
        print(f"❌ Error importing weekly_scheduler: {e}")
    
    print("\n" + "=" * 50)
    print("Enhancement verification completed!")

if __name__ == "__main__":
    test_enhancements()
