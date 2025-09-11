#!/usr/bin/env python3
"""
Autonomous GitHub commit script
Handles staging, committing, and pushing changes with proper error handling
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def main():
    print("=== AUTONOMOUS GITHUB COMMIT SCRIPT ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check git status
    if not run_command("git status --porcelain", "Checking git status"):
        return False
    
    # Check if there are changes to commit
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("ℹ️  No changes to commit - repository is clean")
        return True
    
    print(f"\nChanges detected:")
    changes = result.stdout.strip().split('\n')
    for change in changes[:10]:  # Show first 10 changes
        print(f"   {change}")
    if len(changes) > 10:
        print(f"   ... and {len(changes) - 10} more changes")
    
    # Stage all changes (excluding sensitive files via .gitignore)
    if not run_command("git add .", "Staging changes"):
        return False
    
    # Generate commit message based on recent changes
    commit_msg = f"Enhanced shift conflict resolution and cleanup system\n\n- Added conflict prevention for open/booked shifts on same date\n- Implemented stale booked shift cleanup when cancelled\n- Enhanced email safety to prevent conflicting notifications\n- Added dual tracking for open and booked shifts\n- Comprehensive testing and validation\n\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Commit changes
    commit_cmd = f'git commit -m "{commit_msg}"'
    if not run_command(commit_cmd, "Committing changes"):
        return False
    
    # Push to remote
    if not run_command("git push origin HEAD", "Pushing to GitHub"):
        return False
    
    print("\n🎉 SUCCESS! All changes committed and pushed to GitHub")
    print("✅ Repository is now synchronized")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💥 COMMIT FAILED - Please check errors above")
        sys.exit(1)
    else:
        print("\n🚀 COMMIT COMPLETED SUCCESSFULLY")
        sys.exit(0)