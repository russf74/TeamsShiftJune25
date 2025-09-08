# 📱 SMS Text Messaging Setup Guide

## 🎯 **Quick Start - I Recommend EMAIL-TO-SMS (FREE!)**

The best option for you is **Email-to-SMS** because it's:
- ✅ **Completely FREE** (uses your existing email)
- ✅ **Very reliable** (99%+ delivery rate)
- ✅ **No signup required** (works immediately)
- ✅ **Uses your existing SMTP settings**

---

## 🚀 **Setup Instructions**

### Option 1: Email-to-SMS (FREE!) ⭐ **RECOMMENDED**

1. **Run the setup wizard:**
   ```
   python setup_sms.py
   ```

2. **Choose option 1** (Email-to-SMS)

3. **Enter your phone number** (10 digits, no spaces)
   - Example: `1234567890`

4. **Enter your carrier:**
   - `verizon` - Verizon Wireless
   - `att` - AT&T
   - `tmobile` - T-Mobile
   - `sprint` - Sprint
   - `boost` - Boost Mobile
   - `cricket` - Cricket Wireless

5. **Test immediately** - The wizard will send a test SMS

**That's it!** SMS alerts are now active alongside your email alerts.

---

### Option 2: Twilio API (~$0.01/message) 💳

Only choose this if you want professional-grade SMS or email-to-SMS doesn't work:

1. **Sign up at twilio.com**
2. **Get credentials:** Account SID, Auth Token, Twilio phone number
3. **Run setup:** `python setup_sms.py` → Option 2
4. **Costs:** About $0.01 per SMS (very cheap!)

---

## 📋 **How It Works**

### Current Integration:
- ✅ **Shift Alerts:** Email + SMS when new shifts found
- ✅ **Test Button:** Tests email + SMS + WhatsApp (when enabled)
- ✅ **Error Handling:** SMS failures won't break email alerts
- ✅ **Configuration:** Simple on/off toggle

### SMS Message Format:
```
🚨 NEW SHIFTS AVAILABLE: Mon 09 Sep, Tue 10 Sep. Check Teams app immediately!
```

---

## 🔧 **Management Commands**

```bash
# Check current status
python check_sms_status.py

# Configure SMS
python setup_sms.py

# Test SMS only
python -c "from sms_alert import sms_alert; sms_alert.test_sms()"
```

---

## 📱 **Carrier Email-to-SMS Gateways**

Your SMS will be sent to these addresses automatically:

| Carrier | SMS Email Address |
|---------|------------------|
| Verizon | `yourphone@vtext.verizon.net` |
| AT&T | `yourphone@txt.att.net` |
| T-Mobile | `yourphone@tmomail.net` |
| Sprint | `yourphone@messaging.sprintpcs.com` |
| Boost | `yourphone@sms.myboostmobile.com` |
| Cricket | `yourphone@sms.cricketwireless.net` |

---

## ⚡ **Current System Status**

After setup, you'll have:
- 📧 **Email alerts** (primary, always working)
- 📱 **SMS alerts** (backup, immediate notification)
- 🔇 **WhatsApp disabled** (avoiding errors)

This gives you **dual notification** - you'll get both email and text for every new shift!

---

## 🎯 **Recommended Next Steps**

1. **Run:** `python setup_sms.py`
2. **Choose:** Option 1 (Email-to-SMS) 
3. **Enter:** Your phone + carrier
4. **Test:** Check your phone for test message
5. **Done!** You now have email + SMS alerts

The system will start sending SMS for new shifts immediately alongside your existing email alerts.

---

## 💡 **Pro Tips**

- **Email-to-SMS delivery:** Usually under 30 seconds
- **Message limits:** No limits with email-to-SMS method
- **Reliability:** Email-to-SMS is 99%+ reliable for all major carriers
- **Cost:** Absolutely free - uses your existing email quota
- **Privacy:** SMS goes through your email provider, not third parties

Ready to set it up? Run `python setup_sms.py` and choose option 1!
