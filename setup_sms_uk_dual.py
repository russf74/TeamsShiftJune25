#!/usr/bin/env python3

"""
UK SMS Setup for Multiple Recipients - Teams Shift Alerts

Configure SMS alerts for you and your wife with Twilio.
Just like your email system sends to multiple addresses!
"""

import json
import os
from sms_alert import SMSAlert

def main():
    print("🇬🇧 UK SMS Setup for Multiple Recipients")
    print("=" * 42)
    print()
    
    print("📱 This will configure SMS alerts for you AND your wife")
    print("   Just like how your email system already sends to multiple emails!")
    print()
    
    print("💰 Twilio Pricing:")
    print("   • FREE TRIAL: £15 credit (covers ~1,875 SMS)")
    print("   • Cost: ~£0.008 per SMS (~1 penny)")
    print("   • Send to 2 people = 2p per shift alert")
    print("   • UK phone number: ~£1/month")
    print()
    
    choice = input("Setup dual SMS alerts for you and your wife? (y/n): ").strip().lower()
    
    if choice == 'y':
        setup_dual_sms()
    else:
        print("\nℹ️  No problem! You can set this up later by running:")
        print("   python setup_sms_uk_dual.py")

def setup_dual_sms():
    """Setup SMS for two UK phone numbers"""
    print("\n🚀 Setting up Dual UK SMS Alerts")
    print("-" * 32)
    print()
    
    # Get phone numbers
    print("📱 Enter phone numbers:")
    phone1 = input("Your UK mobile (e.g., 07123456789 or +447123456789): ").strip()
    phone2 = input("Your wife's UK mobile (e.g., 07987654321): ").strip()
    
    # Normalize UK phone numbers
    phone1 = normalize_uk_phone(phone1)
    phone2 = normalize_uk_phone(phone2)
    
    if not phone1 or not phone2:
        print("❌ Invalid phone numbers!")
        return
    
    print(f"\n📱 Numbers configured:")
    print(f"   Your number: {phone1}")
    print(f"   Wife's number: {phone2}")
    print()
    
    # Get Twilio credentials
    print("🔑 Enter Twilio credentials:")
    print("   (Get these from: https://console.twilio.com)")
    print()
    
    account_sid = input("Account SID (starts with AC...): ").strip()
    auth_token = input("Auth Token: ").strip()
    from_number = input("Your Twilio UK number (e.g., +441234567890): ").strip()
    
    if not all([account_sid, auth_token, from_number]):
        print("❌ All Twilio credentials are required!")
        return
    
    # Configure SMS system
    try:
        sms = SMSAlert()
        phone_numbers = [phone1, phone2]
        
        # Convert phone numbers for storage (remove +44)
        clean_numbers = []
        for phone in phone_numbers:
            clean_phone = phone.replace('+44', '')
            clean_numbers.append(clean_phone)
        
        sms.setup_twilio_sms(clean_numbers, account_sid, auth_token, from_number)
        
        print(f"\n✅ Dual SMS configured successfully!")
        print(f"   Recipients: {len(phone_numbers)} phone numbers")
        print(f"   Twilio number: {from_number}")
        print()
        
        # Test SMS
        test_choice = input("Send test SMS to both phones? (y/n): ").strip().lower()
        if test_choice == 'y':
            print("\n🧪 Sending test SMS to both phones...")
            if sms.test_sms():
                print("✅ Test SMS sent to both phones! Check both devices.")
                print("\n🎉 SMS alerts are now active!")
                print("   You'll both receive SMS for every new shift.")
            else:
                print("❌ Test failed. Check Twilio credentials.")
        
        # Show summary
        print("\n📋 Summary:")
        print(f"   • SMS enabled for {len(phone_numbers)} recipients")
        print(f"   • Cost: ~2p per shift alert (1p each)")
        print(f"   • Method: Twilio SMS")
        print(f"   • Status: Active")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

def normalize_uk_phone(phone):
    """Normalize UK phone number to +44 format"""
    if not phone:
        return ""
    
    # Remove spaces and common separators
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Handle different UK formats
    if phone.startswith('+44'):
        return phone
    elif phone.startswith('44'):
        return '+' + phone
    elif phone.startswith('07'):
        return '+44' + phone[1:]  # Convert 07123456789 to +447123456789
    elif phone.startswith('7') and len(phone) == 10:
        return '+44' + phone  # Convert 7123456789 to +447123456789
    else:
        # Assume it's a UK number and add +44
        return '+44' + phone

def show_current_config():
    """Show current SMS configuration"""
    print("\n📋 Current SMS Configuration")
    print("-" * 30)
    
    try:
        sms = SMSAlert()
        config = sms.sms_config
        
        print(f"Enabled: {'✅ YES' if config.get('enabled') else '❌ NO'}")
        print(f"Method: {config.get('method', 'Not set')}")
        
        phone_numbers = config.get('phone_numbers', [])
        if phone_numbers:
            print(f"Recipients: {len(phone_numbers)} phone numbers")
            for i, phone in enumerate(phone_numbers, 1):
                # Show phone with +44 prefix for display
                display_phone = phone if phone.startswith('+44') else f'+44{phone}'
                print(f"   {i}. {display_phone}")
        else:
            single_phone = config.get('phone_number', '')
            if single_phone:
                display_phone = single_phone if single_phone.startswith('+44') else f'+44{single_phone}'
                print(f"Phone: {display_phone} (old single format)")
            else:
                print("Phone: Not configured")
        
        if config.get('method') == 'twilio':
            twilio = config.get('twilio', {})
            print(f"Twilio SID: {twilio.get('account_sid', 'Not set')[:10]}...")
            print(f"From Number: {twilio.get('from_number', 'Not set')}")
            
    except Exception as e:
        print(f"❌ Error reading config: {e}")

if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == 'status':
        show_current_config()
    else:
        main()
