from email_alert import check_whatsapp_quick

result = check_whatsapp_quick()
print(f"WhatsApp Status: {result['status']} - {result['message']}")
