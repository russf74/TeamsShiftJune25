#!/usr/bin/env python3

from health_check import SafeHealthChecker

def test_health_checks():
    print("Testing Enhanced Health Check System")
    print("=" * 50)
    
    checker = SafeHealthChecker()
    results = checker.run_comprehensive_health_check()
    
    print('Health Check Results:')
    for category, result in results.items():
        status = '✅' if result['status'] == 'OK' else '❌' if result['status'] == 'ERROR' else '⚠️'
        print(f'{status} {category}: {result["message"]}')
    
    print("\n" + "=" * 50)
    print("Health check test completed!")

if __name__ == "__main__":
    test_health_checks()
