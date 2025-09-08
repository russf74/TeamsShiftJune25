#!/usr/bin/env python3
"""
Health Check Email Reporter - Completely Isolated
Formats and sends comprehensive health check reports via email and WhatsApp.
"""

import json
import datetime
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from pathlib import Path

class HealthCheckReporter:
    """
    Safely format and send health check reports.
    Completely isolated from main application.
    """
    
    def __init__(self, app_dir=None):
        self.app_dir = Path(app_dir) if app_dir else Path(__file__).parent.absolute()
        self.smtp_settings = None
        self.load_smtp_settings()
    
    def load_smtp_settings(self):
        """Safely load SMTP settings"""
        try:
            smtp_path = self.app_dir / 'smtp_settings.json'
            if smtp_path.exists():
                with open(smtp_path, 'r') as f:
                    self.smtp_settings = json.load(f)
        except Exception as e:
            print(f"[HEALTH REPORTER] Could not load SMTP settings: {e}")
            self.smtp_settings = None
    
    def format_health_status_indicator(self, status):
        """Get professional status indicator"""
        indicators = {
            'HEALTHY': '[PASS]',
            'WARNING': '[WARN]',
            'CRITICAL': '[FAIL]',
            'UNKNOWN': '[UNKN]',
            'PASS': '[PASS]',
            'FAIL': '[FAIL]'
        }
        return indicators.get(status, '[UNKN]')
    
    def analyze_critical_issues(self, health_results):
        """Analyze health results for critical communication issues that could cause missed alerts"""
        critical_issues = []
        warnings = []
        
        # Check WhatsApp connectivity (only if enabled)
        from config import load_config
        config = load_config()
        if config.get('whatsapp_enabled', True):
            whatsapp_result = health_results.get('detailed_results', {}).get('whatsapp_connectivity', {})
            if whatsapp_result.get('status') == 'PASS':
                whatsapp_data = whatsapp_result.get('result', {})
                
                if not whatsapp_data.get('app_running', False):
                    critical_issues.append("🚨 CRITICAL: WhatsApp not running - shift alerts will not be sent via WhatsApp")
                elif not whatsapp_data.get('window_focusable', False):
                    critical_issues.append("🚨 CRITICAL: WhatsApp window cannot be focused - shift alerts will fail")
                elif not whatsapp_data.get('typing_functional', False):
                    critical_issues.append("🚨 CRITICAL: WhatsApp typing not functional - messages cannot be sent")
                elif whatsapp_data.get('app_running') and not whatsapp_data.get('app_found', False):
                    warnings.append("⚠️ WARNING: WhatsApp process running but not connectable - may need restart")
            elif whatsapp_result.get('status') == 'FAIL':
                critical_issues.append("🚨 CRITICAL: WhatsApp connectivity test failed - shift alerts at risk")
        else:
            warnings.append("ℹ️ INFO: WhatsApp disabled in configuration - email-only mode active")
        
        # Check email connectivity
        network_result = health_results.get('detailed_results', {}).get('network_health', {})
        if network_result.get('status') == 'PASS':
            network_data = network_result.get('result', {})
            if not network_data.get('internet', False):
                critical_issues.append("🚨 CRITICAL: No internet connectivity - all email alerts will fail")
            elif network_data.get('smtp_server') == False:
                critical_issues.append("🚨 CRITICAL: SMTP server unreachable - email alerts will fail")
        
        # Check configuration issues
        config_result = health_results.get('detailed_results', {}).get('configuration_health', {})
        if config_result.get('status') == 'PASS':
            config_data = config_result.get('result', {})
            smtp_config = config_data.get('smtp_settings', {})
            if not smtp_config.get('exists', False):
                critical_issues.append("🚨 CRITICAL: SMTP settings missing - email alerts disabled")
            elif smtp_config.get('missing_required_keys'):
                critical_issues.append(f"🚨 CRITICAL: SMTP configuration incomplete - missing: {smtp_config['missing_required_keys']}")
        
        return critical_issues, warnings
    
    def format_detailed_results(self, results):
        """Format detailed test results for email"""
        if not results.get('detailed_results'):
            return "No detailed results available."
        
        sections = []
        
        for test_name, test_result in results['detailed_results'].items():
            status = test_result.get('status', 'UNKNOWN')
            indicator = self.format_health_status_indicator(status)
            exec_time = test_result.get('execution_time', 0)
            
            section = f"\n{indicator} {test_name.replace('_', ' ').upper()} ({exec_time:.2f}s)\n"
            section += "-" * 50 + "\n"
            
            if status == 'PASS':
                result_data = test_result.get('result', {})
                if isinstance(result_data, dict):
                    for key, value in result_data.items():
                        section += f"  {key.replace('_', ' ').title()}: {value}\n"
                else:
                    section += f"  Result: {result_data}\n"
            else:
                error = test_result.get('error', 'Unknown error')
                section += f"  ERROR: {error}\n"
            
            sections.append(section)
        
        return "\n".join(sections)
    
    def format_performance_summary(self, results):
        """Format performance metrics summary"""
        if not results.get('performance_metrics'):
            return "No performance data available."
        
        metrics = results['performance_metrics']
        total_time = sum(metrics.values())
        slowest_test = max(metrics.items(), key=lambda x: x[1]) if metrics else None
        
        summary = f"Total Execution Time: {total_time:.2f} seconds\n"
        summary += f"Average Test Time: {total_time/len(metrics):.2f} seconds\n"
        
        if slowest_test:
            summary += f"Slowest Test: {slowest_test[0]} ({slowest_test[1]:.2f}s)\n"
        
        summary += "Individual Test Performance:\n"
        for test_name, exec_time in sorted(metrics.items(), key=lambda x: x[1], reverse=True):
            summary += f"  {test_name.replace('_', ' ').title()}: {exec_time:.2f}s\n"
        
        return summary
    
    def format_warnings_and_errors(self, results):
        """Format warnings and errors section"""
        warnings = results.get('warnings', [])
        errors = results.get('errors', [])
        
        if not warnings and not errors:
            return "STATUS: No warnings or errors detected."
        
        output = []
        
        if warnings:
            output.append("WARNINGS:")
            for warning in warnings:
                output.append(f"  - {warning}")
            output.append("")
        
        if errors:
            output.append("ERRORS:")
            for error in errors:
                output.append(f"  - {error}")
            output.append("")
        
        return "\n".join(output)
    
    def format_detailed_results_html(self, results):
        """Format detailed test results for HTML email"""
        if not results.get('detailed_results'):
            return "<p>No detailed results available.</p>"
        
        html_parts = []
        
        for test_name, test_result in results['detailed_results'].items():
            status = test_result.get('status', 'UNKNOWN')
            exec_time = test_result.get('execution_time', 0)
            
            status_class = 'test-result' if status == 'PASS' else 'test-result test-fail'
            
            html_part = f'<div class="{status_class}">'
            html_part += f'<strong>{test_name.replace("_", " ").title()}</strong> '
            html_part += f'<span style="color: #666;">({exec_time:.2f}s)</span><br>'
            
            if status == 'PASS':
                result_data = test_result.get('result', {})
                if isinstance(result_data, dict):
                    html_part += '<ul style="margin: 10px 0; padding-left: 20px;">'
                    for key, value in result_data.items():
                        html_part += f'<li>{key.replace("_", " ").title()}: {value}</li>'
                    html_part += '</ul>'
                else:
                    html_part += f'<p style="margin: 5px 0;">Result: {result_data}</p>'
            else:
                error = test_result.get('error', 'Unknown error')
                html_part += f'<p style="color: #dc3545; margin: 5px 0;"><strong>ERROR:</strong> {error}</p>'
            
            html_part += '</div>'
            html_parts.append(html_part)
        
        return "\n".join(html_parts)
    
    def format_performance_summary_html(self, results):
        """Format performance metrics for HTML"""
        if not results.get('performance_metrics'):
            return "<p>No performance data available.</p>"
        
        metrics = results['performance_metrics']
        total_time = sum(metrics.values())
        slowest_test = max(metrics.items(), key=lambda x: x[1]) if metrics else None
        
        html = f"""
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Execution Time</td><td>{total_time:.2f} seconds</td></tr>
<tr><td>Average Test Time</td><td>{total_time/len(metrics):.2f} seconds</td></tr>
"""
        
        if slowest_test:
            html += f'<tr><td>Slowest Test</td><td>{slowest_test[0].replace("_", " ").title()} ({slowest_test[1]:.2f}s)</td></tr>'
        
        html += '</table>'
        
        return html
    
    def format_warnings_and_errors_html(self, results):
        """Format warnings and errors for HTML"""
        warnings = results.get('warnings', [])
        errors = results.get('errors', [])
        
        if not warnings and not errors:
            return '<p style="color: #28a745;"><strong>STATUS:</strong> No warnings or errors detected.</p>'
        
        html_parts = []
        
        if warnings:
            html_parts.append('<div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">')
            html_parts.append('<h4 style="color: #856404; margin: 0 0 10px 0;">WARNINGS:</h4>')
            html_parts.append('<ul style="margin: 0; padding-left: 20px;">')
            for warning in warnings:
                html_parts.append(f'<li>{warning}</li>')
            html_parts.append('</ul></div>')
        
        if errors:
            html_parts.append('<div style="background-color: #f8d7da; padding: 10px; border-radius: 5px;">')
            html_parts.append('<h4 style="color: #721c24; margin: 0 0 10px 0;">ERRORS:</h4>')
            html_parts.append('<ul style="margin: 0; padding-left: 20px;">')
            for error in errors:
                html_parts.append(f'<li>{error}</li>')
            html_parts.append('</ul></div>')
        
        return "\n".join(html_parts)
    
    def get_recommendations_html(self, overall_status):
        """Get HTML formatted recommendations based on status"""
        if overall_status == 'HEALTHY':
            return """
<p style="color: #28a745;"><strong>STATUS:</strong> No action required. System operating optimally.</p>
<ul>
<li>Continue normal automated operation</li>
<li>System safe for hands-free monitoring</li>
<li>Next health check: Friday 7:30pm next week</li>
</ul>
"""
        elif overall_status == 'WARNING':
            return """
<p style="color: #ffc107;"><strong>STATUS:</strong> Investigation recommended within 24-48 hours.</p>
<ul>
<li>Review warnings section above for specific issues</li>
<li>System should continue operating but monitor closely</li>
<li>Consider running manual scan test to verify functionality</li>
<li>Address warnings before next week's health check</li>
</ul>
"""
        else:  # CRITICAL or UNKNOWN
            return """
<p style="color: #dc3545;"><strong>STATUS:</strong> IMMEDIATE ATTENTION REQUIRED</p>
<ul>
<li>System reliability compromised</li>
<li>Manual intervention needed before relying on automation</li>
<li>Review error details above and resolve issues immediately</li>
<li>Run manual test scan to verify system recovery</li>
<li>Do not rely on automated monitoring until issues resolved</li>
</ul>
"""
    
    def create_weekly_health_email(self, health_results):
        """Create comprehensive weekly health check email with mobile-friendly HTML formatting"""
        timestamp = health_results.get('timestamp', 'Unknown')
        overall_status = health_results.get('overall_status', 'UNKNOWN')
        status_indicator = self.format_health_status_indicator(overall_status)
        
        tests_completed = health_results.get('tests_completed', 0)
        tests_failed = health_results.get('tests_failed', 0)
        total_time = health_results.get('total_execution_time', 0)
        success_rate = ((tests_completed - tests_failed) / tests_completed * 100) if tests_completed > 0 else 0
        
        # Email subject
        subject = f"Teams Shift App - Weekly Health Report {status_indicator} {overall_status}"
        
        # Analyze critical communication issues
        critical_issues, warnings = self.analyze_critical_issues(health_results)
        
        # Build alert section for top of email
        alert_section = ""
        if critical_issues:
            alert_section = f"""
<div style="background-color: #f8d7da; border: 2px solid #dc3545; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
<h3 style="color: #721c24; margin: 0 0 10px 0;">🚨 URGENT: CRITICAL COMMUNICATION ISSUES DETECTED</h3>
<p style="color: #721c24; font-weight: bold; margin-bottom: 10px;">These issues may cause you to MISS SHIFT ALERTS:</p>
<ul style="color: #721c24; margin: 0; padding-left: 20px;">
"""
            for issue in critical_issues:
                alert_section += f"<li>{issue}</li>"
            alert_section += """
</ul>
<p style="color: #721c24; font-weight: bold; margin: 10px 0 0 0;">⚡ ACTION REQUIRED: Fix these issues immediately to avoid missing shifts!</p>
</div>
"""
        
        if warnings:
            alert_section += f"""
<div style="background-color: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
<h4 style="color: #856404; margin: 0 0 10px 0;">⚠️ Communication Warnings</h4>
<ul style="color: #856404; margin: 0; padding-left: 20px;">
"""
            for warning in warnings:
                alert_section += f"<li>{warning}</li>"
            alert_section += """
</ul>
</div>
"""
        
        # HTML email body for mobile-friendly viewing
        body = f"""<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
.header {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
.status-healthy {{ color: #28a745; font-weight: bold; }}
.status-warning {{ color: #ffc107; font-weight: bold; }}
.status-critical {{ color: #dc3545; font-weight: bold; }}
.section {{ margin-bottom: 25px; }}
.section-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-bottom: 15px; }}
.test-result {{ background-color: #f8f9fa; padding: 10px; border-left: 4px solid #28a745; margin-bottom: 10px; }}
.test-fail {{ border-left-color: #dc3545; }}
.metric {{ display: inline-block; margin-right: 20px; }}
.recommendation {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
th {{ background-color: #f2f2f2; }}
</style>
</head>
<body>

{alert_section}

<div class="header">
<h2>Teams Shift Application - Weekly Health Report</h2>
<p><strong>Status:</strong> <span class="status-{overall_status.lower()}">{status_indicator} {overall_status}</span><br>
<strong>Generated:</strong> {datetime.datetime.fromisoformat(timestamp).strftime('%A, %B %d, %Y at %I:%M %p')}<br>
<strong>Success Rate:</strong> {success_rate:.1f}%</p>
</div>

<div class="section">
<div class="section-title">Executive Summary</div>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Tests Completed</td><td>{tests_completed}</td></tr>
<tr><td>Tests Failed</td><td>{tests_failed}</td></tr>
<tr><td>Execution Time</td><td>{total_time:.2f} seconds</td></tr>
<tr><td>System Status</td><td>{overall_status}</td></tr>
</table>
<p>This automated health check verifies your Teams Shift monitoring system is operating correctly and can be trusted for hands-free operation.</p>
</div>

<div class="section">
<div class="section-title">Issues & Warnings</div>
{self.format_warnings_and_errors_html(health_results)}
</div>

<div class="section">
<div class="section-title">Test Results</div>
{self.format_detailed_results_html(health_results)}
</div>

<div class="section">
<div class="section-title">Performance Analysis</div>
{self.format_performance_summary_html(health_results)}
</div>

<div class="section">
<div class="section-title">Recommended Actions</div>
<div class="recommendation">
{self.get_recommendations_html(overall_status)}
</div>
</div>

<div class="section">
<div class="section-title">Report Information</div>
<p><strong>System:</strong> Teams Shift Health Check v1.0<br>
<strong>Schedule:</strong> Every Friday at 7:30pm<br>
<strong>Next Report:</strong> {(datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%A, %B %d, %Y at 7:30pm')}</p>
</div>

</body>
</html>"""
        
        return subject, body
    
    def send_health_check_email(self, health_results, recipient="russfray74@gmail.com"):
        """
        Send health check email safely.
        Returns True if successful, False otherwise.
        """
        try:
            if not self.smtp_settings:
                print("[HEALTH REPORTER] No SMTP settings available")
                return False
            
            subject, body = self.create_weekly_health_email(health_results)
            
            # Create HTML email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((
                self.smtp_settings.get('FromName', 'Teams Shift Health Check'),
                self.smtp_settings.get('FromAddress')
            ))
            msg['To'] = recipient
            
            # Create HTML part
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(
                self.smtp_settings.get('SmtpHost'),
                self.smtp_settings.get('SmtpPort', 587),
                timeout=30
            )
            
            if self.smtp_settings.get('EnableSsl', True):
                server.starttls()
            
            server.login(
                self.smtp_settings.get('FromAddress'),
                self.smtp_settings.get('FromPassword')
            )
            
            server.sendmail(
                self.smtp_settings.get('FromAddress'),
                [recipient],
                msg.as_string()
            )
            server.quit()
            
            print(f"[HEALTH REPORTER] Health check email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            print(f"[HEALTH REPORTER] Failed to send health check email: {e}")
            traceback.print_exc()
            return False
    
    def send_whatsapp_notification(self):
        """
        Send brief WhatsApp notification about health check completion.
        Returns True if successful, False otherwise.
        """
        # Check if WhatsApp is enabled in config
        from config import load_config
        config = load_config()
        if not config.get('whatsapp_enabled', True):
            print("[HEALTH REPORTER] WhatsApp disabled in configuration - skipping WhatsApp notification")
            return True  # Return True so email-only mode doesn't show as failure
            
        try:
            # Import WhatsApp automation safely
            import pyautogui
            import time
            from pywinauto.application import Application
            
            print("[HEALTH REPORTER] Attempting to connect to WhatsApp...")
            
            # Try to focus WhatsApp window
            app = None
            try:
                app = Application(backend="uia").connect(title_re=".*WhatsApp.*", timeout=5)
                print("[HEALTH REPORTER] Connected to WhatsApp successfully")
            except Exception as e:
                print(f"[HEALTH REPORTER] WhatsApp not running or not found: {e}")
                return False
            
            if not app:
                print("[HEALTH REPORTER] No WhatsApp application found")
                return False
            
            # Focus WhatsApp window
            print("[HEALTH REPORTER] Focusing WhatsApp window...")
            win = app.top_window()
            win.set_focus()
            time.sleep(2)  # Increased wait time
            
            # Clear any existing text in input field
            pyautogui.hotkey('ctrl', 'a')  # Select all
            time.sleep(0.5)
            
            # Type the message
            message = "Weekly checks completed and status email sent"
            print(f"[HEALTH REPORTER] Typing message: {message}")
            pyautogui.typewrite(message, interval=0.1)  # Slower typing
            time.sleep(1)
            
            # Send the message by pressing Enter
            print("[HEALTH REPORTER] Sending message...")
            pyautogui.press('enter')
            time.sleep(1)
            
            print("[HEALTH REPORTER] WhatsApp message sent successfully")
            return True
            
        except Exception as e:
            print(f"[HEALTH REPORTER] Failed to send WhatsApp notification: {e}")
            import traceback
            traceback.print_exc()
            return False

def send_weekly_health_report(health_results, email_recipient="russfray74@gmail.com"):
    """
    Main function to send weekly health report.
    Completely safe to call.
    """
    try:
        reporter = HealthCheckReporter()
        
        # Send email report
        email_success = reporter.send_health_check_email(health_results, email_recipient)
        
        # Send WhatsApp notification
        whatsapp_success = reporter.send_whatsapp_notification()
        
        return {
            'email_sent': email_success,
            'whatsapp_sent': whatsapp_success,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[HEALTH REPORTER] Critical error in health report: {e}")
        return {
            'email_sent': False,
            'whatsapp_sent': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test with dummy data
    test_results = {
        'overall_status': 'HEALTHY',
        'timestamp': datetime.datetime.now().isoformat(),
        'tests_completed': 6,
        'tests_failed': 0,
        'warnings': [],
        'errors': [],
        'total_execution_time': 15.2
    }
    
    result = send_weekly_health_report(test_results)
    print(json.dumps(result, indent=2))
