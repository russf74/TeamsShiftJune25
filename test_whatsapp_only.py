#!/usr/bin/env python3

print("Testing just WhatsApp connectivity...")

try:
    from health_check import SafeHealthChecker
    checker = SafeHealthChecker()
    
    print("Running WhatsApp connectivity check...")
    result = checker.check_whatsapp_connectivity()
    
    print("WhatsApp Check Results:")
    for key, value in result.items():
        print(f"  {key}: {value}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
