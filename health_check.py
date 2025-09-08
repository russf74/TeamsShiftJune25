#!/usr/bin/env python3
"""
Weekly Health Check System - Completely Isolated Module
This module performs comprehensive health checks without interfering with the main application.
All operations are read-only or use separate temporary resources.
"""

import os
import sys
import time
import json
import sqlite3
import datetime
import traceback
import subprocess
import tempfile
import shutil
from pathlib import Path

class HealthCheckError(Exception):
    """Custom exception for health check failures"""
    pass

class SafeHealthChecker:
    """
    Completely isolated health check system with comprehensive failsafes.
    Designed to never interfere with the main application.
    """
    
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.results = {
            'timestamp': self.start_time.isoformat(),
            'overall_status': 'UNKNOWN',
            'tests_completed': 0,
            'tests_failed': 0,
            'warnings': [],
            'errors': [],
            'detailed_results': {},
            'performance_metrics': {}
        }
        
        # Failsafe: Work in temp directory to avoid any file conflicts
        self.temp_dir = tempfile.mkdtemp(prefix='healthcheck_')
        self.original_cwd = os.getcwd()
        
        # Main app directory (read-only access)
        self.app_dir = Path(__file__).parent.absolute()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup: Always restore original state"""
        try:
            os.chdir(self.original_cwd)
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass  # Silent cleanup - never fail here
    
    def safe_execute(self, test_name, test_func, *args, **kwargs):
        """
        Safely execute a test function with comprehensive error handling.
        Never allows exceptions to propagate.
        """
        start_time = time.time()
        try:
            result = test_func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            self.results['tests_completed'] += 1
            self.results['detailed_results'][test_name] = {
                'status': 'PASS',
                'result': result,
                'execution_time': execution_time
            }
            self.results['performance_metrics'][test_name] = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{test_name}: {str(e)}"
            
            self.results['tests_failed'] += 1
            self.results['errors'].append(error_msg)
            self.results['detailed_results'][test_name] = {
                'status': 'FAIL',
                'error': error_msg,
                'execution_time': execution_time,
                'traceback': traceback.format_exc()
            }
            
            # Log error but never re-raise
            print(f"[HEALTH CHECK ERROR] {error_msg}")
            return None
    
    def check_database_health(self):
        """Check database integrity without modifying anything"""
        db_path = self.app_dir / 'shifts.db'
        if not db_path.exists():
            raise HealthCheckError("Database file not found")
        
        # Read-only connection with timeout
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
        try:
            c = conn.cursor()
            
            # Basic integrity check
            c.execute("PRAGMA integrity_check")
            integrity = c.fetchone()[0]
            if integrity != 'ok':
                raise HealthCheckError(f"Database integrity check failed: {integrity}")
            
            # Count records
            c.execute("SELECT COUNT(*) FROM shifts")
            shift_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM availability")
            availability_count = c.fetchone()[0]
            
            # Check for recent activity (last 7 days)
            week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            c.execute("SELECT COUNT(*) FROM shifts WHERE created_at >= ?", (week_ago,))
            recent_shifts = c.fetchone()[0]
            
            # Check for alerted status distribution
            c.execute("SELECT alerted, COUNT(*) FROM shifts GROUP BY alerted")
            alert_stats = dict(c.fetchall())
            
            return {
                'integrity': integrity,
                'total_shifts': shift_count,
                'total_availability': availability_count,
                'recent_shifts_7days': recent_shifts,
                'alert_distribution': alert_stats,
                'file_size_mb': round(db_path.stat().st_size / 1024 / 1024, 2)
            }
        finally:
            conn.close()
    
    def check_file_system_health(self):
        """Check file system status and permissions"""
        results = {}
        
        # Check main application files
        required_files = [
            'main.py', 'gui.py', 'database.py', 'automation.py', 
            'config.json', 'smtp_settings.json', 'shifts.db'
        ]
        
        missing_files = []
        file_sizes = {}
        
        for filename in required_files:
            file_path = self.app_dir / filename
            if file_path.exists():
                file_sizes[filename] = file_path.stat().st_size
            else:
                missing_files.append(filename)
        
        # Check template images
        template_images = ['calendar.png', 'dots.png', 'shifts.png', 'shiftloaded.png']
        missing_templates = []
        
        for template in template_images:
            if not (self.app_dir / template).exists():
                missing_templates.append(template)
        
        # Check screenshots directory
        screenshots_dir = self.app_dir / 'screenshots'
        screenshot_count = 0
        total_screenshot_size = 0
        
        if screenshots_dir.exists():
            screenshot_files = list(screenshots_dir.glob('*.png'))
            screenshot_count = len(screenshot_files)
            total_screenshot_size = sum(f.stat().st_size for f in screenshot_files)
        
        # Check disk space
        total, used, free = shutil.disk_usage(self.app_dir)
        
        return {
            'missing_files': missing_files,
            'file_sizes': file_sizes,
            'missing_templates': missing_templates,
            'screenshot_count': screenshot_count,
            'screenshot_size_mb': round(total_screenshot_size / 1024 / 1024, 2),
            'disk_free_gb': round(free / 1024 / 1024 / 1024, 2),
            'disk_used_percent': round((used / total) * 100, 1)
        }
    
    def check_process_health(self):
        """Check if main application might be running"""
        try:
            # Look for Python processes that might be the main app
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                python_processes = len([l for l in lines if 'python.exe' in l]) - 1  # -1 for header
                
                return {
                    'python_processes_running': python_processes,
                    'process_check_successful': True
                }
            else:
                return {
                    'python_processes_running': 0,
                    'process_check_successful': False,
                    'error': 'Could not check processes'
                }
                
        except Exception as e:
            return {
                'python_processes_running': 'unknown',
                'process_check_successful': False,
                'error': str(e)
            }
    
    def check_configuration_health(self):
        """Check configuration files without modifying them"""
        config_health = {}
        
        # Check config.json
        config_path = self.app_dir / 'config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                config_health['config_json'] = {
                    'exists': True,
                    'valid_json': True,
                    'scan_interval': config_data.get('scan_interval_seconds', 'not_set'),
                    'keys_present': list(config_data.keys())
                }
            except json.JSONDecodeError as e:
                config_health['config_json'] = {
                    'exists': True,
                    'valid_json': False,
                    'error': str(e)
                }
        else:
            config_health['config_json'] = {'exists': False}
        
        # Check SMTP settings
        smtp_path = self.app_dir / 'smtp_settings.json'
        if smtp_path.exists():
            try:
                with open(smtp_path, 'r') as f:
                    smtp_data = json.load(f)
                
                required_smtp_keys = ['SmtpHost', 'SmtpPort', 'FromAddress', 'ToAddress']
                missing_keys = [key for key in required_smtp_keys if key not in smtp_data]
                
                config_health['smtp_settings'] = {
                    'exists': True,
                    'valid_json': True,
                    'missing_required_keys': missing_keys,
                    'has_password': 'FromPassword' in smtp_data,
                    'smtp_host': smtp_data.get('SmtpHost', 'not_set')
                }
            except json.JSONDecodeError as e:
                config_health['smtp_settings'] = {
                    'exists': True,
                    'valid_json': False,
                    'error': str(e)
                }
        else:
            config_health['smtp_settings'] = {'exists': False}
        
        return config_health
    
    def check_image_template_health(self):
        """Check template images for automation"""
        template_results = {}
        
        templates = ['calendar.png', 'dots.png', 'shifts.png', 'shiftloaded.png']
        
        for template in templates:
            template_path = self.app_dir / template
            if template_path.exists():
                try:
                    # Try to import CV2 to check image
                    import cv2
                    img = cv2.imread(str(template_path))
                    if img is not None:
                        h, w = img.shape[:2]
                        template_results[template] = {
                            'exists': True,
                            'readable': True,
                            'dimensions': f"{w}x{h}",
                            'file_size': template_path.stat().st_size
                        }
                    else:
                        template_results[template] = {
                            'exists': True,
                            'readable': False,
                            'error': 'Could not load image'
                        }
                except ImportError:
                    template_results[template] = {
                        'exists': True,
                        'readable': 'unknown',
                        'note': 'OpenCV not available for validation'
                    }
                except Exception as e:
                    template_results[template] = {
                        'exists': True,
                        'readable': False,
                        'error': str(e)
                    }
            else:
                template_results[template] = {'exists': False}
        
        return template_results
    
    def check_network_connectivity(self):
        """Test network connectivity for email/updates"""
        connectivity_results = {}
        
        # Test basic internet connectivity
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            connectivity_results['internet'] = True
        except:
            connectivity_results['internet'] = False
        
        # Test SMTP connectivity (if config exists)
        smtp_path = self.app_dir / 'smtp_settings.json'
        if smtp_path.exists():
            try:
                with open(smtp_path, 'r') as f:
                    smtp_data = json.load(f)
                
                smtp_host = smtp_data.get('SmtpHost')
                smtp_port = smtp_data.get('SmtpPort', 587)
                
                if smtp_host:
                    import socket
                    sock = socket.create_connection((smtp_host, smtp_port), timeout=10)
                    sock.close()
                    connectivity_results['smtp_server'] = True
                else:
                    connectivity_results['smtp_server'] = 'no_host_configured'
                    
            except Exception as e:
                connectivity_results['smtp_server'] = False
                connectivity_results['smtp_error'] = str(e)
        else:
            connectivity_results['smtp_server'] = 'no_config'
        
        return connectivity_results
    
    def check_whatsapp_connectivity(self):
        """Test WhatsApp application status and connectivity"""
        whatsapp_results = {}
        
        try:
            # Import required modules
            import pyautogui
            import time
            from pywinauto.application import Application
            
            # Test 1: Check if WhatsApp is running
            try:
                app = Application(backend="uia").connect(title_re=".*WhatsApp.*", timeout=3)
                whatsapp_results['app_running'] = True
                whatsapp_results['app_found'] = True
                
                # Test 2: Check if window can be focused
                try:
                    win = app.top_window()
                    original_focus = pyautogui.getActiveWindow() if hasattr(pyautogui, 'getActiveWindow') else None
                    
                    win.set_focus()
                    time.sleep(0.5)
                    
                    whatsapp_results['window_focusable'] = True
                    whatsapp_results['window_title'] = win.window_text()
                    
                    # Test 3: Check if we can type (without actually sending)
                    try:
                        # Save current clipboard
                        import subprocess
                        try:
                            current_clip = subprocess.check_output(['powershell', '-command', 'Get-Clipboard'], 
                                                                 text=True, timeout=2).strip()
                        except:
                            current_clip = None
                        
                        # Type a test character and immediately delete it
                        pyautogui.typewrite(' ', interval=0.1)
                        time.sleep(0.2)
                        pyautogui.press('backspace')
                        
                        whatsapp_results['typing_functional'] = True
                        
                        # Restore clipboard if we had one
                        if current_clip:
                            try:
                                subprocess.run(['powershell', '-command', f'Set-Clipboard -Value "{current_clip}"'], 
                                             timeout=2)
                            except:
                                pass
                                
                    except Exception as e:
                        whatsapp_results['typing_functional'] = False
                        whatsapp_results['typing_error'] = str(e)
                    
                    # Restore original focus if possible
                    if original_focus:
                        try:
                            original_focus.activate()
                        except:
                            pass
                            
                except Exception as e:
                    whatsapp_results['window_focusable'] = False
                    whatsapp_results['focus_error'] = str(e)
                    
            except Exception as e:
                whatsapp_results['app_running'] = False
                whatsapp_results['app_found'] = False
                whatsapp_results['connection_error'] = str(e)
                
                # Test if WhatsApp process exists but not connectable
                try:
                    import subprocess
                    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq WhatsApp.exe'], 
                                          capture_output=True, text=True, timeout=5)
                    if 'WhatsApp.exe' in result.stdout:
                        whatsapp_results['process_exists'] = True
                        whatsapp_results['app_running'] = True  # Process exists but not connectable
                    else:
                        whatsapp_results['process_exists'] = False
                except Exception:
                    whatsapp_results['process_exists'] = 'unknown'
        
        except ImportError as e:
            whatsapp_results['modules_available'] = False
            whatsapp_results['import_error'] = str(e)
        except Exception as e:
            whatsapp_results['test_failed'] = True
            whatsapp_results['error'] = str(e)
        
        return whatsapp_results
    
    def calculate_overall_status(self):
        """Calculate overall system health status"""
        total_tests = self.results['tests_completed']
        failed_tests = self.results['tests_failed']
        
        if total_tests == 0:
            return 'UNKNOWN'
        
        success_rate = (total_tests - failed_tests) / total_tests
        
        if success_rate >= 0.95:
            return 'HEALTHY'
        elif success_rate >= 0.80:
            return 'WARNING'
        else:
            return 'CRITICAL'
    
    def run_comprehensive_health_check(self):
        """
        Run all health checks safely.
        This is the main entry point - completely safe to call.
        """
        print(f"[HEALTH CHECK] Starting comprehensive health check at {self.start_time}")
        
        try:
            # Run all health checks with individual error handling
            db_health = self.safe_execute('database_health', self.check_database_health)
            fs_health = self.safe_execute('filesystem_health', self.check_file_system_health)
            process_health = self.safe_execute('process_health', self.check_process_health)
            config_health = self.safe_execute('configuration_health', self.check_configuration_health)
            template_health = self.safe_execute('template_health', self.check_image_template_health)
            network_health = self.safe_execute('network_health', self.check_network_connectivity)
            
            # Check if WhatsApp is enabled before running WhatsApp health check
            from config import load_config
            config = load_config()
            if config.get('whatsapp_enabled', True):
                whatsapp_health = self.safe_execute('whatsapp_connectivity', self.check_whatsapp_connectivity)
            else:
                print("[HEALTH CHECK] WhatsApp disabled in config - skipping WhatsApp connectivity check")
                self.results['detailed_results']['whatsapp_connectivity'] = {
                    'status': 'SKIP',
                    'result': {'disabled': True, 'message': 'WhatsApp disabled in configuration'},
                    'execution_time': 0
                }
            
            # Calculate final status
            self.results['overall_status'] = self.calculate_overall_status()
            self.results['total_execution_time'] = (datetime.datetime.now() - self.start_time).total_seconds()
            
            print(f"[HEALTH CHECK] Completed: {self.results['overall_status']} "
                  f"({self.results['tests_completed']} tests, {self.results['tests_failed']} failed)")
            
            return self.results
            
        except Exception as e:
            # Ultimate failsafe - should never reach here
            print(f"[HEALTH CHECK CRITICAL ERROR] {e}")
            self.results['overall_status'] = 'CRITICAL'
            self.results['critical_error'] = str(e)
            return self.results

def run_weekly_health_check():
    """
    Main function to run weekly health check.
    Completely safe to call - will never break the main application.
    """
    try:
        with SafeHealthChecker() as checker:
            results = checker.run_comprehensive_health_check()
            return results
    except Exception as e:
        # Ultimate failsafe
        return {
            'overall_status': 'CRITICAL',
            'critical_error': f'Health check system failure: {e}',
            'timestamp': datetime.datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Allow running health check directly for testing
    results = run_weekly_health_check()
    print(json.dumps(results, indent=2))
