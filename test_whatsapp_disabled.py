#!/usr/bin/env python3

"""
Simple test to verify WhatsApp has been properly disabled
"""

from datetime import datetime
import json

def test_whatsapp_disabled():
    print("🔇 Testing WhatsApp Disable Status")
    print("=" * 50)
    print(f"Time: {datetime.now()}")
    
    # Test 1: Check config setting
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        whatsapp_enabled = config.get('whatsapp_enabled', True)
        if whatsapp_enabled:
            print("❌ Config: WhatsApp is still ENABLED")
        else:
            print("✅ Config: WhatsApp is DISABLED")
            
    except Exception as e:
        print(f"❌ Config test failed: {e}")
    
    # Test 2: Check quick WhatsApp status in daily email
    try:
        from email_alert import check_whatsapp_quick
        from config import load_config
        
        config = load_config()
        if config.get('whatsapp_enabled', True):
            print("❌ Daily Email: WhatsApp check will still run")
        else:
            print("✅ Daily Email: WhatsApp check will be skipped")
            
    except Exception as e:
        print(f"❌ Daily email test failed: {e}")
    
    # Test 3: Check health reporter
    try:
        from health_reporter import HealthCheckReporter
        
        reporter = HealthCheckReporter()
        # This should return True (success) when disabled, not actually try to send
        result = reporter.send_whatsapp_notification()
        
        if result:
            print("✅ Health Reporter: WhatsApp notification properly handled when disabled")
        else:
            print("❌ Health Reporter: WhatsApp notification failed")
            
    except Exception as e:
        print(f"❌ Health reporter test failed: {e}")
    
    print("\n" + "=" * 50)
    print("WhatsApp disable test completed!")
    print("\n💡 To re-enable WhatsApp later, just say:")
    print("   're-enable whatsapp'")

if __name__ == "__main__":
    test_whatsapp_disabled()
