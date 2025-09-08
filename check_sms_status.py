#!/usr/bin/env python3

from sms_alert import SMSAlert

def show_sms_status():
    print("📱 SMS Alert System Status")
    print("=" * 30)
    
    sms = SMSAlert()
    config = sms.sms_config
    
    print(f"SMS Enabled: {'✅ YES' if config.get('enabled') else '❌ NO'}")
    print(f"Method: {config.get('method', 'Not configured')}")
    print(f"Phone Number: {config.get('phone_number', 'Not set')}")
    
    if config.get('method') == 'email':
        print(f"Carrier: {config.get('carrier', 'Not set')}")
        print("\n💡 This is FREE - uses email-to-SMS gateways")
    elif config.get('method') == 'twilio':
        print(f"Twilio configured: {'✅ YES' if config.get('twilio', {}).get('account_sid') else '❌ NO'}")
        print("\n💳 This costs ~$0.01 per message")
    else:
        print("\n🔧 SMS not configured yet")
        print("\n📋 Available options:")
        print("1. Email-to-SMS (FREE!) - Perfect for personal use")
        print("2. Twilio API (~$0.01/msg) - Professional grade")
        
    print(f"\nConfig file: sms_config.json")

if __name__ == "__main__":
    show_sms_status()
