#!/usr/bin/env python3
"""
Preview the new professional email format
"""

from health_check import run_weekly_health_check
from health_reporter import HealthCheckReporter
import datetime

def preview_email_format():
    print("=" * 60)
    print("PREVIEWING NEW PROFESSIONAL EMAIL FORMAT")
    print("=" * 60)
    
    # Run health check
    health_results = run_weekly_health_check()
    
    if health_results:
        # Create reporter and format email
        reporter = HealthCheckReporter()
        subject, body = reporter.create_weekly_health_email(health_results)
        
        print(f"\nEMAIL SUBJECT:")
        print("-" * 40)
        print(subject)
        
        print(f"\nEMAIL BODY PREVIEW (first 50 lines):")
        print("-" * 40)
        body_lines = body.split('\n')
        for i, line in enumerate(body_lines[:50]):
            print(line)
        
        if len(body_lines) > 50:
            print(f"\n... ({len(body_lines) - 50} more lines)")
        
        print(f"\nTotal email length: {len(body)} characters")
        
    else:
        print("Failed to generate health results")

if __name__ == "__main__":
    preview_email_format()
