#!/usr/bin/env python3

"""
SMS Text Messaging Options Research

Comparing affordable and reliable SMS APIs for shift alerts:

1. TWILIO SMS API
   - Cost: ~$0.0075-0.01 per SMS (very cheap)
   - Reliability: Excellent (99.95% uptime)
   - Features: Global coverage, delivery receipts
   - Setup: Simple REST API
   - Python library: twilio

2. EMAIL-TO-SMS (Free!)
   - Cost: FREE (uses your email provider)
   - Reliability: Depends on carrier, usually good
   - Features: Works with all carriers
   - Setup: Very simple - just send email to special addresses
   - Examples: 
     - Verizon: 1234567890@vtext.verizon.net
     - AT&T: 1234567890@txt.att.net
     - T-Mobile: 1234567890@tmomail.net
     - Sprint: 1234567890@messaging.sprintpcs.com

3. TEXTBELT API
   - Cost: $0.01 per SMS
   - Reliability: Good
   - Features: Simple REST API
   - Setup: Very easy

4. AWS SNS
   - Cost: $0.00645 per SMS 
   - Reliability: Excellent
   - Features: Enterprise grade
   - Setup: Moderate complexity

RECOMMENDATION: Start with EMAIL-TO-SMS (FREE) as it's reliable and costs nothing.
If you need more reliability, upgrade to Twilio (~$0.01/message).
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

# Email-to-SMS gateway addresses for major carriers
CARRIER_GATEWAYS = {
    'verizon': '@vtext.verizon.net',
    'att': '@txt.att.net', 
    'tmobile': '@tmomail.net',
    'sprint': '@messaging.sprintpcs.com',
    'boost': '@sms.myboostmobile.com',
    'cricket': '@sms.cricketwireless.net',
    'uscellular': '@email.uscc.net',
    'metro': '@mymetropcs.com'
}

def send_sms_via_email(phone_number, carrier, message, smtp_settings=None):
    """
    Send SMS via email-to-SMS gateway (FREE!)
    
    Args:
        phone_number: 10-digit phone number (e.g., "1234567890")
        carrier: carrier name (e.g., "verizon", "att", "tmobile")
        message: text message to send
        smtp_settings: dict with SMTP settings (optional, uses config if not provided)
    """
    
    if carrier.lower() not in CARRIER_GATEWAYS:
        raise ValueError(f"Unsupported carrier: {carrier}. Supported: {list(CARRIER_GATEWAYS.keys())}")
    
    # Create SMS email address
    sms_email = phone_number + CARRIER_GATEWAYS[carrier.lower()]
    
    # Load SMTP settings
    if not smtp_settings:
        with open('smtp_settings.json', 'r') as f:
            smtp_settings = json.load(f)
    
    # Create email message
    msg = MIMEText(message)
    msg['Subject'] = ""  # Many carriers ignore subject for SMS
    msg['From'] = formataddr(("Teams Shift Alert", smtp_settings['FromAddress']))
    msg['To'] = sms_email
    
    # Send via SMTP
    try:
        server = smtplib.SMTP(smtp_settings['SmtpHost'], smtp_settings['SmtpPort'])
        server.starttls()
        server.login(smtp_settings['FromAddress'], smtp_settings['FromPassword'])
        server.send_message(msg)
        server.quit()
        
        print(f"[SMS] Message sent to {phone_number} via {carrier} gateway")
        return True
        
    except Exception as e:
        print(f"[SMS] Failed to send message: {e}")
        return False

def send_sms_via_twilio(phone_number, message, account_sid, auth_token, from_number):
    """
    Send SMS via Twilio API (~$0.01 per message)
    
    Requires: pip install twilio
    """
    try:
        from twilio.rest import Client
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=message,
            from_=from_number,  # Your Twilio phone number
            to=phone_number     # Format: +1234567890
        )
        
        print(f"[SMS] Twilio message sent: {message.sid}")
        return True
        
    except ImportError:
        print("[SMS] Twilio library not installed. Run: pip install twilio")
        return False
    except Exception as e:
        print(f"[SMS] Twilio error: {e}")
        return False

# Test functions
if __name__ == "__main__":
    print("SMS Messaging Options Demo")
    print("=" * 40)
    
    # Test message
    test_message = "Test: Teams Shift Alert system working!"
    
    # Email-to-SMS test (requires your phone number and carrier)
    # send_sms_via_email("1234567890", "verizon", test_message)
    
    print("Ready to implement SMS alerts!")
