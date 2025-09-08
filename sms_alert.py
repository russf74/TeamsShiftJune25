#!/usr/bin/env python3

"""
SMS Alert System for Teams Shift Notifications

Provides SMS text messaging as WhatsApp replacement.
Supports both free email-to-SMS and paid Twilio API.
"""

import json
import smtplib
import os
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime

class SMSAlert:
    def __init__(self):
        self.config_file = 'sms_config.json'
        self.load_config()
    
    def load_config(self):
        """Load SMS configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.sms_config = json.load(f)
            else:
                # Create default config
                self.sms_config = {
                    "enabled": False,
                    "method": "email",  # "email" or "twilio"
                    "phone_numbers": [],  # Support multiple phone numbers
                    "carrier": "",
                    "twilio": {
                        "account_sid": "",
                        "auth_token": "", 
                        "from_number": ""
                    }
                }
                self.save_config()
        except Exception as e:
            print(f"[SMS] Error loading config: {e}")
            self.sms_config = {"enabled": False}
    
    def save_config(self):
        """Save SMS configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.sms_config, f, indent=4)
        except Exception as e:
            print(f"[SMS] Error saving config: {e}")
    
    def send_shift_alert_sms(self, matched_dates):
        """Send SMS alert for new shifts to all configured phone numbers"""
        if not self.sms_config.get('enabled', False):
            print("[SMS] SMS alerts disabled in config")
            return False
        
        if not matched_dates:
            return True
            
        # Format message
        dates_text = ", ".join([datetime.strptime(date, "%Y-%m-%d").strftime("%a %d %b") for date in matched_dates])
        message = f"🚨 NEW SHIFTS AVAILABLE: {dates_text}. Check Teams app immediately!"
        
        # Get phone numbers (support both old single number and new multiple numbers)
        phone_numbers = self.sms_config.get('phone_numbers', [])
        if not phone_numbers:
            # Backward compatibility with old single phone_number field
            single_phone = self.sms_config.get('phone_number', '')
            if single_phone:
                phone_numbers = [single_phone]
        
        if not phone_numbers:
            print("[SMS] No phone numbers configured")
            return False
        
        # Send to all phone numbers
        success_count = 0
        for phone_number in phone_numbers:
            if self.sms_config.get('method') == 'twilio':
                if self._send_via_twilio_single(message, phone_number):
                    success_count += 1
            else:
                if self._send_via_email_single(message, phone_number):
                    success_count += 1
        
        print(f"[SMS] Sent SMS to {success_count}/{len(phone_numbers)} recipients")
        return success_count > 0
    
    def _send_via_email_single(self, message, phone_number):
        """Send SMS via email-to-SMS gateway to a single phone number (FREE!)"""
        try:
            carrier = self.sms_config.get('carrier', '')
            
            if not phone_number or not carrier:
                print(f"[SMS] Phone number or carrier not configured for {phone_number}")
                return False
            
            # Carrier gateways
            gateways = {
                'verizon': '@vtext.verizon.net',
                'att': '@txt.att.net',
                'tmobile': '@tmomail.net', 
                'sprint': '@messaging.sprintpcs.com',
                'boost': '@sms.myboostmobile.com',
                'cricket': '@sms.cricketwireless.net'
            }
            
            if carrier.lower() not in gateways:
                print(f"[SMS] Unsupported carrier: {carrier}")
                return False
            
            # Create SMS email address
            sms_email = phone_number + gateways[carrier.lower()]
            
            # Load SMTP settings
            smtp_path = os.path.join(os.getcwd(), 'smtp_settings.json')
            if not os.path.exists(smtp_path):
                print("[SMS] SMTP settings not found")
                return False
                
            with open(smtp_path, 'r') as f:
                smtp_settings = json.load(f)
            
            # Create and send email
            msg = MIMEText(message)
            msg['Subject'] = ""  # Most carriers ignore subject for SMS
            msg['From'] = formataddr(("Shift Alert", smtp_settings['FromAddress']))
            msg['To'] = sms_email
            
            server = smtplib.SMTP(smtp_settings['SmtpHost'], smtp_settings['SmtpPort'])
            server.starttls()
            server.login(smtp_settings['FromAddress'], smtp_settings['FromPassword'])
            server.send_message(msg)
            server.quit()
            
            print(f"[SMS] SMS sent to {phone_number} via {carrier} gateway")
            return True
            
        except Exception as e:
            print(f"[SMS] Email-to-SMS failed for {phone_number}: {e}")
            return False
    
    def _send_via_twilio_single(self, message, phone_number):
        """Send SMS via Twilio API to a single phone number (~$0.01/message)"""
        try:
            from twilio.rest import Client
            
            twilio_config = self.sms_config.get('twilio', {})
            account_sid = twilio_config.get('account_sid')
            auth_token = twilio_config.get('auth_token')
            from_number = twilio_config.get('from_number')
            
            if not all([account_sid, auth_token, from_number, phone_number]):
                print(f"[SMS] Twilio configuration incomplete for {phone_number}")
                return False
            
            # Format phone number for Twilio (handle UK and US numbers)
            to_number = phone_number
            if not to_number.startswith('+'):
                # If it's a UK number starting with 7, assume +44
                if to_number.startswith('7') and len(to_number) == 10:
                    to_number = '+44' + to_number
                # If it's a 10-digit US number
                elif len(to_number) == 10:
                    to_number = '+1' + to_number
                # If it starts with 44, add +
                elif to_number.startswith('44'):
                    to_number = '+' + to_number
                else:
                    # Default to US format for backward compatibility
                    to_number = '+1' + to_number
            
            client = Client(account_sid, auth_token)
            message_obj = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            print(f"[SMS] Twilio SMS sent to {to_number}: {message_obj.sid}")
            return True
            
        except ImportError:
            print("[SMS] Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            print(f"[SMS] Twilio error for {phone_number}: {e}")
            return False
    
    def test_sms(self):
        """Send test SMS message to all configured numbers"""
        test_message = f"Test SMS from Teams Shift Alert system - {datetime.now().strftime('%H:%M:%S')}"
        
        # Get phone numbers (support both old single number and new multiple numbers)
        phone_numbers = self.sms_config.get('phone_numbers', [])
        if not phone_numbers:
            # Backward compatibility with old single phone_number field
            single_phone = self.sms_config.get('phone_number', '')
            if single_phone:
                phone_numbers = [single_phone]
        
        if not phone_numbers:
            print("[SMS] No phone numbers configured for testing")
            return False
        
        # Test all phone numbers
        success_count = 0
        for phone_number in phone_numbers:
            if self.sms_config.get('method') == 'twilio':
                if self._send_via_twilio_single(test_message, phone_number):
                    success_count += 1
            else:
                if self._send_via_email_single(test_message, phone_number):
                    success_count += 1
        
        print(f"[SMS] Test SMS sent to {success_count}/{len(phone_numbers)} recipients")
        return success_count > 0
    
    def setup_email_sms(self, phone_numbers, carrier):
        """Setup free email-to-SMS for multiple phone numbers"""
        if isinstance(phone_numbers, str):
            phone_numbers = [phone_numbers]  # Convert single number to list
            
        self.sms_config.update({
            'enabled': True,
            'method': 'email',
            'phone_numbers': phone_numbers,
            'carrier': carrier.lower()
        })
        self.save_config()
        print(f"[SMS] Email-to-SMS configured for {len(phone_numbers)} numbers on {carrier}")
    
    def setup_twilio_sms(self, phone_numbers, account_sid, auth_token, from_number):
        """Setup paid Twilio SMS for multiple phone numbers"""
        if isinstance(phone_numbers, str):
            phone_numbers = [phone_numbers]  # Convert single number to list
            
        self.sms_config.update({
            'enabled': True,
            'method': 'twilio',
            'phone_numbers': phone_numbers,
            'twilio': {
                'account_sid': account_sid,
                'auth_token': auth_token,
                'from_number': from_number
            }
        })
        self.save_config()
        print(f"[SMS] Twilio SMS configured for {len(phone_numbers)} numbers")

# Global SMS instance
sms_alert = SMSAlert()

if __name__ == "__main__":
    print("SMS Alert System")
    print("=" * 30)
    
    # Example usage:
    # sms_alert.setup_email_sms("1234567890", "verizon")
    # sms_alert.test_sms()
    
    print("SMS system ready for configuration!")
