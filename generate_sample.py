#!/usr/bin/env python3
"""
Generate a sample HTML email to view formatting
"""

from health_check import run_weekly_health_check
from health_reporter import HealthCheckReporter

def generate_sample_email():
    print("Generating sample HTML email...")
    
    # Run health check
    health_results = run_weekly_health_check()
    
    if health_results:
        # Create reporter and format email
        reporter = HealthCheckReporter()
        subject, html_body = reporter.create_weekly_health_email(health_results)
        
        # Save to file so you can view it
        with open('sample_health_email.html', 'w', encoding='utf-8') as f:
            f.write(html_body)
        
        print(f"✅ Sample email saved as 'sample_health_email.html'")
        print(f"📧 Subject: {subject}")
        print(f"📱 HTML body length: {len(html_body)} characters")
        print("\nYou can open the HTML file in a browser to see the mobile-friendly formatting!")
        
    else:
        print("❌ Failed to generate health results")

if __name__ == "__main__":
    generate_sample_email()
