#!/usr/bin/env python3

from datetime import datetime
import os

def test_daily_email_with_whatsapp():
    print("Testing Daily Email System with WhatsApp Check")
    print("=" * 50)
    print(f"Time: {datetime.now()}")
    
    try:
        from email_alert import send_summary_email
        
        # Create some mock stats
        mock_stats = {
            'scan_count': 5,
            'error_count': 0,
            'emails_sent': 2,
            'whatsapp_sent': 1,
            'last_scan_time': '2025-09-05 11:30:00',
            'errors': []
        }
        
        print("Sending test daily summary email...")
        print("(This will include the WhatsApp connectivity check)")
        
        # Send the email
        result = send_summary_email(mock_stats)
        
        if result:
            print("✅ Daily summary email sent successfully!")
            print("   Check your email at russfray74@gmail.com")
            print("   The email should include:")
            print("   - Daily scan statistics")
            print("   - Shift status information")
            print("   - WhatsApp connectivity status")
        else:
            print("❌ Failed to send daily summary email")
            
    except Exception as e:
        print(f"❌ Error testing daily email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_daily_email_with_whatsapp()
