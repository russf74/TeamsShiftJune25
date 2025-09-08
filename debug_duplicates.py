#!/usr/bin/env python3

from database import *
import sqlite3

def check_recent_changes():
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    # Check for any September 12th entries with recent timestamps
    c.execute("SELECT * FROM shifts WHERE date LIKE '%-09-12' ORDER BY id")
    all_sept12 = c.fetchall()
    
    print("=== ALL September 12th entries (chronological) ===")
    for entry in all_sept12:
        print(f"  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Alerted: {entry[3]}, Count: {entry[4]}, Added: {entry[6]}")
    
    # Check if there are duplicate entries
    if len(all_sept12) > 1:
        print(f"\n*** WARNING: Found {len(all_sept12)} entries for September 12th! ***")
        
        # Check if any have alerted=0
        unalerted = [e for e in all_sept12 if e[3] == 0]  # alerted column
        if unalerted:
            print("*** FOUND UNALERTED DUPLICATES: ***")
            for entry in unalerted:
                print(f"  UNALERTED: {entry}")
    
    # Check recent database activity (last few entries)
    print("\n=== Last 10 database entries ===")
    c.execute("SELECT * FROM shifts ORDER BY id DESC LIMIT 10")
    recent = c.fetchall()
    for entry in recent:
        print(f"  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Alerted: {entry[3]}, Added: {entry[6]}")
    
    conn.close()

if __name__ == "__main__":
    check_recent_changes()
