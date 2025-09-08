#!/usr/bin/env python3

"""
UK SMS Setup for Teams Shift Alerts

UK-specific SMS options for reliable text messaging.
"""

import json
import os
from sms_alert import SMSAlert

# UK Mobile carriers and their email-to-SMS gateways (limited support)
UK_CARRIERS = {
    'o2': 'Not available',
    'ee': 'Not available', 
    'vodafone': 'Not available',
    'three': 'Not available',
    'giffgaff': 'Not available',
    'tesco': 'Not available'
}

def main():
    print("🇬🇧 UK SMS Setup for Teams Shift Alerts")
    print("=" * 45)
    print()
    
    print("🔍 SMS Options for UK:")
    print()
    print("1. 🌟 TWILIO (RECOMMENDED)")
    print("   ✅ Works perfectly in UK")
    print("   ✅ ~£0.008 per SMS (~1 penny)")
    print("   ✅ 99.9% delivery rate")
    print("   ✅ Instant delivery")
    print("   ✅ Professional grade")
    print()
    
    print("2. 📧 Email-to-SMS")
    print("   ❌ UK carriers don't support email-to-SMS gateways")
    print("   ❌ Not available for O2, EE, Vodafone, Three, etc.")
    print()
    
    print("3. 🌐 Other UK SMS APIs")
    print("   • TextLocal.com (UK-based, ~£0.04 per SMS)")
    print("   • MessageBird (€0.068 per SMS)")
    print("   • More expensive than Twilio")
    print()
    
    print("💡 RECOMMENDATION: Use Twilio")
    print("   • Cheapest option for UK (~1p per SMS)")
    print("   • Most reliable")
    print("   • Used by major companies worldwide")
    print("   • Easy 5-minute setup")
    print()
    
    choice = input("Setup Twilio SMS? (y/n): ").strip().lower()
    
    if choice == 'y':
        setup_twilio_uk()
    else:
        print("\n📋 Manual setup instructions:")
        show_twilio_instructions()

def setup_twilio_uk():
    """Setup Twilio for UK users"""
    print("\n🚀 Setting up Twilio SMS for UK")
    print("-" * 32)
    print()
    
    print("📋 What you need to do:")
    print("1. Go to https://www.twilio.com/try-twilio")
    print("2. Sign up (free trial gives you £15 credit!)")
    print("3. Verify your UK mobile number")
    print("4. Get your credentials from the Twilio Console")
    print()
    
    print("💷 Costs:")
    print("• UK SMS: ~£0.008 per message (~1 penny)")
    print("• Free trial: £15 credit (covers ~1,875 SMS!)")
    print("• After trial: Pay-as-you-go")
    print()
    
    # Get user info
    print("📱 Enter your details:")
    uk_phone = input("UK mobile number (e.g., 447123456789 or +447123456789): ").strip()
    
    if uk_phone:
        if not uk_phone.startswith('+44') and not uk_phone.startswith('44'):
            if uk_phone.startswith('07'):
                uk_phone = '+44' + uk_phone[1:]  # Convert 07123456789 to +447123456789
            else:
                uk_phone = '+44' + uk_phone
    
    account_sid = input("Twilio Account SID (from console): ").strip()
    auth_token = input("Twilio Auth Token (from console): ").strip()  
    from_number = input("Your Twilio phone number (e.g., +441234567890): ").strip()
    
    if all([uk_phone, account_sid, auth_token, from_number]):
        try:
            sms = SMSAlert()
            clean_phone = uk_phone.replace('+44', '').replace('+', '')
            sms.setup_twilio_sms(clean_phone, account_sid, auth_token, from_number)
            
            print(f"\n✅ Twilio SMS configured for UK!")
            print(f"   Your number: {uk_phone}")
            print(f"   Twilio number: {from_number}")
            print("\n🧪 Testing SMS...")
            
            if sms.test_sms():
                print("✅ Test SMS sent! Check your phone.")
                print("🎉 SMS alerts are now active for shift notifications!")
            else:
                print("❌ Test failed. Check your Twilio credentials.")
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
    else:
        print("❌ Missing information. Please complete all fields.")

def show_twilio_instructions():
    """Show detailed Twilio setup instructions"""
    print("\n📋 Twilio Setup Instructions for UK")
    print("=" * 38)
    print()
    print("1. 🌐 SIGN UP:")
    print("   Go to: https://www.twilio.com/try-twilio")
    print("   Use your email and create account")
    print("   Verify your UK mobile number")
    print()
    print("2. 💷 GET FREE CREDIT:")
    print("   Twilio gives £15 free trial credit")
    print("   This covers ~1,875 SMS messages!")
    print()
    print("3. 📱 GET A PHONE NUMBER:")
    print("   In Twilio Console → Phone Numbers → Manage → Buy a number")
    print("   Choose a UK number (+44)")
    print("   Cost: ~£1/month")
    print()
    print("4. 🔑 GET CREDENTIALS:")
    print("   From Twilio Console Dashboard:")
    print("   • Account SID (starts with AC...)")
    print("   • Auth Token (click to reveal)")
    print()
    print("5. ⚙️ CONFIGURE:")
    print("   Run: python setup_sms.py")
    print("   Choose option 2 (Twilio)")
    print("   Enter your credentials")
    print()
    print("💰 TOTAL COST: ~1 penny per SMS after free trial")
    print("📱 RELIABILITY: 99.9% delivery rate")
    print("⚡ SPEED: Instant delivery")

if __name__ == "__main__":
    main()
